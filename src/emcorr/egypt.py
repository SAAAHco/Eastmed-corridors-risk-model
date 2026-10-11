"""Egypt gas balance ("gas cliff") and diversion of exports transiting or originating in Egypt.

Levant gas sent to Egypt for liquefaction (option O2) is exportable only if
Egypt does not need it at home. In shortage years the state has diverted gas
from liquefaction to the domestic market (2012 Damietta feed-gas cut; 2024-25
export halt). Electricity exported from Egyptian renewables (O4a, O4b) faces the
same incentive, because each MWh kept at home saves imported gas. For an export
volume V (bcm, or bcm-equivalent for electricity) the share actually exported is

    S_t = max(0, D_t - P_t - I_t - C_t)          domestic shortfall
    a_t = 1 - theta * min(1, S_t / V)             export availability

theta in [0, 1] is the diversion propensity (1 = domestic market always first);
it differs between gas and power (ring-fencing, contracts, precedent).
All inputs broadcast over Monte Carlo samples (shape (N,)) and years (shape (Y,)).
"""
import numpy as np


def _col(x):
    """Turn a scalar or (N,) array into a column (N, 1) for year broadcasting."""
    return np.asarray(x, dtype=float).reshape(-1, 1)


def ramp(years, start, end, level):
    """Linear ramp 0 -> level between start and end year (inclusive), flat after."""
    y = np.asarray(years, dtype=float).reshape(1, -1)
    s, e, lv = _col(start), _col(end), _col(level)
    frac = np.clip((y - s) / np.maximum(e - s, 1e-9), 0.0, 1.0)
    return lv * frac


def production(years, prod0, decline, add_level, add_start, add_end, floor=0.0, base_year=2024):
    """Legacy-field decline plus new-field additions (bcm/yr)."""
    y = np.asarray(years, dtype=float).reshape(1, -1)
    legacy = _col(prod0) * (1.0 + _col(decline)) ** (y - base_year)
    legacy = np.maximum(legacy, _col(floor))
    return legacy + ramp(years, add_start, add_end, add_level)


def demand(years, dem0, growth, base_year=2024):
    y = np.asarray(years, dtype=float).reshape(1, -1)
    return _col(dem0) * (1.0 + _col(growth)) ** (y - base_year)


def israel_inflow(years, flow0, flow_max, ramp_end, base_year=2024):
    """Israeli pipeline supply to Egypt's domestic market, ramping to flow_max."""
    y = np.asarray(years, dtype=float).reshape(1, -1)
    f0, fm, re_ = _col(flow0), _col(flow_max), _col(ramp_end)
    frac = np.clip((y - base_year) / np.maximum(re_ - base_year, 1e-9), 0.0, 1.0)
    return f0 + (fm - f0) * frac


def cyprus_inflow(years, level, start, ramp_years=2.0):
    return ramp(years, _col(start), _col(start) + _col(ramp_years), level)


def shortfall(P, D, I, C):
    return np.maximum(0.0, D - P - I - C)


def export_availability(S, volume, theta):
    """Share of the contracted export volume that is actually exported each year."""
    return 1.0 - _col(theta) * np.minimum(1.0, S / np.maximum(_col(volume), 1e-9))


def pv_mean(series, wacc, years, start_year):
    """PV-weighted mean of a yearly series over the years >= start_year."""
    y = np.asarray(years, dtype=float).reshape(1, -1)
    d = np.log1p(_col(wacc))
    w = np.exp(-d * (y - _col(start_year))) * (y >= _col(start_year))
    return (series * w).sum(1) / w.sum(1)


def balance(P, years):
    """Egypt's gas balance paths (bcm/yr), shape (N, Y)."""
    yrs = np.asarray(years)
    by = float(np.asarray(P.get("eg_base_year", 2024)).ravel()[0])
    prod = production(yrs, P["eg_prod0"], P["eg_prod_decline"], P["eg_add_level"],
                      P["eg_add_start"], P["eg_add_end"], P["eg_prod_floor"], base_year=by)
    dem = demand(yrs, P["eg_dem0"], P["eg_dem_growth"], base_year=by)
    isr = israel_inflow(yrs, P["eg_il_flow0"], P["eg_il_flow_max"], P["eg_il_ramp_end"], base_year=by)
    cyp = cyprus_inflow(yrs, P["eg_cy_level"], P["eg_cy_start"])
    return {"production": prod, "demand": dem, "israel": isr, "cyprus": cyp,
            "shortfall": shortfall(prod, dem, isr, cyp)}


def diversion_share(P, years, volume_bcm, theta, start_year, life):
    """Mean share of an export volume diverted to Egypt's domestic market over
    the export years [start_year, start_year + life) within `years`."""
    b = balance(P, years)
    a = export_availability(b["shortfall"], volume_bcm, theta)
    y = np.asarray(years, dtype=float).reshape(1, -1)
    start = _col(start_year)
    live = (y >= start) & (y < start + _col(life))
    a_mean = np.nanmean(np.where(live, a, np.nan), axis=1)
    b["availability"] = a
    return 1.0 - a_mean, b


def o2_unavailability(P, years):
    """Mean diversion share for O2 (Levant gas liquefied in Egypt)."""
    return diversion_share(P, years, P["o2_volume_bcm"], P["eg_divert_theta"], P["o2_start_year"], P["o2_life"])