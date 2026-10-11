"""Financial building blocks: cost of capital and levelised cost.

All functions accept floats or numpy arrays and broadcast, so the same code
serves deterministic runs and Monte Carlo draws.

Time convention: t = 0 at final investment decision (FID). Capital is spent
uniformly over the build period B = T + D (planned duration plus delay);
output runs from B to B + life. Discounting is continuous at
delta = ln(1 + r), the exact equivalent of an annual effective rate r.
"""
import numpy as np


# --------------------------------------------------------------------------
# Cost of capital
# --------------------------------------------------------------------------
def levered_beta(beta_unlevered, debt_to_equity, tax_rate):
    """Hamada: beta_L = beta_U * (1 + (1 - t) * D/E)."""
    return beta_unlevered * (1.0 + (1.0 - tax_rate) * debt_to_equity)


def wacc_nominal(rf, erp, crp, default_spread, beta_unlevered, debt_to_equity,
                 tax_rate, lam=1.0, debt_margin=0.0):
    """Damodaran-style after-tax nominal WACC.

    cost of equity = rf + beta_L * ERP_mature + lambda * CRP
    cost of debt   = rf + country default spread + project/debt margin
    """
    beta_l = levered_beta(beta_unlevered, debt_to_equity, tax_rate)
    ke = rf + beta_l * erp + lam * crp
    kd = rf + default_spread + debt_margin
    w_e = 1.0 / (1.0 + debt_to_equity)
    w_d = 1.0 - w_e
    return w_e * ke + w_d * kd * (1.0 - tax_rate)


def real_rate(nominal, inflation):
    """Fisher: (1 + n) / (1 + pi) - 1."""
    return (1.0 + nominal) / (1.0 + inflation) - 1.0


def weighted(values: dict, weights: dict):
    """Exposure-weighted average, e.g. CRP weighted by capex share per country.

    Weights are normalised; keys missing from `values` raise KeyError
    deliberately so a forgotten jurisdiction cannot pass silently.
    """
    total = sum(weights.values())
    return sum(values[k] * w for k, w in weights.items()) / total


# --------------------------------------------------------------------------
# Annuity / capitalisation factors
# --------------------------------------------------------------------------
def crf(r, n):
    """Discrete capital recovery factor r(1+r)^n / ((1+r)^n - 1); 1/n at r = 0."""
    r = np.asarray(r, dtype=float)
    n = np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        g = (1.0 + r) ** n
        out = r * g / (g - 1.0)
    return np.where(np.abs(r) < 1e-12, 1.0 / n, out)


def _delta(r):
    return np.log1p(np.asarray(r, dtype=float))


def annuity_cont(r, n):
    """PV at operation start of 1 unit/yr paid continuously for n years."""
    d = _delta(r)
    n = np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (1.0 - np.exp(-d * n)) / d
    return np.where(np.abs(d) < 1e-12, n, out)


def idc_factor(r, build_years):
    """Value at commissioning of 1 EUR spent uniformly over the build period.

    (e^{delta B} - 1) / (delta B): interest during construction.
    """
    d = _delta(r)
    b = np.asarray(build_years, dtype=float)
    x = d * b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.expm1(x) / x
    return np.where(np.abs(x) < 1e-12, 1.0, out)


# --------------------------------------------------------------------------
# Levelised cost of one asset/segment
# --------------------------------------------------------------------------
def levelized_cost(capex, annual_output, wacc, life, build_years,
                   fom_per_year=0.0, vom_per_unit=0.0, overrun=0.0, delay=0.0,
                   util_pv_factor=1.0, availability=1.0):
    """Levelised cost per unit of output (EUR/MWh if capex in EUR, output in MWh).

    LC = K * IDC(r, T + D) / (Q_eff * annuity(r, life)) + FOM / Q_eff + VOM

    K      = capex * (1 + overrun)
    Q_eff  = annual_output * util_pv_factor * availability

    util_pv_factor is the PV-weighted average utilisation over the asset's
    life (see `util_pv_factor`), e.g. a pipeline whose throughput falls as
    EU gas demand declines. availability scales delivered output for outages.

    Measuring from FID (not from commissioning) gives an identical result,
    because delay is already inside the IDC term: the e^{delta B} factors of
    the cost and output streams cancel exactly.
    """
    k = capex * (1.0 + overrun)
    q_eff = annual_output * util_pv_factor * availability
    b = np.asarray(build_years, dtype=float) + np.asarray(delay, dtype=float)
    cap = k * idc_factor(wacc, b) / annuity_cont(wacc, life)
    return cap / q_eff + fom_per_year / q_eff + vom_per_unit


def util_pv_factor(wacc, life, plateau_years, decline_rate, floor, steps_per_year=4):
    """PV-weighted mean utilisation of a throughput path, relative to full use.

    Path: U = 1 for tau < plateau, then exp(-decline_rate*(tau - plateau)),
    bounded below by `floor`. Numeric integration on a regular grid; inputs
    broadcast, so arrays of samples are supported.
    """
    wacc = np.atleast_1d(np.asarray(wacc, dtype=float))
    life = np.atleast_1d(np.asarray(life, dtype=float))
    plateau = np.atleast_1d(np.asarray(plateau_years, dtype=float))
    dec = np.atleast_1d(np.asarray(decline_rate, dtype=float))
    flo = np.atleast_1d(np.asarray(floor, dtype=float))
    shape = np.broadcast(wacc, life, plateau, dec, flo).shape
    wacc, life, plateau, dec, flo = (np.broadcast_to(a, shape) for a in (wacc, life, plateau, dec, flo))
    nmax = int(np.ceil(life.max() * steps_per_year))
    tau = (np.arange(nmax) + 0.5) / steps_per_year              # (nmax,)
    tau = tau.reshape((1,) * len(shape) + (nmax,))
    d = np.log1p(wacc)[..., None]
    alive = tau < life[..., None]
    u = np.where(tau < plateau[..., None], 1.0,
                 np.exp(-dec[..., None] * (tau - plateau[..., None])))
    u = np.maximum(u, flo[..., None])
    disc = np.exp(-d * tau) * alive
    out = (u * disc).sum(-1) / disc.sum(-1)
    return out if out.shape != (1,) else float(out[0])


# --------------------------------------------------------------------------
# Risk adjustments
# --------------------------------------------------------------------------
def cancellation_adjust(lc, p_cancel, sunk_share):
    """Expected cost of abandoned attempts recovered by successful projects.

    LC_adj = LC * (1 + phi * p / (1 - p)), with phi the share of the asset's
    PV cost sunk when a project is abandoned and p its abandonment probability.
    """
    p = np.clip(np.asarray(p_cancel, dtype=float), 0.0, 0.95)
    return lc * (1.0 + sunk_share * p / (1.0 - p))


def unavailability(hazard_per_year, mean_outage_days):
    """Expected share of the year out of service: lambda * MTTR, capped at 1."""
    return np.minimum(1.0, np.asarray(hazard_per_year) * np.asarray(mean_outage_days) / 365.0)


def combine_unavailability(*u):
    """Independent outage sources: 1 - prod(1 - u_k)."""
    a = 1.0
    for x in u:
        a = a * (1.0 - np.asarray(x, dtype=float))
    return 1.0 - a


def buyer_cost(cost_per_delivered_mwh, u, replacement_price):
    """Expected cost per MWh demanded when a share u is not delivered and
    must be bought at the replacement price."""
    return (1.0 - u) * cost_per_delivered_mwh + u * replacement_price
