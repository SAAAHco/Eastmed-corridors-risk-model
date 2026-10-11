"""Supplementary-information figures (Fig. S1-S19). Run after 10_run_model.py and 11_scenarios.py.

Usage: python scripts/21_si_figures.py [1 2 ...]   (default: all)
Output: outputs/figures/si/FigS*_*.png (600 dpi) and .eps
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from figlib import (ACCENT, CABLES, COAST, EEZC, FIXED_ASSET, FREE, GRIDC, IMPORTS, INK, INK2, LAND, LAYER,  # noqa: E402
                    LAYER_KEYS, MM, OPT, OPTIONS, ROOT, SEA, TAB, W1, W15, W2, ZONE, corridors, diverging,
                    evaluate_grid, hgrid, increments, kde, load_draws, panel, plabel, plt, register, save, shade, style,
                    PARAM_LABEL)
import matplotlib.patheffects as pe      # noqa: E402
from matplotlib.lines import Line2D      # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

HALO = [pe.withStroke(linewidth=1.6, foreground="white")]


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _basemap(ax, ext, land):
    x0, x1, y0, y1 = ext
    ax.set_facecolor(SEA)
    land.cx[x0 - 3:x1 + 3, y0 - 3:y1 + 3].plot(ax=ax, facecolor=LAND, edgecolor=COAST, lw=0.3, zorder=1)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect(1 / np.cos(np.deg2rad((y0 + y1) / 2)))
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}°E"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}°N"))


def _zones(ax, alpha=0.9):
    import geopandas as gpd
    z = gpd.read_file(os.path.join(ROOT, "data", "processed", "contested_zones.geojson"))
    for key, (lab, tint, hcol, hatch) in ZONE.items():
        z[z.zone == key].plot(ax=ax, facecolor=tint, edgecolor=hcol, hatch=hatch, lw=0, alpha=alpha, zorder=2)
    return z


def _land():
    import geopandas as gpd
    return gpd.read_file("zip://" + os.path.join(ROOT, "data", "raw", "naturalearth", "ne_10m_land.zip"))


# ---------------------------------------------------------------------------------------------
# S1  Construction of the overlapping-claim zones from UN-notified lines
# ---------------------------------------------------------------------------------------------
LINES = [
    ("TR_LY_MOU_2019_LINE", "Türkiye-Libya MoU line (2019)", "#C0392B", "-"),
    ("TR_CLAIM_TURKEY_EGYPT_MEDIAN_LINE", "Türkiye: median line with Egypt (A/74/550)", "#E67E22", "-"),
    ("TR_CLAIM_WEST_OF_CYPRUS_MERIDIAN_32E16", "Türkiye: 32°16′18″E limit west of Cyprus", "#F4D03F", "-"),
    ("TR_CLAIM_TRNC_2011_SHELF_LINE", "Türkiye-TRNC shelf line (2011)", "#A04000", "-"),
    ("LY_CLAIM_CS_NORTH_2025", "Libya: continental-shelf limit (A/79/916)", "#1E8449", "-"),
    ("LY_CLAIM_EASTERN_BORDER_2023", "Libya: eastern border claim (A/77/742)", "#58D68D", "-"),
    ("EG_CLAIM_WESTERN_BOUNDARY_DECREE595_2022", "Egypt: western boundary (Decree 595/2022)", "#5DADE2", (0, (3, 1.5))),
    ("GR_EG_EEZ_2020_LINE", "Greece-Egypt EEZ agreement (2020)", "#1F618D", (0, (3, 1.5))),
    ("CY_EG_EEZ_2003_LINE", "Cyprus-Egypt EEZ agreement (2003)", "#7D3C98", (0, (3, 1.5))),
    ("CY_IL_EEZ_2010_LINE", "Cyprus-Israel EEZ agreement (2010)", "#17A589", (0, (3, 1.5))),
    ("IL_LB_MBL_2022_LINE", "Israel-Lebanon boundary (2022)", "#B9770E", (0, (3, 1.5))),
    ("CY_LB_EEZ_2025_LINE", "Cyprus-Lebanon EEZ agreement (2025)", "#EC7063", (0, (3, 1.5))),
]


def s1():
    from pyproj import Geod
    rx = _load("rx", "03_route_exposure.py")
    df = pd.read_csv(rx.COORD)
    land = _land()
    fig, ax = plt.subplots(figsize=(W2, 112 * MM))
    _basemap(ax, (18.5, 36.5, 30.0, 38.6), land)
    z = _zones(ax, alpha=0.75)
    geod = Geod(ellps="WGS84")
    for r in z.itertuples():
        a = abs(geod.geometry_area_perimeter(r.geometry)[0]) / 1e6
        c = r.geometry.representative_point()
        ax.text(c.x, c.y, f"{a:,.0f} km²", fontsize=5.6, ha="center", va="center", color=shade(ZONE[r.zone][2], 0.7),
                fontweight="bold", path_effects=HALO, zorder=9)
    handles = []
    for fid, lab, col, ls in LINES:
        try:
            pts = np.array(rx.line(df, fid))
        except KeyError:
            continue
        ax.plot(pts[:, 0], pts[:, 1], color=col, lw=1.1, ls=ls, zorder=6,
                path_effects=[pe.Stroke(linewidth=2.0, foreground="white"), pe.Normal()])
        handles.append(Line2D([], [], color=col, lw=1.1, ls=ls, label=lab))
    handles += [Patch(facecolor=t, edgecolor=hc, hatch=hh, lw=0.4, label=l) for l, t, hc, hh in ZONE.values()]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=5.8, handlelength=2.2)
    ax.set_title("Claim lines notified to the UN and the resulting overlaps with Greek and Cypriot EEZ claims",
                 loc="left", fontsize=6.8)
    save(fig, "FigS1_claim_construction", si=True)


# ---------------------------------------------------------------------------------------------
# S2  Route variants and their exposure
# ---------------------------------------------------------------------------------------------
def s2():
    rt = _load("rt", "03b_routes.py")
    exp = pd.read_csv(os.path.join(TAB, "route_exposure.csv")).set_index(["option", "variant"])
    land = _land()
    fig, axs = plt.subplots(1, 2, figsize=(W2, 78 * MM), gridspec_kw={"wspace": 0.12})
    cases = [("O4a_GREGY", [("west", "-"), ("east", (0, (3, 1.5)))], (21.5, 28.5, 31.2, 38.4), "GREGY routing options"),
             ("O1_EastMed", [("base", "-"), ("alt", (0, (3, 1.5)))], (22.0, 34.2, 32.6, 37.6), "EastMed alignments")]
    for ax, (k, vars_, ext, title), letter in zip(axs, cases, "ab"):
        _basemap(ax, ext, land)
        _zones(ax)
        for var, ls in vars_:
            pts = np.array([rt.N[n] for n in rt.ROUTES[k][var]])
            r = exp.loc[(k, var)]
            ax.plot(pts[:, 0], pts[:, 1], color=OPT[k][2] if var in ("west", "base") else shade(OPT[k][2], 0.65),
                    lw=1.4, ls=ls, zorder=6, path_effects=[pe.Stroke(linewidth=2.5, foreground="white"), pe.Normal()],
                    label=f"{var}: {r.total_km:,.0f} km, {r.any_contested_share:.0%} in overlapping claims")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), fontsize=5.6, ncol=1)
        ax.set_title(title, loc="left", fontsize=6.8)
        panel(ax, letter, x=-0.04, y=1.0)
    save(fig, "FigS2_route_variants", si=True)


# ---------------------------------------------------------------------------------------------
# S3  Distributions of the most influential uncertain parameters
# ---------------------------------------------------------------------------------------------
def s3():
    sys.path.insert(0, HERE)
    f20 = _load("f20", "20_figures.py")
    sob = pd.read_csv(os.path.join(TAB, "sobol_indices.csv"))
    top = sob.groupby("param").ST.max().sort_values(ascending=False).head(20).index.tolist()
    df, Pb = register()
    meta = df.set_index("name")
    _, par = load_draws()
    fig, axs = plt.subplots(4, 5, figsize=(W2, 158 * MM), gridspec_kw={"hspace": 1.05, "wspace": 0.35})
    for ax, p in zip(axs.ravel(), top):
        import textwrap
        col = f20.GROUP[f20.pgroup(p)][1]
        unit = str(meta.loc[p, "unit"]) if p in meta.index else ""
        x, c0 = par[p], Pb[p]
        if unit == "EUR2025":
            x, c0, unit = x / 1e9, c0 / 1e9, "EUR billion (2025)"
        hi = np.percentile(x, 99.5)
        ax.hist(x[x <= hi], bins=40, density=True, color=shade(col, 1.45), edgecolor=col, lw=0.4)
        ax.axvline(c0, color=shade(col, 0.55), lw=1.0)
        title = textwrap.fill(PARAM_LABEL.get(p, p), 24)
        if p in meta.index and meta.loc[p, "status"] == "judgment":
            title += "$^{" + chr(92) + "dagger}$"
        ax.set_title(title, fontsize=5.8, loc="left", pad=3)
        ax.set_xlabel(unit if unit not in ("-", "nan") else "share", fontsize=5.6)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.tick_params(labelsize=5.4)
    h = [Patch(color=c, label=l) for l, c in f20.GROUP.values()]
    h.append(Line2D([], [], color=INK2, lw=1.0, label="Central value (mode or median)"))
    fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.04), fontsize=5.8)
    fig.text(0.99, -0.04, "† judgment parameter; axes clipped at the 99.5th percentile", ha="right", fontsize=5.6, color=INK2)
    save(fig, "FigS3_parameter_distributions", si=True)


# ---------------------------------------------------------------------------------------------
# S4  Reference-class execution risk and contested-waters delay
# ---------------------------------------------------------------------------------------------
def s4():
    from emcorr import mc
    df, Pb = register()
    rows = df.set_index("name")
    u = np.linspace(0.001, 0.999, 999)
    fig, axs = plt.subplots(1, 3, figsize=(W2, 58 * MM), gridspec_kw={"wspace": 0.38})
    cols = {"hvdc": "#009E73", "pipe": "#0072B2"}
    labs = {"hvdc": "Subsea HVDC", "pipe": "Offshore gas pipeline"}
    refs = {"hvdc": [(0.08, 0.5), (0.435, 0.95)], "pipe": [(0.15, 0.5), (0.83, 0.95)]}
    for cls in ("hvdc", "pipe"):
        r = rows.loc[f"overrun_{cls}"].to_dict()
        r["name"] = f"overrun_{cls}"
        x = mc._ppf(r, u)
        axs[0].plot(x * 100, u, color=cols[cls], lw=1.2, label=labs[cls])
        for xv, q in refs[cls]:
            axs[0].plot(xv * 100, q, "o", ms=3.5, mfc="white", mec=cols[cls], mew=0.9)
        r = rows.loc[f"delay_{cls}"].to_dict()
        r["name"] = f"delay_{cls}"
        d = mc._ppf(r, u)
        axs[1].plot(d * 12, u, color=cols[cls], lw=1.2, label=labs[cls])
    axs[0].set_xlabel("Cost overrun (%)")
    axs[0].set_ylabel("Cumulative probability")
    axs[0].set_xlim(-10, 150)
    axs[0].legend(loc="lower right", fontsize=5.6)
    axs[0].text(0.97, 0.38, "circles: reference-class\nmedian and 95th percentile", transform=axs[0].transAxes,
                ha="right", fontsize=5.3, color=INK2)
    axs[1].set_xlabel("Reference-class delay (months)")
    axs[1].set_xlim(0, 96)
    axs[1].legend(loc="lower right", fontsize=5.6)
    res, par = load_draws()
    cor = corridors()
    for o in FIXED_ASSET:
        cls = "pipe" if o == "O1_EastMed" else "hvdc"
        kap = 1.0 if o == "O1_EastMed" else par["kappa_cable"]
        tot = (par[f"delay_{cls}"] + par["delta_contested"] * cor[o]["x_contested"] * kap) * 12
        g = np.linspace(0, 120, 400)
        d = kde(tot, g)
        axs[2].plot(g, d, color=OPT[o][2], lw=1.1, label=f"{OPT[o][1]} (mean {tot.mean():.0f} months)")
    axs[2].set_xlabel("Total delay (months)")
    axs[2].set_ylabel("Probability density")
    axs[2].legend(loc="upper right", fontsize=5.4, title="Reference class + contested waters", title_fontsize=5.4)
    for ax, letter in zip(axs, "abc"):
        hgrid(ax)
        panel(ax, letter, x=-0.16, y=1.02)
    save(fig, "FigS4_execution_risk", si=True)

# ---------------------------------------------------------------------------------------------
# S5  Cost of capital by layer
# ---------------------------------------------------------------------------------------------
def s5():
    from emcorr import options as O
    df, Pb = register()
    rows = df.set_index("name")
    cor = corridors()
    P = {k: np.float64(v) for k, v in Pb.items()}
    layers = [("L0: financed as a Greek asset", O.FLAGS[0], LAYER["base"][1]),
              ("L1: partner-country risk", O.FLAGS[1], LAYER["cost_of_capital"][1]),
              ("L4: plus contested-waters premium", O.FLAGS[4], LAYER["maritime"][1])]
    items = [("O1_EastMed", "pipe"), ("O3_GSI", "hvdc"), ("O4a_GREGY", "hvdc"), ("O4b_EuroAfrica", "hvdc")]
    fig, axs = plt.subplots(1, 2, figsize=(W2, 62 * MM), gridspec_kw={"width_ratios": [1.6, 1.0], "wspace": 0.38})
    ax, w = axs[0], 0.26
    for j, (lab, f, col) in enumerate(layers):
        vals = [float(O.seg_wacc_real(P, a, cor[k]["weights"], cor[k]["x_contested"], f)) * 100 for k, a in items]
        ax.bar(np.arange(4) + (j - 1) * w, vals, width=w * 0.95, color=col, label=lab)
        for i, v in enumerate(vals):
            ax.text(i + (j - 1) * w, v + 0.07, f"{v:.1f}", ha="center", va="bottom", fontsize=5.2)
    ax.set_xticks(range(4), [OPT[k][1] for k, _ in items])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Real after-tax WACC of the corridor (%)")
    ax.set_ylim(0, 8.5)
    ax.legend(loc="upper left", fontsize=5.6)
    hgrid(ax)
    panel(ax, "a", x=-0.1, y=1.02)
    bx = axs[1]
    gen = [("GR", "Greece (benchmark)", OPT["O5_Greek_RE"][2]), ("IL", "Israel (GSI)", OPT["O3_GSI"][2]),
           ("EG", "Egypt (GREGY, EuroAfrica)", OPT["O4a_GREGY"][2])]
    for i, (cc, lab, col) in enumerate(gen):
        r = rows.loc[f"wacc_re_{cc}"]
        bx.plot([r.low * 100, r.high * 100], [i, i], color=col, lw=2.2, alpha=0.45, solid_capstyle="butt")
        bx.plot(r.base * 100, i, "o", ms=5, color=col, mec=shade(col, 0.6), mew=0.6)
        bx.text(r.high * 100 + 0.4, i, f"{r.base * 100:.1f}%", va="center", fontsize=5.8)
    bx.plot(7.0, 2, "D", ms=4, mfc="white", mec=OPT["O4a_GREGY"][2], mew=0.9)
    bx.text(7.0, 1.72, "DFI-backed PPAs", ha="center", fontsize=5.3, color=INK2)
    bx.set_yticks(range(3), [g[1] for g in gen])
    bx.tick_params(axis="y", length=0)
    bx.invert_yaxis()
    bx.set_xlim(0, 18.5)
    bx.set_xlabel("Real after-tax WACC of renewables (%)")
    bx.spines["left"].set_visible(False)
    hgrid(bx, "x")
    panel(bx, "b", x=-0.62, y=1.02)
    save(fig, "FigS5_cost_of_capital", si=True)


# ---------------------------------------------------------------------------------------------
# S6  Renewable resource inputs
# ---------------------------------------------------------------------------------------------
def _power_curve(v, vr=10.5, vin=3.0, vout=25.0):
    p = np.clip((v ** 3 - vin ** 3) / (vr ** 3 - vin ** 3), 0, 1)
    return np.where((v < vin) | (v > vout), 0.0, p)


def _wind_cf(mean, k=2.0, vr=10.5, loss=0.12):
    from scipy.special import gamma
    v = np.linspace(0, 30, 3001)
    c = mean / gamma(1 + 1 / k)
    f = (k / c) * (v / c) ** (k - 1) * np.exp(-(v / c) ** k)
    return np.trapezoid(_power_curve(v, vr) * f, v) * (1 - loss)


def s6():
    pv = pd.read_csv(os.path.join(TAB, "..", "..", "data", "processed", "pvgis_site_yields.csv"))
    ccol = {"GR": OPT["O5_Greek_RE"][2], "IL": OPT["O3_GSI"][2], "EG": OPT["O4a_GREGY"][2], "CY": OPT["O4b_EuroAfrica"][2]}
    mk = {"fixed_horizontal": ("^", "Fixed, horizontal"), "fixed_optimal": ("o", "Fixed, optimal tilt"),
          "single_inclined_axis": ("s", "Single-axis tracking")}
    sites = pv.drop_duplicates("site").sort_values(["country", "lat"])
    fig, axs = plt.subplots(1, 2, figsize=(W2, 70 * MM), gridspec_kw={"wspace": 0.55})
    ax = axs[0]
    for i, s_ in enumerate(sites.itertuples()):
        q = pv[pv.site == s_.site].set_index("config")
        col = ccol[s_.country]
        ax.plot([q.cf.min(), q.cf.max()], [i, i], color=col, lw=0.8)
        for cfg, (m, lab) in mk.items():
            ax.plot(q.loc[cfg, "cf"], i, m, ms=3.8, mfc="white" if cfg == "fixed_horizontal" else col, mec=col, mew=0.8)
    nice = {"SidiBarrani": "Sidi Barrani", "WestNile_KomOmbo": "Kom Ombo", "Crete_Heraklion": "Heraklion, Crete"}
    ax.set_yticks(range(len(sites)), [nice.get(s_.site.split("_", 1)[1], s_.site.split("_", 1)[1]) + f" ({s_.country})"
                                      for s_ in sites.itertuples()],
                  fontsize=5.8)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Solar capacity factor (PVGIS-SARAH3, 14% losses)")
    ax.spines["left"].set_visible(False)
    hgrid(ax, "x")
    ax.legend(handles=[Line2D([], [], marker=m, ls="", ms=3.8, mfc="white" if c == "fixed_horizontal" else INK2,
                              mec=INK2, label=l) for c, (m, l) in mk.items()], loc="upper left", fontsize=5.5)
    panel(ax, "a", x=-0.55, y=1.02)
    bx = axs[1]
    ms = np.linspace(5, 11, 61)
    for k, vr, ls, col in [(2.0, 10.5, "-", "#7B52AB"), (2.5, 10.5, (0, (3, 1.5)), "#7B52AB"),
                           (2.0, 11.5, "-", "#2E86AB"), (2.5, 11.5, (0, (3, 1.5)), "#2E86AB")]:
        bx.plot(ms, [_wind_cf(m, k, vr) for m in ms], color=col, lw=1.0, ls=ls, label=f"rated {vr} m/s, Weibull k = {k}")
    bx.axvspan(7.3, 8.3, color=OPT["O4a_GREGY"][2], alpha=0.18, lw=0)
    bx.text(7.8, 0.13, "Sidi Barrani\ncoast", ha="center", fontsize=5.4, color=shade(OPT["O4a_GREGY"][2], 0.7))
    bx.axvspan(9.0, 10.0, color="#5DADE2", alpha=0.2, lw=0)
    bx.text(9.5, 0.13, "Gulf of\nSuez", ha="center", fontsize=5.4, color="#1F618D")
    for cf_ in (0.427, 0.511, 0.525):
        bx.plot(9.6, cf_, "D", ms=3.2, mfc="white", mec="#1F618D", mew=0.8)
    bx.axhline(0.38, color=OPT["O4a_GREGY"][2], lw=0.8, ls=(0, (2, 1.5)))
    bx.text(5.1, 0.39, "model mode 0.38", fontsize=5.4, color=shade(OPT["O4a_GREGY"][2], 0.7))
    bx.set_xlabel("Mean wind speed at hub height (m/s)")
    bx.set_ylabel("Net capacity factor")
    bx.set_ylim(0.1, 0.62)
    bx.legend(loc="upper left", fontsize=5.3)
    hgrid(bx)
    panel(bx, "b", x=-0.16, y=1.02)
    save(fig, "FigS6_resource_inputs", si=True)


# ---------------------------------------------------------------------------------------------
# S7  GREGY: dedicated portfolio behind a 3 GW cable
# ---------------------------------------------------------------------------------------------
def _profiles(years=6, seed=1):
    from scipy.special import gamma
    from scipy.stats import norm, weibull_min
    rng = np.random.default_rng(seed)
    H = 8760 * years
    z = np.empty(H)
    z[0] = 0
    e = rng.standard_normal(H) * np.sqrt(1 - 0.97 ** 2)
    for t in range(1, H):
        z[t] = 0.97 * z[t - 1] + e[t]
    u = norm.cdf(z)
    c = 7.69 / gamma(1 + 1 / 2.2)
    w = _power_curve(weibull_min.ppf(u, 2.2, scale=c)) * 0.88
    hrs, day = np.arange(H) % 24, (np.arange(H) // 24) % 365
    dl = 12 + 2.2 * np.sin(2 * np.pi * (day - 80) / 365)
    sh = np.where((hrs + 0.5 > 12 - dl / 2) & (hrs + 0.5 < 12 + dl / 2), np.sin(np.pi * (hrs + 0.5 - 12 + dl / 2) / dl), 0)
    sv = sh * np.repeat(np.clip(rng.normal(0.9, 0.12, H // 24), 0.2, 1.0), 24)
    return w / w.mean(), sv / sv.mean()


def s7():
    w, sv = _profiles()
    fig, axs = plt.subplots(1, 2, figsize=(W2, 64 * MM), gridspec_kw={"wspace": 0.32})
    ax = axs[0]
    out = 5.4 * np.minimum(w * 0.38, 1) + 3.1 * np.minimum(sv * 0.244, 1)
    srt = np.sort(out)[::-1]
    x = np.linspace(0, 100, len(srt))
    ax.fill_between(x, 0, np.minimum(srt, 3.0), color=OPT["O4a_GREGY"][2], alpha=0.75, lw=0, label="Exported through the cable")
    ax.fill_between(x, 3.0, np.maximum(srt, 3.0), color="#E0573F", alpha=0.45, lw=0, label="Sold in Egypt (above cable rating)")
    ax.plot(x, srt, color=shade(OPT["O4a_GREGY"][2], 0.6), lw=0.8)
    ax.axhline(3.0, color="#1F618D", lw=1.0, ls=(0, (3, 1.5)))
    ax.text(99, 3.12, "cable rating 3 GW", ha="right", fontsize=5.6, color="#1F618D")
    uf = np.minimum(out, 3).mean() / 3
    ax.text(50, 6.3, f"cable utilization {uf:.2f}; {1 - np.minimum(out, 3).sum() / out.sum():.0%} of output sold in Egypt",
            ha="center", fontsize=5.6)
    ax.set_xlabel("Share of hours (%)")
    ax.set_ylabel("Output of 5.4 GW wind + 3.1 GW solar (GW)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 7)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.86), fontsize=5.5)
    hgrid(ax)
    panel(ax, "a", x=-0.13, y=1.02)
    bx = axs[1]
    cfs = np.linspace(0.28, 0.50, 12)
    for (wg, sg, lab, col) in [(5.4, 3.1, "5.4 GW wind + 3.1 GW solar (Sep 2026)", OPT["O4a_GREGY"][2]),
                               (7.2, 2.3, "7.2 GW wind + 2.3 GW solar (Jan 2025)", "#7B52AB")]:
        ufs, sp = [], []
        for cf_ in cfs:
            o = wg * np.minimum(w * cf_, 1) + sg * np.minimum(sv * 0.244, 1)
            ufs.append(np.minimum(o, 3).mean() / 3)
            sp.append(1 - np.minimum(o, 3).sum() / o.sum())
        bx.plot(cfs, ufs, color=col, lw=1.2, label=f"{lab}: utilization")
        bx.plot(cfs, sp, color=col, lw=1.0, ls=(0, (3, 1.5)), label=f"{lab}: share sold in Egypt")
    bx.axvspan(0.30, 0.45, color=OPT["O4a_GREGY"][2], alpha=0.1, lw=0)
    bx.set_xlabel("Wind capacity factor")
    bx.set_ylabel("Share")
    bx.set_ylim(0, 1)
    bx.legend(loc="upper left", fontsize=5.0)
    hgrid(bx)
    panel(bx, "b", x=-0.13, y=1.02)
    save(fig, "FigS7_gregy_utilisation", si=True)


# ---------------------------------------------------------------------------------------------
# S8  Egypt gas balance components against history
# ---------------------------------------------------------------------------------------------
def s8():
    from emcorr import egypt as E
    _, par = load_draws()
    P = {k: v[:6000] for k, v in par.items()}
    yrs = np.arange(2025, 2046)
    b = E.balance(P, yrs)
    ei = pd.read_csv(os.path.join(ROOT, "data", "processed", "ei_gas_bcm.csv"))
    ei = ei[ei.country == "Egypt"]
    fig, axs = plt.subplots(2, 2, figsize=(W2, 100 * MM), gridspec_kw={"wspace": 0.25, "hspace": 0.45})
    spec = [("production", "Domestic production", "#2E86AB", ei[ei.variable == "production"]),
            ("demand", "Demand", "#C8443A", ei[ei.variable == "consumption"]),
            ("israel", "Israeli pipeline supply", "#F18F01", pd.DataFrame({"year": [2023, 2024, 2025], "bcm": [8.6, 10.0, 8.9]})),
            ("cyprus", "Cypriot pipeline supply", "#7FB800", None)]
    for ax, (k, lab, col, hist), letter in zip(axs.ravel(), spec, "abcd"):
        q = np.percentile(b[k], [5, 25, 50, 75, 95], axis=0)
        ax.fill_between(yrs, q[0], q[4], color=col, alpha=0.15, lw=0, label="5th-95th percentile")
        ax.fill_between(yrs, q[1], q[3], color=col, alpha=0.3, lw=0, label="interquartile range")
        ax.plot(yrs, q[2], color=col, lw=1.2, label="median")
        if hist is not None and len(hist):
            ax.plot(hist.year, hist.bcm, "o-", color=shade(col, 0.6), ms=2.8, lw=0.7, mfc="white", mew=0.8,
                    label="observed (EI 2026; Israeli ministry)")
        ax.set_title(lab, loc="left", fontsize=6.8)
        ax.set_xlim(2015, 2045)
        ax.set_ylabel("bcm per year")
        hgrid(ax)
        panel(ax, letter, x=-0.1, y=1.02)
    axs[0, 0].legend(loc="upper right", fontsize=5.4)
    save(fig, "FigS8_egypt_balance_components", si=True)


# ---------------------------------------------------------------------------------------------
# S9  Israeli supply interruptions
# ---------------------------------------------------------------------------------------------
def s9():
    import datetime as dt
    from emcorr import finance as F
    ep = [("Tamar", dt.date(2023, 10, 9), dt.date(2023, 11, 13), "35 d"),       # C:TAMAR_OCT2023
          ("Leviathan", dt.date(2025, 6, 13), dt.date(2025, 6, 25), "12 d"),   # C:LEV_KAR_JUN2025
          ("Karish", dt.date(2025, 6, 13), dt.date(2025, 6, 25), "~12 d"),     # restart date not documented
          ("Leviathan", dt.date(2026, 2, 28), dt.date(2026, 4, 2), "32-33 d"),  # C:LEV_2026
          ("Karish", dt.date(2026, 2, 28), dt.date(2026, 4, 9), "41 d")]       # C:KAR_2026
    rowy = {"Tamar": 0, "Leviathan": 1, "Karish": 2}
    fcol = {"Tamar": "#2E86AB", "Leviathan": "#C8443A", "Karish": "#7B52AB"}
    fig, axs = plt.subplots(1, 2, figsize=(W2, 56 * MM), gridspec_kw={"wspace": 0.3, "width_ratios": [1.5, 1]})
    ax = axs[0]
    for f, a, b_, lab in ep:
        x0 = a.year + (a.timetuple().tm_yday - 1) / 365
        x1 = b_.year + (b_.timetuple().tm_yday - 1) / 365
        approx = lab.startswith("~")
        ax.barh(rowy[f], max(x1 - x0, 0.02), left=x0, height=0.5, color=shade(fcol[f], 1.5) if approx else fcol[f],
                edgecolor=fcol[f], hatch="////" if approx else None, lw=0.5)
        ax.text(x1 + 0.03, rowy[f], lab, va="center", fontsize=5.6)
    for lab, x in [("Gaza war", 2023.77), ("June 2025 Iran strikes", 2025.45), ("2026 Iran war", 2026.16)]:
        ax.axvline(x, color="#E8A33D", lw=0.7, ls=(0, (2, 1.5)))
        ax.text(x, 2.62, lab, fontsize=5.3, ha="center", color=shade("#E8A33D", 0.65))
    ax.set_yticks(range(3), ["Tamar", "Leviathan", "Karish"])
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.set_xlim(2023.5, 2026.8)
    ax.set_xticks([2024, 2025, 2026])
    ax.set_ylim(2.9, -0.6)
    ax.set_xlabel("Government-ordered shutdowns of Israeli offshore fields")
    hgrid(ax, "x")
    panel(ax, "a", x=-0.12, y=1.02)
    bx = axs[1]
    _, par = load_draws()
    uw = F.unavailability(par["il_shutdown_rate"] * par["p_il_halt"], par["il_shutdown_days"])
    tot = F.combine_unavailability(uw, par["il_export_cut"])
    g = np.linspace(0, 0.2, 300)
    for v, lab, col in [(uw, "war shutdowns", "#C8443A"), (tot, "war shutdowns + export policy", "#7B52AB")]:
        d = kde(v, g)
        bx.plot(g * 100, d, color=col, lw=1.1, label=f"{lab} (mean {v.mean():.1%})")
    bx.set_xlabel("Expected unavailability of Israeli gas exports (%)")
    bx.set_ylabel("Probability density")
    bx.legend(loc="upper right", fontsize=5.4)
    hgrid(bx)
    panel(bx, "b", x=-0.16, y=1.02)
    save(fig, "FigS9_israel_interruptions", si=True)

# ---------------------------------------------------------------------------------------------
# S10  EastMed throughput under the EU gas-demand pathway
# ---------------------------------------------------------------------------------------------
def s10():
    from emcorr import finance as F
    _, par = load_draws()
    n = 5000
    tau = np.arange(0, 30.25, 0.25)
    p, d, f, u0 = (par[k][:n, None] for k in ("gasdem_plateau", "gasdem_decline", "gasdem_floor", "em_util0"))
    U = np.where(tau[None, :] < p, 1.0, np.exp(-d * (tau[None, :] - p)))
    U = np.maximum(U, f) * u0
    fig, axs = plt.subplots(1, 2, figsize=(W2, 58 * MM), gridspec_kw={"wspace": 0.3})
    col = OPT["O1_EastMed"][2]
    q = np.percentile(U, [5, 25, 50, 75, 95], axis=0)
    axs[0].fill_between(tau, q[0], q[4], color=col, alpha=0.15, lw=0, label="5th-95th percentile")
    axs[0].fill_between(tau, q[1], q[3], color=col, alpha=0.3, lw=0, label="interquartile range")
    axs[0].plot(tau, q[2], color=col, lw=1.2, label="median")
    axs[0].set_xlabel("Years after commissioning")
    axs[0].set_ylabel("Utilization of 10 bcm/yr capacity")
    axs[0].set_ylim(0, 1)
    axs[0].legend(loc="upper right", fontsize=5.6)
    hgrid(axs[0])
    panel(axs[0], "a", x=-0.13, y=1.02)
    pv = F.util_pv_factor(0.057, 30, par["gasdem_plateau"], par["gasdem_decline"], par["gasdem_floor"])
    g = np.linspace(0.3, 1.0, 300)
    axs[1].plot(g, kde(pv, g), color=col, lw=1.2)
    axs[1].fill_between(g, 0, kde(pv, g), color=col, alpha=0.25, lw=0)
    axs[1].axvline(np.median(pv), color=shade(col, 0.6), lw=0.9, ls=(0, (3, 1.5)))
    axs[1].text(np.median(pv) + 0.01, axs[1].get_ylim()[1] * 0.9, f"median {np.median(pv):.2f}", fontsize=5.6)
    axs[1].set_xlabel("PV-weighted utilization relative to full use (5.7% real)")
    axs[1].set_ylabel("Probability density")
    hgrid(axs[1])
    panel(axs[1], "b", x=-0.13, y=1.02)
    save(fig, "FigS10_eastmed_utilisation", si=True)


# ---------------------------------------------------------------------------------------------
# S11  Cost distributions layer by layer
# ---------------------------------------------------------------------------------------------
def s11():
    res, _ = load_draws()
    fig, axs = plt.subplots(2, 3, figsize=(W2, 100 * MM), gridspec_kw={"wspace": 0.25, "hspace": 0.45})
    g = np.linspace(20, 320, 600)
    for ax, o, letter in zip(axs.ravel(), OPTIONS, "abcdef"):
        for l, key in enumerate(LAYER_KEYS):
            x = res[o][l]
            if np.ptp(x) < 1e-9:
                ax.plot([x[0], x[0]], [l, l + 0.8], color=LAYER[key][1], lw=1.2)
                continue
            d = kde(x, g)
            d = 0.85 * d / d.max()
            keep = d > 0.004
            ax.fill_between(g[keep], l, l + d[keep], color=LAYER[key][1], alpha=0.45, lw=0)
            ax.plot(g[keep], l + d[keep], color=shade(LAYER[key][1], 0.7), lw=0.7)
            ax.plot(np.median(x), l, "|", ms=5, mew=1.0, color=shade(LAYER[key][1], 0.5))
        ax.set_yticks(range(5), ["L0", "L1", "L2", "L3", "L4"])
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(30, 300)
        ax.set_title(OPT[o][0], loc="left", fontsize=6.6)
        hgrid(ax, "x")
        ax.spines["left"].set_visible(False)
        panel(ax, letter, x=-0.08, y=1.02)
    for ax in axs[1]:
        ax.set_xlabel("EUR per MWh (2025 prices)")
    h = [Patch(color=LAYER[k][1], label=f"L{i}: {LAYER[k][0]}") for i, k in enumerate(LAYER_KEYS)]
    fig.legend(handles=h, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06), fontsize=5.8)
    save(fig, "FigS11_layer_distributions", si=True)


# ---------------------------------------------------------------------------------------------
# S12  Monte Carlo convergence
# ---------------------------------------------------------------------------------------------
def s12():
    res, _ = load_draws()
    ns = np.unique(np.logspace(2, np.log10(20000), 30).astype(int))
    fig, axs = plt.subplots(1, 2, figsize=(W2, 58 * MM), gridspec_kw={"wspace": 0.3})
    for o in OPTIONS:
        x = res[o][4]
        mu = [x[:n].mean() for n in ns]
        p95 = [np.percentile(x[:n], 95) for n in ns]
        axs[0].plot(ns, (np.array(mu) / x.mean() - 1) * 100, color=OPT[o][2], lw=1.0, label=OPT[o][1])
        axs[1].plot(ns, (np.array(p95) / np.percentile(x, 95) - 1) * 100, color=OPT[o][2], lw=1.0)
    for ax, t, letter in zip(axs, ["Mean, % deviation from N = 20,000", "95th percentile, % deviation"], "ab"):
        ax.set_xscale("log")
        ax.axhspan(-0.5, 0.5, color="#1AA391", alpha=0.12, lw=0)
        ax.axhline(0, color="#1AA391", lw=0.6)
        ax.set_xlabel("Number of Latin-hypercube draws")
        ax.set_ylabel(t)
        ax.set_ylim(-4, 4)
        hgrid(ax)
        panel(ax, letter, x=-0.13, y=1.02)
    axs[0].legend(loc="upper right", fontsize=5.4, ncol=2)
    axs[0].text(110, 0.7, "±0.5% band", fontsize=5.4, color=shade("#1AA391", 0.7))
    save(fig, "FigS12_convergence", si=True)


# ---------------------------------------------------------------------------------------------
# S13  Full matrix of total-order Sobol indices
# ---------------------------------------------------------------------------------------------
def s13():
    from matplotlib.colors import LinearSegmentedColormap
    sob = pd.read_csv(os.path.join(TAB, "sobol_indices.csv"))
    tl = {f"{o}_full": f"{OPT[o][1]}: total" for o in IMPORTS}
    tl.update({f"{o}_geopolitical": f"{OPT[o][1]}: geopolitical" for o in IMPORTS})
    tl.update({f"{o}_maritime": f"{OPT[o][1]}: maritime" for o in FIXED_ASSET})
    tl.update({"O3_minus_O1": "GSI − EastMed", "O4a_minus_O1": "GREGY − EastMed", "O4a_minus_O2": "GREGY − LNG"})
    params = sob.groupby("param").ST.max().sort_values(ascending=False).head(26).index
    M = sob.pivot(index="param", columns="target", values="ST").loc[params, list(tl)].clip(lower=0)
    cmap = LinearSegmentedColormap.from_list("seq", ["#FFF7D6", "#B7E3C0", "#4FB3BF", "#2166AC", "#3A1F7A"])
    df, _ = register()
    status = dict(zip(df.name, df.status))
    fig, ax = plt.subplots(figsize=(W2, 150 * MM))
    im = ax.imshow(M.values, aspect="auto", cmap=cmap, vmin=0, vmax=0.8)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            if v >= 0.05:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=4.8, color="white" if v > 0.4 else INK)
    ax.set_xticks(range(M.shape[1]), list(tl.values()), rotation=60, ha="right", fontsize=5.6)
    ax.set_yticks(range(M.shape[0]), [plabel(p, status.get(p)) for p in M.index], fontsize=5.8)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.outline.set_visible(False)
    cb.set_label("Total-order Sobol index", fontsize=6)
    cb.ax.tick_params(labelsize=5.6, length=1.5)
    save(fig, "FigS13_sobol_matrix", si=True)


# ---------------------------------------------------------------------------------------------
# S14  Break-even against the contested-waters premium and the legal factor
# ---------------------------------------------------------------------------------------------
def s14():
    b = pd.read_csv(os.path.join(TAB, "breakeven_sweep.csv"))
    kaps = sorted(b.kappa.unique())
    fig, axs = plt.subplots(1, len(kaps), figsize=(W2, 60 * MM), sharey=True, gridspec_kw={"wspace": 0.12})
    for ax, k, letter in zip(axs, kaps, "abc"):
        q = b[b.kappa == k]
        for o in IMPORTS:
            ax.plot(q.pi_contested * 100, q[o], color=OPT[o][2], lw=1.2, marker=OPT[o][3], ms=2.2, markevery=4,
                    label=OPT[o][0])
        ax.axvspan(0.3, 2.5, color=LAYER["maritime"][1], alpha=0.08, lw=0)
        ax.set_title(f"Legal factor for cables κ = {k:g}", fontsize=6.6, loc="left")
        hgrid(ax)
        panel(ax, letter, x=-0.06, y=1.02)
    axs[0].set_ylabel("Risk-adjusted cost at central values (EUR/MWh)")
    fig.supxlabel("Contested-waters WACC premium at full exposure (percentage points); shaded: sampled range",
                  fontsize=6.5, y=-0.02, color=INK)
    axs[-1].legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=5.8)
    save(fig, "FigS14_breakeven_premium", si=True)


# ---------------------------------------------------------------------------------------------
# S15  Sensitivity to carbon and gas prices
# ---------------------------------------------------------------------------------------------
def s15():
    res, par = load_draws()
    fig, axs = plt.subplots(1, 2, figsize=(W2, 62 * MM), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, p, lab, letter in [(axs[0], "p_co2", "EU ETS carbon price (EUR/t)", "a"),
                               (axs[1], "p_repl_gas", "Replacement gas price, TTF (EUR/MWh)", "b")]:
        x = par[p]
        edges = np.percentile(x, np.linspace(0, 100, 11))
        mids = 0.5 * (edges[1:] + edges[:-1])
        for o in OPTIONS:
            y = res[o][4]
            mu = [y[(x >= a) & (x <= c)].mean() for a, c in zip(edges[:-1], edges[1:])]
            ax.plot(mids, mu, color=OPT[o][2], lw=1.1, marker=OPT[o][3], ms=2.6, label=OPT[o][0])
        ax.set_xlabel(lab)
        hgrid(ax)
        panel(ax, letter, x=-0.04, y=1.02)
    axs[0].set_ylabel("Mean risk-adjusted cost (EUR/MWh), by decile")
    axs[1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=5.8)
    save(fig, "FigS15_price_sensitivity", si=True)


# ---------------------------------------------------------------------------------------------
# S16  CBAM treatment of electricity imports
# ---------------------------------------------------------------------------------------------
def s16():
    share = np.linspace(0, 1, 41)
    fig, ax = plt.subplots(figsize=(W15, 86 * MM))
    em = evaluate_grid({}, 1)["O1_EastMed"][4][0]
    ax.axhline(em, color=OPT["O1_EastMed"][2], lw=1.2, label="EastMed pipeline (not a CBAM good)")
    cases = [((0.387, 0.443), (0, (1, 1.2)), "grid average (Annex II; proposal basis)"),
             ((0.644, 0.583), (0, (4, 1.5)), "fossil-only (Ember 2025)"),
             ((0.442, 0.480), "-", "Annex III default (Reg. 2025/2621)")]
    for (ef_eg, ef_il), ls, _ in cases:
        r = evaluate_grid({"cbam_share_default": share, "cbam_ef_EG": ef_eg, "cbam_ef_IL": ef_il}, len(share))
        for o in CABLES:
            ax.plot(share * 100, r[o][4], color=OPT[o][2], lw=1.1, ls=ls)
    h = [Line2D([], [], color=OPT[o][2], lw=1.1, label=OPT[o][0]) for o in CABLES]
    h += [Line2D([], [], color=OPT["O1_EastMed"][2], lw=1.2, label="EastMed pipeline (not a CBAM good)")]
    h += [Line2D([], [], color=INK2, lw=1.0, ls=ls, label=f"{lab}: EG {ef_eg:.3f}, IL {ef_il:.3f} tCO$_2$/MWh")
          for (ef_eg, ef_il), ls, lab in cases]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=5.4, frameon=False)
    ax.set_xlabel("Share of cable imports charged CBAM at default values (%)")
    ax.set_ylabel("Risk-adjusted cost at central values (EUR/MWh)")
    hgrid(ax)
    save(fig, "FigS16_cbam", si=True)


# ---------------------------------------------------------------------------------------------
# S17  Correlated replacement prices
# ---------------------------------------------------------------------------------------------
def s17():
    from matplotlib.colors import LinearSegmentedColormap
    sc = _load("sc", "11_scenarios.py")
    from emcorr import mc
    df, _ = register()
    P, U = mc.sample_lhs(df, 20000)
    pe_ = sc.correlate(df, U, "p_repl_el", "p_repl_gas", 0.8)
    cmap = LinearSegmentedColormap.from_list("h", ["#FFF2CC", "#F9C2A8", "#E0573F", "#7A0F1F"])
    fig, axs = plt.subplots(1, 3, figsize=(W2, 58 * MM), gridspec_kw={"wspace": 0.4, "width_ratios": [1, 1, 1.15]})
    for ax, y, t, letter in [(axs[0], P["p_repl_el"], "Independent sampling", "a"),
                             (axs[1], pe_, "Gaussian copula, ρ = 0.8", "b")]:
        ax.hexbin(P["p_repl_gas"], y, gridsize=28, cmap=cmap, mincnt=1, linewidths=0)
        ax.set_xlabel("Replacement gas price (EUR/MWh)")
        ax.set_ylabel("Replacement electricity price (EUR/MWh)")
        ax.set_title(t, loc="left", fontsize=6.6)
        panel(ax, letter, x=-0.2, y=1.02)
    s_ = pd.read_csv(os.path.join(TAB, "scenarios.csv"))
    cx = axs[2]
    w = 0.38
    for j, (scn, lab, a) in enumerate([("base", "independent", 1.0), ("correlated_replacement_prices", "correlated", 0.55)]):
        q = s_[s_.scenario == scn].set_index("option")
        vals = [q.loc[o, "p_cheapest_import"] for o in IMPORTS]
        cx.bar(np.arange(5) + (j - 0.5) * w, vals, width=w * 0.95, color=[OPT[o][2] for o in IMPORTS], alpha=a,
               label=lab)
    cx.set_xticks(range(5), [OPT[o][1].replace("LNG via Egypt", "LNG") for o in IMPORTS], rotation=30, ha="right")
    cx.set_ylabel("Probability of being the cheapest import")
    gc = OPT["O4a_GREGY"][2]
    cx.legend(handles=[Patch(facecolor=gc, label="independent sampling"),
                       Patch(facecolor=gc, alpha=0.55, label="correlated, ρ = 0.8")], loc="upper left", fontsize=5.6)
    hgrid(cx)
    panel(cx, "c", x=-0.2, y=1.02)
    save(fig, "FigS17_correlated_prices", si=True)


# ---------------------------------------------------------------------------------------------
# S18  Cost of capital for renewables across the region
# ---------------------------------------------------------------------------------------------
def s18():
    t = pd.read_csv(os.path.join(TAB, "cost_of_capital_penalty.csv")).sort_values("lcoe_x_solar_pv")
    reg = {"EU member": (["GRC", "CYP", "ITA", "BGR", "ROU", "HRV", "SVN"], "#2E86AB"),
           "Eastern Mediterranean partner": (["ISR", "EGY", "TUR", "JOR", "LBN"], "#E8A33D"),
           "Western Balkans": (["SRB", "BIH", "MNE", "MKD", "ALB", "XKX"], "#7B52AB")}
    colof = {iso: c for _, (isos, c) in reg.items() for iso in isos}
    fig, axs = plt.subplots(1, 2, figsize=(W2, 78 * MM), sharey=True, gridspec_kw={"wspace": 0.06})
    for i, r in enumerate(t.itertuples()):
        c = colof.get(r.iso3, "#1AA391")
        mf = "white" if r.irena_default_solar_pv else c
        axs[0].plot(r.wacc_solar_pv * 100, i, "o", ms=4, mfc=mf, mec=c, mew=0.8)
        axs[0].plot([5.0, r.wacc_solar_pv * 100], [i, i], color=c, lw=0.6, alpha=0.6)
        axs[1].barh(i, r.lcoe_x_solar_pv, height=0.62, color=c, alpha=0.85 if not r.irena_default_solar_pv else 0.4)
        axs[1].text(r.lcoe_x_solar_pv + 0.03, i, f"{r.lcoe_x_solar_pv:.2f}×", va="center", fontsize=5.4)
    axs[0].axvline(t.loc[t.iso3 == "GRC", "wacc_solar_pv"].iloc[0] * 100, color="#2E86AB", lw=0.8, ls=(0, (3, 1.5)))
    axs[0].set_yticks(range(len(t)), t.country)
    axs[0].tick_params(axis="y", length=0)
    axs[0].set_xlabel("Real after-tax WACC, solar PV (IRENA 2025 assumptions, %)")
    axs[1].axvline(1.0, color="#2E86AB", lw=0.8, ls=(0, (3, 1.5)))
    axs[1].set_xlabel("Solar LCOE relative to Greek financing")
    axs[1].set_xlim(0.8, max(3.3, float(t.lcoe_x_solar_pv.max()) + 0.4))
    for ax, letter in zip(axs, "ab"):
        hgrid(ax, "x")
        ax.spines["left"].set_visible(False)
        panel(ax, letter, x=-0.02 if letter == "b" else -0.36, y=1.01)
    h = [Line2D([], [], marker="o", ls="", ms=4, color=c, label=l) for l, (_, c) in reg.items()]
    if t.irena_default_solar_pv.any():
        h.append(Line2D([], [], marker="o", ls="", ms=4, mfc="white", mec=INK2, label="IRENA default value (7.5%)"))
    axs[1].legend(handles=h, loc="lower right", fontsize=5.5)
    save(fig, "FigS18_regional_cost_of_capital", si=True)


# ---------------------------------------------------------------------------------------------
# S19  Components of the base cost (L0, central values)
# ---------------------------------------------------------------------------------------------
def _base_components():
    from emcorr import constants as C
    from emcorr import finance as F
    from emcorr import options as O
    df, Pb = register()
    P = {k: np.float64(v) for k, v in Pb.items()}
    cor = corridors()
    f0 = O.FLAGS[0]
    eta_el = C.lhv_to_gcv_efficiency(P["ccgt_eta_lhv"])
    co2 = C.EF_GAS_T_PER_MWH_GCV / eta_el * P["p_co2"]
    plant = float(O.ccgt_cost(P, 0.0, f0)) - co2
    out = {}
    c = cor["O1_EastMed"]
    w = O.seg_wacc_real(P, "pipe", c["weights"], c["x_contested"], f0)
    eta = 1 - P["em_fuel_pct"]
    q = P["em_capacity_bcm"] * P["em_util0"] * C.MWH_PER_BCM_GCV * eta
    util = F.util_pv_factor(w, P["em_life"], P["gasdem_plateau"], P["gasdem_decline"], P["gasdem_floor"])
    lc = F.levelized_cost(P["em_capex"], q, w, P["em_life"], P["em_build"], fom_per_year=P["em_fom_pct"] * P["em_capex"],
                          util_pv_factor=util)
    p0 = C.usd_per_mmbtu_to_eur_per_mwh(P["p_gas_levant_usd"], P["fx_usd_per_eur"])
    out["O1_EastMed"] = {"Gas at origin": p0 / eta / eta_el, "Gas transport and processing": float(lc) / eta_el,
                         "Carbon (EU ETS)": co2, "Power plant (CCGT)": plant}
    fx = P["fx_usd_per_eur"]
    e_l, e_s, e_r = 1 - P["lng_liq_loss"], 1 - P["lng_ship_loss"], 1 - P["lng_regas_loss"]
    toll = C.usd_per_mmbtu_to_eur_per_mwh(P["lng_toll_usd"], fx)
    ship = C.usd_per_mmbtu_to_eur_per_mwh(P["lng_ship_usd"], fx)
    out["O2_LNG_Egypt"] = {"Gas at origin": p0 / (e_l * e_s * e_r) / eta_el,
                           "Gas transport and processing": (toll / (e_s * e_r) + ship / e_r + P["lng_regas_eur"]) / eta_el,
                           "Carbon (EU ETS)": co2, "Power plant (CCGT)": plant}
    for k, pre in [("O3_GSI", "il"), ("O4a_GREGY", "eg"), ("O4b_EuroAfrica", "eg")]:
        c = cor[k]
        loss = c["n_conv"] * P["hvdc_conv_loss"] + P["hvdc_cable_loss"] * c["subsea_km"] / 1000
        qq = c["mw"] * C.HOURS_PER_YEAR * P[f"uf_{k}"] * (1 - loss)
        wt = O.seg_wacc_real(P, "hvdc", c["weights"], c["x_contested"], f0)
        capex = P[f"capex_{k}"]
        tx = F.levelized_cost(capex, qq, wt, P["hvdc_life"], P[f"build_{k}"], fom_per_year=P["hvdc_fom_pct"] * capex)
        out[k] = {"Renewable generation": float(O.gen_lcoe(P, pre, P["wacc_re_GR"])) / (1 - loss),
                  "Transmission": float(tx), "Firming": P["firming_adder"]}
    out["O5_Greek_RE"] = {"Renewable generation": float(O.gen_lcoe(P, "gr", P["wacc_re_GR"])) / (1 - P["gr_curtail"]),
                          "Firming": P["firming_adder"]}
    return out


def s19():
    comp = _base_components()
    det = pd.read_csv(os.path.join(TAB, "deterministic_by_layer.csv")).set_index("option")["L0_base"]
    for o, d in comp.items():
        assert abs(sum(d.values()) - det[o]) < 0.5, (o, sum(d.values()), det[o])
    ccol = {"Gas at origin": "#2E86AB", "Gas transport and processing": "#5DADE2", "Carbon (EU ETS)": "#C8443A",
            "Power plant (CCGT)": "#7B52AB", "Renewable generation": "#6B8E23", "Transmission": "#E8A33D",
            "Firming": "#1AA391"}
    fig, ax = plt.subplots(figsize=(W15, 70 * MM))
    for i, o in enumerate(OPTIONS):
        left = 0.0
        for k, v in comp[o].items():
            ax.barh(i, v, left=left, height=0.6, color=ccol[k], edgecolor="white", lw=0.6)
            if v > 9:
                ax.text(left + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=5.4, color="white")
            left += v
        ax.text(left + 2, i, f"{left:.0f}", va="center", fontsize=6, fontweight="bold")
    ax.set_yticks(range(len(OPTIONS)), [OPT[o][0] for o in OPTIONS])
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.set_xlabel("Base cost at central values, L0 (EUR per MWh at the Greek grid)")
    ax.spines["left"].set_visible(False)
    hgrid(ax, "x")
    ax.legend(handles=[Patch(color=c, label=k) for k, c in ccol.items()], loc="lower right", fontsize=5.6)
    save(fig, "FigS19_base_cost_components", si=True)


SI = {str(i): f for i, f in enumerate([s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19], 1)}

if __name__ == "__main__":
    style()
    for key in (sys.argv[1:] or list(SI)):
        SI[key]()