"""Main model run: deterministic base, Monte Carlo, decomposition, H0 tests,
value of dispute resolution, break-even sweeps and Sobol sensitivity.

Usage (from analysis/):  python scripts/10_run_model.py [--n 20000] [--sobol 512]
Outputs: outputs/tables/*.csv, *.json
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from emcorr import constants as C          # noqa: E402
from emcorr import mc, options             # noqa: E402

ROOT = os.path.join(HERE, "..")
TAB = os.path.join(ROOT, "outputs", "tables")
os.makedirs(TAB, exist_ok=True)
YEARS = np.arange(2025, 2061)
IMPORTS = ["O1_EastMed", "O2_LNG_Egypt", "O3_GSI", "O4a_GREGY", "O4b_EuroAfrica"]
CABLES = ["O3_GSI", "O4a_GREGY", "O4b_EuroAfrica"]
GAS = ["O1_EastMed", "O2_LNG_Egypt"]
LAYERS = dict(enumerate(options.LAYERS))
TOP = len(LAYERS) - 1                      # full risk-adjusted layer (L4)
COMPONENTS = ["base", "cost_of_capital", "execution", "conflict", "maritime"]


def run(P, cor, n):
    """Evaluate in chunks; return {option: {layer: array(n)}}."""
    out = {o: {l: np.empty(n) for l in LAYERS} for o in options.OPTIONS}
    step = 50000
    for s in range(0, n, step):
        e = min(n, s + step)
        Pc = {k: (v[s:e] if isinstance(v, np.ndarray) and v.shape == (n,) else v) for k, v in P.items()}
        r = options.evaluate(Pc, cor, YEARS)
        for o in options.OPTIONS:
            for l in LAYERS:
                out[o][l][s:e] = np.broadcast_to(np.asarray(r[o][l], dtype=float), (e - s,))
    return out


def annual_twh(P, cor):
    """Annual electricity delivered (TWh_e) per option at central values, for EUR/yr scaling."""
    eta_el = C.lhv_to_gcv_efficiency(P["ccgt_eta_lhv"])
    gas_twh = P["em_capacity_bcm"] * P["em_util0"] * C.MWH_PER_BCM_GCV / 1e6
    out = {"O1_EastMed": gas_twh * eta_el, "O2_LNG_Egypt": P["o2_volume_bcm"] * C.MWH_PER_BCM_GCV / 1e6 * eta_el}
    for k in CABLES:
        out[k] = cor[k]["mw"] * C.HOURS_PER_YEAR * P[f"uf_{k}"] / 1e6
    return out


def increments(r):
    """Layer increments of one option's {layer: array} results."""
    d = {"base": r[0]}
    for i, name in enumerate(COMPONENTS[1:], start=1):
        d[name] = r[i] - r[i - 1]
    d["geopolitical"] = r[TOP] - r[2]          # conflict + maritime
    d["total"] = r[TOP]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--sobol", type=int, default=512, help="Saltelli base sample (0 = skip)")
    a = ap.parse_args()

    df = mc.load_params(os.path.join(ROOT, "config", "parameters.csv"))
    cor = mc.load_corridors(os.path.join(ROOT, "config", "corridors.yaml"))
    status = df["status"].value_counts().to_dict()

    # 1. deterministic central values (mode / median)
    Pb = mc.base_values(df)
    det = run({k: np.full(1, v) for k, v in Pb.items()}, cor, 1)
    rows = [{"option": o, **{LAYERS[l]: det[o][l][0] for l in LAYERS}} for o in options.OPTIONS]
    pd.DataFrame(rows).to_csv(os.path.join(TAB, "deterministic_by_layer.csv"), index=False)

    # 2. Monte Carlo
    P, _ = mc.sample_lhs(df, a.n)
    res = run(P, cor, a.n)
    summ = []
    for o in options.OPTIONS:
        for l, name in LAYERS.items():
            v = res[o][l]
            summ.append({"option": o, "layer": name, "mean": v.mean(), "p5": np.percentile(v, 5),
                         "p50": np.median(v), "p95": np.percentile(v, 95)})
    pd.DataFrame(summ).to_csv(os.path.join(TAB, "mc_summary.csv"), index=False)
    # full draws for figures and supplementary analysis
    os.makedirs(os.path.join(ROOT, "outputs", "data"), exist_ok=True)
    arrays = {f"res__{o}__{l}": res[o][l] for o in options.OPTIONS for l in LAYERS}
    arrays.update({f"par__{k}": np.broadcast_to(np.asarray(v, dtype=float), (a.n,)) for k, v in P.items()})
    np.savez_compressed(os.path.join(ROOT, "outputs", "data", "mc_draws.npz"), **arrays)

    # 3. decomposition of the risk-adjusted cost and value of dispute resolution
    twh = annual_twh(Pb, cor)
    dec = []
    for o in options.OPTIONS:
        inc = increments(res[o])
        d = {"option": o, **{k: v.mean() for k, v in inc.items()}}
        d["maritime_p5"], d["maritime_p95"] = np.percentile(inc["maritime"], [5, 95])
        if o in twh:
            d["annual_twh"] = twh[o]
            d["maritime_meur_per_yr"] = d["maritime"] * twh[o]
            d["geopolitical_meur_per_yr"] = d["geopolitical"] * twh[o]
        dec.append(d)
    dec = pd.DataFrame(dec)
    dec.to_csv(os.path.join(TAB, "risk_decomposition.csv"), index=False)

    # 4. ranking and H0 (cables escape geopolitics <=> their geopolitical increment per MWh is lower)
    LT = np.vstack([res[o][TOP] for o in IMPORTS])
    cheapest = pd.Series(np.array(IMPORTS)[LT.argmin(0)]).value_counts(normalize=True)
    h0 = {}
    for c in CABLES:
        ic = increments(res[c])
        for g in GAS:
            ig = increments(res[g])
            h0[f"P({c} < {g}), full risk"] = float((res[c][TOP] < res[g][TOP]).mean())
            h0[f"P(maritime increment {c} < {g})"] = float((ic["maritime"] < ig["maritime"]).mean())
            h0[f"P(geopolitical increment {c} < {g})"] = float((ic["geopolitical"] < ig["geopolitical"]).mean())
    exposure = {k: cor[k]["x_contested"] for k in ["O1_EastMed"] + CABLES}
    with open(os.path.join(TAB, "ranking_h0.json"), "w") as f:
        json.dump({"prob_cheapest_import": cheapest.to_dict(), "h0_tests": h0,
                   "route_exposure_share": exposure, "parameter_status": status, "n": a.n}, f, indent=2)

    # 5. break-even sweeps (others at central values): contested premium and kappa
    sweep = []
    for pi in np.linspace(0, 0.06, 25):
        for kap in (0.3, 0.6, 1.0):
            Pk = {k: np.full(1, v) for k, v in Pb.items()}
            Pk["pi_contested"], Pk["kappa_cable"] = np.full(1, pi), np.full(1, kap)
            r = run(Pk, cor, 1)
            sweep.append({"pi_contested": pi, "kappa": kap, **{o: r[o][TOP][0] for o in IMPORTS}})
    pd.DataFrame(sweep).to_csv(os.path.join(TAB, "breakeven_sweep.csv"), index=False)

    # 6. Sobol sensitivity (first-order and total indices)
    if a.sobol:
        from SALib.analyze import sobol as sobol_an
        from SALib.sample import sobol as sobol_sa
        prob = mc.sobol_problem(df)
        U = sobol_sa.sample(prob, a.sobol, calc_second_order=False, seed=2026)
        Ps = mc.map_unit(df, U)
        rs = run(Ps, cor, U.shape[0])
        targets = {f"{o}_full": rs[o][TOP] for o in IMPORTS}
        targets.update({f"{o}_maritime": rs[o][TOP] - rs[o][TOP - 1] for o in ["O1_EastMed"] + CABLES})
        targets.update({f"{o}_geopolitical": rs[o][TOP] - rs[o][2] for o in IMPORTS})
        targets.update({"O3_minus_O1": rs["O3_GSI"][TOP] - rs["O1_EastMed"][TOP],
                        "O4a_minus_O1": rs["O4a_GREGY"][TOP] - rs["O1_EastMed"][TOP],
                        "O4a_minus_O2": rs["O4a_GREGY"][TOP] - rs["O2_LNG_Egypt"][TOP]})
        out = []
        for t, y in targets.items():
            Si = sobol_an.analyze(prob, y, calc_second_order=False, seed=2026)
            for nm, s1, s1c, st, stc in zip(prob["names"], Si["S1"], Si["S1_conf"], Si["ST"], Si["ST_conf"]):
                out.append({"target": t, "param": nm, "S1": s1, "S1_conf": s1c, "ST": st, "ST_conf": stc})
        sob = pd.DataFrame(out)
        sob.to_csv(os.path.join(TAB, "sobol_indices.csv"), index=False)
        top = sob.sort_values("ST", ascending=False).groupby("target").head(6)
        top.sort_values(["target", "ST"], ascending=[True, False]).to_csv(os.path.join(TAB, "sobol_top.csv"), index=False)

    print(dec.round(2).to_string(index=False))
    print("\nP(cheapest import, full risk):", cheapest.round(3).to_dict())
    for k, v in h0.items():
        print(f"  {k}: {v:.3f}")
    print(f"\nparameter status: {status} (n = {len(df)})")


if __name__ == "__main__":
    main()
