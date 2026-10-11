"""Scenario and structural sensitivity runs with common random numbers.

Every scenario overrides parameters of the same Latin-hypercube sample (seed 2026)
or the corridor geometry, so differences between scenarios are not sampling noise.

Usage (from analysis/):  python scripts/11_scenarios.py [--n 20000]
Output: outputs/tables/scenarios.csv, scenarios_h0.csv
"""
import argparse
import copy
import os
import sys
from importlib import import_module

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from emcorr import mc                      # noqa: E402
rm = import_module("10_run_model")
ROOT, TAB = rm.ROOT, rm.TAB


def redraw(df, U, name, mode, low, high):
    """Same uniform draws, new triangular marginal (keeps common random numbers)."""
    unc = mc.uncertain(df)
    j = int(unc.index[unc["name"] == name][0])
    return mc._ppf({"dist": "triangular", "base": mode, "low": low, "high": high, "name": name}, U[:, j])


def correlate(df, U, name, partner, rho):
    """Redraw `name` with its own marginal but Gaussian-copula correlation rho with `partner`."""
    from scipy.stats import norm
    unc = mc.uncertain(df)
    j = int(unc.index[unc["name"] == name][0])
    k = int(unc.index[unc["name"] == partner][0])
    z = rho * norm.ppf(U[:, k]) + np.sqrt(1 - rho ** 2) * norm.ppf(U[:, j])
    row = unc.loc[j].to_dict()
    return mc._ppf(row, norm.cdf(z))


def set_route(cor, key, x, weights):
    cor[key]["x_contested"] = x
    cor[key]["weights"] = weights


# name: (description, parameter overrides(P, df, U) -> None, corridor overrides(cor) -> None)
SCENARIOS = {
    "base": ("central assumptions", None, None),
    "no_contested_premium": ("contested-waters WACC premium = 0 (no double counting with sovereign CRP)",
                             lambda P, df, U: P.update(pi_contested=0.0), None),
    "kappa_1": ("no legal asymmetry: cables face pipeline-level contested delay and abandonment",
                lambda P, df, U: P.update(kappa_cable=1.0), None),
    "high_interference": ("Baltic-type interference hazard: 0.2 damaging events/yr on a fully contested route",
                          lambda P, df, U: P.update(lam_geo=0.2), None),
    "no_egypt_diversion": ("Egypt never diverts gas or power exports (full ring-fence)",
                           lambda P, df, U: P.update(eg_divert_theta=0.0, eg_divert_theta_el=0.0), None),
    "symmetric_egypt_diversion": ("power exports diverted with the same propensity as gas",
                                  lambda P, df, U: P.update(eg_divert_theta_el=P["eg_divert_theta"]), None),
    "egypt_dfi_wacc": ("Egyptian renewables financed at the DFI-backed PPA level (7% real)",
                       lambda P, df, U: P.update(wacc_re_EG=0.07), None),
    "gulf_of_suez_wind": ("Egyptian wind at Gulf of Suez resource (CF mode 0.46)",
                          lambda P, df, U: P.update(eg_wind_cf=redraw(df, U, "eg_wind_cf", 0.46, 0.39, 0.525)), None),
    "correlated_replacement_prices": ("Greek power and TTF replacement prices correlated (rho = 0.8)",
                                      lambda P, df, U: P.update(p_repl_el=correlate(df, U, "p_repl_el", "p_repl_gas", 0.8)), None),
    "cbam_half_default": ("CBAM: half of cable imports charged at the Annex III default values (EG 0.442, IL 0.480 tCO2/MWh)",
                          lambda P, df, U: P.update(cbam_share_default=0.5), None),
    "cbam_default": ("CBAM: all cable imports charged at the Annex III default values (EG 0.442, IL 0.480 tCO2/MWh)",
                     lambda P, df, U: P.update(cbam_share_default=1.0), None),
    "cbam_grid_default": ("CBAM: all cable imports charged at grid-average factors (EG 0.387, IL 0.443 tCO2/MWh, Annex II; basis of the December 2025 proposal)",
                          lambda P, df, U: P.update(cbam_share_default=1.0, cbam_ef_EG=0.387, cbam_ef_IL=0.443), None),
    "existing_ccgt": ("gas burned in existing Greek CCGTs (no new-build capex)",
                      lambda P, df, U: P.update(ccgt_capex_share=0.0), None),
    "gsi_trade_link": ("GSI used as a bidirectional trade link (utilisation 0.60)",
                       lambda P, df, U: P.update(uf_O3_GSI=0.60), None),
    "israel_crisis_regime": ("Israeli field shutdowns at the 2023-26 frequency (1 per year)",
                             lambda P, df, U: P.update(il_shutdown_rate=1.0), None),
    "eastmed_12bcm": ("EastMed at 12 bcm/yr with unchanged capex (upper bound on scale economies)",
                      lambda P, df, U: P.update(em_capacity_bcm=12.0), None),
    "gregy_west_route": ("GREGY west of Crete (16.3% in the Libya-claimed zone)", None,
                         lambda cor: set_route(cor, "O4a_GREGY", 0.163, {"GR": 0.8952, "EG": 0.1048})),
    "gregy_east_route": ("GREGY east of Crete (21.0% in Libya- and Turkiye-claimed zones)", None,
                         lambda cor: set_route(cor, "O4a_GREGY", 0.210, {"GR": 0.7623, "EG": 0.2377})),
    "eastmed_alt_route": ("EastMed alternative Crete-Peloponnese alignment", None,
                          lambda cor: set_route(cor, "O1_EastMed", 0.358, cor["O1_EastMed"]["weights"])),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    a = ap.parse_args()
    df = mc.load_params(os.path.join(ROOT, "config", "parameters.csv"))
    cor0 = mc.load_corridors(os.path.join(ROOT, "config", "corridors.yaml"))
    P0, U = mc.sample_lhs(df, a.n)
    rows, h0 = [], []
    for name, (desc, fp, fc) in SCENARIOS.items():
        P = dict(P0)
        cor = copy.deepcopy(cor0)
        if fp:
            fp(P, df, U)
        if fc:
            fc(cor)
        res = rm.run(P, cor, a.n)
        LT = np.vstack([res[o][rm.TOP] for o in rm.IMPORTS])
        cheapest = pd.Series(np.array(rm.IMPORTS)[LT.argmin(0)]).value_counts(normalize=True)
        for o in rm.options.OPTIONS:
            inc = rm.increments(res[o])
            t = inc["total"]
            rows.append({"scenario": name, "option": o, "mean": t.mean(), "p5": np.percentile(t, 5),
                         "p95": np.percentile(t, 95), "maritime": inc["maritime"].mean(),
                         "geopolitical": inc["geopolitical"].mean(), "p_cheapest_import": cheapest.get(o, 0.0),
                         "description": desc})
        em = rm.increments(res["O1_EastMed"])
        for c in rm.CABLES:
            ic = rm.increments(res[c])
            h0.append({"scenario": name, "cable": c,
                       "P_maritime_lt_EastMed": (ic["maritime"] < em["maritime"]).mean(),
                       "P_geopolitical_lt_EastMed": (ic["geopolitical"] < em["geopolitical"]).mean(),
                       "P_total_lt_EastMed": (ic["total"] < em["total"]).mean()})
        print(f"{name:28s} " + "  ".join(f"{o.split('_')[0]} {res[o][rm.TOP].mean():6.1f}" for o in rm.options.OPTIONS)
              + f"   cheapest import: {cheapest.idxmax()} {cheapest.max():.2f}")
    pd.DataFrame(rows).to_csv(os.path.join(TAB, "scenarios.csv"), index=False)
    pd.DataFrame(h0).to_csv(os.path.join(TAB, "scenarios_h0.csv"), index=False)


if __name__ == "__main__":
    main()
