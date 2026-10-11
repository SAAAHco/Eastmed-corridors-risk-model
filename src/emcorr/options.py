"""Cost chains for the five corridor options, with a five-layer risk decomposition.

evaluate(P, corridors, years) returns res[option][layer] = expected cost per MWh of
electricity demanded at the Greek grid (real EUR 2025). Layers are cumulative:

  L0 base            planned cost and schedule, every asset financed as a Greek
                       domestic asset (Greek country risk premium, default spread
                       and tax; generation at the Greek renewables WACC)
  L1 cost of capital + partner-country risk: infrastructure WACC weighted by the
                       jurisdictions crossed; generation at the source country's WACC
  L2 execution       + reference-class overrun, delay, post-FID abandonment and
                       technical unavailability
  L3 conflict        + war shutdowns of Israeli supply, Israeli export curtailment,
                       Egyptian diversion of gas and power exports
  L4 maritime        + contested-waters WACC premium, contested delay and abandonment
                       increments (scaled by the legal-regime factor for cables), and
                       interference outages

Value of dispute resolution = L4 - L3.
"""
import numpy as np

from . import constants as C
from . import finance as F
from .egypt import diversion_share, o2_unavailability

OPTIONS = ["O1_EastMed", "O2_LNG_Egypt", "O3_GSI", "O4a_GREGY", "O4b_EuroAfrica", "O5_Greek_RE"]
LAYERS = ["L0_base", "L1_cost_of_capital", "L2_execution", "L3_conflict", "L4_maritime"]
FLAGS = [dict(coc=c, exe=e, con=k, mar=m) for c, e, k, m in
         [(0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)]]
GREECE = {"GR": 1.0}


def _w(P, weights, prefix):
    return F.weighted({k: P[f"{prefix}_{k}"] for k in weights}, weights)


def seg_wacc_real(P, asset, weights, x, f):
    """Real after-tax WACC of an infrastructure segment under layer flags f."""
    w = weights if f["coc"] else GREECE
    nominal = F.wacc_nominal(P["rf_usd"], P["erp_mature"], _w(P, w, "crp"), _w(P, w, "ds"),
                             P[f"beta_u_{asset}"], P[f"de_{asset}"], _w(P, w, "tax"),
                             lam=1.0, debt_margin=P[f"debt_margin_{asset}"])
    real = F.real_rate(nominal, P["infl_usd"])
    return real + (P["pi_contested"] * x if f["mar"] else 0.0)


def gen_lcoe(P, prefix, wacc):
    """LCOE (EUR/MWh) of a solar/wind mix; capex EUR/kW, FOM EUR/kW-yr."""
    out = 0.0
    for tech in ("solar", "wind"):
        q = C.HOURS_PER_YEAR * P[f"{prefix}_{tech}_cf"]                      # MWh per MW-yr
        lc = F.levelized_cost(1000.0 * P[f"{prefix}_{tech}_capex"], q, wacc, P[f"{tech}_life"],
                              P[f"{tech}_build"], fom_per_year=1000.0 * P[f"{prefix}_{tech}_fom"])
        out = out + P[f"{prefix}_{tech}_share"] * lc
    return out


def ccgt_cost(P, gas_price, f):
    """Electricity from a Greek CCGT (financed in Greece at every layer).
    ccgt_capex_share = 0 treats the plant as existing (capital sunk)."""
    eta = C.lhv_to_gcv_efficiency(P["ccgt_eta_lhv"])
    w = seg_wacc_real(P, "ccgt", GREECE, 0.0, dict(f, coc=0, mar=0))
    q = C.HOURS_PER_YEAR * P["ccgt_cf"]
    capex = 1000.0 * P["ccgt_capex"] * P["ccgt_capex_share"]
    nonfuel = F.levelized_cost(capex, q, w, P["ccgt_life"], P["ccgt_build"],
                               fom_per_year=1000.0 * P["ccgt_fom"], vom_per_unit=P["ccgt_vom"])
    return gas_price / eta + nonfuel + C.EF_GAS_T_PER_MWH_GCV / eta * P["p_co2"]


def _risk(P, cls, x, kappa, f):
    """Delay (yr), overrun, abandonment probability for one infrastructure class."""
    delay = P[f"delay_{cls}"] if f["exe"] else 0.0
    over = P[f"overrun_{cls}"] if f["exe"] else 0.0
    pc = P[f"pcancel_{cls}"] if f["exe"] else 0.0
    if f["mar"]:
        delay = delay + P["delta_contested"] * x * kappa
        pc = pc + P["p_contested"] * x * kappa
    return delay, over, pc


def _outage(P, cls, x, f, origin_u=0.0):
    u = P[f"u_tech_{cls}"] if f["exe"] else 0.0
    if f["con"]:
        u = F.combine_unavailability(u, origin_u)
    if f["mar"]:
        u = F.combine_unavailability(u, F.unavailability(P["lam_geo"] * x, P["mttr_geo"]))
    return u


def israel_war_u(P):
    """Expected share of time Israeli energy exports stop because offshore fields are shut in war."""
    return F.unavailability(P["il_shutdown_rate"] * P["p_il_halt"], P["il_shutdown_days"])


def israel_supply_u(P):
    """Israeli gas exports: war shutdowns plus policy curtailment under the export permits."""
    return F.combine_unavailability(israel_war_u(P), P["il_export_cut"])


def egypt_power_u(P, cor, key, years):
    """Egyptian diversion of exported renewable power, from the same gas balance as O2.
    The export volume is expressed as the gas a CCGT would burn to produce it."""
    q_mwh = cor[key]["mw"] * C.HOURS_PER_YEAR * P[f"uf_{key}"]
    v_bcm = q_mwh / C.lhv_to_gcv_efficiency(P["ccgt_eta_lhv"]) / C.MWH_PER_BCM_GCV
    u, _ = diversion_share(P, years, v_bcm, P["eg_divert_theta_el"], P["eg_cable_cod"], P["hvdc_life"])
    return u


def o1_eastmed(P, cor, f):
    c = cor["O1_EastMed"]
    x = c["x_contested"]
    w = seg_wacc_real(P, "pipe", c["weights"], x, f)
    delay, over, pc = _risk(P, "pipe", x, 1.0, f)
    u = _outage(P, "pipe", x, f, origin_u=israel_supply_u(P))
    eta = 1.0 - P["em_fuel_pct"]
    q = P["em_capacity_bcm"] * P["em_util0"] * C.MWH_PER_BCM_GCV * eta
    util = F.util_pv_factor(w, P["em_life"], P["gasdem_plateau"], P["gasdem_decline"], P["gasdem_floor"])
    lc = F.levelized_cost(P["em_capex"], q, w, P["em_life"], P["em_build"], fom_per_year=P["em_fom_pct"] * P["em_capex"],
                          overrun=over, delay=delay, util_pv_factor=util, availability=1.0 - u)
    lc = F.cancellation_adjust(lc, pc, P["phi_sunk"])
    p0 = C.usd_per_mmbtu_to_eur_per_mwh(P["p_gas_levant_usd"], P["fx_usd_per_eur"])
    gas = F.buyer_cost(p0 / eta + lc, u, P["p_repl_gas"])
    return ccgt_cost(P, gas, f), gas


def o2_lng_egypt(P, cor, years, f):
    fx = P["fx_usd_per_eur"]
    p0 = C.usd_per_mmbtu_to_eur_per_mwh(P["p_gas_levant_usd"], fx)
    toll = C.usd_per_mmbtu_to_eur_per_mwh(P["lng_toll_usd"], fx)
    ship = C.usd_per_mmbtu_to_eur_per_mwh(P["lng_ship_usd"], fx)
    e_l, e_s, e_r = 1 - P["lng_liq_loss"], 1 - P["lng_ship_loss"], 1 - P["lng_regas_loss"]
    gas = p0 / (e_l * e_s * e_r) + toll / (e_s * e_r) + ship / e_r + P["lng_regas_eur"]
    u = P["u_lng_tech"] if f["exe"] else 0.0
    if f["con"]:
        u_div, _ = o2_unavailability(P, years)
        u = F.combine_unavailability(u, israel_supply_u(P), u_div)
    # L4 adds nothing by construction: carriers sail under freedom of navigation and
    # leave no fixed asset or consent requirement in contested waters.
    gas = F.buyer_cost(gas, u, P["p_repl_gas"])
    return ccgt_cost(P, gas, f), gas


def _cable(P, cor, key, gen_prefix, origin_u, f):
    c = cor[key]
    x, km = c["x_contested"], c["subsea_km"]
    w_tx = seg_wacc_real(P, "hvdc", c["weights"], x, f)
    delay, over, pc = _risk(P, "hvdc", x, P["kappa_cable"], f)
    u = _outage(P, "hvdc", x, f, origin_u=origin_u)
    loss = c["n_conv"] * P["hvdc_conv_loss"] + P["hvdc_cable_loss"] * km / 1000.0
    q = c["mw"] * C.HOURS_PER_YEAR * P[f"uf_{key}"] * (1.0 - loss)
    capex = P[f"capex_{key}"]
    lc_tx = F.levelized_cost(capex, q, w_tx, P["hvdc_life"], P[f"build_{key}"], fom_per_year=P["hvdc_fom_pct"] * capex,
                             overrun=over, delay=delay, availability=1.0 - u)
    lc_tx = F.cancellation_adjust(lc_tx, pc, P["phi_sunk"])
    w_gen = P[f"wacc_re_{c['origin']}"] if f["coc"] else P["wacc_re_GR"]
    # generation output that cannot be exported is assumed sold in the origin market at cost
    cost = gen_lcoe(P, gen_prefix, w_gen) / (1.0 - loss) + lc_tx + P["firming_adder"] + cbam_charge(P, c["origin"])
    return F.buyer_cost(cost, u, P["p_repl_el"])


def cbam_charge(P, origin):
    """CBAM on electricity imported into the EU (EUR/MWh): the share of imports charged at default
    values x the country default value for electricity (Implementing Regulation (EU) 2025/2621,
    Annex III: Egypt 1.148, Israel 0.440 tCO2/MWh) x the allowance price. Base case: dedicated
    renewable PPAs meet the Annex IV point 5 actual-emissions conditions, so the share is 0."""
    return P["cbam_share_default"] * P[f"cbam_ef_{origin}"] * P["p_co2"]


def o5_greek_re(P, f):
    return gen_lcoe(P, "gr", P["wacc_re_GR"]) / (1.0 - P["gr_curtail"]) + P["firming_adder"]


def evaluate(P, corridors, years):
    il_u = F.combine_unavailability(israel_war_u(P), P["origin_curtail_IL"])
    eg_u = {k: egypt_power_u(P, corridors, k, years) for k in ("O4a_GREGY", "O4b_EuroAfrica")}
    res = {o: {} for o in OPTIONS}
    for l, f in enumerate(FLAGS):
        res["O1_EastMed"][l], _ = o1_eastmed(P, corridors, f)
        res["O2_LNG_Egypt"][l], _ = o2_lng_egypt(P, corridors, years, f)
        res["O3_GSI"][l] = _cable(P, corridors, "O3_GSI", "il", il_u, f)
        res["O4a_GREGY"][l] = _cable(P, corridors, "O4a_GREGY", "eg", eg_u["O4a_GREGY"], f)
        res["O4b_EuroAfrica"][l] = _cable(P, corridors, "O4b_EuroAfrica", "eg", eg_u["O4b_EuroAfrica"], f)
        res["O5_Greek_RE"][l] = o5_greek_re(P, f)
    return res