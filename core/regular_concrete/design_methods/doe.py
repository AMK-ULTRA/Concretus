from dataclasses import dataclass, field

import numpy as np
from numpy.polynomial import Polynomial

from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from logger import Logger
from settings import (QUARTILES, CONVERSION_FACTORS, W_CM_COEFFICIENTS, STARTING_STRENGTH, MAX_W_CM_DOE, WATER_CONTENT,
                      WATER_CONTENT_REDUCTION, MIN_CEMENTITIOUS_CONTENT_DOE, ENTRAINED_AIR, DENSITY_COEFFICIENTS,
                      FINE_PROPORTION)


# ------------------------------------------------ Class for materials ------------------------------------------------
@dataclass
class CementitiousMaterial:
    relative_density: float
    doe_data_model: DOEDataModel = field(init=False, repr=False)

    def absolute_volume(self, content, water_density, relative_density, cementitious_type=None):
        """
        Calculate the absolute volume of a cementitious material in cubic meters (m³).

        The cementitious material content and water density must use consistent units:
        - If the cementitious material content is in kilograms (kg),
          water density must be in kilograms per cubic meter (kg/m³).
        - If the cementitious material content is in kilogram-force (kgf),
          water density must be in kilogram-force per cubic meter (kgf/m³).

        :param float content: Cementitious material content (kg or kgf).
        :param float water_density: Water density (kg/m³ or kgf/m³).
        :param float relative_density: Relative density of cementitious material.
        :param str cementitious_type: Type of cementitious material (e.g., 'Cemento', 'Cenizas volantes',
                                      'Cemento de escoria', 'Humo de sílice').
        :return: The absolute volume (in m³).
        :rtype: float
        """

        if water_density == 0 or relative_density == 0:
            error_msg = (f"The relative density of the {cementitious_type} is {relative_density}. "
                         f"The water density is {water_density}. None can be zero")
            self.doe_data_model.add_calculation_error('Cementitious volume', error_msg)
            raise ZeroDivisionError(error_msg)

        # This value could change if there is a minimum cementitious content activated when using an SCM
        abs_volume = content / (relative_density * water_density)
        if cementitious_type != "Cemento":
            self.doe_data_model.update_data('cementitious_material.scm.scm_abs_volume_temp', abs_volume * 1000)
        else:
            self.doe_data_model.update_data('cementitious_material.cement.cement_abs_volume_temp', abs_volume * 1000)

        return abs_volume

    def cementitious_content(self, water_content, w_cm, exposure_classes, scm_checked, scm_percentage=None,
                             wra_checked=False, wra_action_water_reducer=False, water_correction_wra=None):
        """
        Calculate the cementitious material content based on water content and water-to-cementitious
        materials ratio (w/cm). If supplementary cementitious materials (SCM) are used,
        this method also calculates the cement and SCM contents separately.

        If a WRA is used as a pure water reducer, the actual water-cement ratio will be lower.
        However, for cementitious content calculations within this scope, the water content without WRA correction
        is used. To do this, the water content received is added to the amount that was reduced when using the WRA.

        :param float water_content: The water content in kg/m³ for the concrete mix.
        :param float w_cm: The water-to-cementitious materials ratio.
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['XC1', 'XS2', 'XF4', 'XA1']).
        :param bool scm_checked: True if a supplementary cementitious material is used, otherwise False.
        :param int scm_percentage: Percentage of total cementitious material that is SCM.
        :param bool wra_checked: True if a water-reducing admixture is used, otherwise False.
        :param bool wra_action_water_reducer: True if a water-reducing admixture is used as a pure water reducer,
                                              otherwise False.
        :param float water_correction_wra: The water content without the WRA correction.
        :return: A tuple containing the cement content and SCM content, respectively (in kg/m³).
        :rtype: tuple[float, float]
        """

        if wra_checked and wra_action_water_reducer:
            water_content = water_content + (-water_correction_wra)
            self.doe_data_model.update_data('water.water_content.without_wra_correction', water_content)

        # Determine minimum required cementitious content based on exposure classes
        min_cementitious_content = max(
            MIN_CEMENTITIOUS_CONTENT_DOE.get(exposure_class, 0) for exposure_class in exposure_classes)

        # Initialize variables
        initial_cementitious_content = 0
        final_cementitious_content = 0
        cement_content = 0
        scm_content = 0

        # Calculate only cement content
        if not scm_checked:
            # Calculate the initial cementitious content from water content and w/cm ratio
            initial_cementitious_content = water_content / w_cm

            # Ensure cementitious content is not less than the minimum required
            final_cementitious_content = max(initial_cementitious_content, min_cementitious_content)

            # Since SCM is not used, cement content equals total cementitious content
            cement_content = final_cementitious_content
            scm_content = 0

        # Calculate cement and SCM content
        elif scm_checked and scm_percentage is not None:
            # First calculate cement and SCM content based on initial w/cm
            cement_content = ((100 - scm_percentage) * water_content) / ((100 - 0.70 * scm_percentage) * w_cm)
            scm_content = (scm_percentage * cement_content) / (100 - scm_percentage)

            # Calculate the initial cementitious content from the sum of the cement and SCM contents
            initial_cementitious_content = cement_content + scm_content

            # Ensure cementitious content is not less than the minimum required
            final_cementitious_content = max(initial_cementitious_content, min_cementitious_content)

            if final_cementitious_content != initial_cementitious_content:
                # Recalculate the w/cm ratio
                w_cm = water_content / final_cementitious_content

                cement_content = ((100 - scm_percentage) * water_content) / ((100 - 0.70 * scm_percentage) * w_cm)
                scm_content = (scm_percentage * cement_content) / (100 - scm_percentage)

        # Store intermediate values in the data model
        self.doe_data_model.update_data('cementitious_material.base_content', initial_cementitious_content)
        self.doe_data_model.update_data('cementitious_material.min_content', min_cementitious_content)
        self.doe_data_model.update_data('cementitious_material.final_content', final_cementitious_content)
        # This value could change if there is a minimum cementitious content activated when using an SCM
        self.doe_data_model.update_data('cementitious_material.cement.cement_content_temp', cement_content)
        self.doe_data_model.update_data('cementitious_material.scm.scm_content_temp', scm_content)

        return cement_content, scm_content

@dataclass
class Cement(CementitiousMaterial):
    cement_class: str

@dataclass
class SCM(CementitiousMaterial):
    scm_checked: bool
    scm_type: str
    scm_percentage: int

@dataclass
class Water:
    density: float
    doe_data_model: DOEDataModel = field(init=False, repr=False)

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
            self.doe_data_model.add_calculation_error('Water volume', error_msg)
            raise ValueError(error_msg)

        return water_content / density

    def water_content(self, slump_range, nms, agg_types, entrained_air, scm_checked=False, scm_percentage=None,
                      wra_checked=False, wra_action_cement_economizer=False, wra_action_water_reducer=False,
                      effectiveness=None):
        """
        Calculate the required water content for concrete, adjusting based on slump, nominal maximum
        size of aggregate (NMS) and aggregate types. If SCM or WRA is used, it is also taken into account for
        water calculation.

        If a WRA is used as a cement economizer or pure water reducer, then the reduction will be effective,
        otherwise it will not.

        :param str slump_range: Slump range of the concrete in fresh state (in mm).
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param tuple[str, str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                               (e.g., ("No triturada", "Triturada")).
        :param bool entrained_air: True if the mixture is air-entrained, otherwise False.
        :param bool scm_checked: True if an SCM is used, otherwise False.
        :param int scm_percentage: Percentage of total cementitious material that is SCM.
        :param bool wra_checked: True if a water-reducing admixture is used, otherwise False.
        :param bool wra_action_cement_economizer: True if a water-reducing admixture is used as a cement economizer,
                                                  otherwise False.
        :param bool wra_action_water_reducer: True if a water-reducing admixture is used as a pure water reducer,
                                              otherwise False.
        :param float effectiveness: WRA effectiveness percentage.
        :return: The water content (in kg/m³).
        :rtype: float
        """

        # Slump ranges
        slump_ranges = ["0 mm - 10 mm", "10 mm - 30 mm", "30 mm - 60 mm", "60 mm - 180 mm"]
        index = slump_ranges.index(slump_range)

        # Reduce the slump range if the mix is air-entrained
        if entrained_air and index != 0:
            index -= 1

        # Select the slump range
        slump_range = slump_ranges[index]

        # Get the base water content
        water_content_for_coarse = WATER_CONTENT.get(nms, {}).get(agg_types[0], {}).get(slump_range)
        water_content_for_fine = WATER_CONTENT.get(nms, {}).get(agg_types[1], {}).get(slump_range)

        if water_content_for_coarse is None or water_content_for_fine is None:
            valid_nms = list(WATER_CONTENT.keys())
            error_msg = f"The NMS ({nms}) is not valid. Valid NMS values are: {valid_nms}"
            self.doe_data_model.add_calculation_error('Water content', error_msg)
            raise ValueError(error_msg)

        # Calculate water content based on aggregate types
        if water_content_for_coarse != water_content_for_fine:
            water_content = (2/3) * water_content_for_fine + (1/3) * water_content_for_coarse
        else:
            water_content = water_content_for_coarse

        # Initialize water corrections
        water_correction_scm = 0
        water_correction_wra = 0

        # Apply SCM corrections if applicable
        if scm_checked:
            # Determine the SCM percentage range
            if 10 <= scm_percentage < 20:
                scm_percentage_range = '10-20'
            elif 20 <= scm_percentage < 30:
                scm_percentage_range = '20-30'
            elif 30 <= scm_percentage < 40:
                scm_percentage_range = '30-40'
            elif 40 <= scm_percentage < 50:
                scm_percentage_range = '40-50'
            elif scm_percentage >= 50:
                scm_percentage_range = '50'
            else:  # Handle case for scm_percentage < 10
                scm_percentage_range = None
                error_msg = f"SCM percentage ({scm_percentage}%) is less than 10%. No water correction applied"
                self.doe_data_model.add_calculation_error('Water content', error_msg)

            # Get water correction value if a valid percentage range is determined
            if scm_percentage_range:
                water_correction_scm = - WATER_CONTENT_REDUCTION.get(scm_percentage_range, {}).get(slump_range, 0)

        # Apply WRA corrections if applicable
        if wra_checked and (wra_action_cement_economizer or wra_action_water_reducer):
            water_correction_wra = -(effectiveness / 100) * water_content

        # Store intermediate values in data model
        self.doe_data_model.update_data('water.water_content.base_agg_fine', water_content_for_fine)
        self.doe_data_model.update_data('water.water_content.base_agg_coarse', water_content_for_coarse)
        self.doe_data_model.update_data('water.water_content.base', water_content)
        self.doe_data_model.update_data('water.water_content.scm_correction', water_correction_scm)
        self.doe_data_model.update_data('water.water_content.wra_correction', water_correction_wra)

        # Apply corrections to base water content
        final_water_content = water_content + water_correction_scm + water_correction_wra

        return final_water_content

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
    entrained_air: bool
    user_defined: float
    exposure_defined: float
    doe_data_model: DOEDataModel = field(init=False, repr=False)

    @staticmethod
    def entrapped_air_volume():
        """
        Calculate the estimated amount of entrapped air in non-air-entrained concrete.

        :return: The entrapped air volume (in m³).
        :rtype: int
        """

        return 0

    @staticmethod
    def entrained_air_volume(exposure_classes):
        """
        Calculate the required entrained air volume for concrete subject to freezing-and-thawing conditions.

        Concrete subject to freezing-and-thawing Exposure Classes XF2, XF3, or XF4 shall be air entrained.
        This method determines the appropriate air content based on exposure classes.

        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['N/A', 'XD1', 'XF3', 'XA3']).
        :return: The entrained air volume in m³ (e.g., 0.05 for 5% air), or 0 if no air entrainment is required.
        :rtype: float
        """

        # Initialize the maximum value
        max_value = 0

        # Check if any of the provided exposure classes require air entrainment
        for exposure_class in exposure_classes:
            # Get the air content table for the exposure class
            air_content_table = ENTRAINED_AIR.get("DoE", {}).get(exposure_class)

            # Skip if this exposure class isn't defined in our tables
            if air_content_table is None:
                continue

            # Update max_value if current air_content_table is greater
            if air_content_table > max_value:
                max_value = air_content_table

        # Convert percentage to fraction
        entrained_air_fraction = max_value / 100

        # Return the calculated fraction
        return entrained_air_fraction

@dataclass
class Aggregate:
    agg_type: str
    relative_density: float
    loose_bulk_density: float
    compacted_bulk_density: float
    moisture_content: float
    moisture_absorption: float
    grading: dict
    doe_data_model: DOEDataModel = field(init=False, repr=False)

    def total_agg_content(self, cement_content, scm_content, water_content, entrained_air_content,
                          combined_relative_density):
        """
        Calculate the total aggregate content based on cement content, SCM, water and
        the wet density of fully compacted concrete.

        :param float cement_content: Cement content (in m³).
        :param float scm_content: Supplementary cementitious material content (in m³).
        :param float water_content: Water content (in m³).
        :param float entrained_air_content: Percentage of entrained air content (in decimal), if
                                            there is no entrained air, then entrained air is zero.
        :param float combined_relative_density: Relative density of the combined aggregate
                                                in the saturated surface-dry condition (SSD).
        :return: Total aggregate content (in m³).
        :rtype: float
        """

        line = DENSITY_COEFFICIENTS.get(combined_relative_density)

        if line is None:
            # If the value is not in the dictionary, we look for the two closest values
            keys = list(DENSITY_COEFFICIENTS.keys())

            # Find the closest values for interpolation
            if combined_relative_density < keys[0]:
                # If the value is less than the minimum, we use the first coefficient
                line = DENSITY_COEFFICIENTS[keys[0]]
                concrete_density = line[1] * water_content + line[0]
            elif combined_relative_density > keys[-1]:
                # If the value is greater than the maximum, we use the last coefficient
                line = DENSITY_COEFFICIENTS[keys[-1]]
                concrete_density = line[1] * water_content + line[0]
            else:
                # Interpolation between two closest values
                lower_key = max(key for key in keys if key < combined_relative_density)
                upper_key = min(key for key in keys if key > combined_relative_density)

                # Calculate densities using both coefficients
                lower_line = DENSITY_COEFFICIENTS[lower_key]
                upper_line = DENSITY_COEFFICIENTS[upper_key]

                lower_density = lower_line[1] * water_content + lower_line[0]
                upper_density = upper_line[1] * water_content + upper_line[0]

                # Linear interpolation
                slope = (upper_density - lower_density) / (upper_key - lower_key)
                concrete_density = lower_density + slope * (combined_relative_density - lower_key)
        else:
            # If the value is in the dictionary, we directly use the coefficients
            concrete_density = line[1] * water_content + line[0]

        # If the mixture is air-entrained, modify the calculated density
        if entrained_air_content:
            concrete_density = concrete_density - 10 * (entrained_air_content * 100) * combined_relative_density

        # Calculate the total aggregate content
        total_aggregate_content = concrete_density - (cement_content + scm_content) - water_content

        # Store intermediate values in the data model
        self.doe_data_model.update_data('concrete.combined_relative_density', combined_relative_density)
        self.doe_data_model.update_data('concrete.wet_density', concrete_density)
        self.doe_data_model.update_data('concrete.total_aggregate_content', total_aggregate_content)

        return total_aggregate_content

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
            self.doe_data_model.add_calculation_error(f"{aggregate_type} apparent volumen", error_msg)
            raise ZeroDivisionError(error_msg)

        LITERS_PER_CUBIC_METER = 1000
        # The loose bulk density is in kg/m³, so it is converted to kg/(L) by dividing by 1000
        return content / (loose_bulk_density / LITERS_PER_CUBIC_METER)

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
            self.doe_data_model.add_calculation_error(f"{aggregate_type} absolute volume", error_msg)
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
            self.doe_data_model.add_calculation_error('Aggregate moisture correction', error_msg)
            raise ValueError(error_msg)

        return ssd_content * ((100 + moisture_content) / denominator)

@dataclass
class FineAggregate(Aggregate):
    fineness_modulus: float

    def fine_content(self, passing_600, w_cm, slump_range, nms, total_agg_content):
        """
        Calculate the fine aggregate content in kilogram per cubic meter (kg/m³)

        :param float | int passing_600: Fine percentage passing through 600 µm sieve.
        :param float w_cm: Water-to-cementitious materials ratio (w/cm).
        :param int slump_range: Slump range of the concrete in fresh state (in mm).
        :param str nms: Nominal maximum size designation (e.g., "N/A (10 mm)")
        :param float total_agg_content: Total aggregate content in kg/m³.

        :return: The mass of saturated surface-dry (SSD) fine aggregate for a cubic meter of concrete in kg.
        :rtype: float
        """

        # Check the percentage passing 600 µm sieve
        if passing_600 is None:
            error_msg = "The percentage passing through the 600 µm sieve must have a value"
            self.doe_data_model.add_calculation_error('Fine Content', error_msg)
            raise KeyError(error_msg)

        # Find the coefficients for the given percentage passing 600 µm sieve
        fine_proportion_coeff = FINE_PROPORTION.get(nms, {}).get(slump_range, {}).get(passing_600)

        # If the exact value is not in the dictionary, interpolate
        if fine_proportion_coeff is None:
            # Standard percentage values for interpolation
            keys = [100, 80, 60, 40, 15] # Percentage passing 600 µm sieve

            # Find the closest values for interpolation
            if passing_600 > keys[0]:
                # If the value is greater than the maximum, use the maximum percentage
                fine_proportion_coeff = FINE_PROPORTION.get(nms, {}).get(slump_range, {}).get(keys[0])
                fine_proportion = fine_proportion_coeff[1] * w_cm + fine_proportion_coeff[0]
            elif passing_600 < keys[-1]:
                # If the value is less than the minimum, use the minimum percentage
                fine_proportion_coeff = FINE_PROPORTION.get(nms, {}).get(slump_range, {}).get(keys[-1])
                fine_proportion = fine_proportion_coeff[1] * w_cm + fine_proportion_coeff[0]
            else:
                # Interpolation between two closest values
                lower_percentage = max(key for key in keys if key < passing_600)
                upper_percentage = min(key for key in keys if key > passing_600)

                # Calculate proportion using both lines
                lower_fine_proportion_coeff = FINE_PROPORTION.get(nms, {}).get(slump_range, {}).get(lower_percentage)
                lower_fine_proportion = lower_fine_proportion_coeff[1] * w_cm + lower_fine_proportion_coeff[0]

                upper_fine_proportion_coeff = FINE_PROPORTION.get(nms, {}).get(slump_range, {}).get(upper_percentage)
                upper_fine_proportion = upper_fine_proportion_coeff[1] * w_cm + upper_fine_proportion_coeff[0]

                # Linear interpolation
                slope = (upper_fine_proportion - lower_fine_proportion) / (upper_percentage - lower_percentage)
                fine_proportion = lower_fine_proportion + slope * (passing_600 - lower_percentage)
        else:
            # Calculate the fine proportion using the polynomial coefficients
            fine_proportion = fine_proportion_coeff[1] * w_cm + fine_proportion_coeff[0]

        # Store intermediate values in the data model
        self.doe_data_model.update_data('fine_aggregate.fine_proportion', fine_proportion)

        # Calculate the total fine content (in SSD condition)
        fine_content_ssd = total_agg_content * (fine_proportion / 100.0)  # Convert percentage to fraction

        return fine_content_ssd

@dataclass
class CoarseAggregate(Aggregate):
    nominal_max_size: str

    @staticmethod
    def coarse_content(total_agg_content, fine_content_ssd):
        """
        Calculate the coarse content in kilogram per cubic meter (kg/m³).

        :param float fine_content_ssd: Fine aggregate content (in m³).
        :param float total_agg_content: Total aggregate content in kg/m³.
        :return: The mass of saturated surface-dry (SSD) coarse aggregate for a cubic meter of concrete in kg.
        :rtype: float
        """

        coarse_content_ssd = total_agg_content - fine_content_ssd

        return coarse_content_ssd

@dataclass
class FreshConcrete:
    slump_range: str

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
    user_defined_margin: int
    doe_data_model: DOEDataModel = field(init=False, repr=False)

    def target_strength(self, design_strength, std_dev_known, std_dev_value, sample_size, defective_level,
                        std_dev_unknown, user_defined_margin, entrained_air_content):
        """
        Calculate the target (or required average compressive) strength based on design strength and variability parameters.

        :param int design_strength: The design strength of the concrete in megapascals (MPa).
        :param bool std_dev_known: True if the standard deviation is known.
        :param float std_dev_value: The value of the standard deviation in megapascals (MPa).
        :param int sample_size: The number of samples.
        :param str defective_level: The defective level key used to obtain the z-value.
        :param bool std_dev_unknown: True if the standard deviation is unknown.
        :param int user_defined_margin: A user-specified margin for strength calculation.
        :param float entrained_air_content: Percentage of entrained air content (in decimal), if
                                            there is no entrained air, then entrained air is zero.
        :return: The target strength in megapascals (MPa).
        """

        # Initialize the variable
        f_cr = 0
        std_dev_value_1 = 0
        std_dev_value_2 = 0

        # Case 1: The margin is specified by the user (the standard deviation is unknown)
        if user_defined_margin >= 0 and std_dev_unknown:
            f_cr = design_strength + user_defined_margin

        # Case 2: The standard deviation is known
        elif std_dev_known:
            z = QUARTILES.get(defective_level)  # Get z value (quartile) based on defective level

            if sample_size < 20:  # Curve A
                if design_strength <= 20:
                    std_dev_value_1 = std_dev_value
                    std_dev_value_2 = 0.4 * design_strength
                    std_dev_value = max(std_dev_value_1, std_dev_value_2)
                    f_cr = design_strength - z * std_dev_value
                else:
                    std_dev_value_1 = std_dev_value
                    std_dev_value_2 = 8
                    std_dev_value = max(std_dev_value_1, std_dev_value_2)
                    f_cr = design_strength - z * std_dev_value
            elif sample_size >= 20:  # Curve B
                if design_strength <= 20:
                    std_dev_value_1 = std_dev_value
                    std_dev_value_2 = 0.2 * design_strength
                    std_dev_value = max(std_dev_value_1, std_dev_value_2)
                    f_cr = design_strength - z * std_dev_value
                else:
                    std_dev_value_1 = std_dev_value
                    std_dev_value_2 = 4
                    std_dev_value = max(std_dev_value_1, std_dev_value_2)
                    f_cr = design_strength - z * std_dev_value

            # Update the DoE data model with intermediate values
            self.doe_data_model.update_data('spec_strength.target_strength.z_value', z)
            self.doe_data_model.update_data('spec_strength.target_strength.std_dev_value_1', std_dev_value_1)
            self.doe_data_model.update_data('spec_strength.target_strength.std_dev_value_2', std_dev_value_2)
            self.doe_data_model.update_data('spec_strength.target_strength.std_dev_used', std_dev_value)
            self.doe_data_model.update_data('spec_strength.target_strength.margin', user_defined_margin)

        else:
            # If no condition is met, raises a value error exception
            error_msg = f"The 'std_dev_known' and 'std_dev_unknown' values are {std_dev_known} and {std_dev_unknown} respectively"
            self.doe_data_model.add_calculation_error('Target strength', error_msg)
            raise ValueError(error_msg)

        # Target strength for air-entrained concrete
        if entrained_air_content:
            f_cr = f_cr / (1 - 0.055 * (entrained_air_content * 100))

        return f_cr

@dataclass
class AbramsLaw:
    doe_data_model: DOEDataModel = field(init=False, repr=False)

    def water_cementitious_materials_ratio(self, cement_class, agg_types, target_strength, target_strength_time,
                                           exposure_classes, scm_checked):
        """
        Calculate the water-to-cementitious materials ratio (w/cm) based on strength requirements
        and exposure conditions.

        This method determines the appropriate w/cm ratio by:
        1. Finding the starting strength at a w/cm ratio of 0.5 for the given cement class and aggregate types
        2. Interpolating between strength curves to create a custom relationship specific to the inputs
        3. Solving for the w/cm ratio that would achieve the target strength
        4. Checking durability requirements based on exposure classes
        5. Selecting the more restrictive (lower) w/cm ratio to satisfy both strength and durability

        :param str cement_class: Cement strength class (e.g., "42.5", "52.5")
        :param tuple[str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                                            (e.g., ("Triturada", "No triturada")).
        :param float target_strength: The target compressive strength of concrete in MPa.
        :param str target_strength_time: The expected time to reach the target strength,
                                         also known as the age of the test (e.g., "7 días", "27 días", "90 días").
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['XC1', 'XS2', 'XF4', 'XA1']).
        :param bool scm_checked: True if an SCM is used, otherwise False.
        :return: The recommended water-to-cementitious materials ratio.
        :rtype: float
        """

        # Initialize the variable
        index = 0

        # Calculate w/cm ratio based on target strength
        # Selected the starting point (w/cm -> 0.50; f_0)
        f_0_for_coarse = STARTING_STRENGTH.get(cement_class, {}).get(agg_types[0], {}).get(target_strength_time)
        f_0_for_fine = STARTING_STRENGTH.get(cement_class, {}).get(agg_types[1], {}).get(target_strength_time)

        # Get the average value if the coarse and fine aggregate type are different
        f_0 = (f_0_for_coarse + f_0_for_fine) / 2 # If they are the same this does not change its value

        # Create the list with all the third degree polynomials that represent the fitted curves
        polynomials = [Polynomial(coefficients) for coefficients in W_CM_COEFFICIENTS.values()] # From the lowest curve to the highest

        # 1. Find between which curves the starting point f_0 is located
        vals = [p(0.5) for p in polynomials]
        for i in range(len(vals) - 1):
            if vals[i] <= f_0 <= vals[i+1]:
                index = i
                break

        # 2. Find the fraction "alpha"
        alpha = (f_0 - vals[index]) / (vals[index + 1] - vals[index])

        # 3. Create the interpolated polynomial
        p_i = polynomials[index]
        p_i1 = polynomials[index + 1]

        p_diff = Polynomial(np.subtract(p_i1.coef, p_i.coef))
        p_star_coef = np.add(p_i.coef, alpha * p_diff.coef)
        p_star = Polynomial(p_star_coef)

        # 4. Solve for the target strength value
        p_equation = Polynomial(np.copy(p_star_coef))
        p_equation.coef[0] -= target_strength  # subtract target_strength from the independent term

        roots = p_equation.roots() # it returns the roots (possibly complex)

        # 5. Choose the real root in the range [0.3, 0.9]
        x_candidates = [r.real for r in roots if abs(r.imag) < 1e-7]
        x_valid = [r for r in x_candidates if 0.3 <= r <= 0.9]

        if len(x_valid) == 0:
            error_msg = "No solution found in the expected range"
            self.doe_data_model.add_calculation_error('Water-cement ratio', error_msg)
            raise KeyError(error_msg)
        else:
            # It could be more than one, but usually only one
            w_cm_by_strength = x_valid[0]

        # Calculate w/cm ratio based on durability requirements
        # The most restrictive (lowest) w/cm from all exposure classes is selected
        if not scm_checked:
            w_cm_by_durability = [MAX_W_CM_DOE.get(exposure_class, 1.0) for exposure_class in exposure_classes]
            w_cm_by_durability = min(w_cm_by_durability)
        else: # If an SCM is used, do not compare the w/cm calculated above with the limits, as this will be done later
            w_cm_by_durability = 1

        # Store intermediate calculation results in the DoE data model for reference
        self.doe_data_model.update_data('water_cementitious_materials_ratio.w_cm_curve', p_star)
        self.doe_data_model.update_data('water_cementitious_materials_ratio.w_cm_by_strength', w_cm_by_strength)
        self.doe_data_model.update_data('water_cementitious_materials_ratio.w_cm_by_durability', w_cm_by_durability)
        self.doe_data_model.update_data('water_cementitious_materials_ratio.w_cm_previous', min(w_cm_by_strength, w_cm_by_durability))

        # Return the more restrictive (lower) w/cm ratio to satisfy both strength and durability
        return min(w_cm_by_strength, w_cm_by_durability)

@dataclass
class Admixture:
    doe_data_model: DOEDataModel = field(init=False, repr=False)

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
            self.doe_data_model.add_calculation_error('Admixture content', error_msg)
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
            self.doe_data_model.add_calculation_error('Admixture volume', error_msg)
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

@dataclass
class AEA(Admixture):
    aea_checked: bool
    relative_density: float
    dosage: float


# ------------------------------------------------ Main class ------------------------------------------------
class DOE:
    def __init__(self, data_model, doe_data_model):
        """
        Initialize the DoE calculation engine.
        :param data_model: An instance of the data model containing all necessary design data.
        """

        self.data_model: RegularConcreteDataModel = data_model  # Connect to the global data model
        self.doe_data_model: DOEDataModel = doe_data_model # Connect to the DoE data model
        self.logger = Logger(__name__)  # Initialize the logger
        self.logger.info('Calculation mode for the DoE method has initialized')

        # References to material components (they will be created in load_inputs method)
        self.cement = None
        self.scm = None
        self.water = None
        self.air = None
        self.fine_agg = None
        self.coarse_agg = None
        self.fresh_concrete = None
        self.hardened_concrete = None
        self.std_deviation = None
        self.abrams_law = None
        self.wra = None
        self.aea = None

        # Dictionary to store the calculated results for later use in the report
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
            user_defined_margin = self.data_model.get_design_value('field_requirements.strength.std_dev_unknown.margin')
            if self.data_model.units == "MKS":
                design_strength = self.convert_value(design_strength, "stress")
                std_dev_value = self.convert_value(std_dev_value, "stress")
                user_defined_margin = self.convert_value(user_defined_margin, "stress")

            # Instantiate the components with their corresponding data
            self.cement = Cement(
                relative_density=self.data_model.get_design_value('cementitious_materials.cement_relative_density'),
                cement_class=self.data_model.get_design_value("cementitious_materials.cement_class")
            )
            self.scm = SCM(
                relative_density=self.data_model.get_design_value('cementitious_materials.SCM.SCM_relative_density'),
                scm_checked=self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked'),
                scm_type=self.data_model.get_design_value('cementitious_materials.SCM.SCM_type'),
                scm_percentage=self.data_model.get_design_value('cementitious_materials.SCM.SCM_content')
            )
            self.water = Water(density=self.data_model.get_design_value('water.water_density'))
            self.air = Air(
                entrained_air=self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked'),
                user_defined=self.data_model.get_design_value('field_requirements.entrained_air_content.user_defined'),
                exposure_defined=self.data_model.get_design_value('field_requirements.entrained_air_content.exposure_defined')
            )
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
            self.fresh_concrete = FreshConcrete(slump_range=self.data_model.get_design_value("field_requirements.slump_range"))
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
                user_defined_margin=user_defined_margin
            )
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
            self.aea = AEA(
                aea_checked=self.data_model.get_design_value('chemical_admixtures.AEA.AEA_checked'),
                relative_density=self.data_model.get_design_value('chemical_admixtures.AEA.AEA_relative_density'),
                dosage=self.data_model.get_design_value('chemical_admixtures.AEA.AEA_dosage')
            )

            # Connect to the DoE data model
            self.cement.doe_data_model = self.doe_data_model
            self.scm.doe_data_model = self.doe_data_model
            self.water.doe_data_model = self.doe_data_model
            self.air.doe_data_model = self.doe_data_model
            self.fine_agg.doe_data_model = self.doe_data_model
            self.coarse_agg.doe_data_model = self.doe_data_model
            self.std_deviation.doe_data_model = self.doe_data_model
            self.abrams_law.doe_data_model = self.doe_data_model
            self.wra.doe_data_model = self.doe_data_model
            self.aea.aci_data_model = self.doe_data_model

            self.logger.debug("Input data loaded and converted successfully")
        except Exception as e:
            self.logger.error(f"Error loading or converting input data: {str(e)}")
            raise

    def perform_calculations(self):
        """
        Execute the full calculation sequence using the material objects.
        If any step fails, log the error and stop the calculation.

        The calculated values are stored in self.calculation_results, which is then used
        to update the DoE data model.

        :return: True if the calculations were successful, False otherwise.
        """

        try:
            # A. Air Content
            entrained_air = self.air.entrained_air
            exposure_classes = list(self.hardened_concrete.exposure_classes.values())
            entrained_air_content = 0
            entrapped_air_content = 0

            if entrained_air:
                if self.air.exposure_defined:
                    entrained_air_content = self.air.entrained_air_volume(exposure_classes)
                else:
                    entrained_air_content = self.air.user_defined / 100
            else:
                entrapped_air_content = self.air.entrapped_air_volume()

            # B. Target Strength
            design_strength = self.hardened_concrete.design_strength
            std_dev_known = self.std_deviation.std_dev_known
            std_dev_value = self.std_deviation.std_dev_value
            sample_size = self.std_deviation.sample_size
            defective_level = self.std_deviation.defective_level
            std_dev_unknown = self.std_deviation.std_dev_unknown
            user_defined_margin = self.std_deviation.user_defined_margin

            target_strength = self.std_deviation.target_strength(design_strength, std_dev_known, std_dev_value,
                                                                 sample_size, defective_level, std_dev_unknown,
                                                                 user_defined_margin, entrained_air_content)

            # C. Water-Cementitious Materials ratio, aka alpha or a/cm
            cement_class = self.cement.cement_class[:4]
            agg_types = (self.coarse_agg.agg_type, self.fine_agg.agg_type)
            target_strength_time = self.hardened_concrete.spec_strength_time
            scm_checked = self.scm.scm_checked

            w_cm = self.abrams_law.water_cementitious_materials_ratio(cement_class, agg_types, target_strength,
                                                                      target_strength_time, exposure_classes,
                                                                      scm_checked)

            # D. Water Content and Absolute Volume
            slump_range = self.fresh_concrete.slump_range
            nominal_max_size = self.coarse_agg.nominal_max_size
            scm_percentage = self.scm.scm_percentage
            wra_checked = self.wra.wra_checked
            wra_effectiveness = self.wra.effectiveness
            water_density = self.water.density
            wra_action_cement_economizer = self.wra.wra_action_cement_economizer
            wra_action_water_reducer = self.wra.wra_action_water_reducer

            water_content = self.water.water_content(slump_range, nominal_max_size, agg_types, entrained_air, scm_checked,
                                                     scm_percentage, wra_checked, wra_action_cement_economizer,
                                                     wra_action_water_reducer, wra_effectiveness)
            water_abs_volume = self.water.water_volume(water_content, water_density)

            # E. Cementitious Materials Content and Absolute Volume
            cement_relative_density = self.cement.relative_density
            scm_relative_density = self.scm.relative_density
            scm_type = self.scm.scm_type
            water_correction_wra = self.doe_data_model.get_data('water.water_content.wra_correction')

            cement_content, scm_content = self.cement.cementitious_content(water_content, w_cm, exposure_classes,
                                                                           scm_checked, scm_percentage, wra_checked,
                                                                           wra_action_water_reducer, water_correction_wra)
            cement_abs_volume = self.cement.absolute_volume(cement_content, water_density, cement_relative_density,
                                                            "Cemento")

            if scm_checked:
                scm_abs_volume = self.scm.absolute_volume(scm_content, water_density, scm_relative_density, scm_type)
            else:
                scm_abs_volume = 0

            # F. Review the Water-Cementitious Materials ratio
            if scm_checked:
                w_cm_recalculated = water_content / (cement_content + scm_content)
                w_cm_by_durability = min([MAX_W_CM_DOE.get(exposure_class, 1.0) for exposure_class in exposure_classes])
                self.doe_data_model.update_data('water_cementitious_materials_ratio.w_cm_by_durability',
                                                w_cm_by_durability)

                if w_cm_by_durability < w_cm_recalculated:
                    cement_content, scm_content = self.cement.cementitious_content(water_content, w_cm_by_durability,
                                                                                   exposure_classes, scm_checked,
                                                                                   scm_percentage, wra_checked,
                                                                                   wra_action_water_reducer,
                                                                                   water_correction_wra)
                    # If there is a change in the cementing materials, then their respective absolute volumes change
                    cement_abs_volume = self.cement.absolute_volume(cement_content, water_density,
                                                                    cement_relative_density,
                                                                    "Cemento")
                    scm_abs_volume = self.scm.absolute_volume(scm_content, water_density, scm_relative_density,
                                                              scm_type)
                    w_cm = w_cm_by_durability
                else:
                    w_cm = w_cm_recalculated
            else:
                w_cm_recalculated = water_content / (cement_content + scm_content)

                if w_cm_recalculated != w_cm: # If the minimum cementitious material has been selected, or a WRA has been
                    w_cm = w_cm_recalculated  # used as a cement economizer, then the w/cm ratio is adjusted.

            # G. Fine Content and Absolute Volume
            fine_relative_density = self.fine_agg.relative_density
            coarse_relative_density = self.coarse_agg.relative_density
            combined_relative_density = (fine_relative_density + coarse_relative_density) / 2
            passing_600 = self.fine_agg.grading["No. 30 (0,600 mm)"]

            # G.1. Determine the total aggregate content
            total_agg_content = self.fine_agg.total_agg_content(cement_content, scm_content, water_content,
                                                                entrained_air_content, combined_relative_density)

            fine_content_ssd = self.fine_agg.fine_content(passing_600, w_cm, slump_range, nominal_max_size, total_agg_content)
            fine_abs_volume = self.fine_agg.absolute_volume(fine_content_ssd, water_density, fine_relative_density,
                                                            'fine')

            # H. Coarse Content and Absolute Volume
            coarse_content_ssd = self.coarse_agg.coarse_content(total_agg_content, fine_content_ssd)
            coarse_abs_volume = self.coarse_agg.absolute_volume(coarse_content_ssd, water_density,
                                                                coarse_relative_density, 'coarse')

            # Moisture adjustments
            fine_moisture_content = self.fine_agg.moisture_content
            coarse_moisture_content = self.coarse_agg.moisture_content
            fine_moisture_absorption = self.fine_agg.moisture_absorption
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
            fine_loose_bulk_density = self.fine_agg.loose_bulk_density
            coarse_loose_bulk_density = self.coarse_agg.loose_bulk_density

            fine_volume = self.fine_agg.apparent_volume(fine_content_wet, fine_loose_bulk_density, "fine")
            coarse_volume = self.coarse_agg.apparent_volume(coarse_content_wet, coarse_loose_bulk_density, "coarse")

            # Admixture dosage
            wra_relative_density = self.wra.relative_density
            wra_dosage = self.wra.dosage
            aea_checked = self.aea.aea_checked
            aea_relative_density = self.aea.relative_density
            aea_dosage = self.aea.dosage
            total_cementitious_content = cement_content + scm_content

            # Water-Reducing Admixture
            if wra_checked:
                wra_content = self.wra.admixture_content(total_cementitious_content, wra_dosage)
                wra_volume = self.wra.admixture_volume(wra_content, water_density, wra_relative_density)
            else:
                wra_content = None
                wra_volume = None

            # Air-Entraining Admixture
            if aea_checked:
                aea_content = self.wra.admixture_content(total_cementitious_content, aea_dosage)
                aea_volume = self.wra.admixture_volume(aea_content, water_density, aea_relative_density)
            else:
                aea_content = None
                aea_volume = None

            # Convert absolute from m3 to L
            water_abs_volume = 1000 * water_abs_volume
            water_volume = 1000 * water_volume
            cement_abs_volume = 1000 * cement_abs_volume
            scm_abs_volume = 1000 * scm_abs_volume
            fine_abs_volume = 1000 * fine_abs_volume
            coarse_abs_volume = 1000 * coarse_abs_volume
            if entrained_air:
                entrained_air_content = 1000 * entrained_air_content
            else:
                entrapped_air_content = 1000 * entrapped_air_content
            if wra_checked:
                wra_volume = 1000 * wra_volume
            if aea_checked:
                aea_volume = 1000 * aea_volume

            # Add up all absolute volumes and contents
            if entrained_air:
                total_abs_volume = sum(
                    [water_abs_volume, cement_abs_volume, scm_abs_volume, fine_abs_volume, coarse_abs_volume,
                     entrained_air_content])
            else:
                total_abs_volume = sum(
                    [water_abs_volume, cement_abs_volume, scm_abs_volume, fine_abs_volume, coarse_abs_volume,
                     entrapped_air_content])

            total_content = sum(
                [water_content_correction, cement_content, scm_content, fine_content_wet, coarse_content_wet])

            # Store all the results in a dictionary
            self.calculation_results = {
                "target_strength_value": target_strength,
                "w_cm": w_cm,
                "entrapped_air_content": entrapped_air_content if not entrained_air else None,
                "entrained_air_content": entrained_air_content if entrained_air else None,
                "final_content": water_content,
                "water_content_correction": water_content_correction,
                "water_abs_volume": water_abs_volume,
                "water_volume": water_volume,
                "cement_content": cement_content,
                "cement_abs_volume": cement_abs_volume,
                "cement_volume": "-",
                "scm_content": scm_content if scm_checked else None,
                "scm_abs_volume": scm_abs_volume if scm_checked else None,
                "scm_volume": "-",
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
                "AEA_content": aea_content,
                "AEA_volume": aea_volume,
                "total_abs_volume": total_abs_volume,
                "total_content": total_content
            }

            self.logger.info(f"Calculations completed successfully")
            return True

        except Exception: # Capturing all exceptions to ensure robust calculation process
            self.logger.error("Error during calculations", exc_info=True)
            return False

    def update_data_model(self):
        """
        Update the DoE data model with the calculated results stored in self.calculation_results.
        """

        if not self.calculation_results:
            self.logger.error("No calculation results to update in the data model")
            return

        for key, value in self.calculation_results.items():
            # The key paths according to DoE data model schema
            if key == "target_strength_value":
                data_key = "spec_strength.target_strength.target_strength_value"
            elif key == "w_cm":
                data_key = "water_cementitious_materials_ratio.w_cm"
            elif key in ("entrapped_air_content", "entrained_air_content"):
                data_key = f"air.{key}"
            elif key == "final_content":
                data_key = f"water.water_content.{key}"
            elif key in ("water_content_correction", "water_abs_volume", "water_volume"):
                data_key = f"water.{key}"
            elif key in ("cement_content", "cement_abs_volume", "cement_volume"):
                data_key = f"cementitious_material.cement.{key}"
            elif key in ("scm_content", "scm_abs_volume", "scm_volume"):
                data_key = f"cementitious_material.scm.{key}"
            elif key in ("fine_content_ssd", "fine_content_wet", "fine_abs_volume", "fine_volume"):
                data_key = f"fine_aggregate.{key}"
            elif key in ("coarse_content_ssd", "coarse_content_wet", "coarse_abs_volume", "coarse_volume"):
                data_key = f"coarse_aggregate.{key}"
            elif key in ("WRA_content", "WRA_volume"):
                data_key = f"chemical_admixtures.WRA.{key}"
            elif key in ("AEA_content", "AEA_volume"):
                data_key = f"chemical_admixtures.AEA.{key}"
            elif key in ("total_abs_volume", "total_content"):
                data_key = f"summation.{key}"
            else:
                continue

            self.doe_data_model.update_data(data_key, value)
        self.logger.debug("DoE data model updated with calculation results")

    def run(self):
        """
        Execute the full DoE calculation process:
          1. Load input data.
          2. Perform calculations.
          3. Update the data model with the results.
        """

        self.logger.info("Starting DoE calculation process...")
        self.load_inputs()
        if self.perform_calculations():
            self.update_data_model()
            self.logger.info("DoE calculation process completed successfully")
            return True
        else:
            self.logger.error("DoE calculation process terminated due to an error")
            return False