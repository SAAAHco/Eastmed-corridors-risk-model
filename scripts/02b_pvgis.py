"""PVGIS (EU JRC) yields at representative utility-scale PV sites; logged in MANIFEST.

Sites are resource zones where utility-scale PV is built or planned, not capitals.
Configurations: fixed at optimal tilt/azimuth (optimalangles=1); fixed horizontal
(a request with trackingtype=1, which PVcalc ignores; the response mounting is
fixed, slope 0); single inclined N-S axis tracker at optimal inclination
(inclined_axis=1, inclined_optimum=1).
"""
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
dl = import_module("02_download_data")

SITES = {  # name: (country, lat, lon, note)
    "GR_Kozani": ("GR", 40.30, 21.79, "West Macedonia PV cluster"),
    "GR_Megalopolis": ("GR", 37.40, 22.14, "Peloponnese"),
    "GR_Crete_Heraklion": ("GR", 35.25, 25.10, "Crete"),
    "IL_Ashalim": ("IL", 30.96, 34.70, "Negev"),
    "IL_Ketura": ("IL", 29.97, 35.06, "Arava"),
    "EG_Benban": ("EG", 24.45, 32.73, "Benban solar park, Aswan"),
    "EG_Zafarana": ("EG", 29.11, 32.65, "Gulf of Suez coast"),
    "EG_WestNile_KomOmbo": ("EG", 24.47, 32.95, "Kom Ombo"),
    "EG_SidiBarrani": ("EG", 31.55, 25.95, "GREGY dedicated RES zone, Matrouh coast"),
    "CY_Larnaca": ("CY", 34.95, 33.55, "Larnaca district"),
    "CY_Nicosia": ("CY", 35.12, 33.25, "Nicosia district"),
}
BASE = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"

CONFIGS = {  # label: (file suffix, extra query params, totals key in response)
    "fixed_optimal": ("track0", {"optimalangles": 1}, "fixed"),
    "fixed_horizontal": ("track1", {"trackingtype": 1}, "fixed"),
    "single_inclined_axis": ("inclined", {"inclined_axis": 1, "inclined_optimum": 1}, "inclined_axis"),
}
out = []
for name, (cc, lat, lon, note) in SITES.items():
    for label, (suffix, extra, key) in CONFIGS.items():
        q = {"lat": lat, "lon": lon, "peakpower": 1, "loss": 14, "outputformat": "json", **extra}
        url = requests.Request("GET", BASE, params=q).prepare().url
        path = dl.fetch("pvgis", url, f"{name}_{suffix}.json")
        j = json.load(open(path))
        tot = j["outputs"]["totals"]
        ey = tot[key]["E_y"]
        db = j["inputs"]["meteo_data"]["radiation_db"]
        out.append({"site": name, "country": cc, "lat": lat, "lon": lon, "config": label,
                    "E_y_kwh_per_kwp": ey, "cf": ey / 8760.0, "radiation_db": db, "note": note})
        time.sleep(1.5)
import pandas as pd
df = pd.DataFrame(out)
pro = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "processed", "pvgis_site_yields.csv")
df.to_csv(pro, index=False)
print(df.pivot_table(index=["country", "site"], columns="config", values="cf").round(3).to_string())
