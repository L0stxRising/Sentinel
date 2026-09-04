# RainFall Data!
'''
rain_prob_pct          : daily rain-occurrence probability
total_rainfall_mm      : average total rainfall for the month
avg_event_duration_hr  : average rain-event duration
intensity_range_mmph   : range of effective intensity
intensity_typical_mmph : typical / representative intensity
'''

MONTHLY_DATA = {
    "January":   {"rain_prob_pct": 0.95,  "total_rainfall_mm": 17.1,  "avg_event_duration_hr": 1.0, "intensity_range_mmph": (1, 8),   "intensity_typical_mmph": 4},
    "February":  {"rain_prob_pct": 1.06,  "total_rainfall_mm": 22.7,  "avg_event_duration_hr": 1.0, "intensity_range_mmph": (1, 8),   "intensity_typical_mmph": 4},
    "March":     {"rain_prob_pct": 1.46,  "total_rainfall_mm": 29.9,  "avg_event_duration_hr": 1.0, "intensity_range_mmph": (1, 10),  "intensity_typical_mmph": 5},
    "April":     {"rain_prob_pct": 1.79,  "total_rainfall_mm": 39.3,  "avg_event_duration_hr": 1.0, "intensity_range_mmph": (2, 12),  "intensity_typical_mmph": 6},
    "May":       {"rain_prob_pct": 2.91,  "total_rainfall_mm": 61.4,  "avg_event_duration_hr": 1.1, "intensity_range_mmph": (2, 15),  "intensity_typical_mmph": 8},
    "June":      {"rain_prob_pct": 7.73,  "total_rainfall_mm": 165.4, "avg_event_duration_hr": 1.2, "intensity_range_mmph": (3, 18),  "intensity_typical_mmph": 10},
    "July":      {"rain_prob_pct": 13.66, "total_rainfall_mm": 280.4, "avg_event_duration_hr": 1.3, "intensity_range_mmph": (3, 18),  "intensity_typical_mmph": 11},
    "August":    {"rain_prob_pct": 12.38, "total_rainfall_mm": 254.9, "avg_event_duration_hr": 1.3, "intensity_range_mmph": (3, 18),  "intensity_typical_mmph": 11},
    "September": {"rain_prob_pct": 8.18,  "total_rainfall_mm": 167.9, "avg_event_duration_hr": 1.3, "intensity_range_mmph": (3, 18),  "intensity_typical_mmph": 10},
    "October":   {"rain_prob_pct": 3.81,  "total_rainfall_mm": 75.4,  "avg_event_duration_hr": 1.2, "intensity_range_mmph": (2, 16),  "intensity_typical_mmph": 8},
    "November":  {"rain_prob_pct": 1.40,  "total_rainfall_mm": 29.7,  "avg_event_duration_hr": 1.1, "intensity_range_mmph": (2, 12),  "intensity_typical_mmph": 6},
    "December":  {"rain_prob_pct": 0.78,  "total_rainfall_mm": 15.9,  "avg_event_duration_hr": 1.0, "intensity_range_mmph": (1, 8),   "intensity_typical_mmph": 4},
}
# Seasonal RainFall Data
SEASONAL_RAINFALL = {
    "winter": {
        "total_mm": 39.8,
        "pct_of_annual": 3.4,
    },
    "pre_monsoon": {
        "total_mm": 130.6,
        "pct_of_annual": 11.3,
    },
    "monsoon": {
        "total_mm": 868.6,
        "pct_of_annual": 74.9,
    },
    "post_monsoon": {
        "total_mm": 121.0,
        "pct_of_annual": 10.4,
    },
}
MONTH_TO_SEASON = {
    "January":"winter","February":  "winter",
    "March":"pre_monsoon","April":"pre_monsoon","May":"pre_monsoon",
    "June":"monsoon","July":"monsoon","August":"monsoon","September":"monsoon",
    "October":"post_monsoon","November":"post_monsoon","December":"post_monsoon",
}

# Rainfall Duration Based on the Season
# Values = probability of duration for each season
EVENT_DURATION_DISTRIBUTION = {
    "pre_monsoon": {
        "<=1h": 0.60, "1-2h": 0.16, "2-3h": 0.08, "3-4h": 0.06, ">4h": 0.10,
    },
    "winter": {
        "<=1h": 0.60, "1-2h": 0.16, "2-3h": 0.08, "3-4h": 0.06, ">4h": 0.10,
    },
    "post_monsoon": {
        "<=1h": 0.60, "1-2h": 0.16, "2-3h": 0.08, "3-4h": 0.06, ">4h": 0.10,
    },
    "monsoon": {
        "<=1h": 0.60, "1-2h": 0.20, "2-3h": 0.085, "3-4h": 0.05, ">4h": 0.06,
    },
}

# Basically the ranges of the Duration To be randomly picked
DURATION_BUCKET_HOURS = {
    "<=1h": (0.25, 1.0),
    "1-2h": (1.0, 2.0),
    "2-3h": (2.0, 3.0),
    "3-4h": (3.0, 4.0),
    ">4h":  (4.0, 8.0),
}


# ============================================================
# 4. RAINFALL — EVENT SIZE / AMOUNT
# ============================================================
# range_mm = (min, max) total rainfall per event. None = open-ended.

EVENT_SIZE_CLASSES = {
    "light":      {"range_mm": (0.5, 10)},
    "moderate":   {"range_mm": (10, 25)},
    "heavy":      {"range_mm": (25, 50)},
    "very_heavy": {"range_mm": (50, 100)},
    "extreme":    {"range_mm": (100, None)},
}

EVENT_INTENSITY_DISTRIBUTION_WITHIN_CLASS = {
    "lower_half_pct": 0.70,
    "upper_half_pct": 0.25,
    "unusually_intense_pct": 0.05,
}


# ============================================================
# 5. RAINFALL — STORM SHAPE / SUB-EVENT INTENSITY
# ============================================================
# Relative multipliers across sequential phases of one event.
# Normalize so the sum of short-duration intervals equals total event rainfall.

STORM_PROFILES = {
    "normal":       [0.5, 0.8, 1.0, 1.3, 1.0, 0.7, 0.3],
    "front_loaded": [1.0, 1.5, 1.8, 1.2, 0.7, 0.3],
    "back_loaded":  [0.3, 0.6, 0.8, 1.2, 1.7, 1.3, 0.6],
}

STORM_PROFILE_WEIGHTS = {
    "normal":       0.50,
    "front_loaded": 0.30,
    "back_loaded":  0.20,
}

NORMAL_EVENT_SHAPE_GUIDANCE = {
    "start_multiplier_range": (0.4, 0.7),
    "peak_multiplier_range":  (1.2, 2.0),
    "end_multiplier_range":   (0.1, 0.5),
}

PEAK_MULTIPLIER_BY_EVENT_CLASS = {
    "light":      (1.3, 1.7),
    "moderate":   (1.5, 2.2),
    "heavy":      (1.8, 3.0),
    "very_heavy": (2.5, 4.0),
    "extreme":    (2.5, 4.0),
}


# Human Demand Data
HOURLY_DEMAND_MULTIPLIERS = {
     0: 0.40, 1: 0.30, 2: 0.30, 3: 0.30, 4: 0.40,
     5: 0.70, 6: 1.20, 7: 1.60, 8: 1.40, 9: 1.20,
    10: 1.10, 11: 1.00, 12: 1.00, 13: 1.00, 14: 1.00,
    15: 1.00, 16: 1.10, 17: 1.20, 18: 1.40, 19: 1.50,
    20: 1.40, 21: 1.20, 22: 0.90, 23: 0.60
}


# ============================================================
# 7. HUMAN DEMAND — ANALYTICAL MODEL PARAMETERS
# ============================================================
# Q(t, E) = E * [ B + A1*exp(-(t-μ1)²/(2σ1²)) + A2*exp(-(t-μ2)²/(2σ2²)) ]
# Then divide the bracketed term by its 24-h mean so the unscaled
# base curve averages exactly 1.0. Then multiply by E.

DEMAND_MODEL_PARAMS = {
    "B":      0.3,     # night-time floor
    "A1":     1.3,     # morning peak amplitude
    "mu1":    7.0,     # morning peak centre (hours)
    "sigma1": 1.5,     # morning peak width
    "A2":     1.2,     # evening peak amplitude
    "mu2":    19.0,    # evening peak centre (hours)
    "sigma2": 2.5,     # evening peak width
}

# Precomputed 24-h mean of the un-normalized curve (E = 1).
# Use as: q_base(t) = unnormalized_q(t) / NORMALIZATION_CONSTANT
NORMALIZATION_CONSTANT = 0.7673


# ============================================================
# 8. ENVIRONMENT — MONTHLY CLIMATE BASELINE
# ============================================================
# India-wide representative values, not city-specific.
# temp_c_mean / temp_c_range : daily mean and typical half-range (°C)
# rh_pct_mean / rh_pct_range : daily mean RH and typical half-range (%)

MONTHLY_CLIMATE = {
    "January":   {"temp_c_mean": 18.0, "temp_c_range": 4.0, "rh_pct_mean": 58, "rh_pct_range": 10},
    "February":  {"temp_c_mean": 21.0, "temp_c_range": 4.0, "rh_pct_mean": 52, "rh_pct_range": 10},
    "March":     {"temp_c_mean": 26.0, "temp_c_range": 4.5, "rh_pct_mean": 46, "rh_pct_range": 10},
    "April":     {"temp_c_mean": 30.5, "temp_c_range": 4.5, "rh_pct_mean": 40, "rh_pct_range": 10},
    "May":       {"temp_c_mean": 33.0, "temp_c_range": 4.0, "rh_pct_mean": 44, "rh_pct_range": 12},
    "June":      {"temp_c_mean": 31.0, "temp_c_range": 3.5, "rh_pct_mean": 70, "rh_pct_range": 12},
    "July":      {"temp_c_mean": 28.5, "temp_c_range": 2.5, "rh_pct_mean": 82, "rh_pct_range": 8},
    "August":    {"temp_c_mean": 28.0, "temp_c_range": 2.5, "rh_pct_mean": 84, "rh_pct_range": 8},
    "September": {"temp_c_mean": 28.0, "temp_c_range": 2.5, "rh_pct_mean": 80, "rh_pct_range": 8},
    "October":   {"temp_c_mean": 26.5, "temp_c_range": 3.5, "rh_pct_mean": 66, "rh_pct_range": 10},
    "November":  {"temp_c_mean": 22.5, "temp_c_range": 3.5, "rh_pct_mean": 60, "rh_pct_range": 10},
    "December":  {"temp_c_mean": 19.0, "temp_c_range": 4.0, "rh_pct_mean": 58, "rh_pct_range": 10},
}


# ============================================================
# 9. ENVIRONMENT — COMPONENT FACTORS
# ============================================================
# E = F_temperature * F_humidity * F_season * F_weather

ENVIRONMENT_FACTOR_COMPONENTS = [
    "F_temperature",
    "F_humidity",
    "F_season",
    "F_weather",
]

# How the season itself shifts whole-day demand.
F_SEASON_BY_KEY = {
    "winter":       0.92,   # cooler, lower outdoor / bathing demand
    "pre_monsoon":  1.12,   # hottest, highest outdoor + cooling demand
    "monsoon":      0.96,   # humid, rain suppresses outdoor use
    "post_monsoon": 1.01,   # near-normal
}

# Weather-state catalogue. Rain intensity (mm/h) selects the state.
# F_weather < 1 on wet days. Clear hot days slightly raise demand.
WEATHER_STATES = {
    "clear":         {"F_weather": 1.04, "sky": "clear",         "min_rain_mmph": None, "max_rain_mmph": 0.0},
    "cloudy":        {"F_weather": 1.00, "sky": "overcast",      "min_rain_mmph": None, "max_rain_mmph": 0.0},
    "drizzle":       {"F_weather": 0.94, "sky": "drizzle",       "min_rain_mmph": 0.01, "max_rain_mmph": 1.0},
    "light_rain":    {"F_weather": 0.90, "sky": "light rain",    "min_rain_mmph": 1.0,  "max_rain_mmph": 4.0},
    "moderate_rain": {"F_weather": 0.86, "sky": "moderate rain", "min_rain_mmph": 4.0,  "max_rain_mmph": 10.0},
    "heavy_rain":    {"F_weather": 0.80, "sky": "heavy rain",    "min_rain_mmph": 10.0, "max_rain_mmph": None},
}

# Dry-day weather mix when it is NOT raining (probabilities).
DRY_WEATHER_MIX = {
    "clear":  0.65,
    "cloudy": 0.35,
}

# Extra RH added on top of the monthly sample, by weather state.
WEATHER_RH_ADJUSTMENT = {
    "clear":         0.0,
    "cloudy":        6.0,
    "drizzle":       12.0,
    "light_rain":    12.0,
    "moderate_rain": 12.0,
    "heavy_rain":    12.0,
}

# Typical already-multiplied composite E presets.
TYPICAL_E = {
    "unusually_low": 0.85,
    "normal":        1.00,
    "hot":           1.10,
    "very_hot":      1.20,
    "extreme":       1.30,
}

#  ============================================================
# 10. ENVIRONMENT — REFERENCE / CLAMP VALUES
# ============================================================
# Used to convert raw temp / RH into factors around 1.0.
#
# F_temperature ≈ 1.0 + (temp_c - temp_c_ref) / temp_c_span
# F_humidity    ≈ 1.0 - (rh_pct - rh_pct_ref) / rh_pct_span * 0.10
# Then clamp each factor, then clamp E.

CLIMATE_REFERENCE = {
    "temp_c_ref":   26.0,            # ~1.0 demand at 26 °C
    "temp_c_span":  15.0,            # 11 °C → ~0.85,  41 °C → ~1.15 before clamp
    "rh_pct_ref":   55.0,            # ~1.0 demand at 55 % RH
    "rh_pct_span":  50.0,            # drier air slightly raises demand
    "rh_pct_effect": 0.10,           # scale of the humidity adjustment
    "rh_pct_clip":  (20.0, 98.0),    # sampled RH is clipped to this
    "F_temp_clamp": (0.80, 1.25),
    "F_rh_clamp":   (0.90, 1.10),
    "E_clamp":      (0.70, 1.45),
}

# Now Setting Up the Actual Simulation
print("Its gonna take a while.......")
print("Its Doing smthing i guess ")