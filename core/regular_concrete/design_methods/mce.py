import re
from dataclasses import dataclass, field
from math import log10

from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from logger import Logger
from settings import (COMBINED_GRADING, CEMENT_FACTOR_1, CEMENT_FACTOR_2, MIN_CEMENT_MCE, K_FACTOR, QUARTILES, CONSTANTS,
                      ALFA_FACTOR_1, ALFA_FACTOR_2, MAX_W_C_MCE, CONVERSION_FACTORS)


# ------------------------------------------------ Class for materials ------------------------------------------------
@dataclass
class CementitiousMaterial:
    relative_density: float
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def absolute_volume(self, content, water_density, relative_density, cementitious_type=None):
        """
        Calculate the absolute volume of a cementitious material in cubic meters (m³).

        The cementitious material content and water density must use consistent units:
        - If the cementitious material content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If the cementitious material content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float content: Cementitious material content (kg or kgf).
        :param float water_density: Water density (kg/m³ or kgf/m³).
        :param float relative_density: Relative density of cementitious material.
        :param str cementitious_type: Type of cementitious material (e.g., 'Cement', 'SCM').
        :return: The absolute volume (in m³).
        :rtype: float
        """

        if water_density == 0 or relative_density == 0:
            error_msg = (f"The relative density of {cementitious_type} is {relative_density}. "
                         f"The water density is {water_density}. None can be zero")
            self.mce_data_model.add_calculation_error('Cementitious volume', error_msg)
            raise ZeroDivisionError(error_msg)
        return content / (relative_density * water_density)

@dataclass
class Cement(CementitiousMaterial):

    def cement_content(self, slump, alpha, nms, agg_types, exposure_classes, k=117.2, n=0.16, m=1.3, theta=None,
                       wra_checked=False, wra_action_cement_economizer=False, wra_action_water_reducer=False,
                       effectiveness=None):
        """
        Calculate the cement content in kilogram-force per cubic meter of mixture (kgf/m³) using the triangular_relationship.
        The parameters k, n, m are constants that depend on the characteristics of the component materials of
        the mixture and the conditions under which it is prepared.

        If a WRA is used as a cement economizer, there will be a reduction in the cement content according to
        the effectiveness of the admixture. For this purpose, a fictitious alpha (water-cement ratio) is used.

        If a WRA is used as a pure water reducer, the actual water-cement ratio (reduced alpha) will be lower.
        However, for cement content calculations within this scope, the original water-cement ratio (original alpha),
        unaffected by the WRA, is used. To obtain original alpha, divide reduced alpha by (1−WRA_effectiveness).

        :param int slump: The required slump of the concrete in fresh state (in mm).
        :param float alpha: The ratio of water to cement used.
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param tuple[str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                                     (e.g., ("Triturado", "Natural")).
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['Agua dulce', 'Moderada', 'Despreciable', 'Atmósfera común']).
        :param float k: Constant (default 117.2).
        :param float n: Constant (default 0.16).
        :param float m: Constant (default 1.3).
        :param float theta: A constant used to modify the triangular relationship,
                            this value will be specific to the particular materials, design and slump (if provided).
        :param bool wra_checked: True if a water-reducing admixture is used, otherwise False.
        :param bool wra_action_cement_economizer: True if a water-reducing admixture is used as a cement economizer,
                                                  otherwise False.
        :param bool wra_action_water_reducer: True if a water-reducing admixture is used as a pure water reducer,
                                              otherwise False.
        :param float effectiveness: WRA effectiveness percentage.
        :return: The calculated cement content in kilogram-force per cubic meter (kgf/m³).
        :rtype: float
        """

        # Convert slump to centimeters
        slump = 0.1 * slump

        # Use a fictitious alpha if a WRA is used as a cement economizer
        if wra_checked and wra_action_cement_economizer:
            alpha = alpha / (1 - effectiveness / 100)
            self.mce_data_model.update_data('cementitious_material.cement.fictitious_alpha', alpha)

        # Use the original alpha if a WRA is used as a pure water reducer
        elif wra_checked and wra_action_water_reducer:
            alpha = alpha / (1 - effectiveness / 100)

        if theta is None or theta <= 0:
            # Calculate the design cement content
            design_cement_content = k * slump ** n * alpha ** (-m)

            if nms is None:
                error_msg = f'The nominal maximum size is {nms}. It cannot be None'
                self.mce_data_model.add_calculation_error('Cement content', error_msg)
                raise ValueError(error_msg)

            # Retrieve correction factors from settings
            correction_factor_1 = CEMENT_FACTOR_1.get(nms, 0) # according to the nominal maximum size
            correction_factor_2 = CEMENT_FACTOR_2.get(agg_types[0], {}).get(agg_types[1], 0) # according to aggregate type

            if correction_factor_1 == 0:
                error_msg = (f"The NMS correction was not possible. No factor correction for {nms}. "
                             f"Valid NMS values are: {list(CEMENT_FACTOR_1.keys())}")
                self.mce_data_model.add_calculation_error('Cement content', error_msg)
                raise ValueError(error_msg)
            if correction_factor_2 == 0:
                error_msg = f"The aggregate type correction was not possible. No factor correction for aggregate types -> {agg_types}"
                self.mce_data_model.add_calculation_error('Cement content', error_msg)
                raise ValueError(error_msg)

            # Calculate corrected cement content
            corrected_cement_content = correction_factor_1 * correction_factor_2 * design_cement_content

            # Determine minimum cement content based on exposure classes
            min_cement_content = [MIN_CEMENT_MCE.get(exposure_class, 0) for exposure_class in exposure_classes]
            min_cement_content = max(min_cement_content)

            # The final cement content is the maximum between the corrected cement content and the maximum cement content
            cement_content = max(corrected_cement_content, min_cement_content)

            # Store intermediate calculation results in the MCE data model for reference
            self.mce_data_model.update_data('cementitious_material.cement.design_cement_content',
                                            design_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.correction_factor_1',
                                            correction_factor_1)
            self.mce_data_model.update_data('cementitious_material.cement.correction_factor_2',
                                            correction_factor_2)
            self.mce_data_model.update_data('cementitious_material.cement.corrected_cement_content',
                                            corrected_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.min_cement_content',
                                            min_cement_content)
        else:
            # When theta is provided, use a different relationship
            design_cement_content = theta * alpha ** (-m)

            # Determine minimum cement content based on exposure classes
            min_cement_content = [MIN_CEMENT_MCE.get(exposure_class, 0) for exposure_class in exposure_classes]
            min_cement_content = max(min_cement_content)

            # The final cement content is the maximum between the design cement content and the maximum cement content
            cement_content = max(design_cement_content, min_cement_content)

            # Update only the available values in the MCE data model.
            self.mce_data_model.update_data('cementitious_material.cement.design_cement_content',
                                            design_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.min_cement_content',
                                            min_cement_content)

        return cement_content

@dataclass
class Water:
    density: float
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def water_volume(self, water_content, density):
        """
        Calculate the volume of water in cubic meter (m³). For water, the absolute volume and total volume are the same.

        The water content and density must use consistent units:
        - If water content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If water content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float water_content: The content of water (kg or kgf).
        :param float density: The water density (kg/m³ or kgf/m³).
        :return: The absolute volume of water (in m³).
        :rtype: float
        """

        if density == 0:
            error_msg = f'The density is {density}. It cannot be zero'
            self.mce_data_model.add_calculation_error('Water volume', error_msg)
            raise ValueError(error_msg)

        return water_content / density

    @staticmethod
    def water_content(cement_content, alpha):
        """
        Calculate the content of water in kilogram-force per cubic meter (kgf/m³).

        :param float cement_content: The cement content in kilogram-force per cubic meter (kgf/m³).
        :param float alpha: The water-cement ratio.
        :return: The water weight (in kgf/m³).
        :rtype: float
        """

        return cement_content * alpha

    @staticmethod
    def water_content_correction(water_content, fine_content_ssd, fine_content_wet, coarse_content_ssd,
                                 coarse_content_wet):
        """
        Calculate the corrected water content for a mixture by accounting for both free water and aggregate absorption.

        This function adjusts the measured free water content by incorporating the differences between
        the saturated surface-dry (SSD) and wet conditions for both fine and coarse aggregates.

        :param float water_content: The measured free water content in the mixture.
        :param float fine_content_ssd: The fine aggregate content measured under SSD conditions.
        :param float fine_content_wet: The fine aggregate content measured under wet conditions.
        :param float coarse_content_ssd: The coarse aggregate content measured under SSD conditions.
        :param float coarse_content_wet: The coarse aggregate content measured under wet conditions.
        :return: The corrected water content.
        :rtype: float
        """

        return water_content + (fine_content_ssd - fine_content_wet) + (coarse_content_ssd - coarse_content_wet)

@dataclass
class Air:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def entrapped_air_volume(self, nms, cement_content):
        """
        Calculate the entrapped air in cubic meter (m³).

        :param str nms: The nominal maximum size of the coarse aggregate (e.g., '2-1/2" (63 mm)').
        :param float cement_content: The cement content in kgf/m³.
        :return: The entrapped air volumen in cubic meter (m³).
        :rtype: float
        """

        # Extract the size between parenthesis in the NMS
        # This regex captures a number (with comma or dot) inside parentheses before "mm".
        match = re.search(r'\(.*?(\d+([,.]\d+)?)', nms)
        if match:
            nms_mm = match.group(1).replace(',', '.')
            nms_mm = float(nms_mm)
            return 0.001 * (cement_content / nms_mm)
        else:
            error_msg = f'No match found for nominal maximum size: {nms}'
            self.mce_data_model.add_calculation_error('Entrapped air volumen', error_msg)
            raise Exception(error_msg)

@dataclass
class Aggregate:
    agg_type: str
    relative_density: float
    loose_bulk_density: float
    compacted_bulk_density: float
    moisture_content: float
    moisture_absorption: float
    grading: dict
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    @staticmethod
    def fill_all_sieves(grading):
        """
        Fill a base dictionary with all available sieves using values from the provided grading dictionary.
        If a sieve is not present, its value remains None.
        Then, based on the available numeric values, for sieves before the one with the maximum value,
        assign 100; for those after the one with the minimum value, assign 0.

        :param dict[str, float | None] grading: A dictionary with the passing percentages for certain sieves.
        :return: A dictionary with all passing percentages for all the available sieves.
        :rtype: dict[str, float | None]
        """

        # Dictionary with all the available sieves
        all_sieves = {
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': None,
            '1/4" (6,3 mm)': None,
            'No. 4 (4,75 mm)': None,
            'No. 8 (2,36 mm)': None,
            'No. 16 (1,18 mm)': None,
            'No. 30 (0,600 mm)': None,
            'No. 50 (0,300 mm)': None,
            'No. 100 (0,150 mm)': None
        }

        # Fill the "all sieves" dictionary with all values from the given dictionary (if there is a key match)
        for key in grading:
            if key in all_sieves:
                all_sieves[key] = grading[key]

        # Get the list of keys to maintain insertion order
        keys_list = list(all_sieves.keys())

        # Extract (index, value) from the keys that have a numeric value (ignoring "None")
        numeric_values = [(i, all_sieves[key]) for i, key in enumerate(keys_list) if all_sieves[key] is not None]

        if numeric_values:
            # Find the index with the maximum value and the index with the minimum value
            max_index, max_value = max(numeric_values, key=lambda x: x[1])
            min_index, min_value = min(numeric_values, key=lambda x: x[1])
        else:
            max_index = min_index = None

        # From the key associated with the maximum value upwards (to the first key) we assign 100
        if max_index is not None:
            for i in range(0, max_index):
                key = keys_list[i]
                all_sieves[key] = 100.0

        # From the key associated with the minimum value downwards (to the last key) we assign 0
        if min_index is not None:
            for i in range(min_index + 1, len(keys_list)):
                key = keys_list[i]
                all_sieves[key] = 0.0

        return all_sieves

    def apparent_volume(self, content, loose_bulk_density, aggregate_type="aggregate"):
        """
        Calculate the apparent volume (in liters) of the aggregate given its content and loose bulk density.
        The "apparent" volume includes the volume of the aggregate particles and the voids between them.

        The aggregate content and loose bulk density must use consistent units:
        - If aggregate content is in kilograms (kg), loose bulk density must be in kilograms per cubic meter (kg/m³).
        - If aggregate content is in kilogram-force (kgf), loose bulk density must be in kilogram-force per cubic meter (kgf/m³).

        The function converts the calculated volume from cubic meters (m³) to liters (L).

        :param float content: The aggregate content (kg or kgf).
        :param float loose_bulk_density: The loose bulk density (kg/m³) or loose unit weight (kgf/m³) of the aggregate.
        :param str aggregate_type: The type of aggregate, for identification (e.g., 'fine' or 'coarse').
        :return: The apparent volume (in liters).
        :rtype: float
        """

        if loose_bulk_density == 0:
            error_msg = f"The loose bulk density of the {aggregate_type} aggregate cannot be zero"
            self.mce_data_model.add_calculation_error(f"{aggregate_type} apparent volumen", error_msg)
            raise ZeroDivisionError(error_msg)

        liters_per_cubic_meter = 1000
        # The loose bulk density is in kg/m³, so it is converted to kg/(L) by dividing by 1000
        return content / (loose_bulk_density / liters_per_cubic_meter)

    def absolute_volume(self, content, water_density, relative_density, aggregate_type="aggregate"):
        """
        Calculate the absolute volume (in m³) of the aggregate given its content, water density and relative density.

        The aggregate content and water density must use consistent units:
        - If aggregate content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If aggregate content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float content: The aggregate content (kg or kgf).
        :param float water_density: Water density (kg/m³ or kgf/m³).
        :param float relative_density: The relative density of the aggregate.
        :param str aggregate_type: The type of aggregate, for identification (e.g., 'fine' or 'coarse').
        :return: The absolute volume (in m³).
        :rtype: float
        """

        if water_density == 0 or relative_density == 0:
            error_msg = f"The relative density ({relative_density}) or the water density ({water_density}) cannot be zero"
            self.mce_data_model.add_calculation_error(f"{aggregate_type} absolute volume", error_msg)
            raise ZeroDivisionError(error_msg)
        return content / (relative_density * water_density)

    def content_moisture_correction(self, ssd_content, moisture_content, absorption):
        """
        Adjust the aggregate content from an SSD (saturated surface-dry) condition to a wet condition.

        This function converts the aggregate content measured under SSD conditions to its equivalent
        wet condition value. The adjustment accounts for the moisture content and absorption capacity
        of the aggregate. Both the moisture content and absorption should be provided as percentages
        (e.g., 2 for 2%).

        :param float ssd_content: Aggregate content under SSD conditions.
        :param float moisture_content: Moisture content of the aggregate as a percentage.
        :param float absorption: Absorption capacity of the aggregate as a percentage.
        :return: Adjusted aggregate content under wet conditions.
        :rtype: float
        """

        denominator = 100 + absorption
        if denominator == 0:
            error_msg = f"Invalid absorption value: {absorption}"
            self.mce_data_model.add_calculation_error('Aggregate moisture correction', error_msg)
            raise ValueError(error_msg)

        return ssd_content * ((100 + moisture_content) / denominator)

@dataclass
class FineAggregate(Aggregate):
    fineness_modulus: float = None

    def fine_content(self, entrapped_air_volume, cement_abs_volume, water_volume, water_density, fine_relative_density,
                     coarse_relative_density, beta_value):
        """
        Calculate the fine content in kilogram-force per cubic meter (kgf/m³).

        The formula calculates the fine aggregate content by subtracting the volumes of
        entrapped air, cement, and water (in m³) from 1 m³ (total volume of the mixture), then dividing by
        an expression that involves the relative densities and beta relationship.

        :param float entrapped_air_volume: Volume of entrapped air (m³).
        :param float cement_abs_volume: Absolute volume of cement (m³).
        :param float water_volume: Volume of water (m³).
        :param float water_density: Water density (kg/m³).
        :param float fine_relative_density: Fine aggregate relative density (SSD).
        :param float coarse_relative_density: Coarse aggregate relative density (SSD).
        :param float beta_value: Beta relationship factor.
        :return: Fine aggregate content (kgf/m³).
        :rtype: float
        """

        # Validate to avoid division by zero
        if fine_relative_density == 0:
            error_msg = f'The relative density of the fine aggregate is {fine_relative_density}. It cannot be zero'
            self.mce_data_model.add_calculation_error('Fine aggregate content', error_msg)
            raise ValueError(error_msg)
        if beta_value == 0:
            error_msg = f'The beta value is {beta_value}. It cannot be zero'
            self.mce_data_model.add_calculation_error('Fine aggregate content', error_msg)
            raise ValueError(error_msg)
        if coarse_relative_density == 0:
            error_msg = f'The relative density of the coarse aggregate is {coarse_relative_density}. It cannot be zero'
            self.mce_data_model.add_calculation_error('Fine aggregate content', error_msg)
            raise ValueError(error_msg)

        # Calculate numerator
        numerator = 1 - (entrapped_air_volume + cement_abs_volume + water_volume)

        # Calculate denominator
        denominator = (1 / water_density) * (
                    (1 / fine_relative_density) + (1 / coarse_relative_density) * ((1 / beta_value) - 1))

        # Return the computed fine aggregate content
        return numerator / denominator

@dataclass
class CoarseAggregate(Aggregate):
    nominal_max_size: str

    def coarse_content(self, fine_content, beta_value):
        """
        Calculate the coarse content in kilogram-force per cubic meter (kgf/m³).
        It is based on the fine aggregate content and beta value.

        :param float fine_content: Fine aggregate content (kgf/m³).
        :param float beta_value: Beta relationship factor.
        :return: Coarse aggregate content (kgf/m³).
        :rtype: float
        """

        if beta_value == 0:
            error_msg = f'The beta value is {beta_value}. It cannot be zero'
            self.mce_data_model.add_calculation_error('Coarse aggregate content', error_msg)
            raise ValueError(error_msg)

        inverse_beta = 1 / beta_value
        result = fine_content * (inverse_beta - 1)
        return result

@dataclass
class FreshConcrete:
    slump: int

@dataclass
class HardenedConcrete:
    design_strength: int
    spec_strength_time: str
    exposure_classes: dict

@dataclass
class StandardDeviation:
    std_dev_known: bool
    std_dev_value: float
    sample_size: int
    defective_level: str
    std_dev_unknown: bool
    quality_control: str
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def target_strength(self, design_strength, std_dev_known, std_dev_value, sample_size, defective_level,
                        std_dev_unknown, quality_control):
        """
        Calculate the target (or required average compressive) strength based on design strength and variability parameters.

        For std_dev_known == True and sample_size >= 15, it calculates two candidate strengths
        using a k-factor (from sample_size) and a z value (from defective_level), then uses the maximum.
        For std_dev_unknown == True, it uses predefined margins based on design strength ranges and quality control.


        :param int design_strength: The design strength of the concrete in kilogram-force per square centimetre (kgf/cm^2).
        :param bool std_dev_known: True if the standard deviation is known.
        :param float std_dev_value: The value of the standard deviation in kilogram-force per square centimetre (kgf/cm^2).
        :param int sample_size: The number of samples.
        :param str defective_level: The defective level key (used to obtain z value).
        :param bool std_dev_unknown: True if the standard deviation is unknown.
        :param str quality_control: A string indicating the level of quality control
                                    ("Excelente", "Aceptable", "Sin control").
        :return: The target strength (in kgf/cm^2).
        :rtype: float
        """

        # Case 1: The standard deviation is known and the sample size is greater than or equal to 15
        if std_dev_known and sample_size >= 15:
            k = K_FACTOR.get(sample_size, 1.00)  # Get k-factor based on sample size
            z = QUARTILES.get(defective_level)  # Get z value (quartile) based on defective level

            if design_strength <= 350:
                f_cr_1 = design_strength - z * k * std_dev_value
                f_cr_2 = design_strength - (z - 1) * k * std_dev_value - 35
            else:  # design_strength > 350
                f_cr_1 = design_strength - z * k * std_dev_value
                f_cr_2 = 0.9 * design_strength - (z - 1) * k * std_dev_value

            f_cr = max(f_cr_1, f_cr_2)

            # Update the MCE data model with intermediate values
            self.mce_data_model.update_data('spec_strength.target_strength.k_factor', k)
            self.mce_data_model.update_data('spec_strength.target_strength.z_value', z)
            self.mce_data_model.update_data('spec_strength.target_strength.f_cr_1', f_cr_1)
            self.mce_data_model.update_data('spec_strength.target_strength.f_cr_2', f_cr_2)

        # Case 2: The standard deviation is unknown
        elif std_dev_unknown:
            margin = None
            if design_strength < 210:
                if quality_control == 'Excelente':
                    margin = 45
                elif quality_control == 'Aceptable':
                    margin = 80
                elif quality_control == 'Sin control':
                    margin = 130
            elif 210 <= design_strength <= 350:
                if quality_control == 'Excelente':
                    margin = 60
                elif quality_control == 'Aceptable':
                    margin = 95
                elif quality_control == 'Sin control':
                    margin = 170
            elif design_strength > 350:
                if quality_control == 'Excelente':
                    margin = 75
                elif quality_control == 'Aceptable':
                    margin = 110
                elif quality_control == 'Sin control':
                    margin = 210

            # Update the data model for the margin
            if margin is not None:
                self.mce_data_model.update_data('spec_strength.target_strength.margin', margin)
                f_cr = design_strength + margin
            else:
                # If no margin was assigned, raises a value error exception
                error_msg = f"No margin found for the design strength: {design_strength}"
                self.mce_data_model.add_calculation_error('Target strength', error_msg)
                raise ValueError(error_msg)

        else:
            # If no condition is met, raises a value error exception
            error_msg = f"The 'std_dev_known' and 'std_dev_unknown' values are {std_dev_known} and {std_dev_unknown} respectively"
            self.mce_data_model.add_calculation_error('Target strength', error_msg)
            raise ValueError(error_msg)

        return f_cr

@dataclass
class Beta:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    @staticmethod
    def remove_unused_sieves(coarse_grading, fine_grading):
        """
        Remove keys with a None value from both coarse_grading and fine_grading.
        If a key has a None value in either dictionary, it will be removed from both.

        :param dict[str, int | float | None] coarse_grading: A dictionary with the passing percentages
                                                             for all sieves except those not used.
        :param dict[str, int | float | None] fine_grading: A dictionary with the passing percentages
                                                           for all sieves except those not used.
        :return: A tuple containing the cleaned coarse_grading and fine_grading dictionaries.
        :rtype: tuple[dict[str, float], dict[str, float]]
        """

        # Create copies to avoid modifying original dictionaries
        coarse_cleaned = coarse_grading.copy()
        fine_cleaned = fine_grading.copy()

        # Create a set of keys to remove (keys with None in either dictionary)
        keys_to_remove = {k for k, v in coarse_grading.items() if v is None} | {k for k, v in fine_grading.items() if
                                                                                v is None}

        # Remove keys from the copies
        for key in keys_to_remove:
            coarse_cleaned.pop(key, None)
            fine_cleaned.pop(key, None)

        return coarse_cleaned, fine_cleaned

    def get_beta(self, nms, coarse_data, fine_data):
        """
        Calculate beta values (minimum and maximum) based on the grading limits and sieve data.

        If the given nominal maximum size has no grading limits, raises a value error exception.

        If the fine and coarse values are equal:
            - If they are either 0 or 100, that sieve is skipped.
            - If the value is not equal to either the minimum or maximum recommended percentages,
              the function raises a value error exception.

        Otherwise, a slope is calculated to obtain a linear equation of two points. The beta values
        are clamped between 0 and 100, and the maximum beta_min and minimum beta_max across all sieves are returned.

        :param str nms: Nominal maximum size to retrieve grading limits.
        :param dict[str, float | None] coarse_data: Data for coarse grading.
        :param dict[str, float | None] fine_data: Data for fine grading.
        :return: A tuple containing the minimum and maximum beta values, respectively.
        :rtype: tuple[float, float]
        """

        # Retrieve the recommended grading limits for the given nominal maximum size
        grading_limits = COMBINED_GRADING.get(nms)
        if grading_limits is None:
            error_msg = (f"No se encontraron límites granulométricos para el TMN: {nms}. "
                         f"Límites granulométricos disponibles para los siguientes TMN: {list(COMBINED_GRADING.keys())}")
            self.mce_data_model.add_calculation_error('Cálculo de Beta', error_msg)
            raise ValueError(error_msg)

        # Clean any unused sieves from the grading
        coarse_grading, fine_grading = self.remove_unused_sieves(coarse_data, fine_data)

        beta_mins = []
        beta_maxs = []

        for sieve, limits in grading_limits.items():
            # if a limit for a sieve is empty or exists but the measured data does not use that sieve, skip it.
            if limits is None or fine_grading.get(sieve) is None or coarse_grading.get(sieve) is None:
                continue

            # Unpack recommended percentages (expected format -> (maximum value, minimum value))
            percentage_max, percentage_min = limits

            fine_value = fine_grading.get(sieve)
            coarse_value = coarse_grading.get(sieve)

            # If fine and coarse values are equal
            if fine_value == coarse_value:
                if fine_value in (0, 100):
                    # Skip if values are at the boundary
                    continue
                elif fine_value not in (percentage_max, percentage_min):
                    # If value does not match expected limits, raises a value error exception
                    error_msg = "La granulometría dada no coincide con ninguno de los límites recomendados."
                    self.mce_data_model.add_calculation_error('Cálculo de Beta', error_msg)
                    raise ValueError(error_msg)
            else:
                # Calculate the slope of a two-point linear equation
                slope = 100 / (fine_value - coarse_value)
                beta_min = (percentage_min - fine_value) * slope + 100
                beta_max = (percentage_max - fine_value) * slope + 100

                # Clamp the beta values between 0 and 100
                beta_min = max(0, beta_min)
                beta_max = min(100, beta_max)

                beta_mins.append(beta_min)
                beta_maxs.append(beta_max)

        if not beta_mins or not beta_maxs:
            error_msg = f"Granulometría vacía o incompleta."
            self.mce_data_model.add_calculation_error('Cálculo de Beta', error_msg)
            raise ValueError(error_msg)

        # Return the maximum of beta_mins and the minimum of beta_maxs if computed, else raises a value error exception
        if max(beta_mins) <= min(beta_maxs):
            self.mce_data_model.update_data('beta.beta_min', max(beta_mins))
            self.mce_data_model.update_data('beta.beta_max', min(beta_maxs))
            return max(beta_mins), min(beta_maxs)
        else:
            error_msg = (f"El conjunto calculado no es posible. "
                         f"El beta mínimo ({max(beta_mins)}) es mayor que el beta máximo ({min(beta_maxs)}).")
            self.mce_data_model.add_calculation_error('Cálculo de Beta', error_msg)
            raise ValueError(error_msg)

@dataclass
class AbramsLaw:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def water_cement_ratio(self, target_strength, target_strength_time, nms, agg_types, exposure_classes,
                           wra_checked=False, wra_action_water_reducer=False, effectiveness=None, m=None, n=None):
        """
        Calculate the water-cement ratio. The parameters m and n are constants that depend on the age of test,
        the characteristics of the component materials of the mixture and the way the mixture is made.

        If a WRA is used as a pure water reducer, there will be a reduction in the w/c ratio
        according to the effectiveness of the admixture.

        :param float target_strength: The target strength of the mixture design.
        :param str target_strength_time: The expected time to reach the target strength,
                                         also known as the age of the test (e.g., "7 días", "27 días", "90 días").
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param tuple[str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                                     (e.g., ("Triturado", "Natural")).
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['Agua dulce', 'Moderada', 'Despreciable', 'Atmósfera común']).
        :param bool wra_checked: True if a water-reducing admixture is used, otherwise False.
        :param bool wra_action_water_reducer: True if a water-reducing admixture is used as a pure water reducer,
                                              otherwise False.
        :param float effectiveness: WRA effectiveness percentage.
        :param float m: A constant.
        :param float n: A constant.
        :return: The water-cement ratio (also known as alpha).
        :rtype: float
        """

        # In case the correction factors are not applied
        correction_factor_1 = 1
        correction_factor_2 = 1

        # If m and n were not provided, then get the n and m constants for the given age of the test
        if m is None and n is None:
            try:
                n = CONSTANTS.get(target_strength_time, {})["n"]
                m = CONSTANTS.get(target_strength_time, {})["m"]
            except KeyError:
                error_msg = f"No constants found for target strength time: {target_strength_time}"
                self.mce_data_model.add_calculation_error('Water-cement ratio', error_msg)
                raise KeyError(error_msg)

            # Only apply correction factors if m and n were not provided
            correction_factor_1 = ALFA_FACTOR_1.get(nms, 0)  # according to the nominal maximum size
            correction_factor_2 = ALFA_FACTOR_2.get(agg_types[0], {}).get(agg_types[1], 0)  # according to aggregate type

            if correction_factor_1 == 0:
                error_msg = (f"The NMS correction was not possible. No factor correction for {nms}. "
                             f"Valid NMS values are: {list(ALFA_FACTOR_1.keys())}")
                self.mce_data_model.add_calculation_error('Water-cement ratio', error_msg)
                raise ValueError(error_msg)
            if correction_factor_2 == 0:
                error_msg = (f"The aggregate type correction was not possible. "
                             f"No factor correction for aggregate types -> {agg_types}")
                self.mce_data_model.add_calculation_error('Water-cement ratio', error_msg)
                raise ValueError(error_msg)

            # Store correction factors in the data model
            self.mce_data_model.update_data('water_cementitious_materials_ratio.correction_factor_1',
                                            correction_factor_1)
            self.mce_data_model.update_data('water_cementitious_materials_ratio.correction_factor_2',
                                            correction_factor_2)

        # Calculate the alpha according to Abrams' Law
        design_alpha = (log10(m) - log10(target_strength)) / log10(n)

        # Calculate corrected alpha
        corrected_alpha = correction_factor_1 * correction_factor_2 * design_alpha

        # Determine the minimum alpha based on exposure classes
        min_alpha_values = [MAX_W_C_MCE.get(exposure_class, 1) for exposure_class in exposure_classes]
        min_alpha = min(min_alpha_values)

        # The final alpha is the minimum between the corrected alpha and the minimum allowed alpha
        alpha = min(corrected_alpha, min_alpha)

        # Apply a reduction to the final alpha if a WRA is used as a pure water reducer
        if wra_checked and wra_action_water_reducer:
            reduced_alpha = (1 - effectiveness / 100) * alpha
        else:
            reduced_alpha = None

        # Store intermediate calculation results in the MCE data model for reference
        self.mce_data_model.update_data('water_cementitious_materials_ratio.design_alpha', design_alpha)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.corrected_alpha', corrected_alpha)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.min_alpha', min_alpha)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.fina_alpha', alpha)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.reduced_alpha', reduced_alpha)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.m', m)
        self.mce_data_model.update_data('water_cementitious_materials_ratio.n', n)

        return reduced_alpha if wra_checked and wra_action_water_reducer else alpha

@dataclass
class Admixture:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def admixture_content(self, cement_content, dosage):
        """
        Calculate the admixture content in kilograms (kg) based on the total cementitious material and dosage.

        :param cement_content: The total cementitious material in kilograms (kg).
        :param dosage: The admixture dosage as a percentage (%).
        :return: The admixture content in kilograms (kg).
        :rtype: float
        """

        if dosage == 0:
            error_msg = "The admixture dosage cannot be zero"
            self.mce_data_model.add_calculation_error('Admixture content', error_msg)
            raise ZeroDivisionError(error_msg)
        return cement_content * (dosage / 100)

    def admixture_volume(self, content, water_density, relative_density):
        """
        Calculate the (absolute) volume of an admixture in cubic meters (m³).

        :param float content: The admixture content in kilograms (kg).
        :param float water_density: The density of water in kg/m³.
        :param float relative_density: The relative density of the admixture.
        :return: The (absolute) volume of the admixture in cubic meters (m³).
        :rtype: float
        """

        if water_density == 0 or relative_density == 0:
            error_msg = (f"The admixture relative density is {relative_density}. "
                         f"The water density is {water_density}. None can be zero")
            self.mce_data_model.add_calculation_error('Admixture volume', error_msg)
            raise ZeroDivisionError(error_msg)
        return content / (relative_density * water_density)

@dataclass
class WRA(Admixture):
    wra_checked: bool
    wra_action_plasticizer: bool
    wra_action_water_reducer: bool
    wra_action_cement_economizer: bool
    relative_density: float
    dosage: float
    effectiveness: float


# ------------------------------------------------ Main class ------------------------------------------------
class MCE:
    def __init__(self, data_model, mce_data_model):
        """
        Initialize the MCE calculation engine.
        :param data_model: An instance of the data model containing all necessary design data.
        """

        self.data_model: RegularConcreteDataModel = data_model  # Connect to the global data model
        self.mce_data_model: MCEDataModel = mce_data_model # Connect to the MCE data model
        self.logger = Logger(__name__)  # Initialize the logger
        self.logger.info('Calculation mode for the MCE method has initialized')

        # References to material components (they will be created in load_inputs)
        self.cement = None
        self.water = None
        self.air = None
        self.fine_agg = None
        self.coarse_agg = None
        self.fresh_concrete = None
        self.hardened_concrete = None
        self.std_deviation = None
        self.beta = None
        self.abrams_law = None
        self.wra = None

        # Dictionary to store the calculated results for later use in the report.
        self.calculation_results = {}

    def convert_value(self, value, unit):
        """
        Convert the given value from the current unit system to the specified target unit type.
        Conversion is applied only if the current unit system (from the data model) has a defined conversion factor
        for the target unit type (e.g., "stress" -> "kgf/cm^2" or "MPa").

        :param float value: The value to convert.
        :param str unit: The target unit type to convert to (e.g., "stress").
        :return: The converted value if a conversion factor is found, otherwise None.
        :rtype: float | None
        """

        if value is None:
            return None

        # Get the current unit system from the data model, e.g. "MKS" or "SI"
        current_units = self.data_model.units

        # Look up the conversion factor for the current unit system and the target unit
        factor = CONVERSION_FACTORS.get(current_units, {}).get(unit)
        if factor is None:
            # Log a warning if no factor is found
            self.logger.warning(
                f"No conversion factor found for unit system '{current_units}' and target unit '{unit}'")
            return None

        # Return the converted value by multiplying with the factor.
        return value * factor

    def load_inputs(self):
        """
        Load data from the data model and perform unit conversion for selected parameters,
        and instantiates the necessary objects.
        """

        try:
            # Convert units if necessary
            design_strength = self.data_model.get_design_value('field_requirements.strength.spec_strength')
            std_dev_value = self.data_model.get_design_value('field_requirements.strength.std_dev_known.std_dev_value')
            if self.data_model.units == "SI":
                design_strength = self.convert_value(design_strength, "stress")
                std_dev_value = self.convert_value(std_dev_value, "stress")

            # Instantiate the components with their corresponding data
            self.cement = Cement(
                relative_density=self.data_model.get_design_value('cementitious_materials.cement_relative_density')
            )
            self.water = Water(density=self.data_model.get_design_value('water.water_density'))
            self.air = Air()
            self.fine_agg = FineAggregate(
                agg_type=self.data_model.get_design_value("fine_aggregate.info.type"),
                relative_density=self.data_model.get_design_value("fine_aggregate.physical_prop.relative_density_SSD"),
                loose_bulk_density=self.data_model.get_design_value("fine_aggregate.physical_prop.PUS"),
                compacted_bulk_density=self.data_model.get_design_value("fine_aggregate.physical_prop.PUC"),
                moisture_content=self.data_model.get_design_value("fine_aggregate.moisture.moisture_content"),
                moisture_absorption=self.data_model.get_design_value("fine_aggregate.moisture.absorption_content"),
                grading=self.data_model.get_design_value("fine_aggregate.gradation.passing"),
                fineness_modulus=self.data_model.get_design_value("fine_aggregate.fineness_modulus")
            )
            self.coarse_agg = CoarseAggregate(
                agg_type=self.data_model.get_design_value("coarse_aggregate.info.type"),
                relative_density=self.data_model.get_design_value("coarse_aggregate.physical_prop.relative_density_SSD"),
                loose_bulk_density=self.data_model.get_design_value("coarse_aggregate.physical_prop.PUS"),
                compacted_bulk_density=self.data_model.get_design_value("coarse_aggregate.physical_prop.PUC"),
                moisture_content=self.data_model.get_design_value("coarse_aggregate.moisture.moisture_content"),
                moisture_absorption=self.data_model.get_design_value("coarse_aggregate.moisture.absorption_content"),
                grading=self.data_model.get_design_value("coarse_aggregate.gradation.passing"),
                nominal_max_size=self.data_model.get_design_value("coarse_aggregate.NMS")
            )
            self.fresh_concrete = FreshConcrete(slump=self.data_model.get_design_value("field_requirements.slump_value"))
            self.hardened_concrete = HardenedConcrete(
                design_strength=design_strength,
                spec_strength_time=self.data_model.get_design_value("field_requirements.strength.spec_strength_time"),
                exposure_classes=self.data_model.get_design_value("validation.exposure_classes")
            )
            self.std_deviation = StandardDeviation(
                std_dev_known=self.data_model.get_design_value(
                    "field_requirements.strength.std_dev_known.std_dev_known_enabled"),
                std_dev_value=std_dev_value,
                sample_size=self.data_model.get_design_value("field_requirements.strength.std_dev_known.test_nro"),
                defective_level=self.data_model.get_design_value(
                    "field_requirements.strength.std_dev_known.defective_level"),
                std_dev_unknown=self.data_model.get_design_value(
                    "field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled"),
                quality_control=self.data_model.get_design_value(
                    "field_requirements.strength.std_dev_unknown.quality_control")
            )
            self.beta = Beta()
            self.abrams_law = AbramsLaw()
            self.wra = WRA(
                wra_checked=self.data_model.get_design_value('chemical_admixtures.WRA.WRA_checked'),
                wra_action_plasticizer=self.data_model.get_design_value(
                    'chemical_admixtures.WRA.WRA_action.plasticizer'),
                wra_action_water_reducer=self.data_model.get_design_value(
                    'chemical_admixtures.WRA.WRA_action.water_reducer'),
                wra_action_cement_economizer=self.data_model.get_design_value(
                    'chemical_admixtures.WRA.WRA_action.cement_economizer'),
                relative_density=self.data_model.get_design_value('chemical_admixtures.WRA.WRA_relative_density'),
                dosage=self.data_model.get_design_value('chemical_admixtures.WRA.WRA_dosage'),
                effectiveness=self.data_model.get_design_value('chemical_admixtures.WRA.WRA_effectiveness')
            )

            # Connect to the MCE data model
            self.cement.mce_data_model = self.mce_data_model
            self.air.mce_data_model = self.mce_data_model
            self.fine_agg.mce_data_model = self.mce_data_model
            self.coarse_agg.mce_data_model = self.mce_data_model
            self.std_deviation.mce_data_model = self.mce_data_model
            self.beta.mce_data_model = self.mce_data_model
            self.abrams_law.mce_data_model = self.mce_data_model
            self.wra.mce_data_model = self.mce_data_model

            self.logger.debug("Input data loaded and converted successfully")
        except Exception as e:
            self.logger.error(f"Error loading or converting input data: {str(e)}")
            raise

    def perform_calculations(self):
        """
        Execute the full calculation sequence using the material objects.
        If any step fails, log the error and stop the calculation.

        The calculated values are stored in self.calculation_results, which is then used
        to update the MCE data model.

        :return: True if the calculations were successful, False otherwise.
        """

        try:
            # A. Target Strength
            design_strength = self.hardened_concrete.design_strength
            std_dev_known = self.std_deviation.std_dev_known
            std_dev_value = self.std_deviation.std_dev_value
            sample_size = self.std_deviation.sample_size
            defective_level = self.std_deviation.defective_level
            std_dev_unknown = self.std_deviation.std_dev_unknown
            quality_control = self.std_deviation.quality_control

            target_strength = self.std_deviation.target_strength(design_strength, std_dev_known, std_dev_value,
                                                                 sample_size, defective_level, std_dev_unknown,
                                                                 quality_control)

            # B. Beta Relationship
            fine_grading = self.fine_agg.fill_all_sieves(self.fine_agg.grading)
            coarse_grading = self.coarse_agg.fill_all_sieves(self.coarse_agg.grading)
            nominal_max_size = self.coarse_agg.nominal_max_size

            beta_min, beta_max = self.beta.get_beta(nominal_max_size, coarse_grading, fine_grading)

            # B.1. Calculating beta using the economic approach
            beta_mean = (beta_min + beta_max) / 2
            beta_economic = (beta_mean + beta_min) / 2
            beta_value = beta_economic / 100

            # C. Water-Cement ratio, aka alpha or a/c (using abrams' law)
            target_strength_time = self.hardened_concrete.spec_strength_time
            agg_types = (self.coarse_agg.agg_type, self.fine_agg.agg_type)
            exposure_classes = list(self.hardened_concrete.exposure_classes.values())
            wra_checked = self.wra.wra_checked
            wra_action_water_reducer = self.wra.wra_action_water_reducer
            wra_effectiveness = self.wra.effectiveness

            alpha = self.abrams_law.water_cement_ratio(target_strength, target_strength_time, nominal_max_size,
                                                       agg_types, exposure_classes, wra_checked, wra_action_water_reducer,
                                                       wra_effectiveness)

            # D. Cement Content and Absolute Volume
            slump = self.fresh_concrete.slump
            cement_relative_density = self.cement.relative_density
            water_density = self.water.density
            wra_action_cement_economizer = self.wra.wra_action_cement_economizer

            cement_content = self.cement.cement_content(slump, alpha, nominal_max_size, agg_types, exposure_classes,
                                                        wra_checked=wra_checked,
                                                        wra_action_cement_economizer=wra_action_cement_economizer,
                                                        wra_action_water_reducer=wra_action_water_reducer,
                                                        effectiveness=wra_effectiveness)
            cement_abs_volume = self.cement.absolute_volume(cement_content, water_density, cement_relative_density)

            # E. Air Content
            entrapped_air_content = self.air.entrapped_air_volume(nominal_max_size, cement_content)

            # F. Water Content and Absolute Volume
            water_content = self.water.water_content(cement_content, alpha)
            water_abs_volume = self.water.water_volume(water_content, water_density)

            # G. Aggregate Content and Absolute Volume
            fine_relative_density = self.fine_agg.relative_density
            fine_loose_bulk_density = self.fine_agg.loose_bulk_density
            coarse_relative_density = self.coarse_agg.relative_density
            coarse_loose_bulk_density = self.coarse_agg.loose_bulk_density

            fine_content_ssd = self.fine_agg.fine_content(entrapped_air_content, cement_abs_volume, water_abs_volume,
                                                          water_density, fine_relative_density, coarse_relative_density,
                                                          beta_value)
            fine_abs_volume = self.fine_agg.absolute_volume(fine_content_ssd, water_density, fine_relative_density, "fine")

            coarse_content_ssd = self.coarse_agg.coarse_content(fine_content_ssd, beta_value)
            coarse_abs_volume = self.coarse_agg.absolute_volume(coarse_content_ssd, water_density, coarse_relative_density,
                                                                "coarse")

            # Moisture adjustments
            fine_moisture_content = self.fine_agg.moisture_content
            fine_moisture_absorption = self.fine_agg.moisture_absorption
            coarse_moisture_content = self.coarse_agg.moisture_content
            coarse_moisture_absorption = self.coarse_agg.moisture_absorption

            fine_content_wet = self.fine_agg.content_moisture_correction(fine_content_ssd, fine_moisture_content,
                                                                         fine_moisture_absorption)
            coarse_content_wet = self.coarse_agg.content_moisture_correction(coarse_content_ssd, coarse_moisture_content,
                                                                             coarse_moisture_absorption)
            water_content_correction = self.water.water_content_correction(water_content, fine_content_ssd,
                                                                           fine_content_wet, coarse_content_ssd,
                                                                           coarse_content_wet)

            # Water Volume (adjusted by moisture correction)
            water_volume = self.water.water_volume(water_content_correction, water_density)

            # Aggregate Apparent Volume (adjusted by moisture correction)
            fine_volume = self.fine_agg.apparent_volume(fine_content_wet, fine_loose_bulk_density, "fine")
            coarse_volume = self.coarse_agg.apparent_volume(coarse_content_wet, coarse_loose_bulk_density, "coarse")

            # Admixture dosage
            wra_relative_density = self.wra.relative_density
            wra_dosage = self.wra.dosage

            # Water-Reducing Admixture
            if wra_checked:
                wra_content = self.wra.admixture_content(cement_content, wra_dosage)
                wra_volume = self.wra.admixture_volume(wra_content, water_density, wra_relative_density)
            else:
                wra_content = None
                wra_volume = None

            # Convert absolute from m3 to L
            water_abs_volume = 1000 * water_abs_volume
            water_volume = 1000 * water_volume
            cement_abs_volume = 1000 * cement_abs_volume
            fine_abs_volume = 1000 * fine_abs_volume
            coarse_abs_volume = 1000 * coarse_abs_volume
            entrapped_air_content = 1000 * entrapped_air_content
            if wra_checked:
                wra_volume = 1000 * wra_volume

            # Add up all absolute volumes and contents
            total_abs_volume = sum(
                [water_abs_volume, cement_abs_volume, fine_abs_volume, coarse_abs_volume, entrapped_air_content])
            total_content = sum([water_content_correction, cement_content, fine_content_wet, coarse_content_wet])

            # Store all the results in a dictionary
            self.calculation_results = {
                "target_strength": target_strength,
                "w_cm": alpha,
                "beta_mean": beta_mean,
                "beta_economic": beta_economic,
                "beta": beta_value,
                "entrapped_air_content": entrapped_air_content,
                "water_content": water_content,
                "water_content_correction": water_content_correction,
                "water_abs_volume": water_abs_volume,
                "water_volume": water_volume,
                "cement_content": cement_content,
                "cement_abs_volume": cement_abs_volume,
                "cement_volume": "-",
                "fine_content_ssd": fine_content_ssd,
                "fine_content_wet": fine_content_wet,
                "fine_abs_volume": fine_abs_volume,
                "fine_volume": fine_volume,
                "coarse_content_ssd": coarse_content_ssd,
                "coarse_content_wet": coarse_content_wet,
                "coarse_abs_volume": coarse_abs_volume,
                "coarse_volume": coarse_volume,
                "WRA_content": wra_content,
                "WRA_volume": wra_volume,
                "total_abs_volume": total_abs_volume,
                "total_content": total_content
            }

            self.logger.info(f"Calculations completed successfully.")
            return True

        except Exception: # Capturing all exceptions to ensure robust calculation process
            self.logger.error("Error during calculations", exc_info=True)
            return False

    def update_data_model(self):
        """
        Update the MCE data model with the calculated results stored in self.calculation_results.
        """

        if not self.calculation_results:
            self.logger.error("No calculation results to update in the data model")
            return

        for key, value in self.calculation_results.items():
            # The key paths according to MCE data model schema
            if key == "target_strength":
                data_key = "spec_strength.target_strength.target_strength_value"
            elif key == "w_cm":
                data_key = "water_cementitious_materials_ratio.w_cm"
            elif key in ("beta_mean", "beta_economic", "beta"):
                data_key = f"beta.{key}"
            elif key == "entrapped_air_content":
                data_key = "air.entrapped_air_content"
            elif key in ("water_content", "water_content_correction", "water_abs_volume", "water_volume"):
                data_key = f"water.{key}"
            elif key in ("cement_content", "cement_abs_volume", "cement_volume"):
                data_key = f"cementitious_material.cement.{key}"
            elif key in ("fine_content_ssd", "fine_content_wet", "fine_abs_volume", "fine_volume"):
                data_key = f"fine_aggregate.{key}"
            elif key in ("coarse_content_ssd", "coarse_content_wet", "coarse_abs_volume", "coarse_volume"):
                data_key = f"coarse_aggregate.{key}"
            elif key in ("WRA_content", "WRA_volume"):
                data_key = f"chemical_admixtures.WRA.{key}"
            elif key in ("total_abs_volume", "total_content"):
                data_key = f"summation.{key}"
            else:
                continue

            self.mce_data_model.update_data(data_key, value)
        self.logger.debug("MCE data model updated with calculation results")

    def run(self):
        """
        Execute the full MCE calculation process:
          1. Load input data.
          2. Perform calculations.
          3. Update the data model with the results.
        """

        self.logger.info("Starting MCE calculation process...")
        self.load_inputs()
        if self.perform_calculations():
            self.update_data_model()
            self.logger.info("MCE calculation process completed successfully")
            return True
        else:
            self.logger.error("MCE calculation process terminated due to an error")
            return False