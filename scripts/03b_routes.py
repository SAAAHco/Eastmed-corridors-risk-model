"""Route exposure per corridor and update of config/corridors.yaml.

Routes run through documented nodes (landing points / converter sites named in
the EU Union lists, TYNDP 2024 and project ESIAs; docs/research/B_coordinates.csv
and A_corridor_parameters.csv). Where a node has no published coordinates, the
named place is geocoded at feature level where an OpenStreetMap feature exists
(power-station site, terminal station, coastal village), otherwise at town level (flagged);
see NODE_SOURCE. Node review of 8 Oct 2026: Korakia replaces the inland Damasta converter as
the GSI/EuroAfrica Crete end; Atherinolakkos moved ~13 km east to the power-station coast. Between nodes the route is the
geodesic; the one documented intermediate constraint is the Kasos strait
(GSI survey area, July 2024). GREGY's routing is unpublished, so a west-of-Crete
and an east-of-Crete variant are both computed.

Cost uses published route lengths; the contested share x comes from GIS.
"""
import importlib.util
import os
import sys

import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from emcorr import geo as G   # noqa: E402

spec = importlib.util.spec_from_file_location("rx", os.path.join(HERE, "03_route_exposure.py"))
rx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rx)

# (lon, lat). Source / method for each node in NODE_SOURCE.
N = {
    "leviathan": (33.61722, 33.16778), "vasilikos": (33.290, 34.720), "atherinolakkos": (26.145, 35.000),
    "sideros": (26.32, 35.33), "crete_n1": (25.00, 35.55), "crete_n2": (24.00, 35.65), "laconia": (23.058, 36.600),
    "crete_s1": (24.50, 34.75), "crete_sw": (23.40, 35.20), "antikythera": (23.20, 35.90),
    "hadera": (34.870, 32.440), "kofinou": (33.39167, 34.82583), "kasos_strait": (26.55, 35.42),
    "damasta": (24.923, 35.353), "korakia": (24.9316, 35.4042), "burullus": (30.90, 31.60), "sidi_barrani": (25.926, 31.611),
    "sw_crete": (23.90, 35.00), "kythira_strait": (23.25, 35.85), "sounion": (24.03, 37.65),
    "attica_e": (24.15, 37.90), "nea_makri": (23.99, 38.08), "kasos_e": (26.60, 34.90), "cyclades": (25.00, 37.00),
}
NODE_SOURCE = {
    "leviathan": "B:EASTMED_01_LEVIATHAN (medium)", "vasilikos": "A:EM_LANDFALL_CYPRUS LF1 Vasilikos industrial area, coast at the power-station site (OSM feature; medium)",
    "atherinolakkos": "A:EM_LANDFALL_CRETE LF2, coast at the Atherinolakkos power-station site (OSM feature; ESIA NTS: stations adjacent to the PPC plant ~800 m NW of LF2; medium)", "laconia": "A:EM_LANDFALL_PELOPONNESE LF3, 300 m N of Agios Fokas (OSM place; medium)",
    "hadera": "B:GSI_01_HADERA_IL, Hadera shoreline (coast geocode; converter 'in the Hadera area' per ADMIE 13.08.2026, 2 km onshore in Israel per TED notice 70566-2018 (OJ S 32/2018); site not published; low)", "kofinou": "B:GSI_02_KOFINOU_CY (medium)",
    "korakia": "B:GSI_03_KORAKIA_LANDING_CRETE, Union-list landing Korakia (OSM feature: Korakia terminal station, Fodele; medium)",
    "kasos_strait": "documented survey area (B:GSI_05, A:GSI_TL_10); point geocoded mid-strait",
    "burullus": "A:EA_ROUTE Kafr El Sheikh/Burullus coast (geocoded, area)",
    "sidi_barrani": "A:GREGY_LAND Sidi Barrani shore, Reg. 2026/764 (OSM place on the coast; medium)",
    "nea_makri": "A:GREGY_LAND Nea Makri / Mesogeia (geocoded, town)",
}
ROUTES = {
    "O1_EastMed": {"base": ["leviathan", "vasilikos", "atherinolakkos", "sideros", "crete_n1", "crete_n2", "laconia"],
                   "alt": ["leviathan", "vasilikos", "atherinolakkos", "crete_s1", "crete_sw", "antikythera", "laconia"]},
    "O3_GSI": {"base": ["hadera", "kofinou", "kasos_strait", "korakia"]},
    "O4a_GREGY": {"west": ["sidi_barrani", "sw_crete", "kythira_strait", "sounion", "attica_e", "nea_makri"],
                  "east": ["sidi_barrani", "kasos_e", "kasos_strait", "cyclades", "sounion", "attica_e", "nea_makri"]},
    "O4b_EuroAfrica": {"base": ["burullus", "kofinou", "kasos_strait", "korakia"]},
}
EEZ_KEY = {"IL": "Israeli Exclusive Economic Zone", "CY": "Cypriote Exclusive Economic Zone",
           "GR": "Greek Exclusive Economic Zone", "EG": "Egyptian Exclusive Economic Zone"}


def main():
    df = pd.read_csv(rx.COORD)
    eez = rx.load_eez()
    Z = rx.zones(df, eez)
    rows = []
    for opt, variants in ROUTES.items():
        for var, nodes in variants.items():
            line = G.densify_route([N[n] for n in nodes], step_km=1.0)
            ex = G.route_exposure(line, Z)
            eezkm = {cc: G.km_inside(line, eez[name]) for cc, name in EEZ_KEY.items()}
            rows.append({"option": opt, "variant": var, **{k: round(v, 3) for k, v in ex.items()},
                         **{f"eez_km_{k}": round(v, 1) for k, v in eezkm.items()}})
    out = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "outputs", "tables"), exist_ok=True)
    out.to_csv(os.path.join(ROOT, "outputs", "tables", "route_exposure.csv"), index=False)
    pd.set_option("display.width", 250)
    print(out[["option", "variant", "total_km", "any_contested_km", "any_contested_share", "TR_vs_GR_km",
               "TR_vs_CY_km", "LY_vs_GR_km", "eez_km_IL", "eez_km_CY", "eez_km_GR", "eez_km_EG"]].to_string(index=False))

    cpath = os.path.join(ROOT, "config", "corridors.yaml")
    cor = yaml.safe_load(open(cpath, encoding="utf-8"))
    for opt in ROUTES:
        q = out[out.option == opt]
        x = float(q.any_contested_share.mean())
        km = {cc: float(q[f"eez_km_{cc}"].mean()) for cc in EEZ_KEY}
        tot = sum(km.values())
        cor[opt]["x_contested"] = round(x, 4)
        cor[opt]["x_contested_range"] = [round(float(q.any_contested_share.min()), 4), round(float(q.any_contested_share.max()), 4)]
        cor[opt]["weights"] = {cc: round(v / tot, 4) for cc, v in km.items() if v / tot > 0.005}
        cor[opt]["waypoints"] = [list(N[n]) for n in list(ROUTES[opt].values())[0]]
        cor[opt]["status"] = "GIS: scripts/03b_routes.py; nodes " + "; ".join(sorted({NODE_SOURCE.get(n, 'geodesic waypoint') for v in ROUTES[opt].values() for n in v} - {'geodesic waypoint'}))[:400]
    yaml.safe_dump(cor, open(cpath, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    print("\ncorridors.yaml updated: x_contested =", {k: cor[k]["x_contested"] for k in ROUTES})


if __name__ == "__main__":
    main()