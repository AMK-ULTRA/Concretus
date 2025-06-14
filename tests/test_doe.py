import unittest

from core.regular_concrete.design_methods.doe import (CementitiousMaterial, Water, Air, FineAggregate, CoarseAggregate,
                                                      StandardDeviation, AbramsLaw, Aggregate)
from core.regular_concrete.models.doe_data_model import DOEDataModel


class TestCementitiousMaterial(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.cementitious = CementitiousMaterial(relative_density=3.15)
        self.cementitious.doe_data_model = self.doe_data_model

    def test_cementitious_content_without_scm(self):
        scm_checked = False
        test_cases = [
            (150, 0.65, ['XC3', 'N/A', 'N/A', 'N/A'], 280),
            (300, 0.60, ['XC1', 'N/A', 'N/A', 'N/A'], 500),
            (100, 0.60, ['XC2', 'XD2', 'XF1', 'N/A'], 300),
            (125, 0.40, ['XC1', 'XD1', 'XF3', 'N/A'], 320),
            (200, 0.40, ['XC2', 'XD1', 'XF3', 'XA3'], 500),
        ]

        for water_content, w_cm, exposure_classes, cement_content_expected in test_cases:
            with self.subTest(water_content=water_content, w_cm=w_cm, exposure_classes=exposure_classes):
                cement_content, scm_content = self.cementitious.cementitious_content(water_content, w_cm, exposure_classes, scm_checked)
                self.assertEqual(cement_content, cement_content_expected)
                self.assertEqual(scm_content, 0)

    def test_cementitious_content_with_scm(self):
        scm_checked = True
        test_cases = [
            (150, 0.65, ['XC3', 'N/A', 'N/A', 'N/A'], 10, 270.9677, 30.1075),
            (300, 0.60, ['XC1', 'N/A', 'N/A', 'N/A'], 20, 465.1163, 116.2791),
            (100, 0.60, ['XC2', 'XD2', 'XF1', 'N/A'], 30, 265.8228, 113.9241),
            (125, 0.40, ['XC1', 'XD1', 'XF3', 'N/A'], 40, 260.4167, 173.6111),
            (200, 0.40, ['XC2', 'XD1', 'XF3', 'XA3'], 50, 384.6154, 384.6154),
        ]

        for water_content, w_cm, exposure_classes, scm_percentage, cement_content_expected, scm_content_expected in test_cases:
            with self.subTest(water_content=water_content, w_cm=w_cm, exposure_classes=exposure_classes):
                cement_content, scm_content = self.cementitious.cementitious_content(water_content, w_cm,
                                                                                     exposure_classes, scm_checked,
                                                                                     scm_percentage)
                self.assertAlmostEqual(cement_content, cement_content_expected, delta=0.0001)
                self.assertAlmostEqual(scm_content, scm_content_expected, delta=0.0001)

    def test_cementitious_content_with_WRA(self):
        exposure_classes = ['N/A', 'N/A', 'N/A', 'N/A']
        scm_checked = False
        scm_percentage = 0
        wra_checked = True
        wra_action_water_reducer = True
        test_cases = [
            (150, 50, 0.65, 153.8462),
            (300, 10, 0.60, 483.3333),
            (100, 0, 0.60, 166.6667),
            (125, 25, 0.40, 250),
            (200, 80, 0.40, 300),
        ]

        for water_content, water_correction_wra, w_cm, cement_content_expected in test_cases:
            with self.subTest(water_content=water_content, water_correction_wra=water_correction_wra, w_cm=w_cm):
                cement_content, scm_content = self.cementitious.cementitious_content(water_content, w_cm,
                                                                                     exposure_classes, scm_checked,
                                                                                     scm_percentage, wra_checked,
                                                                                     wra_action_water_reducer,
                                                                                     water_correction_wra)
                self.assertAlmostEqual(cement_content, cement_content_expected, delta=0.0001)
                self.assertEqual(scm_content, 0)

class TestWater(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.water = Water(density=1000)
        self.water.doe_data_model = self.doe_data_model

    def test_water_content_without_corrections(self):
        air_entrained = False
        test_cases = [
            ("0 mm - 10 mm", "N/A (10 mm)", ("No triturada", "No triturada"), 150),
            ("0 mm - 10 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 180),
            ("0 mm - 10 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 135),
            ("0 mm - 10 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 170),
            ("0 mm - 10 mm", "N/A (40 mm)", ("No triturada", "No triturada"), 115),
            ("0 mm - 10 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 155),

            ("10 mm - 30 mm", "N/A (10 mm)", ("No triturada", "No triturada"), 180),
            ("10 mm - 30 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 205),
            ("10 mm - 30 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 160),
            ("10 mm - 30 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 190),
            ("10 mm - 30 mm", "N/A (40 mm)", ("No triturada", "No triturada"), 140),
            ("10 mm - 30 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 175),

            ("30 mm - 60 mm", "N/A (10 mm)", ("No triturada", "No triturada"), 205),
            ("30 mm - 60 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 230),
            ("30 mm - 60 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 180),
            ("30 mm - 60 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 210),
            ("30 mm - 60 mm", "N/A (40 mm)", ("No triturada", "No triturada"), 160),
            ("30 mm - 60 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 190),

            ("60 mm - 180 mm", "N/A (10 mm)", ("No triturada", "No triturada"), 225),
            ("60 mm - 180 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 250),
            ("60 mm - 180 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 195),
            ("60 mm - 180 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 225),
            ("60 mm - 180 mm", "N/A (40 mm)", ("No triturada", "No triturada"), 175),
            ("60 mm - 180 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 205),

            ("0 mm - 10 mm", "N/A (10 mm)", ("Triturada", "No triturada"), 160),
            ("10 mm - 30 mm", "N/A (20 mm)", ("Triturada", "No triturada"), 170),
            ("30 mm - 60 mm", "N/A (40 mm)", ("No triturada", "Triturada"), 180),
            ("60 mm - 180 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 725 / 3),
        ]

        for slump_range, nms, agg_types, water_content_expected in test_cases:
            with self.subTest(slump_range=slump_range, nms=nms, agg_types=agg_types):
                water_content = self.water.water_content(slump_range, nms, agg_types, air_entrained)
                self.assertEqual(water_content, water_content_expected)

    def test_water_content_with_corrections_for_SCM(self):
        air_entrained = False
        scm_checked = True
        test_cases = [
            ("0 mm - 10 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 5, 180),
            ("0 mm - 10 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 10, 130),
            ("10 mm - 30 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 15, 575 / 3),
            ("10 mm - 30 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 20, 165),
            ("30 mm - 60 mm", "N/A (40 mm)", ("No triturada", "Triturada"), 30, 160),
            ("30 mm - 60 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 39, 160),
            ("60 mm - 180 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 40, 200),
            ("60 mm - 180 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 50, 635 / 3),
        ]

        for slump_range, nms, agg_types, scm_percentage, water_content_expected in test_cases:
            with self.subTest(slump_range=slump_range, nms=nms, agg_types=agg_types):
                water_content = self.water.water_content(slump_range, nms, agg_types, air_entrained, scm_checked,
                                                         scm_percentage)
                self.assertEqual(water_content, water_content_expected)

    def test_water_content_with_corrections_for_WRA(self):
        air_entrained = False
        scm_checked = False
        scm_percentage = 0
        wra_checked = True
        wra_action_water_reducer = True
        wra_action_cement_economizer = False
        test_cases = [
            ("0 mm - 10 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 5, 171),
            ("0 mm - 10 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 10, 121.5),
            ("10 mm - 30 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 15, 1003 / 6),
            ("10 mm - 30 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 20, 140),
            ("30 mm - 60 mm", "N/A (40 mm)", ("No triturada", "Triturada"), 30, 126),
            ("30 mm - 60 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 39, 109.8),
            ("60 mm - 180 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 40, 135),
            ("60 mm - 180 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 50, 725 / 6),
        ]

        for slump_range, nms, agg_types, effectiveness, water_content_expected in test_cases:
            with self.subTest(slump_range=slump_range, nms=nms, agg_types=agg_types):
                water_content = self.water.water_content(slump_range, nms, agg_types, air_entrained, scm_checked,
                                                         scm_percentage, wra_checked, wra_action_cement_economizer,
                                                         wra_action_water_reducer, effectiveness)
                self.assertEqual(water_content, water_content_expected)

    def test_water_content_with_corrections_for_air_entrained(self):
        air_entrained = True
        test_cases = [
            ("0 mm - 10 mm", "N/A (10 mm)", ("Triturada", "Triturada"), 180),
            ("0 mm - 10 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 135),
            ("10 mm - 30 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 170),
            ("10 mm - 30 mm", "N/A (40 mm)", ("Triturada", "Triturada"), 155),
            ("30 mm - 60 mm", "N/A (40 mm)", ("No triturada", "Triturada"), 490 / 3),
            ("30 mm - 60 mm", "N/A (20 mm)", ("No triturada", "No triturada"), 160),
            ("60 mm - 180 mm", "N/A (20 mm)", ("Triturada", "Triturada"), 210),
            ("60 mm - 180 mm", "N/A (10 mm)", ("No triturada", "Triturada"), 665 / 3),
        ]

        for slump_range, nms, agg_types, water_content_expected in test_cases:
            with self.subTest(slump_range=slump_range, nms=nms, agg_types=agg_types):
                water_content = self.water.water_content(slump_range, nms, agg_types, air_entrained)
                self.assertAlmostEqual(water_content, water_content_expected)

    def test_water_content_with_multiple_corrections(self):
        slump_range = "0 mm - 10 mm"
        nms = "N/A (20 mm)"
        agg_types = ("No triturada", "No triturada")
        air_entrained = True
        scm_checked = True
        wra_checked = True
        wra_action_cement_economizer = False
        wra_action_water_reducer = True
        test_cases = [
            (5, 10, 121.5),
            (10, 5, 123.25),
            (25, 18, 100.7),
            (30, 50, 52.5),
            (50, 0, 110),
        ]

        for scm_percentage, effectiveness, water_content_expected in test_cases:
            with self.subTest(scm_percentage=scm_percentage, effectiveness=effectiveness):
                water_content = self.water.water_content(slump_range, nms, agg_types, air_entrained, scm_checked,
                                                         scm_percentage, wra_checked, wra_action_cement_economizer,
                                                         wra_action_water_reducer, effectiveness)
                self.assertAlmostEqual(water_content, water_content_expected)

class TestAir(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.air = Air(entrained_air=True, user_defined=3.5, exposure_defined=True)
        self.air.doe_data_model = self.doe_data_model

    def test_entrapped_air_volume(self):
        pass

    def test_entrained_air_volume(self):
        test_cases = [
            (['XC1', 'XS3', 'XF1', 'XA1'], 0),
            (['N/A', 'XS3', 'N/A', 'XA1'], 0),
            (['XC2', 'XS1', 'XF2', 'XA3'], 0.04),
            (['XC4', 'XS3', 'XF3', 'N/A'], 0.04),
            (['XC3', 'XD1', 'XF4', 'XA1'], 0.04),
        ]

        for exposure_classes, entrained_air_volume_expected in test_cases:
            with self.subTest(exposure_classes=exposure_classes):
                entrained_air_volume = self.air.entrained_air_volume(exposure_classes)
                self.assertEqual(entrained_air_volume, entrained_air_volume_expected)

class TestAggregate(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.agg = Aggregate(
            agg_type="",
            relative_density=2.65,
            loose_bulk_density=1600,
            compacted_bulk_density=1800,
            moisture_content=2.0,
            moisture_absorption=1.0,
            grading={}
        )
        self.agg.doe_data_model = self.doe_data_model

    def test_total_agg_content_without_entrained_air(self):
        entrained_air_content = 0
        cement_content = -160
        scm_content = 0
        water_content = 160
        test_cases = [
            (2.3, 2250),
            (2.4, 2250),
            (2.5, 2330),
            (2.6, 2400),
            (2.7, 2480),
            (2.8, 2550),
            (2.9, 2620),
            (3.0, 2620),
        ]

        for combined_relative_density, total_agg_content_expected in test_cases:
            with self.subTest(combined_relative_density=combined_relative_density):
                total_agg_content = self.agg.total_agg_content(cement_content, scm_content, water_content,
                                                               entrained_air_content, combined_relative_density)
                self.assertAlmostEqual(total_agg_content, total_agg_content_expected, delta=5)

    def test_total_agg_content_with_entrained_air(self):
        cement_content = -160
        scm_content = 0
        water_content = 160
        test_cases = [
            (2.3, 0.045, 2146.5),
            (2.4, 0.045, 2142),
            (2.5, 0.030, 2255),
            (2.6, 0.020, 2348),
            (2.7, 0.050, 2345),
            (2.8, 0.060, 2382),
            (2.9, 0.085, 2373.5),
            (2.95, 0.085, 2369.25),
        ]

        for combined_relative_density, entrained_air_content, total_agg_content_expected in test_cases:
            with self.subTest(combined_relative_density=combined_relative_density):
                total_agg_content = self.agg.total_agg_content(cement_content, scm_content, water_content,
                                                               entrained_air_content, combined_relative_density)
                self.assertAlmostEqual(total_agg_content, total_agg_content_expected, delta=5)

class TestFineAggregate(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
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
        self.fine_agg.doe_data_model = self.doe_data_model

    def test_fine_content(self):
        total_agg_content = 100
        w_cm = 0.4
        test_cases = [
            ("0 mm - 10 mm", "N/A (10 mm)", 100, 24.8),
            ("0 mm - 10 mm", "N/A (10 mm)", 80, 28.3),
            ("0 mm - 10 mm", "N/A (10 mm)", 60, 34.7),
            ("0 mm - 10 mm", "N/A (10 mm)", 40, 41.5),
            ("0 mm - 10 mm", "N/A (10 mm)", 15, 53.4),
            ("0 mm - 10 mm", "N/A (10 mm)", 55, 36.325),
            ("0 mm - 10 mm", "N/A (10 mm)", 70, 31.45),

            ("10 mm - 30 mm", "N/A (10 mm)", 100, 25.8),
            ("10 mm - 30 mm", "N/A (10 mm)", 80, 30.3),
            ("10 mm - 30 mm", "N/A (10 mm)", 60, 36.1),
            ("10 mm - 30 mm", "N/A (10 mm)", 40, 43.4),
            ("10 mm - 30 mm", "N/A (10 mm)", 15, 55.3),
            ("10 mm - 30 mm", "N/A (10 mm)", 95, 27.0),
            ("10 mm - 30 mm", "N/A (10 mm)", 101, 25.8),

            ("30 mm - 60 mm", "N/A (10 mm)", 100, 27.7),
            ("30 mm - 60 mm", "N/A (10 mm)", 80, 32.6),
            ("30 mm - 60 mm", "N/A (10 mm)", 60, 39.2),
            ("30 mm - 60 mm", "N/A (10 mm)", 40, 46.3),
            ("30 mm - 60 mm", "N/A (10 mm)", 15, 59.9),
            ("30 mm - 60 mm", "N/A (10 mm)", 45, 44.2),
            ("30 mm - 60 mm", "N/A (10 mm)", 10, 59.9),

            ("60 mm - 180 mm", "N/A (10 mm)", 100, 30.9),
            ("60 mm - 180 mm", "N/A (10 mm)", 80, 35.8),
            ("60 mm - 180 mm", "N/A (10 mm)", 60, 43.2),
            ("60 mm - 180 mm", "N/A (10 mm)", 40, 52.8),
            ("60 mm - 180 mm", "N/A (10 mm)", 15, 66.5),
            ("60 mm - 180 mm", "N/A (10 mm)", 85, 34.3),
            ("60 mm - 180 mm", "N/A (10 mm)", 35, 55.5),

            ("0 mm - 10 mm", "N/A (20 mm)", 100, 18.5),
            ("0 mm - 10 mm", "N/A (20 mm)", 80, 21.8),
            ("0 mm - 10 mm", "N/A (20 mm)", 60, 26.2),
            ("0 mm - 10 mm", "N/A (20 mm)", 40, 30.8),
            ("0 mm - 10 mm", "N/A (20 mm)", 15, 39.9),
            ("0 mm - 10 mm", "N/A (20 mm)", 90, 20.2),
            ("0 mm - 10 mm", "N/A (20 mm)", 50, 28.8),

            ("10 mm - 30 mm", "N/A (20 mm)", 100, 20.4),
            ("10 mm - 30 mm", "N/A (20 mm)", 80, 23.3),
            ("10 mm - 30 mm", "N/A (20 mm)", 60, 27.6),
            ("10 mm - 30 mm", "N/A (20 mm)", 40, 33.7),
            ("10 mm - 30 mm", "N/A (20 mm)", 15, 42.8),
            ("10 mm - 30 mm", "N/A (20 mm)", 20, 40.6),
            ("10 mm - 30 mm", "N/A (20 mm)", 85, 22.3),

            ("30 mm - 60 mm", "N/A (20 mm)", 100, 22.0),
            ("30 mm - 60 mm", "N/A (20 mm)", 80, 25.4),
            ("30 mm - 60 mm", "N/A (20 mm)", 60, 30.4),
            ("30 mm - 60 mm", "N/A (20 mm)", 40, 36.0),
            ("30 mm - 60 mm", "N/A (20 mm)", 15, 46.2),
            ("30 mm - 60 mm", "N/A (20 mm)", 50, 33.3),
            ("30 mm - 60 mm", "N/A (20 mm)", 90, 23.6),

            ("60 mm - 180 mm", "N/A (20 mm)", 100, 25.1),
            ("60 mm - 180 mm", "N/A (20 mm)", 80, 28.7),
            ("60 mm - 180 mm", "N/A (20 mm)", 60, 34.2),
            ("60 mm - 180 mm", "N/A (20 mm)", 40, 42.2),
            ("60 mm - 180 mm", "N/A (20 mm)", 15, 53.1),
            ("60 mm - 180 mm", "N/A (20 mm)", 85, 27.7),
            ("60 mm - 180 mm", "N/A (20 mm)", 35, 44.6),

            ("0 mm - 10 mm", "N/A (40 mm)", 100, 15.0),
            ("0 mm - 10 mm", "N/A (40 mm)", 80, 18.0),
            ("0 mm - 10 mm", "N/A (40 mm)", 60, 21.4),
            ("0 mm - 10 mm", "N/A (40 mm)", 40, 26.2),
            ("0 mm - 10 mm", "N/A (40 mm)", 15, 33.4),
            ("0 mm - 10 mm", "N/A (40 mm)", 90, 16.7),
            ("0 mm - 10 mm", "N/A (40 mm)", 50, 23.8),

            ("10 mm - 30 mm", "N/A (40 mm)", 100, 16.9),
            ("10 mm - 30 mm", "N/A (40 mm)", 80, 19.2),
            ("10 mm - 30 mm", "N/A (40 mm)", 60, 22.7),
            ("10 mm - 30 mm", "N/A (40 mm)", 40, 28.0),
            ("10 mm - 30 mm", "N/A (40 mm)", 15, 35.1),
            ("10 mm - 30 mm", "N/A (40 mm)", 20, 33.5),
            ("10 mm - 30 mm", "N/A (40 mm)", 90, 17.9),

            ("30 mm - 60 mm", "N/A (40 mm)", 100, 18.9),
            ("30 mm - 60 mm", "N/A (40 mm)", 80, 21.8),
            ("30 mm - 60 mm", "N/A (40 mm)", 60, 25.9),
            ("30 mm - 60 mm", "N/A (40 mm)", 40, 32.1),
            ("30 mm - 60 mm", "N/A (40 mm)", 15, 39.5),
            ("30 mm - 60 mm", "N/A (40 mm)", 55, 27.7),
            ("30 mm - 60 mm", "N/A (40 mm)", 90, 20.2),

            ("60 mm - 180 mm", "N/A (40 mm)", 100, 21.8),
            ("60 mm - 180 mm", "N/A (40 mm)", 80, 25.5),
            ("60 mm - 180 mm", "N/A (40 mm)", 60, 30.0),
            ("60 mm - 180 mm", "N/A (40 mm)", 40, 36.9),
            ("60 mm - 180 mm", "N/A (40 mm)", 15, 46.4),
            ("60 mm - 180 mm", "N/A (40 mm)", 50, 33.6),
            ("60 mm - 180 mm", "N/A (40 mm)", 20, 44.3),
        ]

        for slump_range, nms, passing_600, fine_content_ssd_expected in test_cases:
            with self.subTest(passing_600=passing_600, slump_range=slump_range, nms=nms):
                fine_content_ssd = self.fine_agg.fine_content(passing_600, w_cm, slump_range, nms, total_agg_content)
                self.assertAlmostEqual(fine_content_ssd, fine_content_ssd_expected, delta=0.35)

class TestCoarseAggregate(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
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
        self.coarse_agg.doe_data_model = self.doe_data_model

    def test_coarse_content(self):
        test_cases = [
            (1970, 335, 1635),
            (1845, 405, 1440),
            (1900, 515, 1385),
            (1985, 0, 1985),
            (1450, 1450, 0),
        ]

        for total_agg_content,  fine_content_ssd, coarse_content_expected in test_cases:
            with self.subTest(total_agg_content=total_agg_content, fine_content_ssd=fine_content_ssd):
                coarse_content = self.coarse_agg.coarse_content(total_agg_content, fine_content_ssd)
                self.assertEqual(coarse_content, coarse_content_expected)

class TestStandardDeviation(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.std_dev = StandardDeviation(
            std_dev_known=True,
            std_dev_value=2.5,
            sample_size=20,
            defective_level="",
            std_dev_unknown=False,
            user_defined_margin=0
        )
        self.std_dev.doe_data_model = self.doe_data_model

    def test_target_strength_with_std_dev_known(self):
        std_dev_known = True
        std_dev_unknown = False
        entrained_air_content = 0
        user_defined_margin = 0
        test_cases = [
            ('5', 10, 4, 21, 16.58),
            ('5', 15, 3, 25, 19.935),
            ('5', 5, 0.5, 30, 6.645),
            ('5', 40, 2, 40, 46.58),
            ('5', 10, 5, 10, 18.225),
            ('5', 15, 3, 5, 24.87),
            ('5', 30, 5, 15, 43.16),

            ('1', 30, 3.5, 10, 48.608),
            ('3', 20, 7, 15, 35.048),
            ('8', 55, 5, 20, 62.025),
            ('20', 35, 1.5, 25, 38.368),
            ('25', 40, 2, 30, 42.696),
        ]

        for defective_level, design_strength, std_dev_value, sample_size, target_strength_expected in test_cases:
            with self.subTest(defective_level=defective_level, design_strength=design_strength, sample_size=sample_size):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown,
                                                               user_defined_margin, entrained_air_content)
                self.assertAlmostEqual(target_strength, target_strength_expected)

    def test_target_strength_with_std_dev_unknown(self):
        std_dev_known = False
        std_dev_unknown = True
        defective_level = '5'
        std_dev_value = 0
        sample_size = 15
        entrained_air_content = 0
        test_cases = [
            (20, 45, 65),
            (25, 25, 50),
            (30, 85, 115),
        ]

        for design_strength, user_defined_margin, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown,
                                                               user_defined_margin, entrained_air_content)
                self.assertEqual(target_strength, target_strength_expected)

    def test_target_strength_with_entrained_air(self):
        std_dev_known = False
        std_dev_unknown = True
        defective_level = '5'
        std_dev_value = 0
        sample_size = 15
        test_cases = [
            (20, 45, 0.045, 86.3787),
            (25, 25, 0.015, 54.4959),
            (30, 85, 0.070, 186.9919),
        ]

        for design_strength, user_defined_margin, entrained_air_content, target_strength_expected in test_cases:
            with self.subTest(design_strength=design_strength):
                target_strength = self.std_dev.target_strength(design_strength, std_dev_known, std_dev_value,
                                                               sample_size, defective_level, std_dev_unknown,
                                                               user_defined_margin, entrained_air_content)
                self.assertAlmostEqual(target_strength, target_strength_expected, delta=0.0001)

class TestAbramsLaw(unittest.TestCase):
    def setUp(self):
        self.doe_data_model = DOEDataModel()
        self.abrams_law = AbramsLaw()
        self.abrams_law.doe_data_model = self.doe_data_model

    def test_water_cementitious_materials_ratio_without_exposure_classes(self):
        exposure_classes = ['N/A', 'N/A', 'N/A', 'N/A']
        scm_checked = False
        test_cases = [
            ("42.5", ("No triturada", "No triturada"), 30, "3 días", 0.424),
            ("42.5", ("No triturada", "No triturada"), 40, "7 días", 0.422),
            ("42.5", ("No triturada", "No triturada"), 50, "28 días", 0.439),
            ("42.5", ("No triturada", "No triturada"), 60, "91 días", 0.421),
            ("42.5", ("Triturada", "Triturada"), 40, "3 días", 0.393),
            ("42.5", ("Triturada", "Triturada"), 50, "7 días", 0.391),
            ("42.5", ("Triturada", "Triturada"), 60, "28 días", 0.420),
            ("42.5", ("Triturada", "Triturada"), 70, "91 días", 0.400),

            ("52.5", ("No triturada", "No triturada"), 30, "3 días", 0.492),
            ("52.5", ("No triturada", "No triturada"), 40, "7 días", 0.474),
            ("52.5", ("No triturada", "No triturada"), 50, "28 días", 0.489),
            ("52.5", ("No triturada", "No triturada"), 60, "91 días", 0.450),
            ("52.5", ("Triturada", "Triturada"), 50, "3 días", 0.379),
            ("52.5", ("Triturada", "Triturada"), 60, "7 días", 0.380),
            ("52.5", ("Triturada", "Triturada"), 70, "28 días", 0.388),
            ("52.5", ("Triturada", "Triturada"), 80, "91 días", 0.368),
        ]

        for cement_class, agg_types, target_strength, target_strength_time, w_cm_expected in test_cases:
            with self.subTest(cement_class=cement_class, agg_types=agg_types, target_strength=target_strength):
                water_cementitious_materials_ratio = self.abrams_law.water_cementitious_materials_ratio(cement_class,
                                                                                                        agg_types,
                                                                                                        target_strength,
                                                                                                        target_strength_time,
                                                                                                        exposure_classes,
                                                                                                        scm_checked)
                self.assertAlmostEqual(water_cementitious_materials_ratio, w_cm_expected, delta=0.005)

    def test_water_cementitious_materials_ratio_with_exposure_classes(self):
        cement_class = "52.5"
        agg_types = ("No triturada", "No triturada")
        target_strength = 30
        target_strength_time = "28 días"
        scm_checked = False
        test_cases = [
            (['XC1', 'N/A', 'N/A', 'N/A'], 0.65),
            (['XC2', 'N/A', 'N/A', 'N/A'], 0.60),
            (['XC3', 'N/A', 'N/A', 'N/A'], 0.55),
            (['XC4', 'N/A', 'N/A', 'N/A'], 0.50),

            (['N/A', 'XS1', 'N/A', 'N/A'], 0.50),
            (['N/A', 'XS2', 'N/A', 'N/A'], 0.45),
            (['N/A', 'XS3', 'N/A', 'N/A'], 0.45),
            (['N/A', 'XD1', 'N/A', 'N/A'], 0.55),
            (['N/A', 'XD2', 'N/A', 'N/A'], 0.55),
            (['N/A', 'XD3', 'N/A', 'N/A'], 0.45),

            (['N/A', 'N/A', 'XF1', 'N/A'], 0.55),
            (['N/A', 'N/A', 'XF2', 'N/A'], 0.55),
            (['N/A', 'N/A', 'XF3', 'N/A'], 0.50),
            (['N/A', 'N/A', 'XF4', 'N/A'], 0.45),

            (['N/A', 'N/A', 'N/A', 'XA1'], 0.55),
            (['N/A', 'N/A', 'N/A', 'XA2'], 0.50),
            (['N/A', 'N/A', 'N/A', 'XA3'], 0.45),

            (['XC4', 'XD1', 'XF3', 'XA3'], 0.45),
            (['XC1', 'XS2', 'XF2', 'XA2'], 0.45),
            (['XC4', 'XD3', 'XF4', 'XA3'], 0.45),
        ]

        for exposure_classes, w_cm_expected in test_cases:
            with self.subTest(exposure_classes=exposure_classes):
                water_cementitious_materials_ratio = self.abrams_law.water_cementitious_materials_ratio(cement_class,
                                                                                                        agg_types,
                                                                                                        target_strength,
                                                                                                        target_strength_time,
                                                                                                        exposure_classes,
                                                                                                        scm_checked)
                self.assertEqual(water_cementitious_materials_ratio, w_cm_expected)

##############################################
# Run all the tests
##############################################
if __name__ == '__main__':
    unittest.main()