"""Global Energy Monitor GGIT (pipelines Nov 2025, LNG terminals Sep 2025):
region extract, EastMed route geometry, and reference-class completion rates."""
import os
import warnings

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(H, "data", "raw", "manual")
PRO = os.path.join(H, "data", "processed")
REG = ["Greece", "Cyprus", "Israel", "Egypt", "Türkiye", "Turkey", "Italy", "Bulgaria", "Albania", "North Macedonia",
       "Montenegro", "Serbia", "Bosnia", "Croatia", "Romania", "Libya", "Lebanon", "Syria", "Jordan", "Palestin"]

p = pd.read_excel(os.path.join(RAW, "GEM-GGIT-Gas-Pipelines-2025-11.xlsx"), sheet_name="Pipelines")
inreg = p["CountriesOrAreas"].astype(str).str.contains("|".join(REG))
keep = ["ProjectID", "PipelineName", "SegmentName", "Status", "Fuel", "CountriesOrAreas", "StartYear1", "ShelvedYear",
        "CancelledYear", "CapacityBcm/y", "LengthMergedKm", "ProjectLevelCost", "ProjectLevelCostUnits", "CostUSD",
        "FIDStatus", "FIDYear", "PCI5", "PCI6", "RouteAccuracy", "RouteType", "Wiki"]
p.loc[inreg, keep].to_csv(os.path.join(PRO, "gem_pipelines_region.csv"), index=False)

l = pd.read_excel(os.path.join(RAW, "GEM-GGIT-LNG-Teminals-2025-09.xlsx"), sheet_name="LNG Terminals")
lc = [c for c in l.columns if c.lower().startswith(("country", "terminal", "unit", "status", "facility", "capacity",
                                                       "start", "cost", "fid", "floating", "owner", "wiki", "lat", "lon"))]
lr = l[l.astype(str).apply(lambda r: r.str.contains("|".join(REG[:9] + ["Libya", "Lebanon", "Jordan"])).any(), axis=1)]
lr[lc].to_csv(os.path.join(PRO, "gem_lng_terminals_region.csv"), index=False)
print("LNG terminal columns kept:", lc)

# Reference class: pipelines touching Europe, Middle East or North Africa
eur = p["StartRegion"].astype(str).str.contains("Europe|Middle East|Africa") | \
      p["EndRegion"].astype(str).str.contains("Europe|Middle East|Africa")
rc = p[eur & (p["Fuel"] == "Gas")].copy()
rc["offshore"] = rc["RouteType"].astype(str).str.contains("offshore|subsea", case=False)
out = []
for name, g in [("all_gas_EU_ME_AF", rc), ("offshore_gas_EU_ME_AF", rc[rc.offshore])]:
    st = g["Status"].value_counts()
    fid = g[g["FIDStatus"].astype(str).str.contains("FID", case=False) & ~g["FIDStatus"].astype(str).str.contains("Pre", case=False)]
    pre = g[g["FIDStatus"].astype(str).str.contains("Pre", case=False)]
    row = {"set": name, "n": len(g), **{f"n_{k}": int(v) for k, v in st.items()},
           "n_postFID": len(fid), "postFID_cancelled_or_shelved": int(fid["Status"].isin(["cancelled", "shelved"]).sum()),
           "n_preFID": len(pre), "preFID_cancelled_or_shelved": int(pre["Status"].isin(["cancelled", "shelved"]).sum())}
    resolved = st.get("operating", 0) + st.get("cancelled", 0) + st.get("shelved", 0)
    row["completion_rate_resolved"] = st.get("operating", 0) / resolved if resolved else float("nan")
    out.append(row)
rcs = pd.DataFrame(out)
rcs.to_csv(os.path.join(PRO, "gem_reference_class.csv"), index=False)
print(rcs.T.to_string())
print("FIDStatus values:", p["FIDStatus"].dropna().unique()[:12])
print("RouteType values:", p["RouteType"].dropna().unique()[:12])

# EastMed geometry (GEM digitised route)
g = gpd.read_file(os.path.join(RAW, "GEM-GGIT-Gas-Pipelines-2025-11", "GEM-GGIT-Gas-Pipelines-2025-11.geojson"))
em = g[g["PipelineName"].astype(str).str.contains("EastMed", case=False)]
em.to_file(os.path.join(PRO, "gem_eastmed_route.geojson"), driver="GeoJSON")
print(em[["PipelineName", "SegmentName", "Status", "RouteAccuracy", "LengthMergedKm"]].to_string(index=False))
