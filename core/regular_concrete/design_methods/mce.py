import re
from dataclasses import dataclass, field
from math import log10

from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.core.regular_concrete.models.mce_data_model import MCEDataModel
from Concretus.logger import Logger
from Concretus.settings import COMBINED_GRADING, CEMENT_FACTOR_1, CEMENT_FACTOR_2, MAX_CEMENT, K_FACTOR, QUARTILES, \
    CONSTANTS, ALFA_FACTOR_1, ALFA_FACTOR_2, MAX_ALFA, CONVERSION_FACTORS


# ------------------------------------------------ Class for materials ------------------------------------------------
@dataclass
class CementitiousMaterial:
    relative_density: float
    mce_data_model: MCEDataModel = field(init=False, repr=False)

@dataclass
class Cement(CementitiousMaterial):

    def cement_abs_volume(self, cement_content, water_density, relative_density=3.33):
        """
        Calculates the absolute volume of cement grains in cubic meters (m³).

        The cement content and water density must use consistent units:
        - If cement content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If cement content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float cement_content: The cement content (kg or kgf).
        :param float water_density: The water density (kg/m³ or kgf/m³).
        :param float relative_density: The relative density of cement (default 3.33).
        :return: The absolute volume of cement grains in cubic meters (m³).
        :rtype: float
        """

        if water_density != 0 and relative_density != 0:
            return cement_content / (relative_density * water_density)
        else:
            self.mce_data_model.add_calculation_error('Cement volume',
                                                      f'The relative density of the cement is {relative_density}. '
                                                      f'The water density is {water_density}')
            raise ZeroDivisionError("The relative density of cement or the water density is zero")

    def cement_volume(self):
        pass

    def cement_content(self, slump, alpha, nms, agg_types, exposure_classes, theta=None, k=117.2, n=0.16, m=1.3):
        """
        Calculate the cement content in kilogram-force per cubic meter of mixture (kgf/m³) using the triangular_relationship.
        The parameters k, n, m are constants that depend on the characteristics of the component materials of
        the mixture and the conditions under which it is prepared.

        :param int slump: The required slump of the concrete in fresh state (in mm).
        :param float alpha: The ratio of water to cement used.
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param tuple[str, str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                               (e.g., ("Triturado", "Natural")).
        :param list[str, str, str, str] exposure_classes: A list containing all possible exposure classes,
                                         in no particular order,
                                         (e.g., ['Agua dulce', 'Moderada', 'Despreciable', 'Atmósfera común']).
        :param float k: Constant (default 117.2).
        :param float n: Constant (default 0.16).
        :param float m: Constant (default 1.3).
        :param float theta: A constant used to modify the triangular relationship,
                            this value will be specific to the particular materials, design and slump (if provided).
        :return: The calculated cement content in kilogram-force per cubic meter (kgf/m³).
        :rtype: float
        """

        # Convert slump to centimeters
        slump = 0.1 * slump

        if not theta:
            # Calculate the design cement content
            design_cement_content = k * slump ** n * alpha ** (-m)

            if nms is None:
                self.mce_data_model.add_calculation_error('Cement content',
                                                          f'The nominal maximum size is {nms}')
                raise ValueError("The nominal maximum size cannot be None")
            # Retrieve correction factors from settings
            correction_factor_1 = CEMENT_FACTOR_1.get(nms, 0) # according to the nominal maximum size
            correction_factor_2 = CEMENT_FACTOR_2.get(agg_types[0], {}).get(agg_types[1], 0) # according to aggregate type

            # Calculate corrected cement content
            corrected_cement_content = correction_factor_1 * correction_factor_2 * design_cement_content

            # Determine maximum cement content based on exposure classes
            max_cement_content = (MAX_CEMENT.get(exposure_classes[0], 0), MAX_CEMENT.get(exposure_classes[1], 0),
                                  MAX_CEMENT.get(exposure_classes[2], 0), MAX_CEMENT.get(exposure_classes[3], 0))
            max_cement_content = max(max_cement_content)

            # The final cement content is the maximum between the corrected cement content and the maximum cement content
            cement_content = max(corrected_cement_content, max_cement_content)

            # Update the MCE data model with all intermediate values
            self.mce_data_model.update_data('cementitious_material.cement.design_cement_content',
                                            design_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.correction_factor_1',
                                            correction_factor_1)
            self.mce_data_model.update_data('cementitious_material.cement.correction_factor_2',
                                            correction_factor_2)
            self.mce_data_model.update_data('cementitious_material.cement.corrected_cement_content',
                                            corrected_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.max_cement_content',
                                            max_cement_content)
        else:
            # When theta is provided, use a different relationship
            design_cement_content = theta * alpha ** (-m)

            # Determine maximum cement content based on exposure classes
            max_cement_content = (MAX_CEMENT.get(exposure_classes[0], 0), MAX_CEMENT.get(exposure_classes[1], 0),
                                  MAX_CEMENT.get(exposure_classes[2], 0), MAX_CEMENT.get(exposure_classes[3], 0))
            max_cement_content = max(max_cement_content)

            # The final cement content is the maximum between the design cement content and the maximum cement content
            cement_content = max(design_cement_content, max_cement_content)

            # Update only the available values in the MCE data model.
            self.mce_data_model.update_data('cementitious_material.cement.design_cement_content',
                                            design_cement_content)
            self.mce_data_model.update_data('cementitious_material.cement.max_cement_content',
                                            max_cement_content)

        return cement_content

@dataclass
class Water:
    density: float
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def water_abs_volume(self, water_content, density):
        """
        Calculates the volume of water in cubic meter (m³). For water, the absolute volume and total volume are the same.

        The water content and density must use consistent units:
        - If water content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If water content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float water_content: The content of water (kg or kgf).
        :param float density: The water density (kg/m³ or kgf/m³).
        :return: The volume of water in cubic meter (m³).
        :rtype: float
        """

        if density == 0:
            self.mce_data_model.add_calculation_error('Water volume',
                                                      f'The density is {density}')
            raise ValueError("Density cannot be zero")

        return water_content / density

    @staticmethod
    def water_volume(water_abs_volume):
        """
        Convert the absolute volume of water from cubic meters (m³) to liters (L).

        :param water_abs_volume: The absolute volume of water in cubic meters (m³).
        :return: The volume of water in liters (L).
        """

        return 1000 * water_abs_volume

    @staticmethod
    def water_content(cement_content, alpha):
        """
        Calculate the content of water in kilogram-force per cubic meter (kgf/m³).

        :param float cement_content: The cement content in kilogram-force per cubic meter (kgf/m³).
        :param float alpha: The water-cement ratio.
        :return: The weight of water in kilogram-force per cubic meter (kgf/m³).
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

        :param str nms: The nominal maximum size (e.g., '2-1/2" (63 mm)').
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
            self.mce_data_model.add_calculation_error('Entrapped air volumen',
                                                      f'Error trying to match regular expression for {nms}')
            raise Exception("No match found")

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
        Fill a base dictionary (with all sieves) with data from a given dictionary
        and fill empty values with 100 or 0, depending on certain conditions.

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

    @staticmethod
    def agg_content_moisture_correction(ssd_content, moisture_content, absorption):
        """
        Adjust the aggregate content from an SSD (saturated surface-dry) condition to a wet condition.

        This function converts the aggregate content measured under SSD conditions to its equivalent
        wet condition value. The adjustment accounts for the moisture content and absorption capacity
        of the aggregate. Both the moisture_content and absorption should be provided as percentages
        (e.g., 2 for 2%).

        :param float ssd_content: Aggregate content under SSD conditions.
        :param float moisture_content: Moisture content of the aggregate as a percentage.
        :param float absorption: Absorption capacity of the aggregate as a percentage.
        :return: Adjusted aggregate content under wet conditions.
        :rtype: float
        """

        denominator = 100 + absorption
        if denominator == 0:
            raise ValueError("Invalid absorption value: 100 + absorption cannot be zero.")

        return ssd_content * ((100 + moisture_content) / denominator)

@dataclass
class FineAggregate(Aggregate):
    fineness_modulus: float = None

    def fine_abs_volume(self, fine_content, water_density, relative_density):
        """
        Calculate the absolute volume of fine aggregate in cubic meters (m³).

        The fine content and water density must use consistent units:
        - If fine content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If fine content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float fine_content: The fine content (kg or kgf).
        :param water_density: The water density (kg/m³ or kgf/m³).
        :param float relative_density: The relative density of fine aggregate.
        :return: The absolute volume of fine aggregate in cubic meters (m³).
        :rtype: float
        """

        if water_density != 0 and relative_density != 0:
            return fine_content / (relative_density * water_density)
        else:
            self.mce_data_model.add_calculation_error('Fine aggregate volume',
                                                      f'The relative density of the fine aggregate is {relative_density}. '
                                                      f'The water density is {water_density}')
            raise ZeroDivisionError("The relative density of fine aggregate or the water density is zero")

    def fine_volume(self, fine_content, loose_bulk_density):
        """
        Calculate the apparent volume of fine aggregate in liters (L). The "apparent" volume includes the volume
        of the aggregate particles and the voids between them.

        Unit consistency is crucial:
        - If fine_content is in kilograms (kg), loose_bulk_density must be in kilograms per cubic meter (kg/m³).
        - If fine_content is in kilogram-force (kgf), loose_bulk_density must be in kilogram-force per cubic meter (kgf/m³).

        The function converts the calculated volume from cubic meters (m³) to liters (L).

        :param float fine_content: The fine aggregate content (kg or kgf).
        :param float loose_bulk_density: The loose bulk density (kg/m³) or loose unit weight (kgf/m³) of the fine aggregate.
        :return: The apparent volume of fine aggregate in liters (L).
        :rtype: float
        """

        if loose_bulk_density == 0:
            self.mce_data_model.add_calculation_error('Fine aggregate volume',
                                                      f'The loose bulk density of the fine aggregate is {loose_bulk_density}')
            raise ZeroDivisionError("The loose bulk density for the fine aggregate cannot be zero.")

        LITERS_PER_CUBIC_METER = 1000
        loose_bulk_density_liters_per_cubic_meter = loose_bulk_density / LITERS_PER_CUBIC_METER

        return fine_content / loose_bulk_density_liters_per_cubic_meter

    def fine_content(self, entrapped_air, cement_abs_volume, water_volume, water_density, fine_relative_density,
                     coarse_relative_density, beta_value):
        """
        Calculate the fine content in kilogram-force per cubic meter (kgf/m³).

        The formula calculates the fine aggregate content by subtracting the volumes of
        entrapped air, cement, and water (in m³) from 1 m³ (total volume of the mixture), then dividing by
        an expression that involves the relative densities and beta relationship.

        :param float entrapped_air: The volume of entrapped air in cubic meter (m³).
        :param float cement_abs_volume: The absolute volume of cement grains in cubic meter (m³).
        :param float water_volume: The volume of water in cubic meter (m³).
        :param float water_density: The water density.
        :param float fine_relative_density: The relative density if the fine aggregate.
        :param float coarse_relative_density: The relative density if the coarse aggregate.
        :param float beta_value: The beta relationship.
        :return: The calculated fine aggregate content in kilogram-force per cubic meter (kgf/m³).
        :rtype: float
        """

        # Validate to avoid division by zero
        if fine_relative_density == 0:
            self.mce_data_model.add_calculation_error('Fine aggregate content',
                                                      f'The relative density of the fine aggregate is {fine_relative_density}')
            raise ValueError("The relative density of the fine aggregate cannot be zero")
        if beta_value == 0:
            self.mce_data_model.add_calculation_error('Fine aggregate content',
                                                      f'The beta value is {beta_value}')
            raise ValueError("The beta value cannot be zero")
        if coarse_relative_density == 0:
            self.mce_data_model.add_calculation_error('Fine aggregate content',
                                                      f'The relative density of the coarse aggregate is {coarse_relative_density}')
            raise ValueError("The relative density of the coarse aggregate cannot be zero")

        # Calculate numerator:
        numerator = 1 - (entrapped_air + cement_abs_volume + water_volume)

        # Calculate denominator:
        denominator = (1 / water_density) * (
                    (1 / fine_relative_density) + (1 / coarse_relative_density) * ((1 / beta_value) - 1))

        # Return the computed fine aggregate content
        return numerator / denominator

@dataclass
class CoarseAggregate(Aggregate):
    nominal_max_size: float

    def coarse_abs_volume(self, coarse_content, water_density, relative_density):
        """
        Calculate the absolute volume of coarse aggregate in cubic meters (m³).

        The coarse content and water density must use consistent units:
        - If coarse content is in kilograms (kg), water density must be in kilograms per cubic meter (kg/m³).
        - If coarse content is in kilogram-force (kgf), water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float coarse_content: The coarse content (kg or kgf).
        :param water_density: The water density (kg/m³ or kgf/m³).
        :param float relative_density: The relative density of coarse aggregate.
        :return: The absolute volume of coarse aggregate in cubic meters (m³).
        :rtype: float
        """

        if water_density != 0 and relative_density != 0:
            return coarse_content / (relative_density * water_density)
        else:
            self.mce_data_model.add_calculation_error('Coarse aggregate volume',
                                                      f'The relative density of the coarse aggregate is {relative_density}. '
                                                      f'The water density is {water_density}')
            raise ZeroDivisionError("The relative density of coarse aggregate or the water density is zero")

    def coarse_volume(self, coarse_content, loose_bulk_density):
        """
        Calculate the apparent volume of coarse aggregate in liters (L). The "apparent" volume includes the volume
        of the aggregate particles and the voids between them.

        Unit consistency is crucial:
        - If coarse_content is in kilograms (kg), loose_bulk_density must be in kilograms per cubic meter (kg/m³).
        - If coarse_content is in kilogram-force (kgf), loose_bulk_density must be in kilogram-force per cubic meter (kgf/m³).

        The function converts the calculated volume from cubic meters (m³) to liters (L).

        :param float coarse_content: The coarse aggregate content (kg or kgf).
        :param float loose_bulk_density: The loose bulk density (kg/m³) or loose unit weight (kgf/m³) of the coarse aggregate.
        :return: The apparent volume of coarse aggregate in liters (L).
        :rtype: float
        """

        if loose_bulk_density == 0:
            self.mce_data_model.add_calculation_error('Fine aggregate volume',
                                                      f'The loose bulk density of the fine aggregate is {loose_bulk_density}')
            raise ZeroDivisionError("The loose bulk density for the fine aggregate cannot be zero.")

        LITERS_PER_CUBIC_METER = 1000
        loose_bulk_density_liters_per_cubic_meter = loose_bulk_density / LITERS_PER_CUBIC_METER

        return coarse_content / loose_bulk_density_liters_per_cubic_meter

    def coarse_content(self, fine_content, beta_value):
        """
        Calculate the coarse content in kilogram-force per cubic meter (kgf/m³).
        It is based on the fine aggregate content and beta value.

        :param float fine_content: The fine aggregate content in kilogram-force per cubic meter (kgf/m³).
        :param float beta_value: The beta relationship.
        :return: The coarse aggregate content in kilogram-force per cubic meter (kgf/m³).
        :rtype: float
        """

        if beta_value == 0:
            self.mce_data_model.add_calculation_error('Coarse aggregate content',
                                                      f'The beta value is {beta_value}')
            raise ValueError("The beta value cannot be zero")

        inverse_beta = 1 / beta_value
        result = fine_content * (inverse_beta - 1)
        return result

@dataclass
class FreshConcrete:
    slump: float

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
        :return: The target strength value in kilogram-force per square centimetre (kgf/cm^2).
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
                # If no margin was assigned, None is returned
                self.mce_data_model.add_calculation_error('Target strength', 'No margin found')
                raise ValueError("No margin found")

        else:
            # If no condition is met, None is returned
            self.mce_data_model.add_calculation_error('Target strength',
                                                      'Else statement was triggered')
            raise ValueError("A error occurred")

        return f_cr

@dataclass
class Beta:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    @staticmethod
    def unused_sieves(coarse_grading, fine_grading):
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

        # Create a set of keys to remove (keys with None in either dictionary)
        keys_to_remove = {k for k, v in coarse_grading.items() if v is None} | {k for k, v in fine_grading.items() if
                                                                                v is None}

        # Remove the identified keys from both dictionaries
        for key in keys_to_remove:
            coarse_grading.pop(key, None)
            fine_grading.pop(key, None)

        return coarse_grading, fine_grading

    def get_beta(self, nms, coarse_data, fine_data):
        """
        Calculate beta values (minimum and maximum) based on the grading limits and sieve data.

        If the given nominal maximum size has no grading limits, return None twice.

        If the fine and coarse values are equal:
            - If they are either 0 or 100, that sieve is skipped.
            - If the value is not equal to either the minimum or maximum recommended percentages,
              the function returns (0, 0).

        Otherwise, a slope is calculated to obtain a linear equation of two points. The beta values
        are clamped between 0 and 100, and the maximum beta_min and minimum beta_max across all sieves are returned.

        :param str nms: Nominal maximum size to retrieve grading limits.
        :param dict[str, float | None] coarse_data: Data for coarse grading.
        :param dict[str, float | None] fine_data: Data for fine grading.
        :return: A tuple containing the minimum and maximum beta values, respectively.
                 Or two 0s or two None, as appropriate.
        :rtype: tuple[float | None, float | None]
        """

        # Retrieve the recommended grading limits for the given nominal maximum size
        grading_limits = COMBINED_GRADING.get(nms)
        if grading_limits is None:
            self.mce_data_model.add_calculation_error('Get beta', f"Grading limits not found for NMS: {nms}")
            return None, None

        # Clean any unused sieves from the grading
        coarse_grading, fine_grading = self.unused_sieves(coarse_data, fine_data)

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
                    # If value does not match expected limits,
                    self.mce_data_model.add_calculation_error('Get beta',
                                                              "The given grading does not match the recommended limits")
                    # returns two None indicating that no posible beta values where found
                    return None, None
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

        # Return the maximum of beta_mins and the minimum of beta_maxs if computed, else return None twice
        if beta_mins and beta_maxs:
            if max(beta_mins) <= min(beta_maxs):
                self.mce_data_model.update_data('beta.beta_min', max(beta_mins))
                self.mce_data_model.update_data('beta.beta_max', min(beta_maxs))
                return max(beta_mins), min(beta_maxs)
            else:
                self.mce_data_model.add_calculation_error('Get beta', f"The calculated set is not possible. "
                                  f"The minimum beta ({max(beta_mins)}) is greater than the maximum ({min(beta_maxs)}).")
                return None, None
        else:
            self.mce_data_model.add_calculation_error('Get beta',
                                                      f"There is an empty set. beta_mins -> {beta_mins}; beta_maxs -> {beta_maxs}")
            return None, None

class AbramsLaw:
    mce_data_model: MCEDataModel = field(init=False, repr=False)

    def water_cement_ratio(self, target_strength, target_strength_time, nms, agg_types, exposure_classes, m=None,
                           n=None):
        """
        Calculated the water-cement ratio. The parameters m and n are constants that depend on the age of test,
        the characteristics of the component materials of the mixture and the way the mixture is made.

        :param float target_strength: The target strength of the mixture design.
        :param str target_strength_time: The expected time to reach the target strength,
                                         also known as the age of the test (e.g., "7 días", "27 días", "90 días").
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param tuple[str, str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                               (e.g., ("Triturado", "Natural")).
        :param list[str, str, str, str] exposure_classes: A list containing all possible exposure classes,
                                         in no particular order,
                                         (e.g., ['Agua dulce', 'Moderada', 'Despreciable', 'Atmósfera común']).
        :param float m: A constant.
        :param float n: A constant.
        :return: The water-cement ratio (also known as alpha).
        :rtype: float
        """

        # Get the n and m constants for the given age of the test.
        if m is None and n is None:
            n = CONSTANTS.get(target_strength_time, {})["n"]
            m = CONSTANTS.get(target_strength_time, {})["m"]

        # Calculate the alpha according to Abrams' Law
        design_alpha = (log10(m) - log10(target_strength)) / log10(n)

        # Retrieve correction factors from settings
        correction_factor_1 = ALFA_FACTOR_1.get(nms, 1)  # according to the nominal maximum size
        correction_factor_2 = ALFA_FACTOR_2.get(agg_types[0], {}).get(agg_types[1], 1)  # according to aggregate type

        # Calculate corrected alpha
        corrected_alpha = correction_factor_1 * correction_factor_2 * design_alpha

        # Determine the minimum alpha based on exposure classes
        min_alpha = (MAX_ALFA.get(exposure_classes[0], 1), MAX_ALFA.get(exposure_classes[1], 1),
                              MAX_ALFA.get(exposure_classes[2], 1), MAX_ALFA.get(exposure_classes[3], 1))
        min_alpha = min(min_alpha)

        # The final alpha is the maximum between the corrected alpha and the maximum alpha
        alpha = min(corrected_alpha, min_alpha)

        # Update the MCE data model with all intermediate values
        self.mce_data_model.update_data('water_cement_ratio.design_alpha', design_alpha)
        self.mce_data_model.update_data('water_cement_ratio.correction_factor_1', correction_factor_1)
        self.mce_data_model.update_data('water_cement_ratio.correction_factor_2', correction_factor_2)
        self.mce_data_model.update_data('water_cement_ratio.corrected_alpha', corrected_alpha)
        self.mce_data_model.update_data('water_cement_ratio.min_alpha', min_alpha)
        self.mce_data_model.update_data('water_cement_ratio.m', m)
        self.mce_data_model.update_data('water_cement_ratio.n', n)

        return alpha


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
                f"No conversion factor found for unit system '{current_units}' and target unit '{unit}'.")
            return None

        # Return the converted value by multiplying with the factor.
        return value * factor

    def load_inputs(self):
        """
        Loads data from the data model, performs unit conversion for selected parameters,
        and instantiates the necessary objects.
        """

        try:
            # For each parameter, retrieve and convert if needed.
            design_strength = self.data_model.get_design_value('field_requirements.strength.spec_strength')
            std_dev_value = self.data_model.get_design_value('field_requirements.strength.std_dev_known.std_dev_value')
            if self.data_model.units == "SI":
                design_strength = self.convert_value(design_strength, "stress")
                std_dev_value = self.convert_value(std_dev_value, "stress")

            # Instantiate the components with their corresponding data
            self.cement = Cement(
                relative_density=self.data_model.get_design_value('cementitious_materials.relative_density'))
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

            self.fresh_concrete = FreshConcrete(slump=self.data_model.get_design_value("field_requirements.slump"))
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

            # Connect to the MCE data model
            self.cement.mce_data_model = self.mce_data_model
            self.air.mce_data_model = self.mce_data_model
            self.fine_agg.mce_data_model = self.mce_data_model
            self.coarse_agg.mce_data_model = self.mce_data_model
            self.std_deviation.mce_data_model = self.mce_data_model
            self.beta.mce_data_model = self.mce_data_model
            self.abrams_law.mce_data_model = self.mce_data_model

            self.logger.debug("Input data loaded and converted successfully.")
        except Exception:
            self.logger.error("Error loading or converting input data")
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
            # A. Target strength
            design_strength = self.hardened_concrete.design_strength
            std_dev_known = self.std_deviation.std_dev_known
            std_dev_value = self.std_deviation.std_dev_value
            sample_size = self.std_deviation.sample_size
            defective_level = self.std_deviation.defective_level
            std_dev_unknown = self.std_deviation.std_dev_unknown
            quality_control = self.std_deviation.quality_control

            target_strength = self.std_deviation.target_strength(
                design_strength, std_dev_known, std_dev_value, sample_size,
                defective_level, std_dev_unknown, quality_control
            )

            # B. Beta Relationship
            fine_grading = self.fine_agg.fill_all_sieves(self.fine_agg.grading)
            coarse_grading = self.coarse_agg.fill_all_sieves(self.coarse_agg.grading)
            nominal_max_size = self.coarse_agg.nominal_max_size

            beta_min, beta_max = self.beta.get_beta(nominal_max_size, coarse_grading, fine_grading)
            if beta_min is None or beta_max is None:
                self.logger.error("Beta relationship calculation failed")
                return False

            # C. Water-Cement ratio, aka alpha or a/c (using abrams' law)
            target_strength_time = self.hardened_concrete.spec_strength_time
            agg_types = (self.coarse_agg.agg_type, self.fine_agg.agg_type)
            exposure_classes = list(self.hardened_concrete.exposure_classes.values())

            alpha = self.abrams_law.water_cement_ratio(
                target_strength, target_strength_time, nominal_max_size, agg_types, exposure_classes
            )

            # D. Cement Content (using triangular relationship)
            slump = self.fresh_concrete.slump
            cement_content = self.cement.cement_content(
                slump, alpha, nominal_max_size, agg_types, exposure_classes
            )

            # E. Cement Absolute Volume
            cement_relative_density = self.cement.relative_density
            water_density = self.water.density
            cement_abs_volume = self.cement.cement_abs_volume(cement_content, water_density, cement_relative_density)

            # F. Entrapped Air Volume
            entrapped_air_volume = self.air.entrapped_air_volume(nominal_max_size, cement_content)

            # G. Water Content
            water_content = self.water.water_content(cement_content, alpha)

            # H. Water (Absolute) Volume
            water_abs_volume = self.water.water_abs_volume(water_content, water_density)
            water_volume = self.water.water_volume(water_abs_volume)

            # I. Aggregate Content

            # Calculate beta: use the economic approach
            beta_mean = (beta_min + beta_max) / 2
            beta_economic = (beta_mean + beta_min) / 2
            beta_value = beta_economic / 100

            fine_relative_density = self.fine_agg.relative_density
            coarse_relative_density = self.coarse_agg.relative_density

            fine_content = self.fine_agg.fine_content(entrapped_air_volume, cement_abs_volume, water_abs_volume, water_density,
                                                      fine_relative_density, coarse_relative_density, beta_value)
            coarse_content = self.coarse_agg.coarse_content(fine_content, beta_value)

            # J. Aggregate Absolute Volume
            fine_abs_volume = self.fine_agg.fine_abs_volume(fine_content, water_density, fine_relative_density)
            coarse_abs_volume = self.coarse_agg.coarse_abs_volume(coarse_content, water_density, coarse_relative_density)

            # K. Aggregate Volume
            fine_loose_bulk_density = self.fine_agg.loose_bulk_density
            coarse_loose_bulk_density = self.coarse_agg.loose_bulk_density

            fine_volume = self.fine_agg.fine_volume(fine_content, fine_loose_bulk_density)
            coarse_volume = self.coarse_agg.coarse_volume(coarse_content, coarse_loose_bulk_density)

            # Moisture adjustments
            fine_moisture_content = self.fine_agg.moisture_content
            coarse_moisture_content = self.coarse_agg.moisture_content
            fine_moisture_absorption = self.fine_agg.moisture_absorption
            coarse_moisture_absorption = self.coarse_agg.moisture_absorption

            fine_content_wet = self.fine_agg.agg_content_moisture_correction(fine_content, fine_moisture_content,
                                                                         fine_moisture_absorption)
            coarse_content_wet = self.coarse_agg.agg_content_moisture_correction(coarse_content, coarse_moisture_content,
                                                                             coarse_moisture_absorption)
            water_content_correction = self.water.water_content_correction(water_content, fine_content, fine_content_wet,
                                                                coarse_content, coarse_content_wet)

            # Since the water and aggregate contents (fine and coarse) were adjusted,
            # their apparent volumes change accordingly.
            water_volume = self.water.water_abs_volume(water_content_correction, water_density)
            water_volume = self.water.water_volume(water_volume)
            fine_volume = self.fine_agg.fine_volume(fine_content_wet, fine_loose_bulk_density)
            coarse_volume = self.coarse_agg.coarse_volume(coarse_content_wet, coarse_loose_bulk_density)

            # Convert absolute from m3 to L.
            water_abs_volume = 1000 * water_abs_volume
            cement_abs_volume = 1000 * cement_abs_volume
            fine_abs_volume = 1000 * fine_abs_volume
            coarse_abs_volume = 1000 * coarse_abs_volume
            entrapped_air_volume = 1000 * entrapped_air_volume

            # Add up all absolute volumes and contents
            total_abs_volume = sum(
                [water_abs_volume, cement_abs_volume, fine_abs_volume, coarse_abs_volume, entrapped_air_volume])
            total_content = sum([water_content_correction, cement_content, fine_content_wet, coarse_content_wet])

            # Store all the results in a dictionary
            self.calculation_results = {
                "target_strength": target_strength,
                "alpha": alpha,
                "beta_mean": beta_mean,
                "beta_economic": beta_economic,
                "beta": beta_value,
                "entrapped_air": entrapped_air_volume,
                "water_content": water_content,
                "water_content_correction": water_content_correction,
                "water_abs_volume": water_abs_volume,
                "water_volume": water_volume,
                "cement_content": cement_content,
                "cement_abs_volume": cement_abs_volume,
                "cement_volume": "-",
                "fine_content": fine_content,
                "fine_content_wet": fine_content_wet,
                "fine_abs_volume": fine_abs_volume,
                "fine_volume": fine_volume,
                "coarse_content": coarse_content,
                "coarse_content_wet": coarse_content_wet,
                "coarse_abs_volume": coarse_abs_volume,
                "coarse_volume": coarse_volume,
                "total_abs_volume": total_abs_volume,
                "total_content": total_content
            }

            self.logger.info(f"Calculations completed successfully.")
            return True

        except Exception as e: # Capturing all exceptions to ensure robust calculation process.
            self.logger.error("Error during calculations", exc_info=True)
            return False

    def update_data_model(self):
        """
        Update the MCE data model with the calculated results stored in self.calculation_results.
        """

        if not self.calculation_results:
            self.logger.error("No calculation results to update in the data model.")
            return

        for key, value in self.calculation_results.items():
            # The key paths according to MCE data model schema
            if key == "target_strength":
                data_key = "spec_strength.target_strength.target_strength_value"
            elif key == "alpha":
                data_key = "water_cement_ratio.alpha"
            elif key in ("beta_mean", "beta_economic", "beta"):
                data_key = f"beta.{key}"
            elif key == "entrapped_air":
                data_key = "air.entrapped_air"
            elif key in ("water_content", "water_content_correction", "water_abs_volume", "water_volume"):
                data_key = f"water.{key}"
            elif key in ("cement_content", "cement_abs_volume", "cement_volume"):
                data_key = f"cementitious_material.cement.{key}"
            elif key in ("fine_content", "fine_content_wet", "fine_abs_volume", "fine_volume"):
                data_key = f"fine_aggregate.{key}"
            elif key in ("coarse_content", "coarse_content_wet", "coarse_abs_volume", "coarse_volume"):
                data_key = f"coarse_aggregate.{key}"
            elif key in ("total_abs_volume", "total_content"):
                data_key = f"summation.{key}"
            else:
                continue

            self.mce_data_model.update_data(data_key, value)
        self.logger.debug("MCE data model updated with calculation results.")

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
            self.logger.info("MCE calculation process completed successfully.")
        else:
            self.logger.error("MCE calculation process terminated due to an error.")