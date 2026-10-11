"""Shared style, palette and data access for the paper figures.

Journal conventions (Elsevier / Energy Policy): Arial, 7 pt text (6.5 pt ticks), 0.5 pt
axes, outward ticks, lower-case bold panel letters, widths of 90 mm (single column),
140 mm (1.5 column) and 190 mm (double column); 600 dpi PNG plus EPS (no other formats).

Color rules (author's standard): every data element is drawn in a distinct color, never
in black or gray. Options use the Okabe-Ito color-blind-safe set (plus olive for the
domestic benchmark); risk layers use a separately validated set; maritime claims use
distinct pastel tints by overlapping pair (no color is assigned to any state); text and
axes are dark navy. Palettes were checked with the dataviz validator (CVD separation,
lightness band, chroma floor); hues below 3:1 contrast always carry labels.
"""
import os
import sys

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402
from matplotlib.colors import to_rgb     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
TAB = os.path.join(ROOT, "outputs", "tables")
DATA = os.path.join(ROOT, "outputs", "data")
FIG_MAIN = os.path.join(ROOT, "outputs", "figures", "main")
FIG_SI = os.path.join(ROOT, "outputs", "figures", "si")
for d in (FIG_MAIN, FIG_SI):
    os.makedirs(d, exist_ok=True)

MM = 1 / 25.4
W1, W15, W2 = 90 * MM, 140 * MM, 190 * MM

INK = "#1F2A44"        # dark navy: text and axes
INK2 = "#3D5A80"       # slate blue: secondary text
GRIDC = "#DCE6F2"      # light blue gridlines
SEA = "#EAF3FA"
LAND = "#F4ECDC"
COAST = "#B9A27A"
EEZC = "#5B7DB1"
ACCENT = "#C8443A"

OPT = {  # key: (label, short label, color, marker)
    "O1_EastMed": ("EastMed pipeline", "EastMed", "#0072B2", "o"),
    "O2_LNG_Egypt": ("Levant LNG via Egypt", "LNG via Egypt", "#D55E00", "s"),
    "O3_GSI": ("Great Sea Interconnector", "GSI", "#009E73", "D"),
    "O4a_GREGY": ("GREGY", "GREGY", "#E69F00", "^"),
    "O4b_EuroAfrica": ("EuroAfrica", "EuroAfrica", "#CC79A7", "v"),
    "O5_Greek_RE": ("Greek renewables", "Greek RE", "#6B8E23", "P"),
}
OPTIONS = list(OPT)
IMPORTS = OPTIONS[:5]
CABLES = ["O3_GSI", "O4a_GREGY", "O4b_EuroAfrica"]
FIXED_ASSET = ["O1_EastMed"] + CABLES
LAYER_KEYS = ["base", "cost_of_capital", "execution", "conflict", "maritime"]
LAYER = {
    "base": ("Base cost (Greek financing)", "#3FA7E0"),
    "cost_of_capital": ("Partner-country cost of capital", "#7B52AB"),
    "execution": ("Execution risk", "#E8A33D"),
    "conflict": ("Conflict and diversion", "#C8443A"),
    "maritime": ("Maritime disputes", "#1AA391"),
}
ZONE = {  # overlapping claims: pastel tint, hatch color, hatch
    "TR_vs_GR": ("Greece-Türkiye overlap", "#D7BDE2", "#8E44AD", "////"),
    "TR_vs_CY": ("Cyprus-Türkiye overlap", "#FAD7A0", "#CA6F1E", "\\\\\\\\"),
    "LY_vs_GR": ("Greece-Libya overlap", "#A9DFBF", "#1E8449", "...."),
}
FREE = ("Undisputed waters", "#D6EAF8", "#5DADE2")


def diverging():
    """Blue - cream - red diverging map (no gray midpoint)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(
        "blue_cream_red", ["#08519C", "#4A90C8", "#BFDCF0", "#FFF2CC", "#F9C2A8", "#E0573F", "#A50F15"])


def shade(c, f):
    """Darken (f < 1) or lighten (f > 1, towards white) a color."""
    r, g, b = to_rgb(c)
    if f <= 1:
        return (r * f, g * f, b * f)
    t = f - 1
    return (r + (1 - r) * t, g + (1 - g) * t, b + (1 - b) * t)


def style():
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5, "legend.title_fontsize": 6.5, "axes.titleweight": "bold", "axes.titlepad": 3,
        "axes.linewidth": 0.5, "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
        "axes.titlecolor": INK, "axes.labelpad": 2.5, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "axes.axisbelow": True, "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.color": INK, "ytick.color": INK, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
        "xtick.major.pad": 2, "ytick.major.pad": 2,
        "lines.linewidth": 1.0, "lines.markersize": 3.5, "patch.linewidth": 0.5, "hatch.linewidth": 0.35,
        "legend.frameon": False, "legend.handlelength": 1.5, "legend.handletextpad": 0.5,
        "legend.borderaxespad": 0.2, "legend.columnspacing": 1.0, "legend.labelspacing": 0.35,
        "figure.dpi": 150, "savefig.dpi": 600, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "mathtext.default": "regular",
    })


def panel(ax, letter, x=-0.02, y=1.0, **kw):
    """Bold lower-case panel letter at the top-left corner of an axes (axes fraction)."""
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=8.5, fontweight="bold", va="bottom", ha="right",
            color=INK, **kw)


def hgrid(ax, axis="y"):
    ax.grid(axis=axis, color=GRIDC, lw=0.45, zorder=0)


def _rasterize_transparent(fig):
    """The PostScript backend cannot draw transparency. Before the EPS export, flag every
    partially transparent artist as rasterized so it is embedded as a 600 dpi image with its
    transparency composited, while axes, lines and text stay vector."""
    n = 0
    for a in fig.findobj():
        transparent = (a.get_alpha() is not None and a.get_alpha() < 1)
        if not transparent and hasattr(a, "get_facecolor"):
            try:
                fc = np.atleast_2d(a.get_facecolor())
                transparent = fc.size > 0 and fc.shape[-1] == 4 and bool((fc[:, 3] < 1).any())
            except Exception:
                transparent = False
        if transparent:
            try:
                a.set_rasterized(True)
                n += 1
            except Exception:
                pass
    return n


def save(fig, name, si=False):
    d = FIG_SI if si else FIG_MAIN
    fig.savefig(os.path.join(d, f"{name}.png"))       # 600 dpi raster (rcParams)
    _rasterize_transparent(fig)
    fig.savefig(os.path.join(d, f"{name}.eps"))       # Encapsulated PostScript, Type 42 fonts
    plt.close(fig)
    print("saved", ("si/" if si else "main/") + name)

def load_draws():
    """Monte Carlo draws written by 10_run_model.py: res[option][layer] and sampled parameters."""
    z = np.load(os.path.join(DATA, "mc_draws.npz"))
    res = {o: {l: z[f"res__{o}__{l}"] for l in range(5)} for o in OPTIONS}
    par = {k[5:]: z[k] for k in z.files if k.startswith("par__")}
    return res, par


def increments(r):
    d = {"base": r[0]}
    for i, k in enumerate(LAYER_KEYS[1:], start=1):
        d[k] = r[i] - r[i - 1]
    d["geopolitical"] = r[4] - r[2]
    d["total"] = r[4]
    return d


def register():
    from emcorr import mc
    df = mc.load_params(os.path.join(ROOT, "config", "parameters.csv"))
    return df, mc.base_values(df)


def corridors():
    from emcorr import mc
    return mc.load_corridors(os.path.join(ROOT, "config", "corridors.yaml"))


def evaluate_grid(overrides, n):
    """Deterministic evaluation at central values with some parameters set to arrays of length n."""
    from emcorr import options
    df, Pb = register()
    P = {k: np.full(n, v, dtype=float) for k, v in Pb.items()}
    for k, v in overrides.items():
        P[k] = np.broadcast_to(np.asarray(v, dtype=float), (n,)).copy()
    return options.evaluate(P, corridors(), np.arange(2025, 2061))


def kde(x, grid, bw=None):
    from scipy.stats import gaussian_kde
    return gaussian_kde(x, bw_method=bw)(grid)


PARAM_LABEL = {
    "pi_contested": "Contested-waters WACC premium", "delta_contested": "Contested-waters delay",
    "kappa_cable": "Legal factor for cables (κ)", "lam_geo": "Interference hazard", "mttr_geo": "Interference outage length",
    "p_contested": "Contested abandonment probability", "overrun_hvdc": "HVDC cost overrun",
    "overrun_pipe": "Pipeline cost overrun", "delay_hvdc": "HVDC reference-class delay",
    "delay_pipe": "Pipeline reference-class delay", "uf_O3_GSI": "GSI utilization", "uf_O4a_GREGY": "GREGY utilization",
    "uf_O4b_EuroAfrica": "EuroAfrica utilization", "capex_O3_GSI": "GSI capex", "capex_O4a_GREGY": "GREGY capex",
    "capex_O4b_EuroAfrica": "EuroAfrica capex", "eg_divert_theta_el": "Egypt diverts exported power",
    "eg_divert_theta": "Egypt diverts export gas", "p_repl_el": "Replacement electricity price",
    "p_repl_gas": "Replacement gas price (TTF)", "p_co2": "EU ETS carbon price", "ccgt_capex": "CCGT capex",
    "ccgt_cf": "CCGT capacity factor", "ccgt_fom": "CCGT fixed O&M", "firming_adder": "Firming cost",
    "wacc_re_EG": "Egyptian renewables WACC", "wacc_re_IL": "Israeli renewables WACC", "wacc_re_GR": "Greek renewables WACC",
    "il_export_cut": "Israeli export curtailment", "il_shutdown_rate": "Israeli field shutdown rate",
    "il_shutdown_days": "Israeli shutdown duration", "em_util0": "EastMed initial utilization", "em_capex": "EastMed capex",
    "gasdem_decline": "EU gas demand decline", "gasdem_plateau": "EU gas demand plateau", "gasdem_floor": "EU gas demand floor",
    "p_gas_levant_usd": "Levant gas price", "eg_wind_cf": "Egyptian wind capacity factor", "eg_wind_capex": "Egyptian wind capex",
    "eg_solar_capex": "Egyptian solar capex", "il_solar_capex": "Israeli solar capex", "il_solar_cf": "Israeli solar capacity factor",
    "crp_GR": "Greek country risk premium", "crp_EG": "Egyptian country risk premium", "crp_CY": "Cypriot country risk premium",
    "u_tech_hvdc": "HVDC technical unavailability", "u_tech_pipe": "Pipeline technical unavailability",
    "lng_toll_usd": "Liquefaction toll", "erp_mature": "Mature-market equity risk premium", "rf_usd": "Risk-free rate",
    "gr_curtail": "Greek curtailment", "pcancel_hvdc": "HVDC abandonment probability", "pcancel_pipe": "Pipeline abandonment probability",
    "phi_sunk": "Sunk share at abandonment", "hvdc_fom_pct": "HVDC fixed O&M", "infl_usd": "US inflation",
    "eg_dem_growth": "Egypt gas demand growth", "eg_prod_decline": "Egypt production decline", "eg_add_level": "Egypt new-field output",
    "gr_wind_capex": "Greek wind capex", "gr_solar_capex": "Greek solar capex", "gr_wind_cf": "Greek wind capacity factor",
    "gr_solar_cf": "Greek solar capacity factor", "em_fuel_pct": "EastMed compression fuel", "hvdc_cable_loss": "HVDC cable loss",
    "debt_margin_hvdc": "HVDC debt margin", "debt_margin_pipe": "Pipeline debt margin", "ccgt_eta_lhv": "CCGT efficiency",
}


def plabel(p, status=None):
    s = PARAM_LABEL.get(p, p)
    return s + ("$^{\\dagger}$" if status == "judgment" else "")