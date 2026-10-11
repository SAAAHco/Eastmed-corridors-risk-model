"""Apply researched parameter values (docs/research/A-E, verified) to config/parameters.csv.

source_id convention: "A:<param_id>" = row in docs/research/A_corridor_parameters.csv,
"C:<param_id>" = docs/research/C_risk_parameters.csv, "IL:" = docs/research/R1_israel.csv,
"EG:" = docs/research/R2_egypt.csv, "CY:" = docs/research/R3_cyprus.csv, "EU:" = docs/research/R4_eu_demand.csv,
"WEB:" = docs/source_register.csv entries. Status "judgement" marks
calibrations that are not directly observed; they are varied in the sensitivity analysis.
Price-year conversion to EUR 2025 uses Eurostat HICP (EA20): 2020 x1.226, 2021 x1.195,
2022 x1.102, 2023 x1.045, 2024 x1.021; USD->EUR at the 2025 ECB average 1.13.
"""
import csv
import os

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PF = os.path.join(H, "config", "parameters.csv")
rows = list(csv.DictReader(open(PF, encoding="utf-8")))
idx = {r["name"]: r for r in rows}
FX, I20, I21, I22, I23, I24 = 1.13, 1.226, 1.195, 1.102, 1.045, 1.021


def setp(name, dist, base, low="", high="", src="", status="sourced", notes="", desc=None, unit=None):
    if name not in idx:
        r = {"name": name, "description": desc or name, "unit": unit or "", "dist": dist, "base": "", "low": "",
             "high": "", "source_id": "", "status": "", "notes": ""}
        rows.append(r)
        idx[name] = r
    r = idx[name]
    r.update({"dist": dist, "base": repr(float(base)), "low": "" if low == "" else repr(float(low)),
              "high": "" if high == "" else repr(float(high)), "source_id": src, "status": status, "notes": notes})
    if desc:
        r["description"] = desc
    if unit:
        r["unit"] = unit


T = "triangular"
# ---------------- corridor capex (EUR 2025) ----------------
setp("em_capex", T, 6.039e9 * I23, 6.039e9 * I23 * 0.85, 6.039e9 * I23 * 1.15, "A:EM_CAPEX_IR2023;A:EM_CAPEX_ACCURACY",
     notes="IGI Poseidon investment request May 2023, FEED +/-15%; EU perimeter (~1,300 km offshore + ~500 km onshore), excl. Poseidon; overrun separate")
setp("em_capacity_bcm", "fixed", 10.0, src="A:EM_CAP_INITIAL;A:EM_CAP_NORTHERN_IR2023", notes="initial design; 12 bcm/y southern-line variant in sensitivity")
setp("em_build", T, 5.0, 4.0, 6.0, "A:EM_TL_03;A:EM_COD_IR2023", status="judgement", notes="EPCI 2020 and 2023 request imply ~4-6 yr FID-to-COD")
setp("em_fuel_pct", T, 0.035, 0.02, 0.05, "A:EM_LEN_TOTAL_2023", status="judgement", notes="compression fuel for ~1,900 km incl. 3,000 m depth")
setp("capex_O3_GSI", T, 3.039e9 * I24, 3.039e9 * I24 * 0.9, 3.039e9 * I24 * 1.25, "A:GSI_CAPEX_CBN24_TOTAL;A:GSI_CAPEX_IL_CY;C:GSI_ACER_COMM_DATE",
     notes="Crete-Cyprus 1,939 MEUR (2024) + Israel-Cyprus 1,100 MEUR (TYNDP 2024); high reflects +23% ACER-reported escalation")
setp("build_O3_GSI", T, 5.5, 4.0, 7.0, "A:GSI_TL_04", status="sourced", notes="Nexans contract Jul 2023: Pole 1 2028, Pole 2 2029")
setp("capex_O4a_GREGY", T, 4.2e9, 3.569e9 * I22, 5.2e9, "A:GREGY_CAPEX_PMI;A:HVDC_GREGY_TYNDP2024_INV",
     notes="3,569 MEUR unrevised c.2022 (x1.102 = low); 2025-26 reporting ~4.0-4.2 bn; ACER UIC parametric ~4.1 bn")
setp("build_O4a_GREGY", T, 6.0, 5.0, 8.0, "A:GREGY_FICHE_SCHED", status="judgement")
setp("capex_O4b_EuroAfrica", T, 3.4e9, 2.5e9 * I21, 4.2e9, "A:EA_CAPEX;A:GSI_CAPEX_CBN24_TOTAL",
     notes="stage 1 (1,000 MW) EUR 2.5bn c.2021 (x1.195 = low); mode/high bounded by GSI 2024 unit costs")
setp("build_O4b_EuroAfrica", T, 6.0, 5.0, 8.0, "A:EA_STATUS", status="judgement")
# ---------------- HVDC technical ----------------
setp("hvdc_conv_loss", T, 0.010, 0.007, 0.015, "A:HVDC_CONV_LOSS_VSC_NGFACT;A:HVDC_CONV_LOSS_MMC_TOSATTO", notes="MMC-VSC ~1% per station")
setp("hvdc_cable_loss", T, 0.017, 0.010, 0.035, "A:HVDC_CABLE_LOSS_CALC_GSI;A:HVDC_LINK_LOSS_MEAS_VIKING_2024;A:HVDC_CABLE_LOSS_NORNED_600MW_JRC",
     notes="per 1,000 km at rated power; calc 1.4-2.1%; measured links imply lower; NorNed-type upper")
setp("hvdc_fom_pct", T, 0.020, 0.012, 0.025, "A:HVDC_OM_CABLE_ONDP2024;A:HVDC_OM_CONV_ONDP2024", notes="TYNDP 2024: cable 2.5%, converter 1.5% of capex")
setp("hvdc_life", "fixed", 40, src="A:HVDC_CABLE_LIFE_DEA;A:HVDC_LIFE_NGFACT")
setp("uf_O3_GSI", T, 0.30, 0.22, 0.45, "PVGIS_SARAH3;IL:IL_DOM_CONS", status="judgement", notes="Israeli solar CF 0.21-0.28 x DC/AC oversizing; storage raises upper bound")
setp("uf_O4a_GREGY", T, 0.60, 0.50, 0.70, "A:GREGY_RES", status="judgement", notes="8.5 GW dedicated Egyptian wind+solar behind 3 GW")
setp("uf_O4b_EuroAfrica", T, 0.60, 0.50, 0.70, "A:GREGY_RES", status="judgement", notes="dedicated Egyptian wind+solar, as GREGY")
# ---------------- CCGT (Greece) ----------------
setp("ccgt_capex", T, 908.2 * I24, 536.19 * I24, 1450, "A:GEN_CCGT_CAPEX_ERAA25_DEFAULT;A:GEN_CCGT_CAPEX_ERAA25_GR;A:GEN_CCGT_CAPEX_DEA_2020;A:GEN_CCGT_CAPEX_US_IRENA25",
     notes="ERAA 2025 default (mode) and Greece (low); high reflects 2025-26 turbine shortage")
setp("ccgt_fom", T, 31.0, 11.92 * I24, 36.22 * I24, "A:GEN_CCGT_FOM_ERAA25_DEFAULT;A:GEN_CCGT_FOM_ERAA25_GR;A:GEN_CCGT_FOM_DEA_2020")
setp("ccgt_vom", T, 2.32 * I24, 2.0, 4.68 * I20, "A:GEN_CCGT_VOM_ERAA25_DEFAULT;A:GEN_CCGT_VOM_DEA_2020")
setp("ccgt_eta_lhv", T, 0.60, 0.58, 0.62, "A:GEN_CCGT_EFF_DEA_2020;A:GEN_CCGT_EFF_DEA_2030;A:GEN_CCGT_EFF_IEANEA20_IT")
setp("ccgt_life", "fixed", 25, src="A:GEN_CCGT_LIFE_ERAA25_DEFAULT;A:GEN_CCGT_LIFE_DEA")
setp("ccgt_build", "fixed", 2.5, src="A:GEN_CCGT_CONSTR_DEA")
setp("ccgt_cf", T, 0.40, 0.30, 0.55, "EMBER_2026_10", notes="Greek gas fleet 2025: 23.3 TWh / ~7.0 GW = ~0.38")# ---------------- generation (EUR 2025; IRENA 2025 USD -> EUR at 1.13) ----------------
setp("solar_life", "fixed", 25, src="A:GEN_PV_LIFE_IRENA25", notes="IRENA LCOE economic life, consistent with IRENA WACC")
setp("wind_life", "fixed", 25, src="A:GEN_WIND_LIFE_IRENA25")
setp("gr_solar_capex", T, 823 / FX, 667 / FX, 850, "A:GEN_PV_CAPEX_EUROPE_IRENA25_SEC;A:GEN_PV_CAPEX_GLOBAL_IRENA25", notes="IRENA Europe 2025 (mode), global (low)")
setp("gr_solar_fom", T, 14.0, 10.03, 20.7 / FX, "A:GEN_PV_FOM_DEA_2025;A:GEN_PV_FOM_OECD_IRENA25")
setp("gr_wind_capex", T, 880 * 1.33, 976 / FX, 1184.6 * I20, "A:GEN_WIND_CAPEX_EUREF20_VHIGH2030;A:GEN_WIND_CAPEX_GLOBAL_IRENA25;A:GEN_WIND_CAPEX_DEA_2025",
     notes="EU REF2020 very-high-resource (2015 EUR x1.33), IRENA global, DEA")
setp("gr_wind_fom", T, 30.0, 17.39 * I20, 45 / FX, "A:GEN_WIND_FOM_DEA_2025;A:GEN_WIND_FOM_OTHEROECD_IRENA25")
setp("gr_wind_cf", T, 0.28, 0.25, 0.32, "EMBER_2026_10", notes="Greek fleet 2023-25 realised 0.25-0.27; new turbines higher")
setp("gr_curtail", T, 0.075, 0.035, 0.15, "WEB:RICARDO_2025_CURTAIL;WEB:PVMAG_2026_CURTAIL", notes="2024 3.4%, 2025 ~7-7.6%, 2026 projected ~12%")
setp("il_solar_capex", T, 667 / FX, 500, 823 / FX, "A:GEN_PV_CAPEX_GLOBAL_IRENA25;A:GEN_PV_CAPEX_EUROPE_IRENA25_SEC", status="judgement",
     notes="no IRENA Israel value; global (mode) to Europe (high)")
setp("il_solar_fom", T, 14.0, 10.0, 20.7 / FX, "A:GEN_PV_FOM_OECD_IRENA25")
setp("eg_solar_capex", T, 667 / FX, 450, 837 / FX, "A:GEN_PV_CAPEX_GLOBAL_IRENA25;A:GEN_PV_CAPEX_AFRICA_IRENA25_SEC", notes="global (mode), Africa (high); Egyptian tariffs USD 20-27/MWh suggest low end")
setp("eg_solar_fom", T, 11 / FX, 8.0, 13.0, "A:GEN_PV_FOM_NONOECD_IRENA25")
setp("eg_solar_cf", T, 0.27, 0.25, 0.30, "A:CF_EG_BENBAN_SCATEC_390MW;A:CF_EG_BENBAN_GCF_LOADFACTOR;PVGIS_SARAH3")
setp("eg_wind_capex", T, 976 / FX, 780, 1100, "A:GEN_WIND_CAPEX_GLOBAL_IRENA25", status="judgement", notes="no IRENA Egypt value")
setp("eg_wind_fom", T, 38 / FX, 25.0, 40.0, "A:GEN_WIND_FOM_OTHERNONOECD_IRENA25")
setp("eg_wind_cf", T, 0.46, 0.39, 0.525, "A:CF_EG_SUEZWIND_ACWA_1100MW;A:CF_EG_WESTBAKR_250MW;A:CF_EG_RSWE_GOS2_500MW;EMBER_2026_10",
     notes="lender-stated 42.7-52.5%; Ember fleet mean 2023-25 ~0.39")
# IRENA 2025 real after-tax WACC (data file of RPGC in 2025, sheet Table A2), weighted by each country's solar/wind mix
# (updated 2026-10-11 from the IRENA 2024 values 0.1355, 0.0499, 0.0491; ranges unchanged)
setp("wacc_re_EG", T, 0.1360, 0.07, 0.155, "IRENA_RPGC2025_DATA;A:PPA_EG_AMUNET_AMEA_505MW;A:PPA_EG_SUEZWIND_ACWA_1100MW", status="judgement",
     notes="mode IRENA 2025 Table A2 (PV 13.38%, onshore 13.68%) weighted 27/73; low = WACC implied by DFI-backed PPAs (USD 28-30/MWh wind); high about +2pp")
setp("wacc_re_GR", T, 0.0585, 0.04, 0.065, "IRENA_RPGC2025_DATA", notes="IRENA 2025 Table A2 (PV 5.77%, onshore 5.97%) weighted 60/40")
setp("wacc_re_IL", T, 0.0410, 0.04, 0.07, "IRENA_RPGC2025_DATA", notes="IRENA 2025 Table A2, solar PV (Israel modeled as all solar)")
setp("wacc_re_CY", T, 0.0863, 0.0763, 0.1013, "IRENA_RPGC2025_DATA")
setp("wacc_re_TR", T, 0.1047, 0.0947, 0.1197, "IRENA_RPGC2025_DATA")
setp("firming_adder", T, 15.0, 5.0, 36.0, "A:GEN_PV_BESS_FIRMLCOE_IRENA25;A:GEN_PV_LCOE_GLOBAL_IRENA25", status="judgement",
     notes="upper = IRENA 2025 gap between firm solar+storage (95%) and plain PV LCOE (USD 41/MWh)")
# ---------------- gas chain ----------------
setp("p_gas_levant_usd", T, 6.2, 5.2, 7.5, "IL:IL_REALISED_PRICE", notes="Leviathan realised USD 5.19-6.55/MMBtu (2024-2Q2026); upper = reported Egypt deal level")
setp("lng_toll_usd", T, 1.4, 1.0, 2.5, "A:LNG_SEGAS_CRONOS_TOLLING;A:LNG_EG_TRANSIT_TARIFF_CRONOS;CY:CY_CRONOS_TOLLING_FEE",
     notes="Damietta tolling ~USD 1.0 + Egyptian transit <0.5; upper allows renegotiation/new train")
setp("lng_liq_loss", T, 0.09, 0.06, 0.14, "WEB:LNG_FUEL_SHARE", notes="liquefaction fuel 6-14% of feed (8-10% typical)")
setp("lng_ship_usd", T, 0.25, 0.10, 0.60, "WEB:LNG_SHIP_CALC", status="judgement", notes="~6-7 day round trip Damietta-Greece; charter USD 20-150k/day; ~3.7m MMBtu cargo")
setp("lng_ship_loss", T, 0.003, 0.002, 0.006, "WEB:LNG_BOR", notes="boil-off 0.10-0.15%/day, ~1.5 days laden plus heel")
setp("lng_regas_eur", T, 0.60, 0.22, 1.50, "WEB:ARGUS_DESFA_2025", status="judgement", notes="Revithoussa 2025 ~EUR 0.30/MWh (50% socialised); full cost and commercial FSRU higher")
setp("u_lng_tech", T, 0.01, 0.005, 0.02, "", status="judgement")
# ---------------- EU demand path for pipeline utilisation ----------------
setp("gasdem_plateau", T, 5, 0, 10, "EU:EU_GASDEM_TYNDP2024;EU:EU_GASDEM_SWD2024", status="judgement",
     notes="EU extra-EU import need 276-287 bcm (2030) -> 129-132 bcm (2040)")
setp("gasdem_decline", T, 0.075, 0.03, 0.10, "EU:EU_GASDEM_TYNDP2024", notes="-54% 2030-2040 implies ~7.5%/yr")
setp("gasdem_floor", T, 0.35, 0.20, 0.50, "EU:EU_GASDEM_SWD2024", status="judgement")
# ---------------- prices ----------------
setp("p_co2", T, 110, 70, 160, "WEB:LSEG_EUA_2025;WEB:CARBONPULSE_POLL", status="judgement", notes="2025 avg ~EUR 74/t; >EUR 90 Jan 2026; levelised 2030-2055")
setp("p_repl_el", T, 105, 90, 180, "WEB:EMAPS_GR_2025", notes="Greek DAM 2025 ~EUR 103/MWh (2024 ~101)")# ---------------- Egypt balance (2025 base) ----------------
setp("eg_il_flow0", "fixed", 8.9, src="IL:IL_EXP_EGYPT", notes="Israeli exports to Egypt 2025 (Ministry of Energy)")
setp("eg_il_flow_max", T, 14.0, 10.0, 17.0, "IL:IL_EXPORT_POLICY;IL:IL_EXPORT_ROUTE_CAP;IL:IL_NITZANA",
     notes="Leviathan 2nd increment 11.9-12.9 bcm/y from 2029 + Tamar ~3; capped by EMG 8.5 + Jordan route + Nitzana 6")
setp("eg_il_ramp_end", T, 2030, 2029, 2032, "IL:IL_LEV_EXPAND;IL:IL_NITZANA", notes="Leviathan expansion FID Jan 2026; Nitzana 2028")
setp("eg_cy_level", T, 6.0, 1.0, 8.3, "CY:CY_APHRODITE_OFFTAKE_DCQ;CY:CY_CRONOS_EGYPT_DOMESTIC_SHARE",
     notes="Aphrodite DCQ 700 MMscf/d (~7.2 bcm/y) to EGAS + ~1/5 of Cronos domestic")
setp("eg_cy_start", T, 2030, 2028, 2032, "CY:CY_CRONOS_FIRST_GAS;CY:CY_APHRODITE_FIRST_GAS")
setp("eg_dem_growth", T, 0.02, 0.0, 0.035, "EI_2026_GAS", notes="2024->2025 +2.8%; 2019-2025 avg +0.7%/yr")
setp("eg_add_level", T, 4.0, 0.0, 10.0, "EG:EG_PROD", status="judgement", notes="new-field additions; Kpler forecasts 37.3 bcm in 2026 (continued decline)")
setp("eg_add_end", T, 2031, 2028, 2034, "", status="judgement")
setp("eg_divert_theta", T, 0.75, 0.4, 1.0, "A:LNG_EG_EXP_2025;A:LNG_EG_IMP_2025;C:EGYPT_LNG_IDKU_HIST", status="judgement",
     notes="2024-25: exports 0.5-0.8 Mt vs imports 9 Mt; exports halted ~17 months")
setp("o2_start_year", "fixed", 2029, src="CY:CY_CRONOS_FIRST_GAS", notes="Cronos LNG via Damietta from 2028")
# ---------------- risk channels ----------------
setp("overrun_hvdc", "shiftlognorm", 0.13, -0.05, 0.80, "C:OVR_TX_MEAN;C:OVR_BOOK_TX;C:HVDC_IFA2_COST", notes="P1: median +8%, mean +12.9%, P95 +43.5%")
setp("overrun_pipe", "shiftlognorm", 0.20, -0.05, 0.90, "C:OVR_BOOK_PIPE;C:OVR_BOOK_OILGAS;C:OVR_OGM_MEAN", notes="P2: median +15%, mean +25%, P95 +83%")
setp("delay_hvdc", "delaymix", 1.5, 0.40, 0.60, "C:HVDC_WL_DELAY;C:HVDC_VIKING_DELAY;C:ACER22_ELEC_DELAY_MONTHS", notes="P4: 40% no material delay; else median 18 months")
setp("delay_pipe", "delaymix", 1.67, 0.40, 0.70, "C:ACER22_GAS_DELAY_MONTHS;C:ACER22_GAS_RESCHED_MONTHS", status="judgement", notes="gas PCIs: mean delay 20 months")
setp("pcancel_hvdc", T, 0.03, 0.0, 0.10, "C:ACER14_STATUS", notes="post-FID abandonment; ACER 2014: 3.8% of components cancelled in ~2 yr")
setp("pcancel_pipe", T, 0.02, 0.0, 0.06, "GEM_GGIT_2025", notes="0 of 65 post-FID gas pipelines in EU/ME/AF cancelled or shelved")
setp("p_contested", T, 0.10, 0.03, 0.20, "C:P6a", status="judgement", notes="P6a: contested/unresolved finance mean 20% vs 10% uncontested")
setp("delta_contested", T, 3.0, 0.5, 8.0, "C:HVDC_ACER_SLIP_SUBSEA;C:P5", notes="subsea PCIs slip mean 4.6 yr vs generic 2.3 yr; GSI +6.1, Hadera-Kofinou +9.1")
setp("pi_contested", T, 0.010, 0.003, 0.025, "C:MIGA_PREMIUM_AVG;C:PRI_LATAM_2021;C:P15", status="judgement",
     notes="PRI ~1%/yr of insured amount; incremental to sovereign CRP (Bekaert et al. 2016 double counting)")
setp("kappa_cable", T, 0.6, 0.3, 1.0, "", status="judgement", notes="UNCLOS 79(3) asymmetry; Israel, Turkiye and Libya non-parties")
setp("phi_sunk", T, 0.25, 0.10, 0.50, "", status="judgement")
setp("u_tech_hvdc", T, 0.06, 0.03, 0.11, "A:HVDC_AVAIL_NORDIC_ALL_2024;A:HVDC_AVAIL_NORNED_2024;C:SYS_AVAIL_NSL",
     desc="technical unavailability of a subsea HVDC link", unit="-", notes="ENTSO-E 2024: Nordic/Baltic links 11%, NorNed 11.2%; NSL model 7.1%")
setp("u_tech_pipe", T, 0.02, 0.005, 0.04, "C:PARLOC_STEEL_GT16;C:P12", status="judgement",
     desc="technical unavailability of an offshore gas pipeline", unit="-", notes="LOC 6e-5/km-yr x 1,300 km x 180 d repair ~ 3.8% upper")
setp("lam_geo", T, 0.05, 0.0, 0.20, "C:P9", status="judgement", desc="annual probability of damaging interference, fully contested route",
     unit="1/yr", notes="Baltic/Red Sea precedents; no East Med physical-damage case (obstruction only)")
setp("mttr_geo", T, 180, 60, 270, "C:ESTLINK2_DEC24;C:BALTICCONNECTOR_2023", notes="Baltic outages 6-7 months")
setp("il_shutdown_rate", T, 0.6, 0.1, 1.3, "C:ISRAEL_HAZARD;C:P13a", status="judgement", notes="3 episodes in 36 months (crisis regime) = upper; long-run lower")
setp("il_shutdown_days", T, 28, 12, 45, "C:TAMAR_OCT2023;C:LEV_KAR_JUN2025;C:LEV_2026;C:KAR_2026")
setp("p_il_halt", "fixed", 0.67, src="C:P13c", desc="share of shutdown episodes that halt exports", unit="-", notes="2 of 3 episodes")
setp("il_export_cut", T, 0.03, 0.0, 0.12, "IL:IL_EXPORT_POLICY", status="judgement", desc="expected policy curtailment of Israeli exports",
     unit="-", notes="Dec 2025 permit: Commissioner may cut up to 60% of maximum daily export from 2036")
setp("origin_curtail_EG", T, 0.03, 0.0, 0.10, "C:EGYPT_LNG_IDKU_HIST", status="judgement")
setp("origin_curtail_IL", T, 0.01, 0.0, 0.03, "", status="judgement")
# remove superseded per-km fault parameters
for old in ("fault_hvdc", "mttr_hvdc", "fault_pipe", "mttr_pipe"):
    if old in idx:
        rows.remove(idx.pop(old))

with open(PF, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "description", "unit", "dist", "base", "low", "high", "source_id", "status", "notes"])
    w.writeheader()
    w.writerows(rows)
st = {}
for r in rows:
    st[r["status"]] = st.get(r["status"], 0) + 1
print("parameters:", len(rows), st)
print("still provisional:", [r["name"] for r in rows if r["status"] == "provisional"])
# ---------------- remaining entries: explicit design choices, judgements, unused ----------------
rows = list(csv.DictReader(open(PF, encoding="utf-8")))
idx = {r["name"]: r for r in rows}
LABEL = {
    "infl_usd": ("triangular", 0.023, 0.020, 0.026, "judgement", "Fed 2% target; 10-yr breakeven ~2.2-2.4% (2025)"),
    "debt_margin_pipe": ("triangular", 0.015, 0.008, 0.025, "judgement", "project-finance spread over sovereign"),
    "debt_margin_hvdc": ("triangular", 0.012, 0.008, 0.020, "judgement", "regulated-asset project finance"),
    "debt_margin_ccgt": ("triangular", 0.015, 0.008, 0.025, "judgement", ""),
    "em_util0": ("triangular", 0.85, 0.70, 0.95, "judgement", "anchored by non-binding market test 10.3 bcm/y (A:EM_MKT_TEST_2023)"),
    "em_life": ("fixed", 30, "", "", "design", "economic life"),
    "em_fom_pct": ("triangular", 0.012, 0.008, 0.020, "judgement", "offshore pipeline O&M share of capex"),
    "lng_regas_loss": ("fixed", 0.01, "", "", "judgement", "regas fuel ~1%"),
    "eg_add_start": ("fixed", 2026, "", "", "judgement", ""),
    "eg_prod_floor": ("fixed", 10, "", "", "judgement", "floor of legacy output"),
    "o2_volume_bcm": ("fixed", 10.0, "", "", "design", "set equal to EastMed capacity for like-for-like comparison"),
    "o2_life": ("fixed", 20, "", "", "design", "contract life"),
    "il_solar_share": ("fixed", 1.0, "", "", "design", "Israeli exports assumed solar (limited wind resource)"),
    "il_wind_share": ("fixed", 0.0, "", "", "design", ""),
    "eg_solar_share": ("fixed", 0.4, "", "", "design", "GREGY/EuroAfrica RES mix not published; wind-rich Gulf of Suez"),
    "eg_wind_share": ("fixed", 0.6, "", "", "design", ""),
    "gr_solar_share": ("fixed", 0.6, "", "", "design", "Greek new-build mix"),
    "gr_wind_share": ("fixed", 0.4, "", "", "design", ""),
    "solar_build": ("fixed", 1, "", "", "judgement", ""),
    "wind_build": ("fixed", 2, "", "", "judgement", ""),
}
for n in ("wacc_re_CY", "wacc_re_TR", "il_wind_cf", "il_wind_capex", "il_wind_fom"):
    if n in idx:
        idx[n]["status"], idx[n]["notes"] = "unused", "not used by the option chains (share 0 or country not a source)"
for n, (d, b, lo, hi, st, nt) in LABEL.items():
    r = idx[n]
    r.update({"dist": d, "base": repr(float(b)), "low": "" if lo == "" else repr(float(lo)),
              "high": "" if hi == "" else repr(float(hi)), "status": st, "notes": nt})
with open(PF, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "description", "unit", "dist", "base", "low", "high", "source_id", "status", "notes"])
    w.writeheader()
    w.writerows(rows)
st = {}
for r in rows:
    st[r["status"]] = st.get(r["status"], 0) + 1
print("final status counts:", st)

# ---------------- revisions after model review (2026-10-08) ----------------
rows = list(csv.DictReader(open(PF, encoding="utf-8")))
idx = {r["name"]: r for r in rows}
# Egyptian export renewables: GREGY's dedicated portfolio is reserved near Sidi Barrani (Matrouh coast),
# not in the Gulf of Suez where the operating wind farms are.
setp("eg_wind_cf", T, 0.38, 0.30, 0.525, "WEB:SHATA_2008_NWCOAST;A:GREGY_RES;A:CF_EG_SUEZWIND_ACWA_1100MW;A:CF_EG_WESTBAKR_250MW;A:CF_EG_RSWE_GOS2_500MW",
     status="judgement", notes="NW coast 450-555 W/m2 at 100 m (Shata et al. 2008) -> 7.3-8.3 m/s -> net CF 0.30-0.45 with a generic "
     "modern power curve (rated 10.5-11.5 m/s, 12% losses; authors' calculation); high = Gulf of Suez lender-stated 0.525")
setp("eg_solar_cf", T, 0.244, 0.210, 0.299, "PVGIS_SARAH3;A:CF_EG_BENBAN_SCATEC_390MW",
     notes="PVGIS Sidi Barrani: fixed-optimal 0.210, single-axis 0.278 (mode = midpoint); high = Benban single-axis 0.299")
setp("eg_wind_share", "fixed", 0.73, src="A:GREGY_RES", status="design",
     notes="GREGY portfolio 5.4 GW wind + 3.1 GW PV (Sep 2026) x mode CFs = 73% of energy from wind; same portfolio assumed for EuroAfrica")
setp("eg_solar_share", "fixed", 0.27, src="A:GREGY_RES", status="design", notes="complement of eg_wind_share")
for k in ("O4a_GREGY", "O4b_EuroAfrica"):
    setp(f"uf_{k}", T, 0.67, 0.55, 0.84, "A:GREGY_RES;A:GREGY_CAP", status="judgement",
         notes="8.5 GW wind+PV behind 3 GW: synthetic hourly profiles give UF 0.64-0.70 with 19-34% of output sold in Egypt "
         "(authors' calculation); high = promoter ~22 TWh/yr with storage; same portfolio design assumed for EuroAfrica")
# Egyptian diversion: one balance, separate propensities for gas and power
setp("eg_divert_theta", T, 0.65, 0.20, 1.0,
     "A:LNG_EG_EXP_2025;A:LNG_EG_IMP_2025;C:EGYPT_LNG_IDKU_HIST;A:LNG_SEGAS_CRONOS_TOLLING;CY:CY_CRONOS_COMMERCIAL_AGREEMENTS;WEB:UFG_ICSID_2018",
     status="judgement", desc="propensity to divert export gas to the domestic market", unit="-",
     notes="mode = 0.38 x 0.25 (Cronos-type tolled, IOC-owned gas in a pipeline bypassing the grid, ~3.8 of 10 bcm) + 0.62 x 0.9 "
     "(gas through the national grid); high = 2012 Damietta feed-gas cut (ICSID ARB/14/4) and 2024-25 export halt; low = full ring-fence")
setp("eg_divert_theta_el", T, 0.20, 0.0, 0.65, "WEB:GG_GREGY;WEB:AGBI_EG_POWER_EXPORTS_2025", status="judgement",
     desc="propensity to divert exported renewable power to the domestic market", unit="-",
     notes="dedicated RES under bespoke PPAs but connected through national interconnection infrastructure; no report of Egypt "
     "curtailing its power exports during 2023-24 load-shedding while gas exports were halted; high = gas mode (symmetric)")
setp("eg_cable_cod", "fixed", 2031, src="A:GREGY_FICHE_SCHED;A:GREGY_STATUS_2026", status="sourced",
     desc="first year of Egyptian power exports (diversion window start)", unit="year",
     notes="GREGY fiche commissioning 06/2031; also used for EuroAfrica (stage 1 slipped to 2029+)")
if "origin_curtail_EG" in idx:
    rows.remove(idx.pop("origin_curtail_EG"))      # replaced by the structural diversion channel
setp("origin_curtail_IL", T, 0.01, 0.0, 0.03, "", status="judgement",
     desc="policy curtailment of Israeli power exports beyond war shutdowns", unit="-",
     notes="war shutdowns are applied to Israeli power exports as to gas (il_shutdown_*); this is the residual policy cut")
setp("ccgt_capex_share", "fixed", 1.0, src="", status="design", desc="share of new-build CCGT capex charged to gas options", unit="-",
     notes="1 = new plant (like-for-like with cables, which include new generation); 0 = existing Greek fleet (sensitivity)")
setp("eg_prod0", "fixed", 40.8, src="EI_2026_GAS", desc="Egypt gas production in the base year", unit="bcm", notes="2025 (EI 2026)")
setp("eg_dem0", "fixed", 61.5, src="EI_2026_GAS", desc="Egypt gas consumption in the base year", unit="bcm", notes="2025 (EI 2026)")
setp("eg_il_flow0", "fixed", 8.9, src="IL:IL_EXP_EGYPT", desc="Israeli pipeline supply to Egypt in the base year", unit="bcm",
     notes="Israeli exports to Egypt 2025 (Ministry of Energy)")
# CBAM on electricity imports (Regulation (EU) 2023/956; default values in IR (EU) 2025/2621, Annex III)
setp("cbam_share_default", "fixed", 0.0, src="WEB:CBAM_REG_2023_956;WEB:CBAM_REVIEW_2025", status="design",
     desc="share of cable imports charged CBAM at default values", unit="-",
     notes="0 = dedicated renewable PPAs meet the Annex IV point 5 actual-emissions conditions (PPA with the producer, direct connection or no congestion, firm nomination of interconnection capacity, and the further conditions of point 5); scenarios 0.5 and 1")
setp("cbam_ef_EG", "fixed", 0.442, src="WEB:CBAM_IR_2025_2621", status="sourced",
     desc="CBAM default emission factor for electricity imported from Egypt", unit="tCO2/MWh",
     notes="Implementing Regulation (EU) 2025/2621, Annex III (IEA-based CO2 factor of fossil generation; recital 8); value re-read on 9 Oct 2026 from the official OJ PDF and the consolidated text (02025R2621-20260101) with word-coordinate pairing: the 8 Oct reading (1.148) had paired each value with the next row (1.148 is Bosnia and Herzegovina); grid-average alternative 0.387 (Annex II) used in the grid-average scenario; Ember 2025: fossil-only 0.644, grid 0.557 tCO2e/MWh")
setp("cbam_ef_IL", "fixed", 0.480, src="WEB:CBAM_IR_2025_2621", status="sourced",
     desc="CBAM default emission factor for electricity imported from Israel", unit="tCO2/MWh",
     notes="Implementing Regulation (EU) 2025/2621, Annex III; re-read 9 Oct 2026 with word-coordinate pairing (the 8 Oct reading, 0.440, is the Georgia row); grid-average alternative 0.443 (Annex II; the earlier 0.469 is the Japan row); Ember 2025: fossil-only 0.583, grid 0.493 tCO2e/MWh")
for old in ("cbam_ef_default",):   # superseded by the country values above
    if old in idx:
        rows.remove(idx.pop(old))
with open(PF, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "description", "unit", "dist", "base", "low", "high", "source_id", "status", "notes"])
    w.writeheader()
    w.writerows(rows)
st = {}
for r in rows:
    st[r["status"]] = st.get(r["status"], 0) + 1
print("after model review:", len(rows), st)
