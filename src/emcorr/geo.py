"""Route geometry and exposure to contested maritime zones.

Routes are polylines through landing points/waypoints (lon, lat; WGS84),
densified along geodesics so that planar intersection in lon/lat introduces
negligible error. Lengths are always measured geodesically (WGS84 ellipsoid).
"""
from __future__ import annotations

import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, MultiLineString, Polygon, shape
from shapely.ops import unary_union

GEOD = Geod(ellps="WGS84")


def densify_route(waypoints, step_km: float = 2.0) -> LineString:
    """Geodesic polyline through waypoints [(lon, lat), ...] with ~step_km spacing."""
    pts = []
    for (lon1, lat1), (lon2, lat2) in zip(waypoints[:-1], waypoints[1:]):
        _, _, dist_m = GEOD.inv(lon1, lat1, lon2, lat2)
        n_inner = max(int(dist_m / 1000.0 / step_km) - 1, 0)
        seg = [(lon1, lat1)]
        if n_inner > 0:
            seg += GEOD.npts(lon1, lat1, lon2, lat2, n_inner)
        pts.extend(seg)
    pts.append(tuple(waypoints[-1]))
    return LineString(pts)


def length_km(geom) -> float:
    """Geodesic length in km of a (Multi)LineString in lon/lat."""
    if geom is None or geom.is_empty:
        return 0.0
    return GEOD.geometry_length(geom) / 1000.0


def km_inside(route: LineString, area) -> float:
    """Geodesic km of `route` lying inside polygon/multipolygon `area`."""
    if area is None or area.is_empty:
        return 0.0
    inter = route.intersection(area)
    if inter.is_empty:
        return 0.0
    # keep only linear parts (intersection may include points on boundaries)
    if inter.geom_type in ("LineString", "MultiLineString"):
        return length_km(inter)
    lines = [g for g in getattr(inter, "geoms", []) if g.geom_type in ("LineString", "MultiLineString")]
    return length_km(MultiLineString([l for g in lines for l in getattr(g, "geoms", [g])])) if lines else 0.0


def overlap(claim_a, claim_b):
    """Contested area = intersection of two incompatible claims."""
    return claim_a.intersection(claim_b)


def contested_union(pairs):
    """Union of overlapping-claim areas from an iterable of (claim_a, claim_b)."""
    parts = [overlap(a, b) for a, b in pairs]
    parts = [p for p in parts if not p.is_empty]
    return unary_union(parts) if parts else Polygon()


def polygon_from_coords(lonlat):
    """Polygon from [(lon, lat), ...] (closed automatically)."""
    return Polygon(lonlat)


def geojson_to_geom(feature_or_geometry):
    g = feature_or_geometry.get("geometry", feature_or_geometry)
    return shape(g)


def route_exposure(route: LineString, zones: dict) -> dict:
    """Km and share of a route inside each named zone plus the union of all zones."""
    total = length_km(route)
    out = {"total_km": total}
    for name, area in zones.items():
        km = km_inside(route, area)
        out[f"{name}_km"] = km
        out[f"{name}_share"] = km / total if total else 0.0
    if zones:
        u = unary_union([z for z in zones.values() if z is not None and not z.is_empty])
        km = km_inside(route, u)
        out["any_contested_km"] = km
        out["any_contested_share"] = km / total if total else 0.0
    return out
