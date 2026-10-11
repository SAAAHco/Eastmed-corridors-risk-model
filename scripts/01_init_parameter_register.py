"""Create config/parameters.csv with PROVISIONAL values for smoke-testing.

Every row with status=provisional must be replaced by a sourced value
(source_id pointing to docs/source_register.csv) before results are used.
dist: fixed | uniform(low, high) | triangular(low, mode=base, high)
"""
import csv
import os

H = ["name", "description", "unit", "dist", "base", "low", "high", "source_id", "status", "notes"]
R = []


def p(name, desc, unit, dist, base, low=None, high=None, src="", status="provisional", notes=""):
    R.append([name, desc, unit, dist, base, "" if low is None else low, "" if high is None else high,
              src, status, notes])


T = "triangular"
# macro and prices
p("fx_usd_per_eur", "USD per EUR, 2025 average", "USD/EUR", "fixed", 1.13)
p("infl_usd", "long-run expected US inflation (nominal to real)", "1/yr", "fixed", 0.023)
p("rf_usd", "risk-free rate, US 10y Treasury", "1/yr", T, 0.043, 0.040, 0.047)
p("erp_mature", "mature-market equity risk premium (Damodaran implied)", "1/yr", T, 0.043, 0.040, 0.050)
p("p_co2", "EU ETS allowance price, levelised 2030-2055", "EUR/t", T, 100, 70, 150)
p("p_repl_gas", "replacement gas price when supply is interrupted", "EUR/MWh_GCV", T, 45, 30, 70)
p("p_repl_el", "replacement electricity price when a cable is out", "EUR/MWh_e", T, 130, 90, 250)
p("firming_adder", "firming/integration cost for variable renewables", "EUR/MWh_e", T, 15, 5, 30)
p("p_gas_levant_usd", "Levant gas price at origin/Egyptian border", "USD/MMBtu", T, 7.0, 6.0, 8.5)
# country risk (Damodaran; triangular over 2022/2024/2026 vintages, mode = 2026)
for cc, lo, mode, hi in [("IL", 0.0122, 0.0207, 0.0213), ("CY", 0.0155, 0.0155, 0.0432),
                         ("GR", 0.0285, 0.0285, 0.0621), ("EG", 0.0949, 0.0971, 0.1001),
                         ("TR", 0.0466, 0.0466, 0.1122), ("IT", 0.0200, 0.0293, 0.0379)]:
    p(f"crp_{cc}", f"country risk premium {cc}", "1/yr", T, mode, lo, hi, "DAMODARAN_CRP",
      notes="mode=2026 from Group 6 sheet; replace with Damodaran 2026 file")
for cc, v in [("IL", 0.0158), ("CY", 0.0119), ("GR", 0.0248), ("EG", 0.0743), ("TR", 0.0446), ("IT", 0.0218)]:
    p(f"ds_{cc}", f"sovereign default spread {cc}", "1/yr", "fixed", v, src="DAMODARAN_CRP", notes="2024 vintage placeholder")
for cc, v in [("IL", 0.23), ("CY", 0.15), ("GR", 0.22), ("EG", 0.225), ("TR", 0.25), ("IT", 0.24)]:
    p(f"tax_{cc}", f"corporate income tax rate {cc}", "-", "fixed", v)
# capital structure by asset class
for a, b, de, m in [("pipe", 0.60, 1.0, 0.015), ("hvdc", 0.40, 1.5, 0.012), ("ccgt", 0.50, 1.0, 0.015)]:
    p(f"beta_u_{a}", f"unlevered beta, {a}", "-", "fixed", b, notes="Damodaran industry betas")
    p(f"de_{a}", f"debt/equity, {a}", "-", "fixed", de)
    p(f"debt_margin_{a}", f"project debt margin over sovereign, {a}", "1/yr", "fixed", m)
# renewable WACC by country: IRENA RPGC 2024 real after-tax (solar PV column)
for cc, v in [("GR", 0.0499), ("IL", 0.0491), ("EG", 0.1355), ("CY", 0.0569), ("TR", 0.105)]:
    p(f"wacc_re_{cc}", f"real after-tax WACC for renewables, {cc}", "1/yr", T, v, v - 0.01, v + 0.015,
      "IRENA_RPGC2024", "provisional", "IRENA Fig A1 via Group 6; verify")
# O1 EastMed
p("em_capex", "EastMed pipeline capex (incl. Cyprus/Crete legs)", "EUR2025", T, 8.0e9, 6.5e9, 11.0e9)
p("em_capacity_bcm", "EastMed design capacity", "bcm/yr", "fixed", 10.0)
p("em_util0", "initial utilisation", "-", T, 0.85, 0.70, 0.95)
p("em_fuel_pct", "compression fuel use, share of throughput", "-", T, 0.03, 0.02, 0.05)
p("em_build", "planned construction period", "yr", T, 4, 3, 5)
p("em_life", "economic life", "yr", "fixed", 30)
p("em_fom_pct", "fixed O&M, share of capex per year", "1/yr", T, 0.012, 0.008, 0.02)
p("gasdem_plateau", "years at full utilisation before EU demand decline bites", "yr", T, 8, 3, 15)
p("gasdem_decline", "utilisation decline rate after plateau", "1/yr", T, 0.07, 0.03, 0.12)
p("gasdem_floor", "utilisation floor", "-", T, 0.3, 0.1, 0.5)
# O2 LNG via Egypt
p("lng_toll_usd", "liquefaction tolling fee (brownfield Idku/Damietta)", "USD/MMBtu", T, 2.5, 2.0, 3.5)
p("lng_liq_loss", "liquefaction fuel and losses, share of feed", "-", T, 0.10, 0.08, 0.12)
p("lng_ship_usd", "LNG shipping Egypt-Greece", "USD/MMBtu", T, 0.5, 0.3, 0.9)
p("lng_ship_loss", "boil-off on voyage", "-", T, 0.004, 0.002, 0.006)
p("lng_regas_eur", "Greek regasification tariff", "EUR/MWh", T, 1.8, 1.0, 3.0)
p("lng_regas_loss", "regasification fuel", "-", "fixed", 0.01)
p("u_lng_tech", "technical unavailability of the LNG chain", "-", T, 0.01, 0.005, 0.02)
# Egypt gas balance
p("eg_prod0", "Egypt gas production 2024", "bcm", "fixed", 49.4, src="OIES_2025", notes="Group 6 Parameters sheet citing OIES")
p("eg_prod_decline", "decline of legacy production", "1/yr", T, -0.07, -0.11, -0.03)
p("eg_add_level", "new-field production at plateau", "bcm/yr", T, 6, 2, 12)
p("eg_add_start", "new-field ramp start", "year", "fixed", 2026)
p("eg_add_end", "new-field ramp end", "year", T, 2030, 2028, 2033)
p("eg_prod_floor", "floor of legacy production", "bcm/yr", "fixed", 10)
p("eg_dem0", "Egypt gas demand 2024", "bcm", "fixed", 62.0, src="OIES_2025")
p("eg_dem_growth", "Egypt demand growth", "1/yr", T, 0.015, 0.0, 0.03)
p("eg_il_flow0", "Israeli pipeline supply to Egypt 2024", "bcm", "fixed", 10.1, src="OIES_2025")
p("eg_il_flow_max", "Israeli supply to Egypt at plateau (domestic contracts)", "bcm/yr", T, 13, 10, 18)
p("eg_il_ramp_end", "year Israeli supply reaches plateau", "year", T, 2029, 2027, 2032)
p("eg_cy_level", "Cypriot gas to Egypt at plateau", "bcm/yr", T, 3, 0, 6)
p("eg_cy_start", "first Cypriot gas to Egypt", "year", T, 2029, 2027, 2033)
p("o2_volume_bcm", "Levant volume contracted for re-export via Egypt", "bcm/yr", "fixed", 10.0)
p("eg_divert_theta", "propensity to divert export gas to the domestic market", "-", T, 0.7, 0.3, 1.0)
p("o2_start_year", "first year of O2 exports", "year", "fixed", 2029)
p("o2_life", "O2 contract life", "yr", "fixed", 20)
# CCGT in Greece
p("ccgt_capex", "CCGT overnight capex", "EUR/kW", T, 950, 800, 1200)
p("ccgt_fom", "CCGT fixed O&M", "EUR/kW-yr", T, 20, 15, 28)
p("ccgt_vom", "CCGT variable O&M", "EUR/MWh", T, 3, 2, 4)
p("ccgt_eta_lhv", "CCGT efficiency, LHV", "-", T, 0.58, 0.55, 0.61)
p("ccgt_cf", "CCGT capacity factor", "-", T, 0.45, 0.30, 0.60)
p("ccgt_life", "CCGT life", "yr", "fixed", 25)
p("ccgt_build", "CCGT build period", "yr", "fixed", 3)
# HVDC common
p("hvdc_conv_loss", "loss per converter station", "-", T, 0.010, 0.007, 0.015)
p("hvdc_cable_loss", "HVDC cable loss per 1000 km", "-", T, 0.03, 0.02, 0.04)
p("hvdc_life", "HVDC asset life", "yr", "fixed", 40)
p("hvdc_fom_pct", "HVDC fixed O&M, share of capex per year", "1/yr", T, 0.010, 0.005, 0.015)
# cables
p("capex_O3_GSI", "GSI capex Israel-Cyprus-Crete", "EUR2025", T, 2.4e9, 1.9e9, 3.2e9)
p("build_O3_GSI", "GSI planned build period", "yr", T, 5, 4, 7)
p("uf_O3_GSI", "GSI utilisation for Israeli solar exports", "-", T, 0.35, 0.25, 0.50)
p("capex_O4a_GREGY", "GREGY capex", "EUR2025", T, 4.5e9, 3.5e9, 6.0e9)
p("build_O4a_GREGY", "GREGY build period", "yr", T, 6, 5, 8)
p("uf_O4a_GREGY", "GREGY utilisation (Egyptian wind-solar hybrid)", "-", T, 0.55, 0.45, 0.65)
p("capex_O4b_EuroAfrica", "EuroAfrica capex", "EUR2025", T, 3.2e9, 2.5e9, 4.5e9)
p("build_O4b_EuroAfrica", "EuroAfrica build period", "yr", T, 6, 5, 8)
p("uf_O4b_EuroAfrica", "EuroAfrica utilisation", "-", T, 0.55, 0.45, 0.65)
# generation: (prefix, solar share, wind share, solar cf, solar capex, solar fom, wind cf, wind capex, wind fom)
for pre, sh_s, sh_w, s_cf, s_cx, s_fom, w_cf, w_cx, w_fom in [
        ("il", 1.0, 0.0, (0.20, 0.22, 0.25), (600, 750, 950), (10, 13, 17), (0.20, 0.25, 0.30), (1200, 1400, 1700), (28, 35, 45)),
        ("eg", 0.4, 0.6, (0.24, 0.26, 0.29), (450, 550, 700), (8, 10, 13), (0.40, 0.45, 0.50), (1000, 1200, 1450), (25, 32, 40)),
        ("gr", 0.6, 0.4, (0.17, 0.19, 0.21), (500, 620, 800), (10, 12, 14), (0.25, 0.29, 0.33), (1100, 1300, 1550), (25, 32, 40))]:
    p(f"{pre}_solar_share", f"{pre} solar share of energy", "-", "fixed", sh_s)
    p(f"{pre}_wind_share", f"{pre} wind share of energy", "-", "fixed", sh_w)
    p(f"{pre}_solar_cf", f"{pre} solar capacity factor", "-", T, s_cf[1], s_cf[0], s_cf[2])
    p(f"{pre}_solar_capex", f"{pre} solar capex", "EUR/kW", T, s_cx[1], s_cx[0], s_cx[2])
    p(f"{pre}_solar_fom", f"{pre} solar fixed O&M", "EUR/kW-yr", T, s_fom[1], s_fom[0], s_fom[2])
    p(f"{pre}_wind_cf", f"{pre} wind capacity factor", "-", T, w_cf[1], w_cf[0], w_cf[2])
    p(f"{pre}_wind_capex", f"{pre} wind capex", "EUR/kW", T, w_cx[1], w_cx[0], w_cx[2])
    p(f"{pre}_wind_fom", f"{pre} wind fixed O&M", "EUR/kW-yr", T, w_fom[1], w_fom[0], w_fom[2])
p("solar_life", "solar PV life", "yr", "fixed", 30)
p("wind_life", "onshore wind life", "yr", "fixed", 27)
p("solar_build", "solar build period", "yr", "fixed", 1)
p("wind_build", "wind build period", "yr", "fixed", 2)
p("gr_curtail", "curtailment share for Greek renewables", "-", T, 0.08, 0.03, 0.15)
# risk channels
p("delay_pipe", "reference-class delay, offshore pipelines", "yr", T, 1.5, 0.0, 4.0)
p("delay_hvdc", "reference-class delay, subsea HVDC", "yr", T, 1.5, 0.0, 4.0)
p("overrun_pipe", "reference-class cost overrun, offshore pipelines", "-", T, 0.10, -0.05, 0.50)
p("overrun_hvdc", "reference-class cost overrun, subsea HVDC", "-", T, 0.08, -0.05, 0.40)
p("pcancel_pipe", "post-FID abandonment probability, pipelines", "-", T, 0.05, 0.02, 0.12)
p("pcancel_hvdc", "post-FID abandonment probability, HVDC", "-", T, 0.05, 0.02, 0.12)
p("phi_sunk", "share of PV cost sunk at abandonment", "-", T, 0.25, 0.10, 0.50)
p("pi_contested", "WACC premium at full contested exposure", "1/yr", T, 0.015, 0.005, 0.030)
p("delta_contested", "extra delay at full contested exposure", "yr", T, 2.0, 0.5, 5.0)
p("p_contested", "extra abandonment probability at full exposure", "-", T, 0.20, 0.05, 0.40)
p("kappa_cable", "legal-regime factor for cables vs pipelines (UNCLOS 79(3))", "-", T, 0.6, 0.3, 1.0)
p("fault_hvdc", "technical faults per 1000 km-yr, subsea HVDC", "1/yr", T, 0.10, 0.05, 0.30)
p("mttr_hvdc", "mean time to repair, subsea HVDC", "days", T, 60, 30, 120)
p("fault_pipe", "technical incidents per 1000 km-yr, offshore pipeline", "1/yr", T, 0.03, 0.01, 0.08)
p("mttr_pipe", "mean time to repair, offshore pipeline", "days", T, 45, 20, 120)
p("lam_geo", "interference/sabotage events per 1000 contested km-yr", "1/yr", T, 0.05, 0.01, 0.15)
p("mttr_geo", "outage per interference event", "days", T, 60, 15, 180)
p("il_shutdown_rate", "conflict shutdowns of Israeli offshore fields per year", "1/yr", T, 0.7, 0.2, 1.2)
p("il_shutdown_days", "duration of an Israeli field shutdown", "days", T, 21, 7, 45)
p("origin_curtail_IL", "conflict-related curtailment of Israeli power exports", "-", T, 0.01, 0.0, 0.03)
p("origin_curtail_EG", "shortage-driven curtailment of Egyptian power exports", "-", T, 0.03, 0.0, 0.10)

out = os.path.join(os.path.dirname(__file__), "..", "config", "parameters.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(H)
    w.writerows(R)
print(f"wrote {len(R)} parameters -> config/parameters.csv")