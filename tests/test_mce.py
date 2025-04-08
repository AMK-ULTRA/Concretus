import unittest

from Concretus.core.regular_concrete.design_methods.mce import (Cement, Air, FineAggregate, CoarseAggregate,
                                                                StandardDeviation, AbramsLaw, Beta)
from Concretus.core.regular_concrete.models.mce_data_model import MCEDataModel


class TestCement(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
        self.cement = Cement(relative_density=3.33)
        self.cement.mce_data_model = self.mce_data_model

    def test_cement_content_without_correction(self):
        nms = '1" (25 mm)'
        agg_types = ("Triturado", "Natural")
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        test_cases = [
            (75, 0.455, 450.3214128),
            (85, 0.49, 417.2340426),
            (50.8, 0.48, 394.686432),
            (60, 0.48, 405.338824),
            (80, 0.43, 489.680733),
            (10, 0.50, 288.580251),
            (0, 0.50, 270),
        ]

        for slump, alpha, cement_content_expected in test_cases:
            with self.subTest(slump=slump, alpha=alpha):
                cement_content = self.cement.cement_content(slump, alpha, nms, agg_types, exposure_classes)
                self.assertAlmostEqual(cement_content, cement_content_expected, delta=0.000001)

    def test_cement_content_with_correction(self):
        slump = 100
        alpha = 0.5
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        test_cases = [
            ('3" (75 mm)', ("Triturado", "Natural"), 0.82 * 500),
            ('2-1/2" (63 mm)', ("Triturado", "Natural"), 0.85 * 500),
            ('2" (50 mm)', ("Triturado", "Natural"), 0.88 * 500),
            ('1-1/2" (37,5 mm)', ("Triturado", "Natural"), 0.93 * 500),
            ('1" (25 mm)', ("Triturado", "Natural"), 1.00 * 500),
            ('3/4" (19 mm)', ("Triturado", "Natural"), 1.05 * 500),
            ('1/2" (12,5 mm)', ("Triturado", "Natural"), 1.14 * 500),
            ('3/8" (9,5 mm)', ("Triturado", "Natural"), 1.20 * 500),
            ('1/4" (6,3 mm)', ("Triturado", "Natural"), 1.33 * 500),

            ('1" (25 mm)', ("Triturado", "Natural"), 1.00 * 500),
            ('1" (25 mm)', ("Triturado", "Triturada"), 1.28 * 500),
            ('1" (25 mm)', ("Semitriturado", "Natural"), 0.93 * 500),
            ('1" (25 mm)', ("Semitriturado", "Triturada"), 1.23 * 500),
            ('1" (25 mm)', ("Grava natural", "Natural"), 0.90 * 500),
            ('1" (25 mm)', ("Grava natural", "Triturada"), 0.96 * 500),
        ]

        for nms, agg_types, cement_content_expected in test_cases:
            with self.subTest(nms=nms, agg_types=agg_types):
                cement_content = self.cement.cement_content(slump, alpha, nms, agg_types, exposure_classes, k=500, n=0, m=0)
                self.assertEqual(cement_content, cement_content_expected)

    def test_cement_content_with_theta(self):
        nms = '1" (25 mm)'
        agg_types = ("Triturado", "Natural")
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        slump = 40
        test_cases = [
            (134.8, 0.50, 331.9165),
            (136.8, 0.55, 297.5874),
            (141.8, 0.35, 555.1211),
            (222, 0.60, 431.2771),
            (0, 0.35, 270),
            (-10, 0.50, 360.2435),
        ]

        for theta, alpha, cement_content_expected in test_cases:
            with self.subTest(theta=theta, alpha=alpha):
                cement_content = self.cement.cement_content(slump, alpha, nms, agg_types, exposure_classes, theta)
                self.assertAlmostEqual(cement_content, cement_content_expected, delta=0.0001)

class TestAir(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
        self.air = Air()
        self.air.mce_data_model = self.mce_data_model

    def test_entrapped_air_volume(self):
        cement_content = 100
        test_cases = [
            ('3-1/2" (90 mm)', 0.001 * cement_content / 90),
            ('3" (75 mm)', 0.001 * cement_content / 75),
            ('2-1/2" (63 mm)', 0.001 * cement_content / 63),
            ('2" (50 mm)', 0.001 * cement_content / 50),
            ('1-1/2" (37,5 mm)', 0.001 * cement_content / 37.5),
            ('1" (25 mm)', 0.001 * cement_content / 25),
            ('3/4" (19 mm)', 0.001 * cement_content / 19),
            ('1/2" (12,5 mm)', 0.001 * cement_content / 12.5),
            ('3/8" (9,5 mm)', 0.001 * cement_content / 9.5),
            ('1/4" (6,3 mm)', 0.001 * cement_content / 6.3),
        ]

        for nms, entrapped_air_volume_expected in test_cases:
            with self.subTest(nms=nms):
                entrapped_air_volume = self.air.entrapped_air_volume(nms, cement_content)
                self.assertAlmostEqual(entrapped_air_volume, entrapped_air_volume_expected)

class TestFineAggregate(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
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
        self.fine_agg.mce_data_model = self.mce_data_model

    def test_fine_content(self):
        entrapped_air_volume = 0.015
        cement_abs_volume = 83 / 630
        water_volume = 0.21
        water_density = 1000
        fine_relative_density = 2.68
        coarse_relative_density = 2.70
        beta_value = 0.45

        fine_content_ssd = self.fine_agg.fine_content(entrapped_air_volume, cement_abs_volume, water_volume,
                                                      water_density, fine_relative_density, coarse_relative_density,
                                                      beta_value)
        fine_content_ssd_expected = 778.93773574
        self.assertAlmostEqual(fine_content_ssd, fine_content_ssd_expected)

class TestCoarseAggregate(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
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
        self.coarse_agg.mce_data_model = self.mce_data_model

    def test_coarse_content(self):
        beta_value = 0.25
        fine_content = 100

        coarse_content_ssd = self.coarse_agg.coarse_content(fine_content, beta_value)
        coarse_content_expected = 300
        self.assertEqual(coarse_content_ssd, coarse_content_expected)

class TestStandardDeviation(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
        self.std_dev = StandardDeviation(
            std_dev_known=True,
            std_dev_value=2.5,
            sample_size=20,
            defective_level="",
            std_dev_unknown=False,
            quality_control=""
        )
        self.std_dev.mce_data_model = self.mce_data_model

    def test_target_strength_with_std_dev_known(self):
        std_dev_known = True
        std_dev_unknown = False
        defective_level = '9'
        quality_control = "Excelente"
        test_cases = [
            (210, 35, 15, 270.0446),
            (250, 70, 20, 391.9796),
            (300, 50, 25, 385.5615),
            (350, 15, 30, 370.115),
            (365, 20, 35, 391.82),
            (410, 50, 15, 504.778),
        ]

        for design_strength, std_dev_value, sample_size, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown,
                                                               quality_control)
                self.assertAlmostEqual(target_strength, target_strength_expected)

    def test_target_strength_without_std_dev_known(self):
        std_dev_known = False
        std_dev_unknown = True
        defective_level = '9'
        std_dev_value = 0
        sample_size = 15
        test_cases = [
            (200, "Excelente", 245),
            (200, "Aceptable", 280),
            (200, "Sin control", 330),

            (210, "Excelente", 270),
            (210, "Aceptable", 305),
            (210, "Sin control", 380),

            (350, "Excelente", 410),
            (350, "Aceptable", 445),
            (350, "Sin control", 520),

            (360, "Excelente", 435),
            (360, "Aceptable", 470),
            (360, "Sin control", 570),
        ]

        for design_strength, quality_control, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown,
                                                               quality_control)
                self.assertAlmostEqual(target_strength, target_strength_expected)

class TestBeta(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
        self.beta = Beta()
        self.beta.mce_data_model = self.mce_data_model

    def test_get_beta(self):
        nms = '1" (25 mm)'
        coarse_data = {
            '3-1/2" (90 mm)': 100,
            '3" (75 mm)': 100,
            '2-1/2" (63 mm)': 100,
            '2" (50 mm)': 100,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': 97,
            '3/4" (19 mm)': 52,
            '1/2" (12,5 mm)': 25,
            '3/8" (9,5 mm)': 6,
            '1/4" (6,3 mm)': 1,
            'No. 4 (4,75 mm)': 0,
            'No. 8 (2,36 mm)': 0,
            'No. 16 (1,18 mm)': 0,
            'No. 30 (0,600 mm)': 0,
            'No. 50 (0,300 mm)': 0,
            'No. 100 (0,150 mm)': 0,
        }
        fine_data = {
            '3-1/2" (90 mm)': 100,
            '3" (75 mm)': 100,
            '2-1/2" (63 mm)': 100,
            '2" (50 mm)': 100,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': 100,
            '3/4" (19 mm)': 100,
            '1/2" (12,5 mm)': 100,
            '3/8" (9,5 mm)': 100,
            '1/4" (6,3 mm)': 96,
            'No. 4 (4,75 mm)': 86,
            'No. 8 (2,36 mm)': 68,
            'No. 16 (1,18 mm)': 40,
            'No. 30 (0,600 mm)': 32,
            'No. 50 (0,300 mm)': 12,
            'No. 100 (0,150 mm)': 4,
        }

        beta_min, beta_max = self.beta.get_beta(nms, coarse_data, fine_data)
        beta_min_expected = 41.5
        beta_max_expected = 62.5
        self.assertAlmostEqual(beta_min, beta_min_expected, delta=0.5)
        self.assertAlmostEqual(beta_max, beta_max_expected, delta=0.5)

class TestAbramsLaw(unittest.TestCase):
    def setUp(self):
        self.mce_data_model = MCEDataModel()
        self.abrams_law = AbramsLaw()
        self.abrams_law.mce_data_model = self.mce_data_model

    def test_water_cement_ratio_without_corrections(self):
        target_strength = 300
        nms = '1" (25 mm)'
        agg_types = ("Triturado", "Natural")
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        test_cases = [
            ('7 días', 0.4099),
            ('28 días', 0.5090),
            ('90 días', 0.5764),
        ]

        for target_strength_time, water_cement_ratio_expected in test_cases:
            with self.subTest(target_strength_time=target_strength_time):
                water_cement_ratio = self.abrams_law.water_cement_ratio(target_strength, target_strength_time, nms,
                                                                        agg_types, exposure_classes)
                self.assertAlmostEqual(water_cement_ratio, water_cement_ratio_expected, delta=0.001)

    def test_water_cement_ratio_with_corrections(self):
        target_strength = 500
        target_strength_time = "28 días"
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        test_cases = [
            ('3" (75 mm)', ("Triturado", "Natural"), 0.74 * 0.2731329123),
            ('2-1/2" (63 mm)', ("Triturado", "Natural"), 0.78 * 0.2731329123),
            ('2" (50 mm)', ("Triturado", "Natural"), 0.82 * 0.2731329123),
            ('1-1/2" (37,5 mm)', ("Triturado", "Natural"), 0.91 * 0.2731329123),
            ('1" (25 mm)', ("Triturado", "Natural"), 1.00 * 0.2731329123),
            ('3/4" (19 mm)', ("Triturado", "Natural"), 1.05 * 0.2731329123),
            ('1/2" (12,5 mm)', ("Triturado", "Natural"), 1.10 * 0.2731329123),
            ('3/8" (9,5 mm)', ("Triturado", "Natural"), 1.30 * 0.2731329123),
            ('1/4" (6,3 mm)', ("Triturado", "Natural"), 1.60 * 0.2731329123),

            ('1" (25 mm)', ("Triturado", "Natural"), 1.00 * 0.2731329123),
            ('1" (25 mm)', ("Triturado", "Triturada"), 1.14 * 0.2731329123),
            ('1" (25 mm)', ("Semitriturado", "Natural"), 0.97 * 0.2731329123),
            ('1" (25 mm)', ("Semitriturado", "Triturada"), 1.10 * 0.2731329123),
            ('1" (25 mm)', ("Grava natural", "Natural"), 0.91 * 0.2731329123),
            ('1" (25 mm)', ("Grava natural", "Triturada"), 0.93 * 0.2731329123),
        ]

        for nms, agg_types, water_cement_ratio_expected in test_cases:
            with self.subTest(nms=nms, agg_types=agg_types):
                water_cement_ratio = self.abrams_law.water_cement_ratio(target_strength, target_strength_time, nms,
                                                                        agg_types, exposure_classes)
                self.assertAlmostEqual(water_cement_ratio, water_cement_ratio_expected)

    def test_water_cement_ratio_with_different_constant(self):
        target_strength = 300
        nms = '1" (25 mm)'
        agg_types = ("Triturado", "Natural")
        exposure_classes = ['Despreciable', 'Despreciable', 'Despreciable', 'Atmósfera común']
        test_cases = [
            ('7 días', 945.6, 13.1, 0.4463),
            ('28 días', 945.6, 8.69, 0.5310),
            ('90 días', 945.6, 7.71, 0.5621),
        ]

        for target_strength_time, m, n, water_cement_ratio_expected in test_cases:
            with self.subTest(target_strength_time=target_strength_time):
                water_cement_ratio = self.abrams_law.water_cement_ratio(target_strength, target_strength_time, nms,
                                                                        agg_types, exposure_classes, m, n)
                self.assertAlmostEqual(water_cement_ratio, water_cement_ratio_expected, delta=0.0001)

##############################################
# Run all the tests
##############################################
if __name__ == '__main__':
    unittest.main()