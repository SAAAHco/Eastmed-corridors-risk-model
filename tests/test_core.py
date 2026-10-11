import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from emcorr import constants as C          # noqa: E402
from emcorr import finance as F            # noqa: E402
from emcorr import geo as G                # noqa: E402


class TestConstants(unittest.TestCase):
    def test_gas_energy_content(self):
        self.assertAlmostEqual(C.MWH_PER_BCM_GCV / 1e6, 11.111, places=3)  # TWh per bcm (40 PJ GCV)
        self.assertAlmostEqual(C.MWH_PER_T_LNG_GCV, 15.11, places=2)
        # EI 2026 table: 1 bcm = 36 PJ net -> 34.121 trillion Btu net
        self.assertAlmostEqual(C.MMBTU_PER_BCM_GCV * C.NCV_PER_GCV_GAS / 1e6, 34.121, places=2)

    def test_lng_bcm_consistency(self):
        # 1 Mt LNG = 1.36 bcm must agree with the energy contents within 0.5%
        ratio = C.MMBTU_PER_T_LNG_GCV * 1e6 / C.MMBTU_PER_BCM_GCV
        self.assertAlmostEqual(ratio, C.BCM_PER_MT_LNG, delta=0.01)

    def test_emission_factor(self):
        self.assertAlmostEqual(C.EF_GAS_T_PER_MWH_GCV, 0.1818, places=3)
        # 36 PJ net per bcm x 56.1 t/TJ = 2.02 MtCO2 per bcm burned
        self.assertAlmostEqual(C.EF_GAS_T_PER_MWH_GCV * C.MWH_PER_BCM_GCV / 1e6, 2.0196, places=3)

    def test_price_roundtrip(self):
        eur = C.usd_per_mmbtu_to_eur_per_mwh(7.5, 1.13)
        self.assertAlmostEqual(eur, 22.65, places=1)
        self.assertAlmostEqual(C.eur_per_mwh_to_usd_per_mmbtu(eur, 1.13), 7.5, places=9)


class TestFinance(unittest.TestCase):
    def test_crf_values_quoted_to_coauthor(self):
        # 25-year capital recovery charge at IRENA country WACCs
        self.assertAlmostEqual(float(F.crf(0.05, 25)), 0.0710, places=4)
        self.assertAlmostEqual(float(F.crf(0.135, 25)), 0.1409, places=3)
        self.assertAlmostEqual(float(F.crf(0.235, 25)), 0.2362, places=3)

    def test_crf_zero_rate(self):
        self.assertAlmostEqual(float(F.crf(0.0, 20)), 0.05)

    def test_idc_factor(self):
        self.assertAlmostEqual(float(F.idc_factor(0.08, 0.0)), 1.0)
        # uniform spend over 4 years at 8%: ~ (1.08^4-1)/(4 ln1.08) = 1.1714
        self.assertAlmostEqual(float(F.idc_factor(0.08, 4.0)), (1.08 ** 4 - 1) / (4 * np.log(1.08)), places=9)

    def test_levelized_cost_simple(self):
        # instant build, constant output: LC = capex/(Q*annuity) + FOM/Q
        lc = F.levelized_cost(capex=1000.0, annual_output=10.0, wacc=0.07, life=30,
                              build_years=0.0, fom_per_year=5.0)
        expect = 1000.0 / (10.0 * float(F.annuity_cont(0.07, 30))) + 0.5
        self.assertAlmostEqual(float(lc), expect, places=9)
        # continuous annuity is close to the discrete CRF
        self.assertAlmostEqual(1 / float(F.annuity_cont(0.07, 30)), float(F.crf(0.07, 30)), delta=0.003)

    def test_delay_overrun_raise_cost(self):
        base = F.levelized_cost(1000, 10, 0.08, 30, 4)
        late = F.levelized_cost(1000, 10, 0.08, 30, 4, delay=3)
        over = F.levelized_cost(1000, 10, 0.08, 30, 4, overrun=0.3)
        self.assertGreater(float(late), float(base))
        self.assertAlmostEqual(float(over), 1.3 * float(base), places=9)

    def test_vectorised(self):
        r = np.array([0.05, 0.10])
        lc = F.levelized_cost(1000, 10, r, 30, 3)
        self.assertEqual(lc.shape, (2,))
        self.assertLess(lc[0], lc[1])

    def test_util_pv_factor(self):
        self.assertAlmostEqual(F.util_pv_factor(0.07, 30, plateau_years=40, decline_rate=0.1, floor=0.0), 1.0, places=9)
        f = F.util_pv_factor(0.07, 30, plateau_years=5, decline_rate=0.1, floor=0.2)
        self.assertTrue(0.2 < f < 1.0)
        arr = F.util_pv_factor(np.array([0.05, 0.10]), 30, 5, 0.1, 0.2)
        self.assertEqual(arr.shape, (2,))

    def test_wacc_build_up(self):
        # all-equity, beta 1, no country risk -> rf + ERP
        w = F.wacc_nominal(rf=0.04, erp=0.05, crp=0.0, default_spread=0.0,
                           beta_unlevered=1.0, debt_to_equity=0.0, tax_rate=0.25)
        self.assertAlmostEqual(w, 0.09)
        # country risk raises WACC
        w2 = F.wacc_nominal(0.04, 0.05, 0.03, 0.02, 0.6, 1.5, 0.22)
        w1 = F.wacc_nominal(0.04, 0.05, 0.0, 0.0, 0.6, 1.5, 0.22)
        self.assertGreater(w2, w1)
        self.assertAlmostEqual(F.real_rate(0.0712, 0.02), 1.0712 / 1.02 - 1)

    def test_cancellation_and_buyer_cost(self):
        self.assertAlmostEqual(float(F.cancellation_adjust(100.0, 0.0, 0.5)), 100.0)
        self.assertAlmostEqual(float(F.cancellation_adjust(100.0, 0.5, 0.2)), 120.0)
        u = float(F.combine_unavailability(0.1, 0.1))
        self.assertAlmostEqual(u, 0.19)
        self.assertAlmostEqual(float(F.buyer_cost(80.0, 0.1, 200.0)), 92.0)

    def test_weighted(self):
        self.assertAlmostEqual(F.weighted({"GR": 0.03, "EG": 0.09}, {"GR": 3, "EG": 1}), 0.045)
        with self.assertRaises(KeyError):
            F.weighted({"GR": 0.03}, {"GR": 1, "TR": 1})


class TestGeo(unittest.TestCase):
    def test_length_along_equator(self):
        r = G.densify_route([(0.0, 0.0), (1.0, 0.0)], step_km=5)
        self.assertAlmostEqual(G.length_km(r), 111.32, delta=0.05)

    def test_km_inside_box(self):
        r = G.densify_route([(0.0, 0.0), (2.0, 0.0)], step_km=1)
        box = G.polygon_from_coords([(0.5, -1), (1.5, -1), (1.5, 1), (0.5, 1)])
        self.assertAlmostEqual(G.km_inside(r, box), 111.32, delta=0.5)
        exp = G.route_exposure(r, {"box": box})
        self.assertAlmostEqual(exp["any_contested_share"], 0.5, delta=0.01)

    def test_overlap(self):
        a = G.polygon_from_coords([(0, 0), (2, 0), (2, 2), (0, 2)])
        b = G.polygon_from_coords([(1, 1), (3, 1), (3, 3), (1, 3)])
        self.assertAlmostEqual(G.overlap(a, b).area, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)


class TestOptionSanity(unittest.TestCase):
    """Hand-calculated checks of generation and CCGT cost (catches unit slips)."""

    def setUp(self):
        from emcorr import options as O
        self.O = O

    def test_solar_lcoe_by_hand(self):
        P = {"x_solar_share": 1.0, "x_wind_share": 0.0, "x_solar_cf": 0.19, "x_solar_capex": 620.0,
             "x_solar_fom": 12.0, "x_wind_cf": 0.3, "x_wind_capex": 1300.0, "x_wind_fom": 30.0,
             "solar_life": 30, "wind_life": 27, "solar_build": 0.0, "wind_build": 0.0}
        lc = float(self.O.gen_lcoe(P, "x", 0.05))
        q = 8760 * 0.19
        expect = (620e3 / float(F.annuity_cont(0.05, 30)) + 12e3) / q
        self.assertAlmostEqual(lc, expect, places=6)
        self.assertTrue(25 < lc < 40)          # plausible Greek utility PV LCOE, EUR/MWh

    def test_ccgt_cost_components(self):
        P = {"ccgt_eta_lhv": 0.58, "ccgt_capex": 950.0, "ccgt_cf": 0.45, "ccgt_life": 25, "ccgt_build": 3,
             "ccgt_fom": 20.0, "ccgt_vom": 3.0, "p_co2": 100.0, "rf_usd": 0.043, "erp_mature": 0.043,
             "crp_GR": 0.0285, "ds_GR": 0.0248, "tax_GR": 0.22, "beta_u_ccgt": 0.5, "de_ccgt": 1.0,
             "debt_margin_ccgt": 0.015, "infl_usd": 0.023, "ccgt_capex_share": 1.0}
        total = float(self.O.ccgt_cost(P, 30.0, self.O.FLAGS[0]))
        eta = 0.58 * 0.9
        fuel, carbon = 30.0 / eta, 0.1818 * 100 / eta
        nonfuel = total - fuel - carbon
        self.assertTrue(15 < nonfuel < 40, nonfuel)   # capex+O&M of a mid-merit CCGT, EUR/MWh


class TestRegister(unittest.TestCase):
    """The full register must load, evaluate to finite positive costs at every layer,
    and respect the structural properties of the decomposition."""

    @classmethod
    def setUpClass(cls):
        from emcorr import mc, options as O
        here = os.path.join(os.path.dirname(__file__), "..")
        df = mc.load_params(os.path.join(here, "config", "parameters.csv"))   # raises if malformed
        cor = mc.load_corridors(os.path.join(here, "config", "corridors.yaml"))
        P, _ = mc.sample_lhs(df, 500, seed=1)
        cls.O = O
        cls.res = O.evaluate(P, cor, np.arange(2025, 2061))
        cls.layers = range(len(O.LAYERS))

    def v(self, o, l):
        return np.broadcast_to(np.asarray(self.res[o][l], dtype=float), (500,))

    def test_finite_positive(self):
        for o in self.O.OPTIONS:
            for l in self.layers:
                v = self.v(o, l)
                self.assertTrue(np.isfinite(v).all(), f"{o} L{l} has non-finite values")
                self.assertTrue((v > 0).all(), f"{o} L{l} has non-positive cost")

    def test_layer_structure(self):
        top = len(self.O.LAYERS) - 1
        # domestic renewables carry no cross-border risk layers
        for l in self.layers:
            np.testing.assert_allclose(self.v("O5_Greek_RE", l), self.v("O5_Greek_RE", 0))
        # LNG carriers leave no fixed asset in contested waters
        np.testing.assert_allclose(self.v("O2_LNG_Egypt", top), self.v("O2_LNG_Egypt", top - 1))
        # maritime disputes add cost on average for every fixed-asset corridor
        for o in ("O1_EastMed", "O3_GSI", "O4a_GREGY", "O4b_EuroAfrica"):
            self.assertGreater((self.v(o, top) - self.v(o, top - 1)).mean(), 0.0, o)
        # the pipeline's maritime increment is non-negative draw by draw
        self.assertTrue((self.v("O1_EastMed", top) >= self.v("O1_EastMed", top - 1) - 1e-9).all())
