"""Main-text figures (Fig. 1-8). Run after 10_run_model.py and 11_scenarios.py.

Usage: python scripts/20_figures.py [1 2 3 ...]   (default: all)
Output: outputs/figures/main/FigN_*.png (600 dpi) and .eps
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import (ACCENT, CABLES, diverging, COAST, EEZC, FIXED_ASSET, FREE, GRIDC, IMPORTS, INK, INK2, LAND, LAYER,  # noqa: E402
                    LAYER_KEYS, MM, OPT, OPTIONS, ROOT, SEA, TAB, W2, ZONE, corridors, evaluate_grid, hgrid,
                    increments, kde, load_draws, panel, plabel, plt, register, save, shade, style)
import matplotlib.patheffects as pe      # noqa: E402
from matplotlib.lines import Line2D      # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

HALO = [pe.withStroke(linewidth=1.6, foreground="white")]


def plot_lines(ax, geoms, **kw):
    """Draw (Multi)LineString geometries with full control of dash patterns."""
    for g in geoms:
        if g is None or g.is_empty:
            continue
        for p in getattr(g, "geoms", [g]):
            x, y = p.xy
            ax.plot(x, y, **kw)


# ---------------------------------------------------------------------------------------------
# Fig. 1  Corridors, overlapping maritime claims and route exposure
# ---------------------------------------------------------------------------------------------
def fig1():
    import geopandas as gpd
    land = gpd.read_file("zip://" + os.path.join(ROOT, "data", "raw", "naturalearth", "ne_10m_land.zip"))
    zones = gpd.read_file(os.path.join(ROOT, "data", "processed", "contested_zones.geojson"))
    mr = os.path.join(ROOT, "data", "raw", "marineregions")
    eezb = pd.concat([gpd.read_file(os.path.join(mr, f)) for f in ("eez_boundaries_eastmed.geojson",
                                                                     "eez_boundaries_eastmed_west.geojson")])
    cor = corridors()
    exp = pd.read_csv(os.path.join(TAB, "route_exposure.csv"))

    fig = plt.figure(figsize=(W2, 92 * MM))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 1.0], wspace=0.12)
    ax = fig.add_subplot(gs[0])
    x0, x1, y0, y1 = 19.4, 36.3, 30.35, 38.45
    ax.set_facecolor(SEA)
    land.cx[5:45, 22:48].plot(ax=ax, facecolor=LAND, edgecolor=COAST, lw=0.3, zorder=1)
    for key, (lab, tint, hcol, hatch) in ZONE.items():
        zones[zones.zone == key].plot(ax=ax, facecolor=tint, edgecolor=hcol, hatch=hatch, lw=0, alpha=0.9, zorder=2)
    plot_lines(ax, eezb.geometry, color=EEZC, lw=0.35, ls=(0, (2.5, 1.5)), zorder=3)
    for k in ["O1_EastMed", "O4b_EuroAfrica", "O3_GSI", "O4a_GREGY"]:
        w = np.array(cor[k]["waypoints"])
        ls = (0, (3.2, 1.8)) if k == "O3_GSI" else "-"
        ax.plot(w[:, 0], w[:, 1], color=OPT[k][2], lw=1.35, ls=ls, solid_capstyle="round", zorder=6,
                path_effects=[pe.Stroke(linewidth=2.5, foreground="white"), pe.Normal()])
    ends = {"Leviathan": (33.617, 33.168, 0.12, -0.32, "left"), "Peloponnese": (23.05, 36.6, -0.12, 0.15, "right"),
            "Hadera": (34.917, 32.45, 0.15, -0.05, "left"), "Kofinou": (33.392, 34.826, 0.1, -0.33, "left"),
            "Korakia": (24.923, 35.353, 0.0, -0.36, "center"), "Sidi Barrani": (25.92, 31.61, 0.1, -0.32, "left"),
            "Attica": (23.98, 38.08, 0.14, 0.02, "left"), "Kafr El Sheikh": (30.9, 31.6, 0.1, -0.32, "left")}
    for name, (lx, ly, dx, dy, ha) in ends.items():
        ax.plot(lx, ly, "o", ms=2.6, mfc="white", mec=INK, mew=0.6, zorder=7)
        ax.text(lx + dx, ly + dy, name, fontsize=5.5, color=INK, ha=ha, va="center", zorder=8, path_effects=HALO)
    for name, (lx, ly) in {"GREECE": (22.0, 38.05), "TÜRKIYE": (31.6, 37.85), "CYPRUS": (33.25, 35.27),
                           "EGYPT": (29.2, 30.6), "LIBYA": (22.2, 30.8), "ISRAEL": (35.25, 31.15),
                           "Crete": (25.95, 34.72)}.items():
        ax.text(lx, ly, name, fontsize=5.2, color=INK2, ha="center", va="center", zorder=8,
                fontstyle="italic" if name == "Crete" else "normal", path_effects=HALO)
    sx, sy = 31.85, 31.62                    # scale bar (true length at 34 N)
    dx = 200 / (111.32 * np.cos(np.deg2rad(34)))
    ax.plot([sx, sx + dx], [sy, sy], color=INK, lw=0.8, solid_capstyle="butt", zorder=9)
    for t in (sx, sx + dx / 2, sx + dx):
        ax.plot([t, t], [sy - 0.06, sy + 0.06], color=INK, lw=0.6, zorder=9)
    ax.text(sx + dx / 2, sy + 0.14, "200 km", fontsize=5.5, ha="center", va="bottom", zorder=9, path_effects=HALO)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect(1 / np.cos(np.deg2rad(34.4)))
    ax.set_xticks([20, 24, 28, 32, 36], [f"{v}°E" for v in [20, 24, 28, 32, 36]])
    ax.set_yticks([31, 33, 35, 37], [f"{v}°N" for v in [31, 33, 35, 37]])
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
    # no locator inset: Energy Policy does not allow maps that show more than the study area
    h = [Line2D([], [], color=OPT[k][2], lw=1.35, ls=(0, (3.2, 1.8)) if k == "O3_GSI" else "-", label=OPT[k][0])
         for k in FIXED_ASSET]
    h += [Line2D([], [], color=EEZC, lw=0.5, ls=(0, (2.5, 1.5)), label="EEZ boundary (Marine Regions)"),
          Line2D([], [], marker="o", ls="", ms=2.6, mfc="white", mec=INK, mew=0.6, label="Landing point / field")]
    leg = ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.005, 0.075), fontsize=5.4, frameon=True,
                    framealpha=0.92, edgecolor="none", borderpad=0.5)
    leg.get_frame().set_linewidth(0)
    panel(ax, "a", x=-0.035, y=1.005)

    bx = fig.add_subplot(gs[1])
    rows = [("O1_EastMed", "base", "EastMed pipeline"), ("O1_EastMed", "alt", "EastMed, alternative alignment"),
            ("O3_GSI", "base", "Great Sea Interconnector"), ("O4b_EuroAfrica", "base", "EuroAfrica"),
            ("O4a_GREGY", "west", "GREGY, west of Crete"), ("O4a_GREGY", "east", "GREGY, east of Crete")]
    for i, (k, var, lab) in enumerate(rows):
        r = exp[(exp.option == k) & (exp.variant == var)].iloc[0]
        free = r.total_km - r.any_contested_km
        bx.barh(i, free, height=0.5, color=FREE[1], edgecolor=FREE[2], lw=0.4)
        left = free
        for z, (zl, tint, hcol, hatch) in ZONE.items():
            v = r[f"{z}_km"]
            if v > 0:
                bx.barh(i, v, left=left, height=0.5, color=tint, edgecolor=hcol, hatch=hatch, lw=0.4)
                left += v
        bx.text(left + 25, i, f"{r.any_contested_km / r.total_km * 100:.0f}%", va="center", ha="left", fontsize=6)
        bx.plot(12, i - 0.43, "s", ms=3.0, color=OPT[k][2], clip_on=False)
        bx.text(45, i - 0.43, lab, fontsize=6, va="center", ha="left", color=INK)
    bx.set_yticks([])
    bx.set_ylim(len(rows) - 0.55, -0.85)
    bx.set_xlim(0, 1450)
    bx.set_xlabel("Route length (km)")
    bx.spines["left"].set_visible(False)
    hgrid(bx, "x")
    zh = [Patch(facecolor=FREE[1], edgecolor=FREE[2], lw=0.4, label=FREE[0])]
    zh += [Patch(facecolor=t, edgecolor=hc, hatch=hh, lw=0.4, label=l) for l, t, hc, hh in ZONE.values()]
    bx.legend(handles=zh, loc="upper center", bbox_to_anchor=(0.42, -0.16), ncol=2, fontsize=5.6, handlelength=1.6,
              columnspacing=0.8)
    bx.text(1.0, 1.02, "share in overlapping claims", transform=bx.transAxes, ha="right", va="bottom", fontsize=5.6,
            color=INK2)
    panel(bx, "b", x=-0.03, y=1.005)
    fig.canvas.draw()                      # align panel b with the map frame
    pa, pb = ax.get_position(), bx.get_position()
    bx.set_position([pb.x0, pa.y0 + 0.1 * pa.height, pb.width, 0.9 * pa.height])
    save(fig, "Fig1_corridors_and_claims")

# ---------------------------------------------------------------------------------------------
# Fig. 2  Building up the risk-adjusted cost, layer by layer (waterfalls)
# ---------------------------------------------------------------------------------------------
def fig2():
    res, _ = load_draws()
    green = increments(res["O5_Greek_RE"])["total"].mean()
    fig = plt.figure(figsize=(W2, 100 * MM))
    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.10)
    slots = {"O1_EastMed": gs[0, 0], "O2_LNG_Egypt": gs[0, 1], "O3_GSI": gs[1, 0], "O4a_GREGY": gs[1, 1],
             "O4b_EuroAfrica": gs[1, 2]}
    labels = ["Base", "Capital", "Execution", "Conflict", "Maritime", "Total"]
    axes = {}
    for k, slot in slots.items():
        ax = fig.add_subplot(slot, sharey=axes.get("O1_EastMed"))
        axes[k] = ax
        inc = increments(res[k])
        m = {c: inc[c].mean() for c in LAYER_KEYS}
        tot = inc["total"]
        cum = 0.0
        for i, c in enumerate(LAYER_KEYS):
            v, col = m[c], LAYER[c][1]
            if i == 0:
                ax.bar(i, v, width=0.66, color=col, edgecolor="none", zorder=2)
                cum = v
            elif v >= 0:
                ax.bar(i, v, bottom=cum, width=0.66, color=col, edgecolor="none", zorder=2)
                cum += v
            else:
                ax.bar(i, -v, bottom=cum + v, width=0.66, facecolor="white", edgecolor=col, hatch="//////", lw=0.6, zorder=2)
                cum += v
            ax.plot([i + 0.33, i + 0.67], [cum, cum], color=INK2, lw=0.4, ls=(0, (1.5, 1)), zorder=1)
            if i > 0:
                txt = "0" if abs(v) < 0.05 else f"{v:+.1f}".replace("-", "\u2212")
                ax.text(i, cum + 1.5 if v >= 0 else cum - 1.5, txt, ha="center", va="bottom" if v >= 0 else "top",
                        fontsize=5.6, color=INK)
        lo, hi = np.percentile(tot, [5, 95])
        mu = tot.mean()
        ax.bar(5, mu, width=0.66, color=OPT[k][2], edgecolor="none", zorder=2)
        ax.errorbar(5, mu, yerr=[[mu - lo], [hi - mu]], fmt="none", ecolor=shade(OPT[k][2], 0.5), elinewidth=0.7,
                    capsize=1.8, capthick=0.7, zorder=3)
        ax.text(5, hi + 4, f"{mu:.0f}", ha="center", va="bottom", fontsize=6.3, fontweight="bold")
        ax.axhline(green, color=OPT["O5_Greek_RE"][2], lw=0.8, ls=(0, (2, 1.5)), zorder=1)
        ax.set_xticks(range(6), labels, fontsize=5.6, rotation=40, ha="right", rotation_mode="anchor")
        ax.tick_params(axis="x", length=0, pad=2.5)
        ax.set_xlim(-0.6, 5.6)
        ax.set_title(OPT[k][0], loc="left", fontsize=7, pad=4)
        hgrid(ax)
        if k not in ("O1_EastMed", "O3_GSI"):
            plt.setp(ax.get_yticklabels(), visible=False)
    axes["O1_EastMed"].set_ylim(0, 268)
    axes["O1_EastMed"].text(0.45, green - 3, f"Greek renewables, {green:.0f}", fontsize=5.4,
                            color=shade(OPT["O5_Greek_RE"][2], 0.8), va="top", ha="left")
    fig.supylabel("EUR per MWh at the Greek grid (2025 prices)", fontsize=7, x=0.065, color=INK)
    for k, letter in zip(slots, "abcde"):
        panel(axes[k], letter, x=-0.05, y=1.035)
    lx = fig.add_subplot(gs[0, 2])
    lx.axis("off")
    h = [Patch(facecolor=LAYER[c][1], edgecolor="none", label=LAYER[c][0]) for c in LAYER_KEYS]
    h.insert(2, Patch(facecolor="white", edgecolor=LAYER["cost_of_capital"][1], hatch="//////", lw=0.6,
                      label="Negative: partner cheaper to finance than Greece"))
    h += [Line2D([], [], color=shade(OPT["O1_EastMed"][2], 0.5), lw=0.7, marker="_", ms=4,
                 label="Total (option color): mean, 5th-95th pct."),
          Line2D([], [], color=OPT["O5_Greek_RE"][2], lw=0.8, ls=(0, (2, 1.5)), label="Greek renewables (mean)")]
    lx.legend(handles=h, loc="center left", bbox_to_anchor=(0.02, 0.5), fontsize=6, handlelength=1.6, labelspacing=0.55)
    save(fig, "Fig2_cost_buildup")


# ---------------------------------------------------------------------------------------------
# Fig. 3  Uncertainty and ranking of the risk-adjusted cost
# ---------------------------------------------------------------------------------------------
def fig3():
    res, _ = load_draws()
    tot = {o: res[o][4] for o in OPTIONS}
    order = sorted(OPTIONS, key=lambda o: np.median(tot[o]))
    fig = plt.figure(figsize=(W2, 72 * MM))
    gs = fig.add_gridspec(1, 3, width_ratios=[2.3, 1.0, 1.35], wspace=0.55)
    ax = fig.add_subplot(gs[0])
    grid = np.linspace(30, 300, 500)
    for i, o in enumerate(order):
        x = tot[o]
        d = kde(x, grid)
        d = 0.42 * d / d.max()
        keep = d > 0.004
        g, d = grid[keep], d[keep]
        col = OPT[o][2]
        ax.fill_between(g, i - d, i, color=col, alpha=0.35, lw=0, zorder=2)
        ax.plot(g, i - d, color=shade(col, 0.8), lw=0.7, zorder=3)
        ax.plot([g[0], g[-1]], [i, i], color=shade(col, 0.8), lw=0.5, zorder=3)
        q5, q25, q50, q75, q95 = np.percentile(x, [5, 25, 50, 75, 95])
        ax.plot([q5, q95], [i + 0.13, i + 0.13], color=shade(col, 0.6), lw=0.7, zorder=4)
        ax.add_patch(Rectangle((q25, i + 0.06), q75 - q25, 0.14, facecolor=shade(col, 1.55), edgecolor=shade(col, 0.6),
                               lw=0.6, zorder=5))
        ax.plot([q50, q50], [i + 0.05, i + 0.21], color=shade(col, 0.45), lw=1.1, zorder=6)
        if o in FIXED_ASSET:
            ax.plot(np.median(res[o][3]), i + 0.13, marker="|", ms=6.5, mew=1.1, color=LAYER["maritime"][1], zorder=7)
        ax.text(q95 + 5, i + 0.13, f"{q50:.0f}", va="center", fontsize=6, color=INK)
    ax.set_yticks(range(len(order)), [OPT[o][0] for o in order])
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(len(order) - 0.55, -0.6)
    ax.set_xlim(35, 270)
    ax.set_xlabel("Risk-adjusted cost, EUR per MWh (2025 prices)")
    hgrid(ax, "x")
    ax.spines["left"].set_visible(False)
    c0 = OPT["O1_EastMed"][2]
    leg = [Rectangle((0, 0), 1, 1, facecolor=shade(c0, 1.55), edgecolor=shade(c0, 0.6), lw=0.6,
                     label="Interquartile range and median"),
           Line2D([], [], color=shade(c0, 0.6), lw=0.7, label="5th-95th percentile"),
           Line2D([], [], color=LAYER["maritime"][1], marker="|", ls="", ms=6.5, mew=1.1,
                  label="Median if maritime disputes resolved")]
    ax.legend(handles=leg, loc="upper right", fontsize=5.8)
    panel(ax, "a", x=-0.34, y=1.0)

    bx = fig.add_subplot(gs[1])
    stack = np.vstack([tot[o] for o in IMPORTS])
    win = pd.Series(np.array(IMPORTS)[stack.argmin(0)]).value_counts(normalize=True)
    ordr = sorted(IMPORTS, key=lambda o: -win.get(o, 0))
    for i, o in enumerate(ordr):
        p = win.get(o, 0.0)
        bx.barh(i, p, height=0.6, color=OPT[o][2], edgecolor="none")
        bx.text(p + 0.02, i, f"{p:.0%}" if p >= 0.005 else "<1%", va="center", fontsize=6)
    bx.set_yticks(range(len(ordr)), [OPT[o][1] for o in ordr])
    bx.tick_params(axis="y", length=0)
    bx.invert_yaxis()
    bx.set_xlim(0, 1.18)
    bx.set_xticks([0, 0.5, 1.0], ["0", "0.5", "1"])
    bx.set_xlabel("Probability of being\nthe cheapest import")
    bx.spines["left"].set_visible(False)
    panel(bx, "b", x=-0.62, y=1.0)

    cx = fig.add_subplot(gs[2])
    M = np.array([[np.nan if a == b else (tot[a] < tot[b]).mean() for b in IMPORTS] for a in IMPORTS])
    im = cx.imshow(M, cmap="RdYlBu", vmin=0, vmax=1)
    for i in range(5):
        for j in range(5):
            if i != j:
                v = M[i, j]
                cx.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5.6,
                        color="white" if abs(v - 0.5) > 0.36 else INK)
    short = [OPT[o][1].replace("LNG via Egypt", "LNG") for o in IMPORTS]
    cx.set_xticks(range(5), short, rotation=45, ha="right", fontsize=5.8)
    cx.set_yticks(range(5), short, fontsize=5.8)
    cx.tick_params(length=0)
    for sp in cx.spines.values():
        sp.set_visible(False)
    cx.set_title("P(row cheaper than column)", fontsize=6.2, fontweight="normal", pad=3)
    cb = fig.colorbar(im, ax=cx, fraction=0.045, pad=0.03, ticks=[0, 0.5, 1])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=5.8, length=1.5)
    panel(cx, "c", x=-0.42, y=1.0)
    save(fig, "Fig3_uncertainty_and_ranking")

# ---------------------------------------------------------------------------------------------
# Fig. 4  Do electricity corridors escape geopolitics? Maritime and geopolitical increments
# ---------------------------------------------------------------------------------------------
def _capital_intensity():
    """EUR of capex per MWh of electricity delivered per year (central values)."""
    from emcorr import constants as C
    df, P = register()
    cor = corridors()
    eta = C.lhv_to_gcv_efficiency(P["ccgt_eta_lhv"])
    out = {"O1_EastMed": P["em_capex"] / (P["em_capacity_bcm"] * P["em_util0"] * C.MWH_PER_BCM_GCV * eta)}
    for k in CABLES:
        out[k] = P[f"capex_{k}"] / (cor[k]["mw"] * C.HOURS_PER_YEAR * P[f"uf_{k}"])
    return out, cor


def fig4():
    res, _ = load_draws()
    inc = {o: increments(res[o]) for o in OPTIONS}
    dec = pd.read_csv(os.path.join(TAB, "risk_decomposition.csv")).set_index("option")
    fig = plt.figure(figsize=(W2, 112 * MM))
    gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.30, width_ratios=[1.05, 1.0])

    ax = fig.add_subplot(gs[0, 0])
    keys = FIXED_ASSET
    data = [np.clip(inc[o]["maritime"], None, np.percentile(inc[o]["maritime"], 99.5)) for o in keys]
    vp = ax.violinplot(data, positions=range(4), widths=0.75, showextrema=False, points=200)
    for b, o in zip(vp["bodies"], keys):
        b.set_facecolor(OPT[o][2])
        b.set_edgecolor(shade(OPT[o][2], 0.7))
        b.set_alpha(0.45)
        b.set_linewidth(0.6)
    for i, (o, x) in enumerate(zip(keys, data)):
        q5, q25, q50, q75, q95 = np.percentile(x, [5, 25, 50, 75, 95])
        col = OPT[o][2]
        ax.plot([i, i], [q5, q95], color=shade(col, 0.55), lw=0.7, zorder=3)
        ax.add_patch(Rectangle((i - 0.07, q25), 0.14, q75 - q25, facecolor=shade(col, 1.5), edgecolor=shade(col, 0.55),
                               lw=0.6, zorder=4))
        ax.plot([i - 0.07, i + 0.07], [q50, q50], color=shade(col, 0.4), lw=1.1, zorder=5)
        if o != "O1_EastMed":
            p = (inc[o]["maritime"] < inc["O1_EastMed"]["maritime"]).mean()
            ax.text(i, 30.5, f"P(< EastMed)\n= {p:.2f}", ha="center", va="bottom", fontsize=5.4, color=INK)
    ax.set_xticks(range(4), [OPT[o][1] for o in keys])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Maritime-dispute cost (EUR/MWh)")
    ax.set_ylim(0, 35)
    hgrid(ax)
    ax.text(0.99, 0.70, "LNG via Egypt: 0\n(no fixed asset at sea)", transform=ax.transAxes, ha="right", va="top",
            fontsize=5.6, color=OPT["O2_LNG_Egypt"][2])
    panel(ax, "a", x=-0.13, y=1.02)

    bx = fig.add_subplot(gs[0, 1])
    for i, o in enumerate(IMPORTS):
        c, m = inc[o]["conflict"].mean(), inc[o]["maritime"].mean()
        bx.bar(i, c, width=0.62, color=LAYER["conflict"][1], edgecolor="none")
        bx.bar(i, m, bottom=c, width=0.62, color=LAYER["maritime"][1], edgecolor="none")
        g = inc[o]["geopolitical"]
        lo, hi = np.percentile(g, [5, 95])
        bx.errorbar(i, g.mean(), yerr=[[g.mean() - lo], [hi - g.mean()]], fmt="none", ecolor=shade(OPT[o][2], 0.55),
                    elinewidth=0.7, capsize=1.8, capthick=0.7)
        bx.text(i, hi + 1.2, f"{g.mean():.1f}", ha="center", va="bottom", fontsize=6, fontweight="bold")
        bx.plot(i, -3.2, "s", ms=3.2, color=OPT[o][2], clip_on=False)
    bx.set_xticks(range(5), [OPT[o][1].replace("LNG via Egypt", "LNG via\nEgypt") for o in IMPORTS], fontsize=6)
    bx.tick_params(axis="x", length=0, pad=7)
    bx.set_ylim(0, 72)
    bx.set_ylabel("Geopolitical cost (EUR/MWh)")
    hgrid(bx)
    bx.legend(handles=[Patch(color=LAYER["conflict"][1], label="Conflict and diversion"),
                       Patch(color=LAYER["maritime"][1], label="Maritime disputes")], loc="upper right", fontsize=5.8)
    panel(bx, "b", x=-0.13, y=1.02)

    cx = fig.add_subplot(gs[1, 0])
    ci, cor = _capital_intensity()
    for o in FIXED_ASSET:
        x = cor[o]["x_contested"]
        y = inc[o]["maritime"] / x
        lo, mid, hi = np.percentile(y, [5, 50, 95])
        cx.errorbar(ci[o], y.mean(), yerr=[[y.mean() - lo], [hi - y.mean()]], fmt=OPT[o][3], ms=5, mfc=OPT[o][2],
                    mec=shade(OPT[o][2], 0.55), mew=0.6, ecolor=shade(OPT[o][2], 0.55), elinewidth=0.7, capsize=1.8,
                    capthick=0.7, zorder=3)
        cx.annotate(f"{OPT[o][1]}\n(x = {x:.0%})", (ci[o], y.mean()), xytext=(6, -2), textcoords="offset points",
                    fontsize=5.6, va="top", color=INK)
    xs = np.array([min(ci.values()) * 0.8, max(ci.values()) * 1.25])
    k_fit = np.exp(np.mean([np.log((inc[o]["maritime"] / cor[o]["x_contested"]).mean() / ci[o]) for o in CABLES]))
    cx.plot(xs, k_fit * xs, color=INK2, lw=0.6, ls=(0, (3, 2)), zorder=1)
    cx.text(0.04, 0.93, "Dashed line: maritime cost" + chr(10) + "proportional to capital intensity", transform=cx.transAxes,
            fontsize=5.4, color=INK2, ha="left", va="top")
    cx.set_xscale("log")
    cx.set_yscale("log")
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    cx.xaxis.set_major_locator(FixedLocator([100, 200, 500, 1000]))
    cx.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    cx.xaxis.set_minor_formatter(NullFormatter())
    cx.yaxis.set_major_locator(FixedLocator([5, 10, 20, 50]))
    cx.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}"))
    cx.yaxis.set_minor_formatter(NullFormatter())
    cx.set_xlabel("Capital intensity (EUR of capex per MWh delivered per year)")
    cx.set_ylabel("Maritime cost per unit of exposure\n(EUR/MWh per share of route contested)")
    cx.grid(which="major", color=GRIDC, lw=0.45)
    panel(cx, "c", x=-0.13, y=1.02)

    dx = fig.add_subplot(gs[1, 1])
    for i, o in enumerate(FIXED_ASSET):
        twh = dec.loc[o, "annual_twh"]
        v = inc[o]["maritime"] * twh
        lo, hi = np.percentile(v, [5, 95])
        dx.barh(i, v.mean(), height=0.55, color=OPT[o][2], edgecolor="none")
        dx.errorbar(v.mean(), i, xerr=[[v.mean() - lo], [hi - v.mean()]], fmt="none", ecolor=shade(OPT[o][2], 0.5),
                    elinewidth=0.7, capsize=1.8, capthick=0.7)
        share = inc[o]["maritime"].mean() / inc[o]["total"].mean()
        dx.text(hi + 6, i, f"{inc[o]['maritime'].mean():.1f} EUR/MWh ({share:.0%} of cost)", va="center", fontsize=5.8)
    dx.set_yticks(range(4), [OPT[o][1] for o in FIXED_ASSET])
    dx.tick_params(axis="y", length=0)
    dx.invert_yaxis()
    dx.set_xlim(0, 420)
    dx.set_xlabel("Value of resolving maritime disputes (EUR million per year)")
    dx.spines["left"].set_visible(False)
    hgrid(dx, "x")
    panel(dx, "d", x=-0.2, y=1.02)
    save(fig, "Fig4_geopolitical_exposure")


# ---------------------------------------------------------------------------------------------
# Fig. 5  The Egypt nexus: gas deficit, diversion and the cost of routes through Egypt
# ---------------------------------------------------------------------------------------------
def fig5():
    from emcorr import egypt as E
    res, par = load_draws()
    n = 4000
    P = {k: v[:n] for k, v in par.items()}
    yrs = np.arange(2025, 2061)
    b = E.balance(P, yrs)
    fig = plt.figure(figsize=(W2, 66 * MM))
    gs = fig.add_gridspec(1, 3, wspace=0.42, width_ratios=[1.15, 1.0, 1.0])

    ax = fig.add_subplot(gs[0])
    sel = yrs <= 2045
    yy = yrs[sel]
    med = {k: np.median(b[k][:, sel], axis=0) for k in ("production", "israel", "cyprus", "demand")}
    cols = {"production": "#2E86AB", "israel": "#F18F01", "cyprus": "#7FB800"}
    labs = {"production": "Domestic production", "israel": "Israeli pipeline gas", "cyprus": "Cypriot pipeline gas"}
    ax.stackplot(yy, med["production"], med["israel"], med["cyprus"], colors=[cols[k] for k in cols], alpha=0.85,
                 labels=[labs[k] for k in cols], lw=0)
    supply = med["production"] + med["israel"] + med["cyprus"]
    ax.fill_between(yy, supply, med["demand"], facecolor="#F9D5D3", edgecolor="#C8443A", hatch="////", lw=0,
                    label="Shortfall: LNG imports")
    lo, hi = np.percentile(b["demand"][:, sel], [5, 95], axis=0)
    ax.fill_between(yy, lo, hi, color="#C8443A", alpha=0.12, lw=0)
    ax.plot(yy, med["demand"], color="#C8443A", lw=1.1, label="Demand (median, 5-95%)")
    ax.set_xlim(2025, 2045)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Gas, bcm per year")
    ax.legend(loc="upper left", fontsize=5.5, ncol=1)
    hgrid(ax)
    panel(ax, "a", x=-0.16, y=1.02)

    bx = fig.add_subplot(gs[1])
    bins = np.linspace(0, 1, 11)
    def cond(theta, cost):
        mids, mu, q1, q3 = [], [], [], []
        for a, c in zip(bins[:-1], bins[1:]):
            m = (theta >= a) & (theta < c)
            if m.sum() > 30:
                mids.append((a + c) / 2)
                mu.append(cost[m].mean())
                q1.append(np.percentile(cost[m], 25))
                q3.append(np.percentile(cost[m], 75))
        return map(np.array, (mids, mu, q1, q3))
    em = res["O1_EastMed"][4]
    bx.axhspan(np.percentile(em, 25), np.percentile(em, 75), color=OPT["O1_EastMed"][2], alpha=0.12, lw=0)
    bx.axhline(em.mean(), color=OPT["O1_EastMed"][2], lw=0.8, ls=(0, (3, 2)))
    bx.text(0.98, np.percentile(em, 25) - 1.5, "EastMed (mean, IQR)", fontsize=5.5, ha="right", va="top",
            color=shade(OPT["O1_EastMed"][2], 0.8))
    for o, th, lab in [("O2_LNG_Egypt", par["eg_divert_theta"], "LNG via Egypt (gas propensity)"),
                       ("O4a_GREGY", par["eg_divert_theta_el"], "GREGY (power propensity)"),
                       ("O4b_EuroAfrica", par["eg_divert_theta_el"], "EuroAfrica (power propensity)")]:
        x, mu, q1, q3 = cond(th, res[o][4])
        bx.fill_between(x, q1, q3, color=OPT[o][2], alpha=0.18, lw=0)
        bx.plot(x, mu, color=OPT[o][2], lw=1.2, marker=OPT[o][3], ms=2.6, label=lab)
    bx.set_xlim(0, 1)
    bx.set_xlabel("Egypt's propensity to divert exports (θ)")
    bx.set_ylabel("Risk-adjusted cost (EUR/MWh)")
    bx.legend(loc="upper left", fontsize=5.4)
    bx.set_ylim(80, 215)
    hgrid(bx)
    panel(bx, "b", x=-0.2, y=1.02)

    cx = fig.add_subplot(gs[2])
    from emcorr import constants as C
    cor = corridors()
    _, Pb = register()
    v_el = cor["O4a_GREGY"]["mw"] * C.HOURS_PER_YEAR * Pb["uf_O4a_GREGY"] / C.lhv_to_gcv_efficiency(Pb["ccgt_eta_lhv"]) / C.MWH_PER_BCM_GCV
    g = np.linspace(0, 90, 400)
    for yr, col in [(2030, "#2E86AB"), (2040, "#7B52AB")]:
        sv = b["shortfall"][:, list(yrs).index(yr)]
        d = kde(sv, g)
        cx.fill_between(g, 0, d, color=col, alpha=0.3, lw=0)
        cx.plot(g, d, color=col, lw=1.0, label=f"Shortfall in {yr} (P > 10 bcm: {(sv > 10).mean():.2f})")
    top = cx.get_ylim()[1]
    for v, col, lab in [(10.0, OPT["O2_LNG_Egypt"][2], "LNG via Egypt" + chr(10) + "export volume"),
                        (v_el, OPT["O4a_GREGY"][2], "GREGY, gas-" + chr(10) + "equivalent")]:
        cx.axvline(v, color=col, lw=1.1, ls=(0, (3, 1.5)))
        cx.text(v + 0.8, top * 0.30, lab.replace(chr(10), " "), fontsize=5.4, color=shade(col, 0.8), va="bottom", ha="left", rotation=90)
    cx.set_xlim(0, 90)
    cx.set_ylim(0, top * 1.05)
    cx.set_xlabel("Egypt's gas shortfall (bcm per year)")
    cx.set_ylabel("Probability density")
    cx.legend(loc="upper right", fontsize=5.3)
    hgrid(cx)
    panel(cx, "c", x=-0.2, y=1.02)
    save(fig, "Fig5_egypt_nexus")

# ---------------------------------------------------------------------------------------------
# Fig. 6  Global sensitivity (Sobol indices) of the comparisons that matter
# ---------------------------------------------------------------------------------------------
GROUP = {
    "maritime": ("Maritime and legal", LAYER["maritime"][1]),
    "conflict": ("Conflict, diversion, Egypt balance", LAYER["conflict"][1]),
    "finance": ("Cost of capital", LAYER["cost_of_capital"][1]),
    "execution": ("Execution", LAYER["execution"][1]),
    "market": ("Prices and markets", "#2E86AB"),
    "tech": ("Technology and resource", "#6B8E23"),
}


def pgroup(p):
    if p in ("pi_contested", "delta_contested", "p_contested", "kappa_cable", "lam_geo", "mttr_geo"):
        return "maritime"
    if p.startswith(("eg_divert", "il_", "origin_", "eg_prod", "eg_dem", "eg_add", "eg_il", "eg_cy", "p_il")):
        return "conflict"
    if p.startswith(("wacc", "crp", "ds_", "erp", "rf_", "debt_margin", "infl", "tax")):
        return "finance"
    if p.startswith(("overrun", "delay", "pcancel", "u_tech", "phi_sunk", "u_lng")):
        return "execution"
    if p.startswith(("p_", "lng_toll", "lng_ship", "gasdem", "lng_regas", "cbam")):
        return "market"
    return "tech"


def fig6():
    sob = pd.read_csv(os.path.join(TAB, "sobol_indices.csv"))
    df, _ = register()
    status = dict(zip(df.name, df.status))
    targets = [("O3_minus_O1", "GSI minus EastMed"), ("O4a_minus_O1", "GREGY minus EastMed"),
               ("O4a_minus_O2", "GREGY minus LNG via Egypt"), ("O3_GSI_maritime", "Maritime-dispute cost of GSI")]
    fig, axs = plt.subplots(2, 2, figsize=(W2, 112 * MM), gridspec_kw={"wspace": 0.95, "hspace": 0.55})
    for ax, (t, title), letter in zip(axs.ravel(), targets, "abcd"):
        q = sob[sob.target == t].sort_values("ST", ascending=False).head(8).iloc[::-1]
        for i, r in enumerate(q.itertuples()):
            col = GROUP[pgroup(r.param)][1]
            lo, hi = max(r.ST - r.ST_conf, 0), r.ST + r.ST_conf
            ax.plot([lo, hi], [i, i], color=shade(col, 0.7), lw=0.8, zorder=2)
            ax.plot(r.ST, i, "o", ms=4.2, color=col, mec=shade(col, 0.6), mew=0.5, zorder=3)
            ax.plot(max(r.S1, 0), i, "D", ms=3.0, mfc="white", mec=col, mew=0.8, zorder=4)
        ax.set_yticks(range(len(q)), [plabel(p, status.get(p)) for p in q.param], fontsize=6.0)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, max(0.55, q.ST.max() + q.ST_conf.max() + 0.03))
        ax.set_xlabel("Sobol index")
        ax.set_title(title, fontsize=6.5, loc="left", pad=4)
        hgrid(ax, "x")
        ax.spines["left"].set_visible(False)
        panel(ax, letter, x=-0.62, y=1.04)
    h = [Line2D([], [], marker="o", ls="", ms=4.2, color=c, label=l) for l, c in GROUP.values()]
    h += [Line2D([], [], marker="o", ls="-", lw=0.8, ms=4.2, color=INK2, label="Total-order index, 95% CI"),
          Line2D([], [], marker="D", ls="", ms=3.0, mfc="white", mec=INK2, mew=0.8, label="First-order index")]
    fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06), fontsize=5.9, columnspacing=1.4)
    fig.text(0.995, -0.06, "† judgment parameter", ha="right", va="bottom", fontsize=5.8, color=INK2)
    save(fig, "Fig6_global_sensitivity")


# ---------------------------------------------------------------------------------------------
# Fig. 7  Scenario matrix
# ---------------------------------------------------------------------------------------------
SCEN_GROUPS = [
    ("Maritime and legal", [("no_contested_premium", "No contested-waters WACC premium"),
                            ("kappa_1", "No legal advantage for cables (κ = 1)"),
                            ("high_interference", "Baltic-type interference hazard")]),
    ("Egypt", [("no_egypt_diversion", "Egypt never diverts exports"),
               ("symmetric_egypt_diversion", "Egypt diverts power like gas"),
               ("egypt_dfi_wacc", "Egyptian renewables at 7% WACC"),
               ("gulf_of_suez_wind", "Gulf of Suez wind resource")]),
    ("EU policy and markets", [("cbam_half_default", "CBAM: half of cable imports at Annex III default value"),
                               ("cbam_default", "CBAM: all cable imports at Annex III default value"),
                               ("cbam_grid_default", "CBAM: all cable imports at grid-average factor"),
                               ("correlated_replacement_prices", "Gas and power prices correlated"),
                               ("existing_ccgt", "Gas burned in existing CCGTs")]),
    ("Corridor design and conflict", [("gsi_trade_link", "GSI used as a trade link (utilization 0.6)"),
                                      ("eastmed_12bcm", "EastMed at 12 bcm/yr"),
                                      ("gregy_west_route", "GREGY routed west of Crete"),
                                      ("gregy_east_route", "GREGY routed east of Crete"),
                                      ("eastmed_alt_route", "EastMed alternative alignment"),
                                      ("israel_crisis_regime", "Israeli shutdowns at 2023-26 rate")]),
]


def fig7():
    from matplotlib.colors import TwoSlopeNorm
    s = pd.read_csv(os.path.join(TAB, "scenarios.csv"))
    base = s[s.scenario == "base"].set_index("option")["mean"]
    rows, ypos, y, heads = [], [], 0, []
    rows.append(("base", "Central case")); ypos.append(y); y += 1.25
    for g, items in SCEN_GROUPS:
        heads.append((y - 0.05, g)); y += 0.85
        for k, lab in items:
            rows.append((k, lab)); ypos.append(y); y += 1
        y += 0.35
    fig = plt.figure(figsize=(W2, (4.3 * y + 26) * MM))
    ax = fig.add_axes([0.33, 0.085, 0.47, 0.86])
    norm = TwoSlopeNorm(vcenter=0, vmin=-70, vmax=70)
    cmap = diverging()
    for (k, lab), yy in zip(rows, ypos):
        q = s[s.scenario == k].set_index("option")
        for j, o in enumerate(IMPORTS):
            d = q.loc[o, "mean"] - base[o]
            ax.add_patch(Rectangle((j - 0.5, yy - 0.45), 1, 0.9, facecolor=cmap(norm(d)), edgecolor="white", lw=0.8))
            ax.text(j, yy, f"{q.loc[o, 'mean']:.0f}", ha="center", va="center", fontsize=5.8,
                    color="white" if abs(d) > 45 else INK)
        ax.text(-0.62, yy, lab, ha="right", va="center", fontsize=5.9, color=INK)
        win = q["p_cheapest_import"].idxmax()
        ax.plot(5.0, yy, "s", ms=3.4, color=OPT[win][2], clip_on=False)
        ax.text(5.2, yy, f"{OPT[win][1]} ({q.loc[win, 'p_cheapest_import']:.2f})", ha="left", va="center", fontsize=5.8)
    for yy, g in heads:
        ax.text(-0.62 - 0.0, yy, g, ha="right", va="center", fontsize=6.0, fontweight="bold", color=INK2)
        ax.plot([-0.55, 4.5], [yy + 0.3, yy + 0.3], color=GRIDC, lw=0.6, clip_on=False)
    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(y - 0.3, -1.6)
    ax.set_xticks(range(5), [OPT[o][1] for o in IMPORTS], fontsize=6.2)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=2)
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.text(5.0, -1.25, "Cheapest import (P)", ha="left", va="center", fontsize=6.0, fontweight="bold", color=INK2)
    cax = fig.add_axes([0.33, 0.035, 0.47, 0.012])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=[-60, -30, 0, 30, 60])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=5.8, length=1.5)
    cb.set_label("Change in mean risk-adjusted cost vs central case (EUR/MWh); cell values are scenario means", fontsize=6)
    save(fig, "Fig7_scenarios")


# ---------------------------------------------------------------------------------------------
# Fig. 8  Policy levers: break-even maps against the EastMed pipeline
# ---------------------------------------------------------------------------------------------
def fig8():
    from matplotlib.colors import TwoSlopeNorm
    _, Pb = register()
    norm = TwoSlopeNorm(vcenter=0, vmin=-60, vmax=120)
    levels = np.arange(-60, 121, 10)
    cmap = diverging()
    specs = [
        ("O3_GSI", "uf_O3_GSI", np.linspace(0.2, 0.75, 56), 1.0, "GSI utilization",
         "pi_contested", np.linspace(0, 0.03, 61), 100.0, "Contested-waters WACC premium (pp)", "GSI minus EastMed"),
        ("O4a_GREGY", "eg_divert_theta_el", np.linspace(0, 1, 51), 1.0, "Egypt's propensity to divert exported power",
         "wacc_re_EG", np.linspace(0.05, 0.16, 56), 100.0, "Egyptian renewables WACC (%, real)", "GREGY minus EastMed"),
        ("O4a_GREGY", "cbam_share_default", np.linspace(0, 1, 51), 1.0, "Share of imports charged CBAM default value",
         "cbam_ef_EG", np.linspace(0.2, 1.0, 51), 1.0, "CBAM factor for Egyptian electricity (tCO$_2$/MWh)", "GREGY minus EastMed"),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(W2, 64 * MM), gridspec_kw={"wspace": 0.42})
    for ax, (o, xn, xs, xsc, xl, yn, ys, ysc, yl, title), letter in zip(axs, specs, "abc"):
        X, Y = np.meshgrid(xs, ys)
        r = evaluate_grid({xn: X.ravel(), yn: Y.ravel()}, X.size)
        Z = (np.asarray(r[o][4]) - np.asarray(r["O1_EastMed"][4])).reshape(X.shape)
        cf = ax.contourf(X * xsc, Y * ysc, Z, levels=levels, cmap=cmap, norm=norm, extend="both")
        cs = ax.contour(X * xsc, Y * ysc, Z, levels=[0], colors=[INK], linewidths=1.0)
        ax.clabel(cs, fmt={0: "break-even"}, fontsize=5.4, inline=True)
        cx_, cy_ = Pb[xn] * xsc, Pb[yn] * ysc
        if xn == "cbam_share_default":
            ax.text(0.03, 0.04, "Central case: share = 0", transform=ax.transAxes, va="bottom",
                    fontsize=5.4, color=INK, path_effects=HALO)
            for yv, lab, above in [(0.442, "Annex III default (Reg. 2025/2621)", True), (0.387, "grid average (Annex II)", False)]:
                ax.axhline(yv, color=INK, lw=0.7, ls=(0, (3, 1.5)))
                ax.text(0.98, yv + 0.015 if above else yv - 0.015, lab, transform=ax.get_yaxis_transform(), ha="right",
                        va="bottom" if above else "top", fontsize=5.2, color=INK, path_effects=HALO)
        else:
            ax.plot(cx_, cy_, marker="*", ms=8, mfc="#FFD447", mec=INK, mew=0.6, zorder=5)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.set_title(title, fontsize=6.5, loc="left", pad=4)
        panel(ax, letter, x=-0.18, y=1.05)
    cb = fig.colorbar(cf, ax=axs, fraction=0.025, pad=0.02, ticks=[-60, -30, 0, 30, 60, 90, 120])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=5.8, length=1.5)
    cb.set_label("Cost difference (EUR/MWh); negative = cable cheaper", fontsize=6)
    fig.text(0.5, -0.06, "Other parameters at central values; star = central case.", ha="center", fontsize=5.8, color=INK2)
    save(fig, "Fig8_policy_breakeven")


FIGS = {"1": fig1, "2": fig2, "3": fig3, "4": fig4, "5": fig5, "6": fig6, "7": fig7, "8": fig8}

if __name__ == "__main__":
    style()
    for key in (sys.argv[1:] or list(FIGS)):
        FIGS[key]()