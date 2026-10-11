"""Cost-of-capital penalty on renewables vs fiscal space (supporting section).

Penalty = LCOE at the country's real after-tax WACC (IRENA's 2025 benchmark estimates, Table A2 of the
RPGC-in-2025 data file, extracted by 04d_extract_irena_wacc.py)
relative to LCOE at a de-risked benchmark WACC (default: Greece, the EU member
in the corridor, i.e. what an EU-guaranteed project could borrow at).
The percentage penalty is independent of the capacity factor:
    LCOE ~ (capex * CRF(r, n) + FOM) / (8760 * CF)
so the ratio LCOE(r_c)/LCOE(r_0) needs only capex, FOM, life, build time and WACC
(taken from config/parameters.csv, as in the corridor model).
"""
import os
import sys

import numpy as np
import pandas as pd

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(H, "src"))
from emcorr import finance as F   # noqa: E402
from emcorr import mc             # noqa: E402

LEG, PRO, TAB = (os.path.join(H, *p) for p in (("data", "legacy"), ("data", "processed"), ("outputs", "tables")))
COUNTRIES = {  # ISO3: (IRENA name, Damodaran name)
    "GRC": ("Greece", "Greece"), "CYP": ("Cyprus", "Cyprus"), "ISR": ("Israel", "Israel"),
    "EGY": ("Egypt", "Egypt"), "TUR": ("Türkiye", "Turkey"), "JOR": ("Jordan", "Jordan"),
    "LBN": ("Lebanon", "Lebanon"), "BGR": ("Bulgaria", "Bulgaria"), "ROU": ("Romania", "Romania"),
    "HRV": ("Croatia", "Croatia"), "SVN": ("Slovenia", "Slovenia"), "SRB": ("Serbia", "Serbia"),
    "BIH": ("Bosnia and Herzegovina", "Bosnia and Herzegovina"), "MNE": ("Montenegro", "Montenegro"),
    "MKD": ("North Macedonia", "Macedonia"), "ALB": ("Albania", "Albania"), "XKX": ("Kosovo", None),
    "ITA": ("Italy", "Italy"),
}
_P = mc.base_values(mc.load_params(os.path.join(H, "config", "parameters.csv")))
TECH = {  # same cost basis as the corridor model (Greek new-build, EUR/kW and EUR/kW-yr)
    "solar_pv": dict(capex=_P["gr_solar_capex"], fom=_P["gr_solar_fom"], life=_P["solar_life"], build=_P["solar_build"]),
    "onshore_wind": dict(capex=_P["gr_wind_capex"], fom=_P["gr_wind_fom"], life=_P["wind_life"], build=_P["wind_build"]),
}
BENCH = "GRC"


def lcoe_ratio(r, r0, capex, fom, life, build):
    """LCOE at WACC r relative to WACC r0, with the model's own levelised-cost formula."""
    lc = lambda w: F.levelized_cost(capex, 1.0, w, life, build, fom_per_year=fom)
    return lc(r) / lc(r0)


irena = pd.read_csv(os.path.join(PRO, "irena_wacc_rpgc2025_tableA2.csv"))   # was data/legacy/irena_wacc_figA1.csv (2024)
irena["country"] = irena["country"].astype(str).str.strip()
names = set(irena.country)
missing = [v[0] for v in COUNTRIES.values() if v[0] not in names]
if missing:   # report alternative spellings present in the IRENA table
    alt = {m: sorted(n for n in names if m.split()[0][:5].lower() in n.lower()) for m in missing}
    print("not found in IRENA table:", alt)

crp = pd.read_csv(os.path.join(PRO, "damodaran_crp_2026.csv"))
crp["country"] = crp["country"].astype(str).str.strip()
imf = pd.read_csv(os.path.join(PRO, "imf_fiscal.csv"))
imf = imf[imf.year == 2025].pivot_table(index="iso3", columns="indicator", values="value")
imf = imf.rename(index={"UVK": "XKX"})

rows = []
r0 = {t: float(irena.loc[irena.country == COUNTRIES[BENCH][0], t].iloc[0]) for t in TECH}
for iso, (iname, dname) in COUNTRIES.items():
    q = irena[irena.country == iname]
    if q.empty:
        continue
    row = {"iso3": iso, "country": iname}
    for t, p in TECH.items():
        r = float(q[t].iloc[0])
        row[f"wacc_{t}"] = r
        row[f"lcoe_x_{t}"] = float(lcoe_ratio(r, r0[t], p["capex"], p["fom"], p["life"], p["build"]))
        row[f"irena_default_{t}"] = abs(r - 0.075) < 1e-9
    c = crp[crp.country == dname] if dname else crp.iloc[0:0]
    row["crp_2026"] = float(c["crp_rating"].iloc[0]) if len(c) else np.nan
    for ind, lab in [("GGXWDG_NGDP", "gross_debt_pct_gdp_2025"), ("GGXCNL_NGDP", "fiscal_balance_pct_gdp_2025"),
                     ("NGDPD", "gdp_usd_bn_2025")]:
        row[lab] = imf.loc[iso, ind] if iso in imf.index and ind in imf.columns else np.nan
    rows.append(row)

out = pd.DataFrame(rows).sort_values("lcoe_x_solar_pv", ascending=False)
out.to_csv(os.path.join(TAB, "cost_of_capital_penalty.csv"), index=False)
pd.set_option("display.width", 220)
print(f"benchmark {BENCH}: solar {r0['solar_pv']:.4f}, wind {r0['onshore_wind']:.4f}")
print(out[["country", "wacc_solar_pv", "lcoe_x_solar_pv", "wacc_onshore_wind", "lcoe_x_onshore_wind",
           "irena_default_solar_pv", "crp_2026", "gross_debt_pct_gdp_2025", "fiscal_balance_pct_gdp_2025"]]
      .round(3).to_string(index=False))
