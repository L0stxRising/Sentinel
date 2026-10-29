import calendar,math,random,time
from dataclasses import dataclass
import numpy as np
import pandas as pd

from Factors import *
# from Factors import DEMAND_MODEL_PARAMS_A

ANOMALOUS=False
if ANOMALOUS:
    DEMAND_MODEL_PARAMS=DEMAND_MODEL_PARAMS_A


SIM_CONFIG={
    "timestep_minutes":5,
    "sensor_interval_minutes":15,
    "extra_event_prob":0.15,
    "max_events_per_day":2,
}
# def_cfg = SIM_CONFIG.copy()


@dataclass
class DrainConfig:
    name:str="Manhole_1"
    catchment_area_m2:float=12000.0
    runoff_coefficient:float=0.75
    base_sewage_lps:float=6.0
    pipe_capacity_lps:float=350.0
    max_level_cm:float=100.0
    level_time_constant_min:float=6.0
    sensor_noise_std_cm:float=0.15
    flow_noise_frac:float=0.02


# class PipeFlowModel:
#     def __init__(self, dia=1.2, s=0.002, rough=0.013):
#         self.dia = dia
#         self.s = s
#         self.n = rough
#         self.vol = 0.0
#
#     def step(self, q_lps, dt):
#         q_m3s = q_lps / 1000.0
#         y = max(0.001, min(self.dia, self.vol / 12.0))
#         theta = 2 * math.acos(1 - 2 * (y / self.dia))
#         a = (self.dia**2 / 8) * (theta - math.sin(theta))
#         p = self.dia * theta / 2
#         rh = a / p if p > 0 else 0
#         v = (1 / self.n) * (rh**(2/3)) * (self.s**0.5)
#         outflow = a * v * 1000.0
#         self.vol += (q_lps - outflow) * (dt * 60)
#         self.vol = max(0.0, self.vol)
#         return (self.vol / (math.pi * (self.dia/2)**2 * 10.0)) * 100



month_names=list(calendar.month_name)[1:]

def get_days_in_m(m_str,yr=2023):
    m_idx=month_names.index(m_str)+1
    return calendar.monthrange(yr,m_idx)[1]


def cat_event(tot_rain):
    if tot_rain<EVENT_SIZE_CLASSES["light"]["range_mm"][0]:
        return "light"
    for c_name,spec in EVENT_SIZE_CLASSES.items():
        lo,hi=spec["range_mm"]
        if hi is None:
            if tot_rain>=lo: return c_name
        elif lo<=tot_rain<hi:
            return c_name
    
    # if tot_rain > 120.0: return 'extreme'
    return "extreme"


def make_event(m_str,rng,do_calib=True):
    szn=MONTH_TO_SEASON[m_str]
    m_dat=MONTHLY_DATA[m_str]

    dur_dist=EVENT_DURATION_DISTRIBUTION[szn]
    bkts,w_list=zip(*dur_dist.items())
    
    
    picked_bkt=rng.choices(bkts,weights=w_list,k=1)[0]
    lo_h,hi_h=DURATION_BUCKET_HOURS[picked_bkt]
    dur=rng.uniform(lo_h,hi_h)

    ilo,ihi=m_dat["intensity_range_mmph"]
    ityp=m_dat["intensity_typical_mmph"]
    r_val=rng.random()
    
    idist=EVENT_INTENSITY_DISTRIBUTION_WITHIN_CLASS
    
    if r_val<idist["lower_half_pct"]:
        avg_i=rng.uniform(ilo,ityp)
    elif r_val<idist["lower_half_pct"]+idist["upper_half_pct"]:
        avg_i=rng.uniform(ityp,ihi)
    else:
        avg_i=rng.uniform(ihi,ihi*1.6)

    # if r_val < 0.6:
    #     avg_i = ilo + (ityp - ilo) * rng.random()
    # else:
    #     avg_i = ityp + (ihi - ityp) * rng.random()
    # tot = avg_i * dur

    tot=avg_i*dur
    # print("tot mm:", tot)
    ev_cls=cat_event(tot)

    # prof = rng.choice(list(STORM_PROFILE_WEIGHTS.keys()))
    prof=rng.choices(list(STORM_PROFILE_WEIGHTS.keys()),weights=list(STORM_PROFILE_WEIGHTS.values()),k=1)[0]
    p_arr=np.array(STORM_PROFILES[prof],dtype=float)

    p_min,p_max=PEAK_MULTIPLIER_BY_EVENT_CLASS[ev_cls]
    pk=rng.uniform(p_min,p_max)
    sc=p_arr*(pk/p_arr.max())
    
    # shp = sc / sc.sum()
    shp=sc/sc.mean()

    n_segs=len(shp)
    seg_dur=dur/n_segs
    seg_rain=shp*avg_i*seg_dur

    if do_calib:
        c_fac=RAIN_CALIBRATION_FACTORS.get(m_str,1.0)
        seg_rain=seg_rain*c_fac

    return {
        "duration_hr":dur,
        "avg_intensity_mmph":avg_i,
        "event_class":ev_cls,
        "profile_name":prof,
        "seg_duration_hr":seg_dur,
        "seg_mm":seg_rain,
        "total_mm":float(seg_rain.sum()),
    }



def get_day_rain(m_str,rng):
    p=MONTHLY_DATA[m_str]["rain_prob_pct"]/100.0
    if rng.random()>=p:
        return []

    evs=[make_event(m_str,rng)]
    if SIM_CONFIG["max_events_per_day"]>1 and rng.random()<SIM_CONFIG["extra_event_prob"]:
        evs.append(make_event(m_str,rng))

    # if len(evs) > 2: evs = evs[:2]
    # print("rain events count:", len(evs))
    for ev in evs:
        ev["start_min_of_day"]=rng.uniform(0,24*60-1)
    return evs




def calc_expected_rain(m_str,n_runs=800,seed=12345):
    rnd=random.Random(seed)
    # tot_val = 0.0
    # for _ in range(n_runs):
    #     tot_val += make_event(m_str, rnd, do_calib=False)["total_mm"]
    # return tot_val / n_runs
    
    tot_val=sum(make_event(m_str,rnd,do_calib=False)["total_mm"] for _ in range(n_runs))
    return tot_val/n_runs


def init_calib_map():
    calib_map={}
    for m_name,m_spec in MONTHLY_DATA.items():
        n_days=get_days_in_m(m_name)
        p=m_spec["rain_prob_pct"]/100.0
        
        e_fac=1.0+SIM_CONFIG["extra_event_prob"]
        m_exp=calc_expected_rain(m_name)
        tot_exp=n_days*p*e_fac*m_exp
        
        
        tgt=m_spec["total_rainfall_mm"]
        calib_map[m_name]=(tgt/tot_exp) if tot_exp>1e-6 else 1.0
        
    return calib_map

RAIN_CALIBRATION_FACTORS=init_calib_map()




def acc_rain(arr,s0,s1,mm,dt):
    if mm<=0:
        return
    
    seg_len=s1-s0
    
    if seg_len<=0:
        return
    
    n_pts=len(arr)
    idx0=int(s0//dt)
    idx1=int(math.ceil(s1/dt))-1
    
    if idx1<0 or idx0>=n_pts: 
        return
    idx0,idx1=max(idx0,0),min(idx1,n_pts-1)

    # for j in range(len(arr)):
    #     t_a, t_b = j * dt, (j + 1) * dt
    #     if s0 < t_b and s1 > t_a:
    #         arr[j] += mm * ((min(s1, t_b) - max(s0, t_a)) / seg_len)

    for i in range(idx0,idx1+1):
        c0,c1=i*dt,(i+1)*dt
        ov=min(s1,c1)-max(s0,c0)
        if ov>0:
            arr[i]+=mm*(ov/seg_len)




class RainfallEngine:
    def __init__(self,timestep_minutes):
        self.step=timestep_minutes

    def simulate(self,start_date,n_days,rng):
        n_steps=int(round(n_days*24*60/self.step))
        rain_arr=np.zeros(n_steps,dtype=float)
        
        
        ev_log=[]
        t0=pd.Timestamp(start_date)

        for d_idx in range(n_days):
            cur_dt=t0+pd.Timedelta(days=d_idx)
            m_name=cur_dt.month_name()
            d_start=d_idx*24*60

            # day_evs = get_day_rain(m_name, rng)
            # if not day_evs: continue
            for ev in get_day_rain(m_name,rng):
                ev_start=d_start+ev["start_min_of_day"]
                seg_m=ev["seg_duration_hr"]*60
                for seg_i,seg_val in enumerate(ev["seg_mm"]):
                    t_a=ev_start+seg_i*seg_m
                    t_b=t_a+seg_m
                    acc_rain(rain_arr,t_a,t_b,seg_val,self.step)

                ev_log.append({
                    "date":cur_dt.date(),"month":m_name,"season":MONTH_TO_SEASON[m_name],
                    "start_min_of_sim":ev_start,"duration_hr":ev["duration_hr"],
                    "avg_intensity_mmph":ev["avg_intensity_mmph"],
                    "total_mm":ev["total_mm"],"event_class":ev["event_class"],
                    "profile":ev["profile_name"]
                })
            # print("day", d_idx, "rain done")

        return rain_arr,ev_log




class EnvironmentEngine:
    def __init__(self,np_rng):
        self.np_rng=np_rng

    def simulate(self,idx,rain):
        n_pts=len(idx)
        
        h_float=idx.hour.values+idx.minute.values/60.0
        m_series=idx.month_name()
        s_series=m_series.map(MONTH_TO_SEASON)


        t_mean=m_series.map(lambda m: MONTHLY_CLIMATE[m]["temp_c_mean"]).values.astype(float)
        t_span=m_series.map(lambda m: MONTHLY_CLIMATE[m]["temp_c_range"]).values.astype(float)
        rh_mean=m_series.map(lambda m: MONTHLY_CLIMATE[m]["rh_pct_mean"]).values.astype(float)
        rh_span=m_series.map(lambda m: MONTHLY_CLIMATE[m]["rh_pct_range"]).values.astype(float)

        ph=2*np.pi*(h_float-15.0)/24.0
        # tc = t_mean + t_span * np.cos(ph)
        
        tc=t_mean+t_span*np.cos(ph)+self.np_rng.normal(0,0.3,n_pts)
        rh_base=rh_mean-rh_span*np.cos(ph)

        wx_arr=self.get_wx(idx,rain)
        rh_adj=np.array([WEATHER_RH_ADJUSTMENT[w] for w in wx_arr])
        rh_clipped=np.clip(rh_base+rh_adj,*CLIMATE_REFERENCE["rh_pct_clip"])

        ref=CLIMATE_REFERENCE
        f_temp=np.clip(1.0+(tc-ref["temp_c_ref"])/ref["temp_c_span"],*ref["F_temp_clamp"])
        f_rh=np.clip(1.0-(rh_clipped-ref["rh_pct_ref"])/ref["rh_pct_span"]*ref["rh_pct_effect"],*ref["F_rh_clamp"])
        
        f_szn=s_series.map(F_SEASON_BY_KEY).values.astype(float)
        f_wx=np.array([WEATHER_STATES[w]["F_weather"] for w in wx_arr])

        e_idx=np.clip(f_temp*f_rh*f_szn*f_wx,*ref["E_clamp"])

        return pd.DataFrame({
            "month":m_series.values,"season":s_series.values,
            "temp_c":tc,"rh_pct":rh_clipped,"weather_state":wx_arr,
            "F_temperature":f_temp,"F_humidity":f_rh,
            "F_season":f_szn,"F_weather":f_wx,"E":e_idx,
        },index=idx)

    def get_wx(self,idx,rain):
        n_pts=len(idx)
        st_arr=np.empty(n_pts,dtype=object)
        wet_mask=rain>1e-4

        c_list=[
            rain<=1.0,
            rain<=4.0,
            rain<=10.0,
            rain>10.0,
        ]
        lbls=["drizzle","light_rain","moderate_rain","heavy_rain"]
        r_chosen=np.select(c_list,lbls,default="light_rain")
        st_arr[wet_mask]=r_chosen[wet_mask]

        day_floors=idx.floor("D")
        uniq_days=day_floors.unique()
        
        d_keys=list(DRY_WEATHER_MIX.keys())
        d_probs=list(DRY_WEATHER_MIX.values())
        
        day_pick={d:self.np_rng.choice(d_keys,p=d_probs) for d in uniq_days}
        dry_vals=day_floors.map(day_pick).values
        st_arr[~wet_mask]=dry_vals[~wet_mask]
        
        return st_arr




class DemandEngine:
    @staticmethod
    def q_base(h):
        p=DEMAND_MODEL_PARAMS
        m_peak=p["A1"]*np.exp(-((h-p["mu1"])**2)/(2*p["sigma1"]**2))
        e_peak=p["A2"]*np.exp(-((h-p["mu2"])**2)/(2*p["sigma2"]**2))
        
        
        raw_q=p["B"]+m_peak+e_peak
        return raw_q/NORMALIZATION_CONSTANT

    @classmethod
    def demand_index(cls,h,E):
        return E*cls.q_base(h)




class DrainSimulator:
    def __init__(self,drain,timestep_minutes,rng_seed=None):
        self.drain=drain
        self.timestep_minutes=timestep_minutes
        self.np_rng=np.random.default_rng(rng_seed)

    def simulate(self,idx,rain,dem):
        n_pts=len(idx)
        d=self.drain

        q_runoff=rain*d.catchment_area_m2*d.runoff_coefficient/3600.0
        q_sew=d.base_sewage_lps*dem
        
        ns=self.np_rng.normal(0,d.flow_noise_frac*d.base_sewage_lps,n_pts)
        q_in=np.clip(q_runoff+q_sew+ns,0,None)

        flow_s=pd.Series(q_in,index=idx)
        # sm_flow = flow_s.rolling(5, min_periods=1).mean().values
        # wl = d.max_level_cm * (sm_flow / d.pipe_capacity_lps)
        # wl = np.clip(wl, 0, d.max_level_cm)
        # return pd.DataFrame({"inflow_lps": q_in, "smoothed_flow_lps": sm_flow, "level_cm": wl}, index=idx)

        sm_flow=flow_s.ewm(halflife=pd.Timedelta(minutes=d.level_time_constant_min),times=idx).mean()

        wl=d.max_level_cm*(1.0-np.exp(-sm_flow.values/d.pipe_capacity_lps))
        # wl = wl * 0.98
        s_err=self.np_rng.normal(0,d.sensor_noise_std_cm,n_pts)
        wl=np.clip(wl+s_err,0,d.max_level_cm)

        return pd.DataFrame({
            "inflow_lps":q_in,
            "smoothed_flow_lps":sm_flow.values,
            "level_cm":wl,
        },index=idx)




def run_simulation(
    start_date="2024-01-01",
    n_days=365,
    drain=None,
    timestep_minutes=SIM_CONFIG["timestep_minutes"],
    sensor_interval_minutes=SIM_CONFIG["sensor_interval_minutes"],
    seed=None):
    
    rng=random.Random(seed)
    
    if seed is None:
        se=None
        sd=None
    else:
        se=seed+1
        sd=seed+1

    t_idx=pd.date_range(
        start=start_date,
        periods=int(round(n_days*24*60/timestep_minutes)),
        freq=f"{timestep_minutes}min",
    )

    rain_sim=RainfallEngine(timestep_minutes)
    rain_data,ev_records=rain_sim.simulate(start_date,n_days,rng)
    r_intensity=rain_data/(timestep_minutes/60.0)

    env_sim=EnvironmentEngine(np.random.default_rng(se))
    env_df=env_sim.simulate(t_idx,r_intensity)

    h_arr=t_idx.hour.values+t_idx.minute.values/60.0
    dem_arr=DemandEngine.demand_index(h_arr,env_df["E"].values)

    if drain is None:
        drain=DrainConfig()
        
    dr_sim=DrainSimulator(drain,timestep_minutes,rng_seed=sd)
    d_hyd=dr_sim.simulate(t_idx,r_intensity,dem_arr)

    res_df=env_df.copy()
    res_df["rain_mm"]=rain_data
    res_df["rain_intensity_mmph"]=r_intensity
    res_df["demand_index"]=dem_arr
    
    
    res_df=pd.concat([res_df,d_hyd],axis=1)
    res_df.index.name="timestamp"

    if sensor_interval_minutes>timestep_minutes:
        stride=sensor_interval_minutes//timestep_minutes
        out=res_df.iloc[::stride].copy()
    else:
        out=res_df

    h_num=out.index.hour+out.index.minute/60.0
    
    out["hour_sin"]=np.sin(2*np.pi*h_num/24)
    out["hour_cos"]=np.cos(2*np.pi*h_num/24)
    out["month_sin"]=np.sin(2*np.pi*out.index.month/12)
    out["month_cos"]=np.cos(2*np.pi*out.index.month/12)

    for sz in ["winter","pre_monsoon","monsoon","post_monsoon"]:
        out[f"season_{sz}"]=(out["season"]==sz).astype(int)

    for w_name in ["clear","cloudy","drizzle","light_rain","moderate_rain","heavy_rain"]:
        out[f"weather_state_{w_name}"]=(out["weather_state"]==w_name).astype(int)

    # out['flow_diff'] = out['inflow_lps'].diff().fillna(0)
    # out['is_spik'] = (out['inflow_lps'] > 15.0).astype(int)
    # out['load_pct'] = (out['smoothed_flow_lps'] / drain.pipe_capacity_lps) * 100
    # features.extend(['flow_diff', 'is_spik'])

    features=[
        'temp_c', 'rh_pct', 'rain_mm', 'rain_intensity_mmph', 'demand_index', 'inflow_lps', 'smoothed_flow_lps', 'level_cm','season','weather_state',
        'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'season_winter', 'season_pre_monsoon', 'season_monsoon', 'season_post_monsoon',
        'weather_state_clear', 'weather_state_cloudy', 'weather_state_drizzle', 'weather_state_light_rain', 'weather_state_moderate_rain', 'weather_state_heavy_rain'
    ]
    out=out[features]

    # ev_df = pd.DataFrame(ev_records) if ev_records else pd.DataFrame()
    ev_df=pd.DataFrame(ev_records)
    return out,ev_df



_days_in_month_name=get_days_in_m
classify_event_size=cat_event
generate_single_event=make_event
generate_rain_day_events=get_day_rain
_accumulate=acc_rain
_expected_mm_per_event=calc_expected_rain
_build_calibration_factors=init_calib_map




if __name__=="__main__":
    t0=time.perf_counter()

    drn=DrainConfig(name="Manhole_1")
    # drn.base_sewage_lps = 8.0
    readings,events=run_simulation(
        start_date="2026-01-01",
        n_days=365*1,
        timestep_minutes=5,
        sensor_interval_minutes=60,
        seed=None,
    )

    dt_elapsed=time.perf_counter()-t0
    print(f"Simulated 1 drain, {len(readings):,} sensor readings in {dt_elapsed:.2f}s")
    print(f"Generated {len(events)} rain events")

    monthly_check=events.groupby("month")["total_mm"].sum().reindex(MONTHLY_DATA.keys())
    print("\nSimulated vs. reference monthly rainfall totals (mm):")
    
    for mon in MONTHLY_DATA:
        sim_val=monthly_check.get(mon,0.0)
        ref_val=MONTHLY_DATA[mon]["total_rainfall_mm"]
        print(f"  {mon:<10s} sim={sim_val:7.1f}  ref={ref_val:7.1f}")

    # print(readings.describe())
    print("\nSample readings:")
    print(readings.head(10))

    # readings.to_csv("test_out.csv")
    readings.to_csv("Validation_Threshold_single_drain_readings.csv")
    print("\nSaved: single_drain_readings.csv, single_drain_rain_events.csv")
