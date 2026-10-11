"""Route exposure to contested maritime zones (GIS).

Contested zone = water claimed by Greece or Cyprus (Marine Regions v12 EEZ
polygons, which follow their median-line claims) that Turkey or Libya also
claim through instruments notified to the UN:
  * Turkey: A/74/550 (median line with Egypt, points A-N, 28E to 32-16-18E;
    meridian 32-16-18E west of Cyprus), A/68/857 (Turkey-TRNC 2011 shelf line),
    Turkey-Libya MoU 2019 (UNTS I-56119, points A-B).
  * Libya: eastern border claim (A/77/742, 2023) and northern continental-shelf
    limit (A/79/916, 2025), which incorporates the MoU A-B segment.
Claim lines are only partly defined, so each claim polygon is closed through
the claimant's own land or along a documented straight closing line; the
closures are listed in CLOSURES and varied in the sensitivity run.

Inputs : docs/research/B_coordinates.csv, data/raw/marineregions/*.geojson
Outputs: outputs/tables/route_exposure.csv, data/processed/contested_zones.geojson,
         config/corridors.yaml (x_contested, subsea_km, weights updated)
"""
import json
import os
import sys

import geopandas as gpd
import pandas as pd
import yaml
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from emcorr import geo as G   # noqa: E402

COORD = os.path.join(ROOT, "docs", "research", "B_coordinates.csv")
MR = os.path.join(ROOT, "data", "raw", "marineregions")


def line(df, fid):
    """Ordered (lon, lat) vertices of one feature."""
    q = df[df.feature_id == fid].sort_values("seq")
    if q.empty:
        raise KeyError(fid)
    bad = q[q.lat.isna() | q.lon.isna()]
    if len(bad):   # unparseable published vertex: drop it and say so
        print(f"note: {fid}: dropped {len(bad)} vertex/vertices with missing coordinates (seq {list(bad.seq)})")
        q = q.drop(bad.index)
    return list(zip(q.lon.astype(float), q.lat.astype(float)))


def load_eez():
    parts = []
    for f in ("eez_eastmed.geojson", "eez_eastmed_west.geojson"):
        parts.append(gpd.read_file(os.path.join(MR, f)))
    g = pd.concat(parts, ignore_index=True)
    g = g[~g.geoname.str.contains("Hawaii")]
    g = g.dissolve(by="geoname", as_index=False)
    return {r.geoname: r.geometry for r in g.itertuples()}


# Closing paths through the claimant's own territory (land is irrelevant for
# subsea routes) - documented assumptions, varied in sensitivity.
CLOSURES = {
    # Turkish mainland behind the south coast, east to the Syrian border.
    "TR_land": [(36.20, 36.60), (36.20, 38.20), (27.00, 38.20)],
    # Libyan mainland behind the coast from the Egyptian border westwards.
    "LY_land": [(12.0, 32.8), (12.0, 29.5), (25.10, 29.5), (25.10, 31.55)],
}


def turkey_claim(df, west_anchor=(27.374409, 36.680635)):
    """Turkey's claimed shelf in the East Med as a polygon (lon, lat)."""
    mou = line(df, "TR_LY_MOU_2019_LINE")                     # A (west) -> B (east)
    med = line(df, "TR_CLAIM_TURKEY_EGYPT_MEDIAN_LINE")       # A (28E) -> N (32-16-18E)
    trnc = line(df, "TR_CLAIM_TRNC_2011_SHELF_LINE")          # 1 (32-16-18E) -> 27 (east)
    ring = [west_anchor] + mou + med + [(32.271667, trnc[0][1])] + trnc + CLOSURES["TR_land"]
    return Polygon(ring).buffer(0)


def libya_claim(df):
    """Libya's claimed continental shelf, from its UN-notified lines: the eastern
    border with Egypt (A/77/742, 2023: land terminus -> point B) and the northern
    outer limit (A/79/916, 2025: point B -> A -> 1..32, west to 12 E), closed
    through Libyan territory."""
    east = line(df, "LY_CLAIM_EASTERN_BORDER_2023")       # land terminus ... -> B
    north = line(df, "LY_CLAIM_CS_NORTH_2025")            # B -> A -> ... -> 12 E
    if abs(east[-1][0] - north[0][0]) < 1e-6 and abs(east[-1][1] - north[0][1]) < 1e-6:
        north = north[1:]                                 # shared point B
    ring = east + north + CLOSURES["LY_land"]
    return Polygon(ring).buffer(0)


def zones(df, eez):
    gr, cy = eez["Greek Exclusive Economic Zone"], eez["Cypriote Exclusive Economic Zone"]
    tr, ly = turkey_claim(df), libya_claim(df)
    return {"TR_vs_GR": tr.intersection(gr), "TR_vs_CY": tr.intersection(cy),
            "LY_vs_GR": ly.intersection(gr)}


def main():
    df = pd.read_csv(COORD)
    eez = load_eez()
    Z = zones(df, eez)
    allz = unary_union(list(Z.values()))
    feats = [{"type": "Feature", "properties": {"zone": k}, "geometry": mapping(v)} for k, v in Z.items()]
    with open(os.path.join(ROOT, "data", "processed", "contested_zones.geojson"), "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    for k, v in Z.items():
        print(f"{k:10s} area {gpd.GeoSeries([v], crs=4326).to_crs(3035).area.iloc[0] / 1e6:10.0f} km2")
    print(f"union      area {gpd.GeoSeries([allz], crs=4326).to_crs(3035).area.iloc[0] / 1e6:10.0f} km2")
    return df, eez, Z


if __name__ == "__main__":
    main()