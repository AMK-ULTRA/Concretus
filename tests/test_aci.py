import unittest
from math import exp

from core.regular_concrete.design_methods.aci import (CementitiousMaterial, Water, Air, FineAggregate,
                                                                CoarseAggregate, StandardDeviation, AbramsLaw)
from core.regular_concrete.models.aci_data_model import ACIDataModel


class TestCementitiousMaterial(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.cementitious = CementitiousMaterial(relative_density=3.15)
        self.cementitious.aci_data_model = self.aci_data_model

    def test_cementitious_content_without_scm(self):
        water_content = 175
        w_cm = 0.5
        scm_checked = False
        test_cases = [
            ('2" (50 mm)', 350),
            ('1-1/2" (37,5 mm)', 350),
            ('1" (25 mm)', 350),
            ('3/4" (19 mm)', 350),
            ('1/2" (12,5 mm)', 350),
            ('3/8" (9,5 mm)', 360),
        ]

        for nms, cement_content_expected in test_cases:
            with self.subTest(nms=nms):
                cement_content, scm_content = self.cementitious.cementitious_content(water_content, w_cm, nms,
                                                                                     scm_checked)
                self.assertEqual(cement_content, cement_content_expected)
                self.assertEqual(scm_content, 0)

    def test_cementitious_content_with_scm(self):
        water_content = 200
        w_cm = 0.5
        nms = '2" (50 mm)' # Do not have minimum cementitious content
        scm_checked = True
        test_cases = [
            (5, 380, 20),
            (10, 360, 40),
            (25, 300, 100),
            (30, 280, 120),
            (45, 220, 180),
        ]

        for scm_percentage, cement_content_expected, scm_content_expected in test_cases:
            with self.subTest(scm_percentage=scm_percentage):
                cement_content, scm_content = self.cementitious.cementitious_content(water_content, w_cm, nms,
                                                                                     scm_checked, scm_percentage)
                self.assertEqual(cement_content, cement_content_expected)
                self.assertEqual(scm_content, scm_content_expected)

class TestWater(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.water = Water(density=1000)
        self.water.aci_data_model = self.aci_data_model

    def test_water_content_without_corrections(self):
        agg_types = ("Angular", "Natural")
        test_cases_for_non_air_entrained_concrete = [
            ("25 mm - 50 mm", '3/8" (9,5 mm)', 207),
            ("25 mm - 50 mm", '1/2" (12,5 mm)', 199),
            ("25 mm - 50 mm", '3/4" (19 mm)', 190),
            ("25 mm - 50 mm", '1" (25 mm)', 179),
            ("25 mm - 50 mm", '1-1/2" (37,5 mm)', 166),
            ("25 mm - 50 mm", '2" (50 mm)', 154),
            ("25 mm - 50 mm", '3" (75 mm)', 130),

            ("75 mm - 100 mm", '3/8" (9,5 mm)', 228),
            ("75 mm - 100 mm", '1/2" (12,5 mm)', 216),
            ("75 mm - 100 mm", '3/4" (19 mm)', 205),
            ("75 mm - 100 mm", '1" (25 mm)', 193),
            ("75 mm - 100 mm", '1-1/2" (37,5 mm)', 181),
            ("75 mm - 100 mm", '2" (50 mm)', 169),
            ("75 mm - 100 mm", '3" (75 mm)', 145),

            ("125 mm - 150 mm", '3/8" (9,5 mm)', 237),
            ("125 mm - 150 mm", '1/2" (12,5 mm)', 222),
            ("125 mm - 150 mm", '3/4" (19 mm)', 208),
            ("125 mm - 150 mm", '1" (25 mm)', 196),
            ("125 mm - 150 mm", '1-1/2" (37,5 mm)', 183),
            ("125 mm - 150 mm", '2" (50 mm)', 172),
            ("125 mm - 150 mm", '3" (75 mm)', 151),

            ("150 mm - 175 mm", '3/8" (9,5 mm)', 243),
            ("150 mm - 175 mm", '1/2" (12,5 mm)', 228),
            ("150 mm - 175 mm", '3/4" (19 mm)', 216),
            ("150 mm - 175 mm", '1" (25 mm)', 202),
            ("150 mm - 175 mm", '1-1/2" (37,5 mm)', 190),
            ("150 mm - 175 mm", '2" (50 mm)', 178),
            ("150 mm - 175 mm", '3" (75 mm)', 160),
        ]
        test_cases_for_air_entrained_concrete = [
            ("25 mm - 50 mm", '3/8" (9,5 mm)', 181),
            ("25 mm - 50 mm", '1/2" (12,5 mm)', 175),
            ("25 mm - 50 mm", '3/4" (19 mm)', 168),
            ("25 mm - 50 mm", '1" (25 mm)', 160),
            ("25 mm - 50 mm", '1-1/2" (37,5 mm)', 150),
            ("25 mm - 50 mm", '2" (50 mm)', 142),
            ("25 mm - 50 mm", '3" (75 mm)', 122),

            ("75 mm - 100 mm", '3/8" (9,5 mm)', 202),
            ("75 mm - 100 mm", '1/2" (12,5 mm)', 193),
            ("75 mm - 100 mm", '3/4" (19 mm)', 184),
            ("75 mm - 100 mm", '1" (25 mm)', 175),
            ("75 mm - 100 mm", '1-1/2" (37,5 mm)', 165),
            ("75 mm - 100 mm", '2" (50 mm)', 157),
            ("75 mm - 100 mm", '3" (75 mm)', 133),

            ("125 mm - 150 mm", '3/8" (9,5 mm)', 211),
            ("125 mm - 150 mm", '1/2" (12,5 mm)', 199),
            ("125 mm - 150 mm", '3/4" (19 mm)', 187),
            ("125 mm - 150 mm", '1" (25 mm)', 178),
            ("125 mm - 150 mm", '1-1/2" (37,5 mm)', 166),
            ("125 mm - 150 mm", '2" (50 mm)', 160),
            ("125 mm - 150 mm", '3" (75 mm)', 142),

            ("150 mm - 175 mm", '3/8" (9,5 mm)', 216),
            ("150 mm - 175 mm", '1/2" (12,5 mm)', 205),
            ("150 mm - 175 mm", '3/4" (19 mm)', 197),
            ("150 mm - 175 mm", '1" (25 mm)', 184),
            ("150 mm - 175 mm", '1-1/2" (37,5 mm)', 174),
            ("150 mm - 175 mm", '2" (50 mm)', 166),
            ("150 mm - 175 mm", '3" (75 mm)', 154),
        ]

        for case, entrained_air in [(test_cases_for_non_air_entrained_concrete, False), (test_cases_for_air_entrained_concrete, True)]:
            for slump_range, nms, water_content_expected in case:
                with self.subTest(slump_range=slump_range, nms=nms, entrained_air=entrained_air):
                    water_content = self.water.water_content(slump_range, nms, entrained_air, agg_types)
                    self.assertEqual(water_content, water_content_expected)

    def test_water_content_with_corrections(self):
        slump_range = "125 mm - 150 mm"
        nms = '2" (50 mm)'
        entrained_air = True
        test_cases = [
            (("Redondeada", "Natural"), "Cenizas volantes", 55, 123.20),
            (("Angular", "Manufacturada"), "Cemento de escoria", 25, 152),
            (("Redondeada", "Manufacturada"), "Cemento de escoria", 35, 131.2),
        ]

        for agg_types, scm, scm_percentage, water_content_expected in test_cases:
            with self.subTest(agg_types=agg_types, scm=scm, scm_percentage=scm_percentage):
                water_content = self.water.water_content(slump_range, nms, entrained_air, agg_types, scm, scm_percentage)
                self.assertAlmostEqual(water_content, water_content_expected, delta=0.001)

class TestAir(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.air = Air(entrained_air=True, user_defined=3.5, exposure_defined=True)
        self.air.aci_data_model = self.aci_data_model

    def test_entrapped_air_volume(self):
        test_cases = [
            ('3-1/2" (90 mm)', 0.0015),
            ('3" (75 mm)', 0.003),
            ('2-1/2" (63 mm)', 0.004),
            ('2" (50 mm)', 0.005),
            ('1-1/2" (37,5 mm)', 0.010),
            ('1" (25 mm)', 0.015),
            ('3/4" (19 mm)', 0.020),
            ('1/2" (12,5 mm)', 0.025),
            ('3/8" (9,5 mm)', 0.030),
        ]

        for nms, entrapped_air_volume_expected in test_cases:
            with self.subTest(nms=nms):
                entrapped_air_volume = self.air.entrapped_air_volume(nms)
                self.assertEqual(entrapped_air_volume, entrapped_air_volume_expected)

    def test_entrained_air_volume(self):
        test_cases = [
            ('3-1/2" (90 mm)', ['F1', 'W0', 'S0', 'C0'], 0.0343),
            ('3" (75 mm)', ['F1', 'W0', 'S0', 'C0'], 0.035),
            ('2-1/2" (63 mm)', ['F1', 'W0', 'S0', 'C0'], 0.0374),
            ('2" (50 mm)', ['F1', 'W0', 'S0', 'C0'], 0.040),
            ('1-1/2" (37,5 mm)', ['F1', 'W0', 'S0', 'C0'], 0.045),
            ('1" (25 mm)', ['F1', 'W0', 'S0', 'C0'], 0.045),
            ('3/4" (19 mm)', ['F1', 'W0', 'S0', 'C0'], 0.050),
            ('1/2" (12,5 mm)', ['F1', 'W0', 'S0', 'C0'], 0.055),
            ('3/8" (9,5 mm)', ['F1', 'W0', 'S0', 'C0'], 0.060),

            ('3-1/2" (90 mm)', ['F2', 'W0', 'S0', 'C0'], 0.0435),
            ('3" (75 mm)', ['F2', 'W0', 'S0', 'C0'], 0.045),
            ('2-1/2" (63 mm)', ['F2', 'W0', 'S0', 'C0'], 0.0474),
            ('2" (50 mm)', ['F2', 'W0', 'S0', 'C0'], 0.050),
            ('1-1/2" (37,5 mm)', ['F2', 'W0', 'S0', 'C0'], 0.055),
            ('1" (25 mm)', ['F3', 'W0', 'S0', 'C0'], 0.060),
            ('3/4" (19 mm)', ['F3', 'W0', 'S0', 'C0'], 0.060),
            ('1/2" (12,5 mm)', ['F3', 'W0', 'S0', 'C0'], 0.070),
            ('3/8" (9,5 mm)', ['F3', 'W0', 'S0', 'C0'], 0.075),
        ]

        for nms, exposure_classes, entrained_air_volume_expected in test_cases:
            with self.subTest(nms=nms, exposure_classes=exposure_classes):
                entrained_air_volume = self.air.entrained_air_volume(nms, exposure_classes)
                self.assertAlmostEqual(entrained_air_volume, entrained_air_volume_expected)

class TestFineAggregate(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.fine_agg = FineAggregate(
            agg_type="fine",
            relative_density=2.65,
            loose_bulk_density=1600,
            compacted_bulk_density=1800,
            moisture_content=2.0,
            moisture_absorption=1.0,
            grading={},
            fineness_modulus=2.8
        )
        self.fine_agg.aci_data_model = self.aci_data_model

    def test_fine_content(self):
        water_volume = 0.135
        air_volume = 0.080
        cement_abs_volume = 0.145
        scm_abs_volume = 0
        coarse_abs_volume = 0.400
        fine_relative_density = 2.64
        water_density = 1000

        fine_content_ssd = self.fine_agg.fine_content(water_volume, air_volume, cement_abs_volume, scm_abs_volume,
                                                      coarse_abs_volume, fine_relative_density, water_density)
        fine_content_ssd_expected = 633.6

        self.assertEqual(fine_content_ssd, fine_content_ssd_expected)

class TestCoarseAggregate(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.coarse_agg = CoarseAggregate(
            agg_type="coarse",
            relative_density=2.7,
            loose_bulk_density=1500,
            compacted_bulk_density=1600,
            moisture_content=1.5,
            moisture_absorption=1.2,
            grading={},
            nominal_max_size=""
        )
        self.coarse_agg.aci_data_model = self.aci_data_model

    def test_coarse_content(self):
        absorption = 0
        compacted_bulk_density = 1
        test_cases = [
            ('3-1/2" (90 mm)', 2.40, 0.871),
            ('3" (75 mm)', 2.40, 0.82),
            ('2-1/2" (63 mm)', 2.40, 0.818),
            ('2" (50 mm)', 2.40, 0.78),
            ('1-1/2" (37,5 mm)', 2.40, 0.75),
            ('1" (25 mm)', 2.40, 0.71),
            ('3/4" (19 mm)', 2.40, 0.66),
            ('1/2" (12,5 mm)', 2.40, 0.59),
            ('3/8" (9,5 mm)', 2.40, 0.50),

            ('3-1/2" (90 mm)', 2.60, 0.851),
            ('3" (75 mm)', 2.60, 0.80),
            ('2-1/2" (63 mm)', 2.60, 0.798),
            ('2" (50 mm)', 2.60, 0.76),
            ('1-1/2" (37,5 mm)', 2.60, 0.73),
            ('1" (25 mm)', 2.60, 0.69),
            ('3/4" (19 mm)', 2.60, 0.64),
            ('1/2" (12,5 mm)', 2.60, 0.57),
            ('3/8" (9,5 mm)', 2.60, 0.48),

            ('3-1/2" (90 mm)', 2.80, 0.831),
            ('3" (75 mm)', 2.80, 0.78),
            ('2-1/2" (63 mm)', 2.80, 0.778),
            ('2" (50 mm)', 2.80, 0.74),
            ('1-1/2" (37,5 mm)', 2.80, 0.71),
            ('1" (25 mm)', 2.80, 0.67),
            ('3/4" (19 mm)', 2.80, 0.62),
            ('1/2" (12,5 mm)', 2.80, 0.55),
            ('3/8" (9,5 mm)', 2.80, 0.46),

            ('3-1/2" (90 mm)', 3.00, 0.811),
            ('3" (75 mm)', 3.00, 0.76),
            ('2-1/2" (63 mm)', 3.00, 0.758),
            ('2" (50 mm)', 3.00, 0.72),
            ('1-1/2" (37,5 mm)', 3.00, 0.69),
            ('1" (25 mm)', 3.00, 0.65),
            ('3/4" (19 mm)', 3.00, 0.60),
            ('1/2" (12,5 mm)', 3.00, 0.53),
            ('3/8" (9,5 mm)', 3.00, 0.44),
        ]

        for nms, fineness_modulus, coarse_content_expected in test_cases:
            with self.subTest(nms=nms, fineness_modulus=fineness_modulus):
                coarse_content = self.coarse_agg.coarse_content(nms, fineness_modulus, compacted_bulk_density,
                                                                absorption)
                self.assertAlmostEqual(coarse_content, coarse_content_expected, delta=0.001)

class TestStandardDeviation(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.std_dev = StandardDeviation(
            std_dev_known=True,
            std_dev_value=2.5,
            sample_size=20,
            defective_level="",
            std_dev_unknown=False
        )
        self.std_dev.aci_data_model = self.aci_data_model

    def test_target_strength_with_std_dev_known(self):
        std_dev_known = True
        std_dev_unknown = False
        defective_level = '9'
        test_cases = [
            (31, 3.5, 15, 36.9598),
            (21, 7, 20, 35.1148),
            (55, 5, 25, 61.901),
            (35, 1.5, 30, 37.01),
            (36, 2, 30, 38.68),
        ]

        for design_strength, std_dev_value, sample_size, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown)
                self.assertAlmostEqual(target_strength, target_strength_expected, delta=0.1)

    def test_target_strength_without_std_dev_known(self):
        std_dev_known = False
        std_dev_unknown = True
        defective_level = '9'
        std_dev_value = 0
        sample_size = 15
        test_cases = [
            (20, 27),
            (21, 29.3),
            (32, 40.3),
            (35, 43.3),
            (36, 44.6),
            (40, 49),
        ]

        for design_strength, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown)
                self.assertEqual(target_strength, target_strength_expected)

class TestAbramsLaw(unittest.TestCase):
    def setUp(self):
        self.aci_data_model = ACIDataModel()
        self.abrams_law = AbramsLaw()
        self.abrams_law.aci_data_model = self.aci_data_model

    def test_water_cementitious_materials_ratio_without_exposure_classes(self):
        exposure_classes = ['F0', 'W0', 'S0', 'C0']
        test_cases = [
            (45, False, 0.38),
            (40, False, 0.42),
            (35, False, 0.47),
            (30, False, 0.54),
            (25, False, 0.61),
            (20, False, 0.69),
            (15, False, 0.79),

            (45, True, 0.30),
            (40, True, 0.34),
            (35, True, 0.39),
            (30, True, 0.45),
            (25, True, 0.52),
            (20, True, 0.60),
            (15, True, 0.70),
        ]

        for target_strength, entrained_air, water_cementitious_materials_ratio_expected in test_cases:
            with self.subTest(target_strength=target_strength, entrained_air=entrained_air):
                water_cementitious_materials_ratio = self.abrams_law.water_cementitious_materials_ratio(target_strength,
                                                                                                        entrained_air,
                                                                                                        exposure_classes)
                self.assertAlmostEqual(water_cementitious_materials_ratio, water_cementitious_materials_ratio_expected,
                                       delta=0.015)

    def test_water_cementitious_materials_ratio_with_exposure_classes(self):
        target_strength = 15
        entrained_air = False
        test_cases = [
            (['F0', 'W0', 'S0', 'C0'], 1.1318 * exp(-0.025 * target_strength)),
            (['F0', 'W0', 'S1', 'C0'], 0.50),
            (['F0', 'W0', 'S2', 'C0'], 0.45),
            (['F0', 'W0', 'S3', 'C0'], 0.40),

            (['F0', 'W0', 'S0', 'C0'], 1.1318 * exp(-0.025 * target_strength)),
            (['F1', 'W0', 'S0', 'C0'], 0.55),
            (['F2', 'W0', 'S0', 'C0'], 0.45),
            (['F3', 'W0', 'S0', 'C0'], 0.40),

            (['F0', 'W0', 'S0', 'C0'], 1.1318 * exp(-0.025 * target_strength)),
            (['F0', 'W1', 'S0', 'C0'], 1.1318 * exp(-0.025 * target_strength)),
            (['F0', 'W2', 'S0', 'C0'], 0.50),

            (['F0', 'W0', 'S0', 'C0'], 1.1318 * exp(-0.025 * target_strength)),
            (['F0', 'W0', 'S0', 'C1'], 1.1318 * exp(-0.025 * target_strength)),
            (['F0', 'W0', 'S0', 'C2'], 0.40),
        ]

        for exposure_classes, water_cementitious_materials_ratio_expected in test_cases:
            with self.subTest(exposure_classes=exposure_classes):
                water_cementitious_materials_ratio = self.abrams_law.water_cementitious_materials_ratio(target_strength,
                                                                                                        entrained_air,
                                                                                                        exposure_classes)
                self.assertEqual(water_cementitious_materials_ratio, water_cementitious_materials_ratio_expected)

##############################################
# Run all the tests
##############################################
if __name__ == '__main__':
    unittest.main()