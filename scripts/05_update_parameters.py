"""Replace provisional parameters with sourced values, reproducibly.

Each update names its source_id (docs/source_register.csv). Run after
scripts/04_process_raw.py. Never edit config/parameters.csv by hand.
"""
import json
import os

import numpy as np
import pandas as pd

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRO = os.path.join(H, "data", "processed")
PF = os.path.join(H, "config", "parameters.csv")
par = pd.read_csv(PF, dtype=str).fillna("")


def setp(name, base, low=None, high=None, dist=None, src="", notes=""):
    i = par.index[par["name"] == name]
    if len(i) != 1:
        raise KeyError(name)
    i = i[0]
    par.loc[i, "base"] = repr(float(base))
    par.loc[i, "low"] = "" if low is None else repr(float(low))
    par.loc[i, "high"] = "" if high is None else repr(float(high))
    if dist:
        par.loc[i, "dist"] = dist
    par.loc[i, "source_id"], par.loc[i, "status"], par.loc[i, "notes"] = src, "sourced", notes


T = "triangular"
# --- macro ----------------------------------------------------------------------
fx = pd.read_csv(os.path.join(PRO, "fx_usd_per_eur.csv"))
setp("fx_usd_per_eur", fx.loc[fx.year == 2025, "usd_per_eur"].item(), dist="fixed", src="ECB_FX",
     notes="ECB reference rate, 2025 annual average")
g = json.load(open(os.path.join(PRO, "damodaran_globals_2026.json")))
setp("erp_mature", g["erp_mature"], 0.040, 0.046, T, "DAMODARAN_CRP_2026",
     "implied ERP, Jan 2026 update; range spans Jan 2022-Jan 2026 editions")
setp("rf_usd", 0.0395, 0.0375, 0.0430, T, "DAMODARAN_WACC_2026",
     "US riskfree net of Aa1 default spread implied by Damodaran Jan 2026 industry cost of equity")

# --- country risk: mode = 2026, range = min/max over 2022/2024/2026 editions -------
names = {"IL": "Israel", "CY": "Cyprus", "GR": "Greece", "EG": "Egypt", "TR": "Turkey", "IT": "Italy"}
panel = pd.read_csv(os.path.join(PRO, "damodaran_crp_panel.csv"))
panel["country"] = panel["country"].str.strip()
for cc, nm in names.items():
    s = panel[panel.country == nm].set_index("vintage")
    v = s["crp_rating"].astype(float)
    setp(f"crp_{cc}", v.loc[2026], v.min(), v.max(), T, "DAMODARAN_CRP_2022_2024_2026",
         "rating-based CRP; mode Jan 2026, range across 2022-2026 editions")
    setp(f"ds_{cc}", float(s.loc[2026, "default_spread_rating"]), dist="fixed", src="DAMODARAN_CRP_2026",
         notes="rating-based sovereign default spread, Jan 2026")
tax = pd.read_csv(os.path.join(PRO, "damodaran_tax_rates_2026.csv"))
tax["country"] = tax["country"].astype(str).str.strip()
for cc, nm in names.items():
    setp(f"tax_{cc}", float(tax.loc[tax.country == nm, "tax_rate_2025_lookup"].iloc[0]), dist="fixed",
         src="DAMODARAN_TAX_2026", notes="statutory corporate tax rate, 2025")

# --- asset-class capital structure: Damodaran Europe industry averages, Jan 2026 ----
# unlevered beta = levered beta / (1 + (1 - t) D/E), from the Group 6 copy of waccEurope.xls
# (Date updated 2026-01-05): Oil/Gas Distribution, Utility (General), Power.
for a, beta_l, dv, t, ind in [("pipe", 0.669989, 0.405838, 0.083718, "Oil/Gas Distribution"),
                              ("hvdc", 0.636660, 0.478584, 0.208650, "Utility (General)"),
                              ("ccgt", 0.616858, 0.376475, 0.222800, "Power")]:
    de = dv / (1 - dv)
    setp(f"beta_u_{a}", beta_l / (1 + (1 - t) * de), dist="fixed", src="DAMODARAN_WACC_2026",
         notes=f"Europe, {ind}: levered beta {beta_l:.3f}, D/V {dv:.3f}, tax {t:.3f}")
    setp(f"de_{a}", de, dist="fixed", src="DAMODARAN_WACC_2026", notes=f"Europe, {ind}: D/V {dv:.3f}")

# --- replacement gas price from World Bank Pink Sheet TTF ------------------------------
ann = pd.read_csv(os.path.join(PRO, "gas_prices_annual_usd_mmbtu.csv")).set_index("year")
k = 3.412142 / fx.loc[fx.year == 2025, "usd_per_eur"].item()      # $/MMBtu -> EUR/MWh
lo, mode = ann.loc[2024, "ttf"] * k, ann.loc[[2025, 2026], "ttf"].mean() * k
setp("p_repl_gas", mode, lo, 2 * mode, T, "WB_PINKSHEET_2026_10",
     "TTF: low = 2024 avg, mode = mean of 2025 and 2026 YTD avg, high = 2x mode (crisis)")

# --- solar capacity factors: PVGIS-SARAH3 at representative utility-scale sites ----------
# low = lowest fixed-optimal site, high = highest single-inclined-axis site,
# mode = midpoint of fixed-optimal and tracker means (mixed fleets); per kWp DC, 14% losses.
pv = pd.read_csv(os.path.join(PRO, "pvgis_site_yields.csv"))
for pre, cc in [("gr", "GR"), ("il", "IL"), ("eg", "EG")]:
    q = pv[pv.country == cc]
    fo, tr = q[q.config == "fixed_optimal"]["cf"], q[q.config == "single_inclined_axis"]["cf"]
    setp(f"{pre}_solar_cf", (fo.mean() + tr.mean()) / 2, fo.min(), tr.max(), T, "PVGIS_SARAH3",
         f"{len(fo)} sites; fixed-optimal mean {fo.mean():.3f}, tracker mean {tr.mean():.3f}")

# --- Egypt gas balance: Energy Institute Statistical Review 2026 (data year 2025) -------
ei = pd.read_csv(os.path.join(PRO, "ei_gas_bcm.csv"))
eg = ei[ei.country == "Egypt"].pivot_table(index="year", columns="variable", values="bcm")
cagr = (eg.loc[2025, "production"] / eg.loc[2021, "production"]) ** (1 / 4) - 1
yoy = eg["production"].pct_change().loc[2022:2025]
setp("eg_prod0", eg.loc[2025, "production"], dist="fixed", src="EI_2026_GAS", notes="Egypt gas production 2025 (bcm)")
setp("eg_dem0", eg.loc[2025, "consumption"], dist="fixed", src="EI_2026_GAS", notes="Egypt gas consumption 2025 (bcm)")
setp("eg_prod_decline", cagr, yoy.min(), -0.03, T, "EI_2026_GAS",
     "mode = 2021-2025 CAGR of legacy output; low = steepest annual decline 2022-2025; high = -3%/yr stabilisation")

par.to_csv(PF, index=False)
print(par[par.status == "sourced"][["name", "dist", "base", "low", "high", "source_id"]].to_string(index=False))
print(f"\nsourced {int((par.status == 'sourced').sum())}/{len(par)}")
