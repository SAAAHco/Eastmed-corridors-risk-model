"""Single source of physical constants and unit conversions.

Every module imports conversions from here; no other file may hard-code
an energy content, emission factor or currency factor.

Conventions
-----------
* Gas energy is on a gross calorific value (GCV/HHV) basis, matching how
  TTF prices and EU gas tariffs are quoted (EUR/MWh, GCV).
* Electricity is MWh_e.
* Money is real EUR at 2025 prices unless a function says otherwise.
"""

HOURS_PER_YEAR = 8760.0

# --- energy units -----------------------------------------------------------
MWH_PER_MMBTU = 0.29307107           # 1 MMBtu = 1.055056 GJ
MMBTU_PER_MWH = 1.0 / MWH_PER_MMBTU   # 3.412142
GJ_PER_MWH = 3.6

# Natural gas, GCV basis. Energy Institute, Statistical Review of World Energy
# 2026, Definitions (p.83) and conversion table (p.84): gas volumes are measured
# at 15 C and 1013 mbar and standardised at a gross calorific value of 40 MJ/m3;
# 1 bcm = 36 PJ net (= 40 PJ gross x 0.9); 1 Mt LNG = 1.360 bcm.  [source: EI_2026_CONV]
GJ_PER_BCM_GCV = 40.0e6
MWH_PER_BCM_GCV = GJ_PER_BCM_GCV / GJ_PER_MWH                     # 11.11 TWh per bcm
MMBTU_PER_BCM_GCV = GJ_PER_BCM_GCV / (MWH_PER_MMBTU * GJ_PER_MWH)  # 37.91 million MMBtu
BCM_PER_MT_LNG = 1.36
MWH_PER_T_LNG_GCV = BCM_PER_MT_LNG * MWH_PER_BCM_GCV / 1e6        # 15.11 MWh per t
MMBTU_PER_T_LNG_GCV = BCM_PER_MT_LNG * MMBTU_PER_BCM_GCV / 1e6    # 51.56 MMBtu per t

# Net/gross calorific value ratio for natural gas (EI 2026: 36 PJ net vs 40 PJ gross per bcm).
NCV_PER_GCV_GAS = 0.90

# --- emission factors -------------------------------------------------------
# IPCC 2006 Guidelines, Vol. 2, Ch. 1, Table 1.4 defaults (tCO2/TJ, NCV basis).
EF_GAS_T_PER_TJ_NCV = 56.1
EF_LIGNITE_T_PER_TJ_NCV = 101.0
EF_COAL_BIT_T_PER_TJ_NCV = 94.6

# Natural gas per MWh of fuel, GCV basis: 56.1 t/TJ * 3.6 GJ/MWh * NCV/GCV.
EF_GAS_T_PER_MWH_GCV = EF_GAS_T_PER_TJ_NCV * GJ_PER_MWH / 1000.0 * NCV_PER_GCV_GAS  # ~0.1818


def lhv_to_gcv_efficiency(eta_lhv: float) -> float:
    """Convert a power-plant efficiency quoted on an LHV basis to a GCV basis."""
    return eta_lhv * NCV_PER_GCV_GAS


def usd_per_mmbtu_to_eur_per_mwh(price_usd_mmbtu, usd_per_eur):
    """$/MMBtu -> EUR/MWh on the same calorific basis."""
    return price_usd_mmbtu * MMBTU_PER_MWH / usd_per_eur


def eur_per_mwh_to_usd_per_mmbtu(price_eur_mwh, usd_per_eur):
    """EUR/MWh -> $/MMBtu on the same calorific basis."""
    return price_eur_mwh * usd_per_eur / MMBTU_PER_MWH
