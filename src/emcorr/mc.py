"""Parameter loading, Latin-hypercube sampling and Sobol sensitivity.

Sobol indices are computed on the unit hypercube and mapped to parameter
space through each marginal's inverse CDF. Because Sobol indices of
independent inputs are invariant to monotone re-parameterisation, the
indices refer directly to the named parameters.
"""
import numpy as np
import pandas as pd
import yaml
from scipy.stats import qmc, triang


def validate(df):
    """Fail loudly on malformed rows (a silent NaN once corrupted a whole option)."""
    bad = []
    for r in df.itertuples():
        if pd.isna(r.base):
            bad.append(f"{r.name}: missing base")
        if r.dist in ("uniform", "triangular"):
            if pd.isna(r.low) or pd.isna(r.high) or not (r.low <= r.base <= r.high) or r.low == r.high:
                bad.append(f"{r.name}: need low <= base <= high, got {r.low}, {r.base}, {r.high}")
        elif r.dist in ("shiftlognorm", "delaymix"):
            if pd.isna(r.low) or pd.isna(r.high) or r.high <= 0 or r.base <= 0:
                bad.append(f"{r.name}: invalid {r.dist} parameters")
        elif r.dist != "fixed":
            bad.append(f"{r.name}: unknown dist {r.dist}")
    if bad:
        raise ValueError("parameter register errors: " + "; ".join(bad))
    return df


def load_params(path):
    df = pd.read_csv(path)
    for c in ("base", "low", "high"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return validate(df)


def load_corridors(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def uncertain(df):
    return df[df["dist"] != "fixed"].reset_index(drop=True)


def base_values(df):
    """Deterministic central values: the mode (triangular), the median (lognormal
    families: shift + median), the stated value (fixed)."""
    out = {}
    for r in df.itertuples():
        v = r.base
        if r.dist in ("shiftlognorm", "delaymix"):
            v = float(_ppf(r._asdict(), 0.5))      # distribution median
        out[r.name] = v
    return out


def _ppf(row, u):
    """Inverse CDF for the register's distributions.

    uniform(low, high) | triangular(low, mode=base, high)
    shiftlognorm: x = low + base * exp(high * z)   (base = median of the lognormal
                  part, low = shift, high = sigma)  e.g. capex overrun
    delaymix:     with prob. low, x ~ U(0, 0.25) yr (no material delay); otherwise
                  x = base * exp(high * z)  (base = median, high = sigma), in years
    """
    from scipy.stats import norm
    if row["dist"] == "shiftlognorm":
        z = norm.ppf(np.clip(u, 1e-9, 1 - 1e-9))
        return row["low"] + row["base"] * np.exp(row["high"] * z)
    if row["dist"] == "delaymix":
        p0 = row["low"]
        u = np.asarray(u, dtype=float)
        z = norm.ppf(np.clip((u - p0) / (1 - p0), 1e-9, 1 - 1e-9))
        return np.where(u < p0, 0.25 * u / p0, row["base"] * np.exp(row["high"] * z))
    if row["dist"] == "uniform":
        return row["low"] + u * (row["high"] - row["low"])
    if row["dist"] == "triangular":
        lo, hi, mode = row["low"], row["high"], row["base"]
        c = (mode - lo) / (hi - lo) if hi > lo else 0.5
        return triang.ppf(u, c, loc=lo, scale=hi - lo)
    raise ValueError(f"unknown dist {row['dist']} for {row['name']}")


def map_unit(df, U):
    """Map a unit-cube sample U (n, k_uncertain) to a full parameter dict."""
    P = base_values(df)
    unc = uncertain(df)
    for j, row in unc.iterrows():
        P[row["name"]] = _ppf(row, U[:, j])
    return P


def sample_lhs(df, n, seed=2026):
    k = len(uncertain(df))
    U = qmc.LatinHypercube(d=k, seed=seed).random(n)
    return map_unit(df, U), U


def sobol_problem(df):
    unc = uncertain(df)
    return {"num_vars": len(unc), "names": unc["name"].tolist(), "bounds": [[0.0, 1.0]] * len(unc)}
