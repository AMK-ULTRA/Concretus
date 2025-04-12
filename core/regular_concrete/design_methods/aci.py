from dataclasses import dataclass, field
from math import log, exp

from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.core.regular_concrete.models.aci_data_model import ACIDataModel
from Concretus.logger import Logger
from Concretus.settings import K_FACTOR, QUARTILES, WATER_CONTENT_NAE, WATER_CONTENT_AE, MAX_W_CM_ACI, \
    MIN_CEMENTITIOUS_CONTENT_ACI, ENTRAPPED_AIR, ENTRAINED_AIR, COEFFICIENTS, CONVERSION_FACTORS


# ------------------------------------------------ Class for materials ------------------------------------------------
@dataclass
class CementitiousMaterial:
    relative_density: float
    aci_data_model: ACIDataModel = field(init=False, repr=False)

    def absolute_volume(self, content, water_density, relative_density, cementitious_type=None):
        """
        Calculates the absolute volume of a cementitious material in cubic meters (m³).

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
            self.aci_data_model.add_calculation_error('Cementitious volume', error_msg)
            raise ZeroDivisionError(error_msg)
        return content / (relative_density * water_density)

    def cementitious_content(self, water_content, w_cm, nms, scm_checked, scm_percentage=None):
        """
        Calculate the cementitious material content based on water content, water-to-cementitious
        materials ratio (w/cm). If supplementary cementitious materials (SCM) are used,
        this method also calculates the cement and SCM contents separately.

        :param float water_content: The water content in kg/m³ for the concrete mix.
        :param float w_cm: The water-to-cementitious materials ratio.
        :param str nms: The nominal maximum size of the coarse aggregate.
        :param bool scm_checked: True if a supplementary cementitious material is used, otherwise False.
        :param int scm_percentage: Percentage of total cementitious material that is SCM.
        :return: A tuple containing the cement content and SCM content (in kg/m³).
        :rtype: tuple[float, float]
        """

        # Calculate the total cementitious content from water content and w/cm ratio
        initial_cementitious_content = water_content / w_cm

        # Check if the calculated cementitious content meets minimum requirements based on NMS
        min_cementitious_content = MIN_CEMENTITIOUS_CONTENT_ACI.get(nms, 0)

        # Ensure cementitious content is not less than the minimum required
        cementitious_content_final = max(initial_cementitious_content, min_cementitious_content)

        # Store intermediate values in the data model
        self.aci_data_model.update_data('cementitious_material.base_content', initial_cementitious_content)
        self.aci_data_model.update_data('cementitious_material.min_content', min_cementitious_content)

        # If SCM is used, calculate SCM content and cement content separately
        if scm_checked and scm_percentage is not None:
            # Calculate SCM content based on the specified percentage
            scm_content = cementitious_content_final * (scm_percentage / 100)

            # Calculate cement content (total cementitious content minus SCM content)
            cement_content = cementitious_content_final - scm_content

            return cement_content, scm_content
        else:
            # If no SCM is used, cement content equals total cementitious content
            cement_content = cementitious_content_final
            scm_content = 0

            return cement_content, scm_content

@dataclass
class Cement(CementitiousMaterial):
    pass

@dataclass
class SCM(CementitiousMaterial):
    scm_checked: bool
    scm_type: str
    scm_percentage: int

@dataclass
class Water:
    density: float
    aci_data_model: ACIDataModel = field(init=False, repr=False)

    def water_volume(self, water_content, density):
        """
        Calculates the volume of water in cubic meter (m³). For water, the absolute volume and total volume are the same.

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
            self.aci_data_model.add_calculation_error('Water volume', error_msg)
            raise ValueError(error_msg)

        return water_content / density

    def water_content(self, slump_range, nms, entrained_air, agg_types, scm=None, scm_percentage=None):
        """
        Calculates the required water content for concrete, adjusting based on slump, nominal maximum
        size of aggregate (NMS), air entrained and aggregate types. If SCM is used, it is also taken into account for
        water calculation.

        :param str slump_range: Slump range of the concrete in fresh state (in mm).
        :param str nms: Nominal maximum size of the coarse aggregate.
        :param bool entrained_air: True if the concrete is entrained air, otherwise False.
        :param tuple[str, str] agg_types: A tuple containing the type of coarse and fine aggregate, respectively
                               (e.g., ("Angular", "Natural")).
        :param str scm: Type of SCM (e.g., "Cenizas volantes", "Cemento de escoria", "Humo de sílice").
        :param int scm_percentage: Percentage of total cementitious material that is SCM.
        :return: The water content (in kg/m³).
        :rtype: float
        """

        # Select the correct dictionary according to the type of concrete (with or without entrained air)
        water_content_table = WATER_CONTENT_AE if entrained_air else WATER_CONTENT_NAE

        # Get the base water content
        water_content = water_content_table.get(slump_range, {}).get(nms)

        if water_content is None:
            valid_nms = list(next(iter(water_content_table.values())).keys())
            error_msg = f"The NMS ({nms}) is not valid. Valid NMS values are: {valid_nms}"
            self.aci_data_model.add_calculation_error('Water content', error_msg)
            raise ValueError(error_msg)

        # Initialize water corrections
        water_correction_coarse = 0
        water_correction_fine = 0
        water_correction_scm = 0

        # Adjust according to the type of aggregate
        if "Redondeada" in agg_types:
            water_correction_coarse = -0.08 * water_content
        if "Manufacturada" in agg_types:
            water_correction_fine = 0.05 * water_content

        # Adjust according to the type of SCM (if used)
        if scm and scm_percentage:
            if scm == "Cenizas volantes":
                multiplier = scm_percentage // 10
                reduction = (multiplier * 3) * 0.01
                water_correction_scm = -reduction * water_content
            elif scm == "Cemento de escoria":
                multiplier = scm_percentage // 10
                reduction = (multiplier * 5) * 0.01
                water_correction_scm = -reduction * water_content

        # Store intermediate values in data model
        self.aci_data_model.update_data('water.water_content.base', water_content)
        self.aci_data_model.update_data('water.water_content.coarse_aggregate_correction', water_correction_coarse)
        self.aci_data_model.update_data('water.water_content.fine_aggregate_correction', water_correction_fine)
        self.aci_data_model.update_data('water.water_content.scm_correction', water_correction_scm)

        # Apply corrections to base water content
        final_water_content = water_content + water_correction_coarse + water_correction_fine + water_correction_scm

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
    aci_data_model: ACIDataModel = field(init=False, repr=False)

    def entrapped_air_volume(self, nms):
        """
        Calculate the estimated amount of entrapped air in non-air-entrained concrete.

        This method converts the percentage of entrapped air (based on the nominal maximum size of the aggregate)
        to a volume fraction.

        :param str nms: The nominal maximum size of the coarse aggregate.
        :return: The entrapped air volume (in m³).
        :rtype: float
        """

        # Look up the entrapped air percentage for the given NMS
        entrapped_air = ENTRAPPED_AIR.get(nms)

        # Validate that a value was found for the provided NMS
        if entrapped_air is None:
            valid_nms = list(ENTRAPPED_AIR.keys())
            error_msg = f"The NMS ({nms}) is outside the valid NMS. Valid NMS -> {valid_nms}"
            self.aci_data_model.add_calculation_error('Entrapped air', error_msg)
            raise ValueError(error_msg)

        # Convert from percentage to fraction
        entrapped_air_fraction = entrapped_air / 100

        return entrapped_air_fraction

    def entrained_air_volume(self, nms, exposure_classes):
        """
        Calculate the required entrained air volume for concrete subject to freezing-and-thawing conditions.

        Concrete subject to freezing-and-thawing Exposure Classes F1, F2, or F3 shall be air entrained.
        This method determines the appropriate air content based on exposure classes and NMS.

        :param str nms: The nominal maximum size of the coarse aggregate.
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['F0', 'W0', 'S1', 'C2']).
        :return: The entrained air volume (in m³), or 0 if no air entrainment is required.
        :rtype: float
        """

        # Default to no entrained air
        entrained_air_fraction = 0

        # Check if any of the provided exposure classes require air entrainment
        for exposure_class in exposure_classes:
            # Look for exposure classes that begin with 'F' (freezing conditions)
            if exposure_class.startswith('F') and exposure_class != 'F0':
                # Get the air content table for the exposure class
                air_content_table = ENTRAINED_AIR.get("ACI", {}).get(exposure_class)

                # Skip if this exposure class isn't defined in our tables
                if air_content_table is None:
                    continue

                # Look up the required air content for the given NMS
                air_content = air_content_table.get(nms)

                # Validate that a value was found for the provided NMS
                if air_content is None:
                    # Get a reference to any valid exposure class table to extract valid NMS values
                    valid_class = next(iter(ENTRAINED_AIR["ACI"]))
                    valid_nms = list(ENTRAINED_AIR["ACI"][valid_class].keys())
                    error_msg = f"The NMS ({nms}) is outside the valid NMS. Valid NMS -> {valid_nms}"
                    self.aci_data_model.add_calculation_error('Entrained air', error_msg)
                    raise ValueError(error_msg)

                # Convert from percentage to fraction
                entrained_air_fraction = air_content / 100

                return entrained_air_fraction

        # If no applicable exposure class was found, return 0
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
    aci_data_model: ACIDataModel = field(init=False, repr=False)

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
            self.aci_data_model.add_calculation_error(f"{aggregate_type} apparent volumen", error_msg)
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
            self.aci_data_model.add_calculation_error(f"{aggregate_type} absolute volume", error_msg)
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
            self.aci_data_model.add_calculation_error('Aggregate moisture correction', error_msg)
            raise ValueError(error_msg)

        return ssd_content * ((100 + moisture_content) / denominator)

@dataclass
class FineAggregate(Aggregate):
    fineness_modulus: float

    def fine_content(self, water_volume, air_volume, cement_abs_volume, scm_abs_volume, coarse_abs_volume,
                     fine_relative_density, water_density):
        """
        Calculate the fine aggregate content in kilogram per cubic meter (kg/m³) using the absolute volume method.
        This method determines the fine aggregate content by subtracting the sum of all other concrete
        component volumes from the unit volume of concrete (1 m³).

        :param float water_volume: Volume of water (in m³).
        :param float air_volume: Volume of air (in m³).
        :param float cement_abs_volume: Absolute volume of cement (in m³).
        :param float scm_abs_volume: Absolute volume of supplementary cementitious materials (in m³).
        :param float coarse_abs_volume: Absolute volume of coarse aggregate (in m³).
        :param float fine_relative_density: Fine aggregate relative density (SSD).
        :param float water_density: Water density in kg/m³.
        :return: The mass of saturated surface-dry (SSD) fine aggregate for a cubic meter of concrete in kg.
        :rtype: float
        """

        if fine_relative_density == 0:
            error_msg = f"The fine aggregate relative density is {water_density}. It cannot can be zero"
            self.aci_data_model.add_calculation_error('Fine content', error_msg)
            raise ValueError(error_msg)

        if water_density == 0:
            error_msg = f"The water density is {water_density}. It cannot can be zero"
            self.aci_data_model.add_calculation_error('Fine content', error_msg)
            raise ValueError(error_msg)

        # Total volume except for fine aggregate
        partial_volume = water_volume + air_volume + cement_abs_volume + scm_abs_volume + coarse_abs_volume

        # The calculated absolute volume of fine aggregate
        fine_abs_volume = 1 - partial_volume

        # Check if the calculated fine aggregate volume is valid
        if fine_abs_volume <= 0:
            error_msg = "Calculated fine aggregate volume is negative or zero. The sum of other component volumes exceeds 1 m³"
            self.aci_data_model.add_calculation_error('Fine content', error_msg)
            raise ValueError(error_msg)

        # The mass of SSD fine aggregate
        fine_content_ssd = fine_abs_volume * fine_relative_density * water_density

        return fine_content_ssd

@dataclass
class CoarseAggregate(Aggregate):
    nominal_max_size: str

    def coarse_content(self, nms, fineness_modulus, compacted_bulk_density, absorption):
        """
        Calculate the coarse content in kilogram per cubic meter (kg/m³).

        :param str nms: The nominal maximum size of the coarse aggregate.
        :param float fineness_modulus: Fineness modulus of the fine aggregate.
        :param float compacted_bulk_density: Compacted bulk density of the coarse aggregate in kg/m³.
                                             Bulk density consolidated by Method A—Rodding according to the ASTM C29/C29M.
        :param float absorption: Absorption of the coarse aggregate in percentage.
        :return: The mass of saturated surface-dry (SSD) coarse aggregate for a cubic meter of concrete in kg.
        :rtype: float
        """

        # Validate input parameters
        if nms not in COEFFICIENTS:
            error_msg = f"Nominal maximum size ({nms}) not found in coefficients table"
            self.aci_data_model.add_calculation_error('Coarse content', error_msg)
            raise KeyError(error_msg)

        if fineness_modulus <= 0:
            error_msg = f"Fineness modulus must be positive"
            self.aci_data_model.add_calculation_error('Coarse content', error_msg)
            raise ValueError(error_msg)

        if compacted_bulk_density <= 0:
            error_msg = f"Compacted bulk density must be positive"
            self.aci_data_model.add_calculation_error('Coarse content', error_msg)
            raise ValueError(error_msg)

        # Get the coefficients for the linear regression
        a = COEFFICIENTS.get(nms, {}).get('a')
        b = COEFFICIENTS.get(nms, {}).get('b')

        # Volume of oven-dry-rodded coarse aggregate per unit volume of concrete
        bulk_volume = a * fineness_modulus + b

        # The oven-dry mass of coarse aggregate for a cubic meter of concrete
        coarse_content_dry = bulk_volume * compacted_bulk_density

        # Absorption will be taken into account to convert the dry-rodded mass to the corresponding SSD mass
        coarse_content_ssd = coarse_content_dry * (1 + absorption / 100)

        # Store intermediate values in the data model
        self.aci_data_model.update_data('coarse_aggregate.oven_dry_rodded_bulk_volume', bulk_volume)
        self.aci_data_model.update_data('coarse_aggregate.coarse_content_oven_dry', coarse_content_dry)

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
    aci_data_model: ACIDataModel = field(init=False, repr=False)

    def target_strength(self, design_strength, std_dev_known, std_dev_value, sample_size, defective_level, std_dev_unknown):
        """
        Calculate the target (or required average compressive) strength based on design strength and variability parameters.

        For std_dev_known == True and sample_size >= 15, it calculates two candidate strengths
        using a k-factor (from sample_size) and a z value (from defective_level), then uses the maximum.
        For std_dev_unknown == True, it uses predefined margins based on the design strength.

        :param int design_strength: The design strength of the concrete in megapascal (MPa).
        :param bool std_dev_known: True if the standard deviation is known.
        :param float std_dev_value: The value of the standard deviation in megapascal (MPa).
        :param int sample_size: The number of samples.
        :param str defective_level: The defective level key (used to obtain z value).
        :param bool std_dev_unknown: True if the standard deviation is unknown.
        :return: The target strength (in MPa).
        :rtype: float
        """

        # Case 1: The standard deviation is known and the sample size is greater than or equal to 15
        if std_dev_known and sample_size >= 15:
            k = K_FACTOR.get(sample_size, 1.00)  # Get k-factor based on sample size
            z = QUARTILES.get(defective_level)  # Get z value (quartile) based on defective level

            if design_strength <= 35:
                f_cr_1 = design_strength - z * k * std_dev_value
                f_cr_2 = design_strength - (z - 1) * k * std_dev_value - 3.5
            else:  # design_strength > 35
                f_cr_1 = design_strength - z * k * std_dev_value
                f_cr_2 = 0.9 * design_strength - (z - 1) * k * std_dev_value

            f_cr = max(f_cr_1, f_cr_2)

            # Update the ACI data model with intermediate values
            self.aci_data_model.update_data('spec_strength.target_strength.k_factor', k)
            self.aci_data_model.update_data('spec_strength.target_strength.z_value', z)
            self.aci_data_model.update_data('spec_strength.target_strength.f_cr_1', f_cr_1)
            self.aci_data_model.update_data('spec_strength.target_strength.f_cr_2', f_cr_2)

        # Case 2: The standard deviation is unknown
        elif std_dev_unknown:
            margin = None
            if design_strength < 21:
                margin = 7.0
            elif 21 <= design_strength <= 35:
                margin = 8.3
            elif design_strength > 35:
                margin = 5.0
                design_strength = 1.10 * design_strength

            # Update the data model for the margin
            if margin is not None:
                self.aci_data_model.update_data('spec_strength.target_strength.margin', margin)
                f_cr = design_strength + margin
            else:
                # If no margin was assigned, raises a value error exception
                error_msg = f"No margin found for the design strength: {design_strength}"
                self.aci_data_model.add_calculation_error('Target strength', error_msg)
                raise ValueError(error_msg)

        else:
            # If no condition is met, raises a value error exception
            error_msg = f"The 'std_dev_known' and 'std_dev_unknown' values are {std_dev_known} and {std_dev_unknown} respectively"
            self.aci_data_model.add_calculation_error('Target strength', error_msg)
            raise ValueError(error_msg)

        return f_cr

@dataclass
class AbramsLaw:
    aci_data_model: ACIDataModel = field(init=False, repr=False)

    def water_cementitious_materials_ratio(self, target_strength, entrained_air, exposure_classes):
        """
        Calculate the water-to-cementitious materials ratio (w/cm) based on Abrams' Law.

        This method determines the w/cm ratio considering both strength requirements and
        durability concerns related to exposure conditions. The lower of the two calculated
        values is returned to ensure both criteria are satisfied.

        :param float target_strength: The target compressive strength of concrete in MPa.
        :param bool entrained_air: Whether the concrete is air-entrained (True) or non-air-entrained (False).
        :param list[str] exposure_classes: A list containing all possible exposure classes, in no particular order,
                                           (e.g., ['F0', 'W0', 'S1', 'C2']).
        :return: The recommended water-to-cementitious materials ratio.
        :rtype: float
        """

        # Calculate w/cm ratio based on target strength
        # Different equations are used for air-entrained and non-air-entrained concrete
        if entrained_air:
            w_cm_by_strength = -0.368 * log(target_strength) + 1.7
        else:
            w_cm_by_strength = 1.1318 * exp(-0.025 * target_strength)

        # Calculate w/cm ratio based on durability requirements
        # The most restrictive (lowest) w/cm from all exposure classes is selected
        w_cm_by_durability = [MAX_W_CM_ACI.get(exposure_class, 1.0) for exposure_class in exposure_classes]
        w_cm_by_durability = min(w_cm_by_durability)

        # Store intermediate calculation results in the ACI data model for reference
        self.aci_data_model.update_data('water_cementitious_materials_ratio.w_cm_by_strength', w_cm_by_strength)
        self.aci_data_model.update_data('water_cementitious_materials_ratio.w_cm_by_durability', w_cm_by_durability)

        # Return the more restrictive (lower) w/cm ratio to satisfy both strength and durability
        return min(w_cm_by_strength, w_cm_by_durability)


# ------------------------------------------------ Main class ------------------------------------------------
class ACI:
    def __init__(self, data_model, aci_data_model):
        """
        Initialize the ACI calculation engine.
        :param data_model: An instance of the data model containing all necessary design data.
        """

        self.data_model: RegularConcreteDataModel = data_model  # Connect to the global data model
        self.aci_data_model: ACIDataModel = aci_data_model # Connect to the ACI data model
        self.logger = Logger(__name__)  # Initialize the logger
        self.logger.info('Calculation mode for the ACI method has initialized')

        # References to material components (they will be created in load_inputs)
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
        Loads data from the data model, performs unit conversion for selected parameters,
        and instantiates the necessary objects.
        """

        try:
            # Convert units if necessary
            design_strength = self.data_model.get_design_value('field_requirements.strength.spec_strength')
            std_dev_value = self.data_model.get_design_value('field_requirements.strength.std_dev_known.std_dev_value')
            if self.data_model.units == "MKS":
                design_strength = self.convert_value(design_strength, "stress")
                std_dev_value = self.convert_value(std_dev_value, "stress")

            # Instantiate the components with their corresponding data
            self.cement = Cement(
                relative_density=self.data_model.get_design_value('cementitious_materials.relative_density')
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
                    "field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled")
            )
            self.abrams_law = AbramsLaw()

            # Connect to the ACI data model
            self.cement.aci_data_model = self.aci_data_model
            self.scm.aci_data_model = self.aci_data_model
            self.water.aci_data_model = self.aci_data_model
            self.air.aci_data_model = self.aci_data_model
            self.fine_agg.aci_data_model = self.aci_data_model
            self.coarse_agg.aci_data_model = self.aci_data_model
            self.std_deviation.aci_data_model = self.aci_data_model
            self.abrams_law.aci_data_model = self.aci_data_model

            self.logger.debug("Input data loaded and converted successfully")
        except Exception as e:
            self.logger.error(f"Error loading or converting input data: {str(e)}")
            raise

    def perform_calculations(self):
        """
        Execute the full calculation sequence using the material objects.
        If any step fails, log the error and stop the calculation.

        The calculated values are stored in self.calculation_results, which is then used
        to update the ACI data model.

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

            target_strength = self.std_deviation.target_strength(design_strength, std_dev_known, std_dev_value,
                                                                 sample_size, defective_level, std_dev_unknown)

            # B. Water Content and Absolute Volume
            slump_range = self.fresh_concrete.slump_range
            nominal_max_size = self.coarse_agg.nominal_max_size
            entrained_air = self.air.entrained_air
            agg_types = (self.coarse_agg.agg_type, self.fine_agg.agg_type)
            scm = self.scm.scm_type
            scm_percentage = self.scm.scm_percentage
            water_density = self.water.density

            water_content = self.water.water_content(slump_range, nominal_max_size, entrained_air, agg_types, scm, scm_percentage)
            water_abs_volume = self.water.water_volume(water_content, water_density)

            # C. Water-Cementitious Materials ratio, aka alpha or a/cm
            exposure_classes = list(self.hardened_concrete.exposure_classes.values())

            w_cm = self.abrams_law.water_cementitious_materials_ratio(target_strength, entrained_air, exposure_classes)

            # D. Cementitious Materials Content and Absolute Volume
            cement_relative_density = self.cement.relative_density
            scm_relative_density = self.scm.relative_density
            scm_type = self.scm.scm_type
            scm_checked = self.scm.scm_checked

            cement_content, scm_content = self.cement.cementitious_content(water_content, w_cm,
                                                                                          nominal_max_size, scm_checked,
                                                                                          scm_percentage)
            cement_abs_volume = self.cement.absolute_volume(cement_content, water_density, cement_relative_density)
            if scm_checked:
                scm_abs_volume = self.scm.absolute_volume(scm_content, water_density, scm_relative_density, scm_type)
            else:
                scm_abs_volume = 0

            # D.1. Review the Water-Cementitious Materials ratio
            w_cm_recalculated = water_content / (cement_content + scm_content)

            # If the minimum cementitious material has been selected, adjust the w/cm ratio
            if w_cm_recalculated != w_cm:
                w_cm = w_cm_recalculated

            # E. Air Content
            entrained_air_content = 0
            entrapped_air_content = 0

            if entrained_air:
                if self.air.exposure_defined:
                    entrained_air_content = self.air.entrained_air_volume(nominal_max_size, exposure_classes)
                else:
                    entrained_air_content = self.air.user_defined / 100
            else:
                entrapped_air_content = self.air.entrapped_air_volume(nominal_max_size)

            # F. Coarse Content and Absolute Volume
            fineness_modulus = self.fine_agg.fineness_modulus
            compacted_bulk_density = self.coarse_agg.compacted_bulk_density
            absorption = self.coarse_agg.moisture_absorption
            coarse_relative_density = self.coarse_agg.relative_density

            coarse_content_ssd = self.coarse_agg.coarse_content(nominal_max_size, fineness_modulus,
                                                                compacted_bulk_density, absorption)
            coarse_abs_volume = self.coarse_agg.absolute_volume(coarse_content_ssd, water_density,
                                                                coarse_relative_density, 'coarse')

            # G. Fine Content and Absolute Volume
            fine_relative_density = self.fine_agg.relative_density

            if entrained_air:
                fine_content_ssd = self.fine_agg.fine_content(water_abs_volume, entrained_air_content, cement_abs_volume,
                                                              scm_abs_volume, coarse_abs_volume, fine_relative_density,
                                                              water_density)
            else:
                fine_content_ssd = self.fine_agg.fine_content(water_abs_volume, entrapped_air_content, cement_abs_volume,
                                                              scm_abs_volume, coarse_abs_volume, fine_relative_density,
                                                              water_density)
            fine_abs_volume = self.fine_agg.absolute_volume(fine_content_ssd, water_density, fine_relative_density,
                                                            'fine')

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

            # Convert absolute from m3 to L
            water_abs_volume = 1000 * water_abs_volume
            water_volume = 1000 * water_volume
            cement_abs_volume = 1000 * cement_abs_volume
            fine_abs_volume = 1000 * fine_abs_volume
            coarse_abs_volume = 1000 * coarse_abs_volume
            scm_abs_volume = 1000 * scm_abs_volume
            if entrained_air:
                entrained_air_content = 1000 * entrained_air_content
            else:
                entrapped_air_content = 1000 * entrapped_air_content

            # Add up all absolute volumes and contents
            if entrained_air:
                total_abs_volume = sum(
                    [water_abs_volume, cement_abs_volume, scm_abs_volume, fine_abs_volume, coarse_abs_volume, entrained_air_content])
            else:
                total_abs_volume = sum(
                    [water_abs_volume, cement_abs_volume, scm_abs_volume, fine_abs_volume, coarse_abs_volume, entrapped_air_content])
            total_content = [water_content_correction, cement_content, scm_content, fine_content_wet, coarse_content_wet]
            total_sum = sum(round(value) for value in total_content)

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
                "total_abs_volume": total_abs_volume,
                "total_content": total_sum
            }

            self.logger.info(f"Calculations completed successfully")
            return True

        except Exception: # Capturing all exceptions to ensure robust calculation process
            self.logger.error("Error during calculations", exc_info=True)
            return False

    def update_data_model(self):
        """
        Update the ACI data model with the calculated results stored in self.calculation_results.
        """

        if not self.calculation_results:
            self.logger.error("No calculation results to update in the data model")
            return

        for key, value in self.calculation_results.items():
            # The key paths according to ACI data model schema
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
            elif key in ("total_abs_volume", "total_content"):
                data_key = f"summation.{key}"
            else:
                continue

            self.aci_data_model.update_data(data_key, value)
        self.logger.debug("ACI data model updated with calculation results")

    def run(self):
        """
        Execute the full ACI calculation process:
          1. Load input data.
          2. Perform calculations.
          3. Update the data model with the results.
        """

        self.logger.info("Starting ACI calculation process...")
        self.load_inputs()
        if self.perform_calculations():
            self.update_data_model()
            self.logger.info("ACI calculation process completed successfully")
            return True
        else:
            self.logger.error("ACI calculation process terminated due to an error")
            return False