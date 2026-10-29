# %%
from __future__ import annotations
import calendar
import math
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from Factors import *

ANOMALOUS = False
if ANOMALOUS:
    DEMAND_MODEL_PARAMS = DEMAND_MODEL_PARAMS_A

# %%
SIM_CONFIG = {
    "timestep_minutes": 5,
    "sensor_interval_minutes": 15,
    "extra_event_prob": 0.15,
    "max_events_per_day": 2,
}


@dataclass
class DrainConfig:
    name: str = "Manhole_1"
    catchment_area_m2: float = 12000.0
    runoff_coefficient: float = 0.75
    base_sewage_lps: float = 6.0
    pipe_capacity_lps: float = 350.0
    max_level_cm: float = 100.0
    level_time_constant_min: float = 6.0
    sensor_noise_std_cm: float = 0.15
    flow_noise_frac: float = 0.02

# %% [markdown]
# ### RainFall

# %%
_MONTH_NAMES = list(calendar.month_name)[1:]


def _days_in_month_name(month: str, year: int = 2023) -> int:
    idx = _MONTH_NAMES.index(month) + 1
    return calendar.monthrange(year, idx)[1]


def classify_event_size(total_mm: float) -> str:
    if total_mm < EVENT_SIZE_CLASSES["light"]["range_mm"][0]:
        return "light"
    for cls, spec in EVENT_SIZE_CLASSES.items():
        lo, hi = spec["range_mm"]
        if hi is None:
            if total_mm >= lo:
                return cls
        elif lo <= total_mm < hi:
            return cls
    return "extreme"


def generate_single_event(month: str, rng: random.Random, apply_calibration: bool = True) -> dict:
    season = MONTH_TO_SEASON[month]
    md = MONTHLY_DATA[month]

    dist = EVENT_DURATION_DISTRIBUTION[season]
    buckets, wts = zip(*dist.items())
    b = rng.choices(buckets, weights=wts, k=1)[0]
    lo, hi = DURATION_BUCKET_HOURS[b]
    dur = rng.uniform(lo, hi)

    ilo, ihi = md["intensity_range_mmph"]
    ityp = md["intensity_typical_mmph"]
    r = rng.random()
    idist = EVENT_INTENSITY_DISTRIBUTION_WITHIN_CLASS
    if r < idist["lower_half_pct"]:
        avgi = rng.uniform(ilo, ityp)
    elif r < idist["lower_half_pct"] + idist["upper_half_pct"]:
        avgi = rng.uniform(ityp, ihi)
    else:
        avgi = rng.uniform(ihi, ihi * 1.6)

    tot = avgi * dur
    evcls = classify_event_size(tot)

    prof = rng.choices(
        list(STORM_PROFILE_WEIGHTS.keys()),
        weights=list(STORM_PROFILE_WEIGHTS.values()), k=1,
    )[0]
    base = np.array(STORM_PROFILES[prof], dtype=float)

    plo, phi = PEAK_MULTIPLIER_BY_EVENT_CLASS[evcls]
    pk = rng.uniform(plo, phi)
    scaled = base * (pk / base.max())
    # shape = scaled / scaled.sum()  # used sum() here originally, broke avg intensity
    shp = scaled / scaled.mean()

    nseg = len(shp)
    sdur = dur / nseg
    segmm = shp * avgi * sdur

    if apply_calibration:
        fac = RAIN_CALIBRATION_FACTORS.get(month, 1.0)
        segmm = segmm * fac

    return {
        "duration_hr": dur,
        "avg_intensity_mmph": avgi,
        "event_class": evcls,
        "profile_name": prof,
        "seg_duration_hr": sdur,
        "seg_mm": segmm,
        "total_mm": float(segmm.sum()),
    }


def generate_rain_day_events(month: str, rng: random.Random) -> List[dict]:
    p = MONTHLY_DATA[month]["rain_prob_pct"] / 100.0
    if rng.random() >= p:
        return []

    evs = [generate_single_event(month, rng)]
    if SIM_CONFIG["max_events_per_day"] > 1 and rng.random() < SIM_CONFIG["extra_event_prob"]:
        evs.append(generate_single_event(month, rng))

    for ev in evs:
        ev["start_min_of_day"] = rng.uniform(0, 24 * 60 - 1)
    return evs


def _expected_mm_per_event(month: str, n_samples: int = 800, seed: int = 12345) -> float:
    rng = random.Random(seed)
    tot = sum(
        generate_single_event(month, rng, apply_calibration=False)["total_mm"]
        for _ in range(n_samples)
    )
    return tot / n_samples


def _build_calibration_factors() -> Dict[str, float]:
    out = {}
    for mon, md in MONTHLY_DATA.items():
        ndays = _days_in_month_name(mon)
        p = md["rain_prob_pct"] / 100.0
        eve = 1.0 + SIM_CONFIG["extra_event_prob"]
        mpe = _expected_mm_per_event(mon)
        exp_tot = ndays * p * eve * mpe
        tgt = md["total_rainfall_mm"]
        out[mon] = (tgt / exp_tot) if exp_tot > 1e-6 else 1.0
    return out


RAIN_CALIBRATION_FACTORS = _build_calibration_factors()


def _accumulate(grid: np.ndarray, seg_start_min: float, seg_end_min: float,
                 seg_mm: float, step_min: float) -> None:
    if seg_mm <= 0:
        return
    slen = seg_end_min - seg_start_min
    if slen <= 0:
        return
    n = len(grid)
    i0 = int(seg_start_min // step_min)
    i1 = int(math.ceil(seg_end_min / step_min)) - 1
    if i1 < 0 or i0 >= n:
        return
    i0, i1 = max(i0, 0), min(i1, n - 1)
    for i in range(i0, i1 + 1):
        c0, c1 = i * step_min, (i + 1) * step_min
        ov = min(seg_end_min, c1) - max(seg_start_min, c0)
        if ov > 0:
            grid[i] += seg_mm * (ov / slen)


class RainfallEngine:
    def __init__(self, timestep_minutes: int):
        self.step = timestep_minutes

    def simulate(self, start_date, n_days: int, rng: random.Random) -> Tuple[np.ndarray, List[dict]]:
        nst = int(round(n_days * 24 * 60 / self.step))
        rain = np.zeros(nst, dtype=float)
        log: List[dict] = []
        t0 = pd.Timestamp(start_date)

        for day in range(n_days):
            dt = t0 + pd.Timedelta(days=day)
            mon = dt.month_name()
            dstart = day * 24 * 60

            for ev in generate_rain_day_events(mon, rng):
                estart = dstart + ev["start_min_of_day"]
                sdm = ev["seg_duration_hr"] * 60
                for i, mm in enumerate(ev["seg_mm"]):
                    s0 = estart + i * sdm
                    s1 = s0 + sdm
                    _accumulate(rain, s0, s1, mm, self.step)

                log.append({
                    "date": dt.date(), "month": mon, "season": MONTH_TO_SEASON[mon],
                    "start_min_of_sim": estart, "duration_hr": ev["duration_hr"],
                    "avg_intensity_mmph": ev["avg_intensity_mmph"],
                    "total_mm": ev["total_mm"], "event_class": ev["event_class"],
                    "profile": ev["profile_name"],
                })

        return rain, log

# %% [markdown]
# ### Environment

# %%
class EnvironmentEngine:
    def __init__(self, np_rng: np.random.Generator):
        self.np_rng = np_rng

    def simulate(self, idx: pd.DatetimeIndex, rain: np.ndarray) -> pd.DataFrame:
        n = len(idx)
        hr = idx.hour.values + idx.minute.values / 60.0
        mons = idx.month_name()
        seas = mons.map(MONTH_TO_SEASON)

        tmean = mons.map(lambda m: MONTHLY_CLIMATE[m]["temp_c_mean"]).values.astype(float)
        trange = mons.map(lambda m: MONTHLY_CLIMATE[m]["temp_c_range"]).values.astype(float)
        rhmean = mons.map(lambda m: MONTHLY_CLIMATE[m]["rh_pct_mean"]).values.astype(float)
        rhrange = mons.map(lambda m: MONTHLY_CLIMATE[m]["rh_pct_range"]).values.astype(float)

        ph = 2 * np.pi * (hr - 15.0) / 24.0
        # tc = tmean + trange * np.cos(ph)  # flat, no jitter, looked fake
        tc = tmean + trange * np.cos(ph) + self.np_rng.normal(0, 0.3, n)
        rhb = rhmean - rhrange * np.cos(ph)

        wx = self._weather_states(idx, rain)
        rha = np.array([WEATHER_RH_ADJUSTMENT[w] for w in wx])
        rh = np.clip(rhb + rha, *CLIMATE_REFERENCE["rh_pct_clip"])

        ref = CLIMATE_REFERENCE
        ft = np.clip(1.0 + (tc - ref["temp_c_ref"]) / ref["temp_c_span"], *ref["F_temp_clamp"])
        fh = np.clip(
            1.0 - (rh - ref["rh_pct_ref"]) / ref["rh_pct_span"] * ref["rh_pct_effect"],
            *ref["F_rh_clamp"])
        fs = seas.map(F_SEASON_BY_KEY).values.astype(float)
        fw = np.array([WEATHER_STATES[w]["F_weather"] for w in wx])

        E = np.clip(ft * fh * fs * fw, *ref["E_clamp"])

        return pd.DataFrame({
            "month": mons.values, "season": seas.values,
            "temp_c": tc, "rh_pct": rh, "weather_state": wx,
            "F_temperature": ft, "F_humidity": fh,
            "F_season": fs, "F_weather": fw, "E": E,
        }, index=idx)

    def _weather_states(self, idx: pd.DatetimeIndex, rain: np.ndarray) -> np.ndarray:
        n = len(idx)
        st = np.empty(n, dtype=object)
        wet = rain > 1e-4

        conds = [
            rain <= 1.0,
            rain <= 4.0,
            rain <= 10.0,
            rain > 10.0,
        ]
        opts = ["drizzle", "light_rain", "moderate_rain", "heavy_rain"]
        rst = np.select(conds, opts, default="light_rain")
        st[wet] = rst[wet]

        dayo = idx.floor("D")
        udays = dayo.unique()
        dkeys = list(DRY_WEATHER_MIX.keys())
        dprobs = list(DRY_WEATHER_MIX.values())
        dchoice = {d: self.np_rng.choice(dkeys, p=dprobs) for d in udays}
        dst = dayo.map(dchoice).values
        st[~wet] = dst[~wet]
        return st

# %%
class DemandEngine:
    @staticmethod
    def q_base(hr: np.ndarray) -> np.ndarray:
        p = DEMAND_MODEL_PARAMS
        m = p["A1"] * np.exp(-((hr - p["mu1"]) ** 2) / (2 * p["sigma1"] ** 2))
        e = p["A2"] * np.exp(-((hr - p["mu2"]) ** 2) / (2 * p["sigma2"] ** 2))
        raw = p["B"] + m + e
        return raw / NORMALIZATION_CONSTANT

    @classmethod
    def demand_index(cls, hr: np.ndarray, E: np.ndarray) -> np.ndarray:
        return E * cls.q_base(hr)


# %%
class DrainSimulator:
    def __init__(self, drain: DrainConfig, timestep_minutes: int, rng_seed: Optional[int] = None):
        self.drain = drain
        self.timestep_minutes = timestep_minutes
        self.np_rng = np.random.default_rng(rng_seed)

    def simulate(self, idx: pd.DatetimeIndex, rain: np.ndarray,
                 dem: np.ndarray) -> pd.DataFrame:
        n = len(idx)
        d = self.drain

        runoff = rain * d.catchment_area_m2 * d.runoff_coefficient / 3600.0
        sewage = d.base_sewage_lps * dem
        noise = self.np_rng.normal(0, d.flow_noise_frac * d.base_sewage_lps, n)
        inflow = np.clip(runoff + sewage + noise, 0, None)

        s = pd.Series(inflow, index=idx)
        # sm = s.rolling(5).mean()  # too laggy, switched to ewm below
        sm = s.ewm(halflife=pd.Timedelta(minutes=d.level_time_constant_min), times=idx).mean()

        lvl = d.max_level_cm * (1.0 - np.exp(-sm.values / d.pipe_capacity_lps))
        sn = self.np_rng.normal(0, d.sensor_noise_std_cm, n)
        lvl = np.clip(lvl + sn, 0, d.max_level_cm)

        return pd.DataFrame({
            "inflow_lps": inflow,
            "smoothed_flow_lps": sm.values,
            "level_cm": lvl,
        }, index=idx)

# %%
def run_simulation(
    start_date: str = "2024-01-01",
    n_days: int = 365,
    drain: Optional[DrainConfig] = None,
    timestep_minutes: int = SIM_CONFIG["timestep_minutes"],
    sensor_interval_minutes: int = SIM_CONFIG["sensor_interval_minutes"],
    seed: Optional[int] = None,
):
    rng = random.Random(seed)
    se = None if seed is None else seed + 1
    sd = None if seed is None else seed + 2

    idx = pd.date_range(
        start=start_date,
        periods=int(round(n_days * 24 * 60 / timestep_minutes)),
        freq=f"{timestep_minutes}min",
    )

    rgen = RainfallEngine(timestep_minutes)
    rain, evlog = rgen.simulate(start_date, n_days, rng)
    rint = rain / (timestep_minutes / 60.0)

    egen = EnvironmentEngine(np.random.default_rng(se))
    env = egen.simulate(idx, rint)

    hr = idx.hour.values + idx.minute.values / 60.0
    dem = DemandEngine.demand_index(hr, env["E"].values)

    if drain is None:
        drain = DrainConfig()
    dsim = DrainSimulator(drain, timestep_minutes, rng_seed=sd)
    hyd = dsim.simulate(idx, rint, dem)

    df = env.copy()
    df["rain_mm"] = rain
    df["rain_intensity_mmph"] = rint
    df["demand_index"] = dem
    df = pd.concat([df, hyd], axis=1)
    df.index.name = "timestamp"

    if sensor_interval_minutes > timestep_minutes:
        ratio = sensor_interval_minutes // timestep_minutes
        out = df.iloc[::ratio].copy()
    else:
        out = df

    hr2 = out.index.hour + out.index.minute / 60.0
    out["hour_sin"] = np.sin(2 * np.pi * hr2 / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hr2 / 24)
    out["month_sin"] = np.sin(2 * np.pi * out.index.month / 12)
    out["month_cos"] = np.cos(2 * np.pi * out.index.month / 12)

    for sname in ["winter", "pre_monsoon", "monsoon", "post_monsoon"]:
        out[f"season_{sname}"] = (out["season"] == sname).astype(int)

    for w in ["clear", "cloudy", "drizzle", "light_rain", "moderate_rain", "heavy_rain"]:
        out[f"weather_state_{w}"] = (out["weather_state"] == w).astype(int)

    features = [
        'temp_c', 'rh_pct', 'rain_mm', 'rain_intensity_mmph', 'demand_index', 'inflow_lps', 'smoothed_flow_lps', 'level_cm','season','weather_state',
        'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'season_winter', 'season_pre_monsoon', 'season_monsoon', 'season_post_monsoon',
        'weather_state_clear', 'weather_state_cloudy', 'weather_state_drizzle', 'weather_state_light_rain', 'weather_state_moderate_rain', 'weather_state_heavy_rain'
    ]
    out = out[features]

    evdf = pd.DataFrame(evlog)
    return out, evdf

# %%
if __name__ == "__main__":
    t0 = time.perf_counter()

    drn = DrainConfig(name="Manhole_1")
    readings, events = run_simulation(
        start_date="2026-01-01",
        n_days=365 * 1,
        timestep_minutes=5,
        sensor_interval_minutes=60,
        seed=None,
    )

    dt_elapsed = time.perf_counter() - t0
    print(f"Simulated 1 drain, {len(readings):,} sensor readings in {dt_elapsed:.2f}s")
    print(f"Generated {len(events)} rain events")

    monthly_check = events.groupby("month")["total_mm"].sum().reindex(MONTHLY_DATA.keys())
    print("\nSimulated vs. reference monthly rainfall totals (mm):")
    for mon in MONTHLY_DATA:
        sim_val = monthly_check.get(mon, 0.0)
        ref_val = MONTHLY_DATA[mon]["total_rainfall_mm"]
        print(f"  {mon:<10s} sim={sim_val:7.1f}  ref={ref_val:7.1f}")

    print("\nSample readings:")
    print(readings.head(10))

    readings.to_csv("Validation_Threshold_single_drain_readings.csv")
    print("\nSaved: single_drain_readings.csv, single_drain_rain_events.csv")