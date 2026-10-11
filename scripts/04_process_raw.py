"""Turn data/raw/ files into tidy inputs in data/processed/ (no manual edits)."""
import json
import os

import numpy as np
import pandas as pd

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW, PRO, LEG = (os.path.join(H, "data", s) for s in ("raw", "processed", "legacy"))
os.makedirs(PRO, exist_ok=True)
ISO = ["GRC", "CYP", "ISR", "EGY", "TUR", "ITA", "JOR", "LBN", "BGR", "ALB", "MKD", "MNE", "XKX",
       "SRB", "BIH", "HRV", "ROU", "SVN", "LBY", "SYR", "PSE"]

# FX and deflator --------------------------------------------------------------
fx = pd.read_csv(os.path.join(RAW, "ecb", "ecb_usd_per_eur_annual.csv"))[["TIME_PERIOD", "OBS_VALUE"]]
fx.columns = ["year", "usd_per_eur"]
fx.to_csv(os.path.join(PRO, "fx_usd_per_eur.csv"), index=False)

h = json.load(open(os.path.join(RAW, "eurostat", "hicp_annual_index.json")))
geo, tim = h["dimension"]["geo"]["category"]["index"], h["dimension"]["time"]["category"]["index"]
rows = []
for g, gi in geo.items():
    for t, ti in tim.items():
        v = h["value"].get(str(gi * len(tim) + ti))
        rows.append({"geo": g, "year": int(t), "hicp_2015eq100": v})
hd = pd.DataFrame(rows).dropna()
hd["factor_to_2025"] = hd.groupby("geo")["hicp_2015eq100"].transform(lambda s: s[hd.loc[s.index, "year"] == 2025].iloc[0] / s)
hd.to_csv(os.path.join(PRO, "hicp_deflator.csv"), index=False)

# Damodaran 2026 + panel with 2022/2024 ------------------------------------------
x = pd.ExcelFile(os.path.join(RAW, "damodaran", "ctryprem_2026-01.xlsx"))
d = pd.read_excel(x, "ERPs by country", header=None)
glob = {"date_of_update": str(d.iloc[1, 1]), "note": str(d.iloc[1, 2]),
        "erp_mature": float(d.iloc[2, 4]), "erp_us": float(d.iloc[3, 4]), "crp_vol_multiplier": float(d.iloc[5, 4])}
json.dump(glob, open(os.path.join(PRO, "damodaran_globals_2026.json"), "w"), indent=2)
start = d.index[d[0].astype(str).str.strip().eq("Abu Dhabi")][0]
d = d.iloc[start:, :9].copy()
d.columns = ["country", "region", "moodys_rating", "default_spread_rating", "erp_total_rating",
             "crp_rating", "default_spread_cds", "erp_total_cds", "crp_cds"]
d = d[d["country"].notna() & d["crp_rating"].apply(lambda v: isinstance(v, (int, float)))]
d.insert(0, "vintage", "2026")
d.to_csv(os.path.join(PRO, "damodaran_crp_2026.csv"), index=False)
panel = pd.concat([pd.read_csv(os.path.join(LEG, f"damodaran_crp_{v}.csv")).drop(columns=["provenance", "verification"])
                   for v in ("2022", "2024")] + [d], ignore_index=True)
keep = ["Greece", "Cyprus", "Israel", "Egypt", "Turkey", "Italy", "Jordan", "Lebanon", "Bulgaria", "Albania",
        "North Macedonia", "Macedonia", "Montenegro", "Serbia", "Bosnia and Herzegovina", "Croatia", "Romania",
        "Slovenia", "Libya", "Syria"]
panel[panel["country"].astype(str).str.strip().isin(keep)].to_csv(os.path.join(PRO, "damodaran_crp_panel.csv"), index=False)
t = pd.read_excel(x, "Country Tax Rates", header=None).iloc[1:, :3]
t.columns = ["country", "tax_rate", "tax_rate_2025_lookup"]
t.dropna(subset=["country"]).to_csv(os.path.join(PRO, "damodaran_tax_rates_2026.csv"), index=False)

# Ember ------------------------------------------------------------------------------
e = pd.read_csv(os.path.join(RAW, "ember", "release_generation_yearly_global.csv"), low_memory=False)
e = e[e["ISO 3 code"].isin(ISO)]
e.to_csv(os.path.join(PRO, "ember_region.csv"), index=False)
cf = []
for (iso, src), g in e[e["Electricity source"].isin(["Solar", "Wind"])].groupby(["ISO 3 code", "Electricity source"]):
    g = g.sort_values("Year").set_index("Year")
    cap_mid = (g["Capacity (GW)"] + g["Capacity (GW)"].shift(1)) / 2
    for yr in g.index:
        if yr >= 2015 and pd.notna(cap_mid.get(yr)) and cap_mid[yr] > 0.05:
            cf.append({"iso3": iso, "source": src, "year": yr, "generation_twh": g.loc[yr, "Generation (TWh)"],
                       "capacity_gw_midyear": cap_mid[yr],
                       "realised_cf": g.loc[yr, "Generation (TWh)"] / (cap_mid[yr] * 8.76)})
pd.DataFrame(cf).to_csv(os.path.join(PRO, "ember_realised_cf.csv"), index=False)

# IMF fiscal ------------------------------------------------------------------------
rows = []
for f, ind in [("imf_balance/imf_GGXCNL_NGDP.json", "GGXCNL_NGDP"), ("imf_debt/imf_GGXWDG_NGDP.json", "GGXWDG_NGDP"),
               ("imf_gdp/imf_NGDPD.json", "NGDPD")]:
    j = json.load(open(os.path.join(RAW, f)))
    for c, ser in j["values"][ind].items():
        for y, v in ser.items():
            rows.append({"iso3": c, "indicator": ind, "year": int(y), "value": v})
pd.DataFrame(rows).to_csv(os.path.join(PRO, "imf_fiscal.csv"), index=False)

# Gas prices (World Bank Pink Sheet) ------------------------------------------------
p = pd.read_excel(os.path.join(RAW, "worldbank", "CMO-Historical-Data-Monthly_2026-10.xlsx"), "Monthly Prices", header=None)
hdr = [str(v) for v in p.iloc[4].tolist()]
cols = {hdr.index("Natural gas, US"): "henry_hub", hdr.index("Natural gas, Europe"): "ttf",
        hdr.index("Liquefied natural gas, Japan"): "lng_japan"}
m = p.iloc[6:, [0] + list(cols)].copy()
m.columns = ["month"] + list(cols.values())
m = m[m["month"].astype(str).str.match(r"^\d{4}M\d{2}$")]
for c in cols.values():
    m[c] = pd.to_numeric(m[c], errors="coerce")
m["year"] = m["month"].str[:4].astype(int)
m.to_csv(os.path.join(PRO, "gas_prices_monthly_usd_mmbtu.csv"), index=False)
ann = m[m["year"] >= 2015].groupby("year")[list(cols.values())].mean().round(3)
ann["n_months"] = m[m["year"] >= 2015].groupby("year").size()
ann.to_csv(os.path.join(PRO, "gas_prices_annual_usd_mmbtu.csv"))

print(json.dumps(glob, indent=1))
print("FX 2025:", fx.loc[fx.year == 2025, "usd_per_eur"].item())
print(hd[hd.geo == "EA20"].tail(6).to_string(index=False))
print(ann.tail(8).to_string())
pr = pd.read_csv(os.path.join(PRO, "damodaran_crp_panel.csv"))
print(pr.pivot_table(index="country", columns="vintage", values="crp_rating").round(4).to_string())
cfd = pd.DataFrame(cf)
print(cfd[(cfd.year >= 2023) & cfd.iso3.isin(["GRC", "EGY", "ISR", "CYP", "TUR"])].pivot_table(index=["iso3", "source"], columns="year", values="realised_cf").round(3).to_string())
