from Concretus.logger import Logger


class DOEDataModel:

    def __init__(self):
        self.doe_data = self.create_empty_doe_data() # data model
        self.calculation_errors: dict[str, str] = {}  # dictionary with all the errors
        self.logger = Logger(__name__)
        self.logger.info("Data model for DoE method initialized")

    # -------------------------------------------- Design MCE data --------------------------------------------
    @staticmethod
    def create_empty_doe_data():
        """Create the empty design data for DoE method."""

        return {
            'cementitious_material': {
                'base_content': None,
                'min_content': None,
                'cement': {
                    'cement_content': None,
                    'cement_abs_volume': None,
                    'cement_volume': None
                },
                'scm': {
                    'scm_content': None,
                    'scm_abs_volume': None,
                    'scm_volume': None,
                }
            },
            'concrete': {
                'wet_density': None
            },
            'water': {
                'water_content': {
                    'base': None,
                    'scm_correction': None,
                    'final_content': None
                },
                'water_content_correction': None,
                'water_volume': None,
                'water_abs_volume': None
            },
            'air': {
                'entrapped_air_content': None,
                'entrained_air_content': None,
                'air_entraining_admixture_content': None
            },
            'fine_aggregate': {
                'fine_content_ssd': None,
                'fine_content_wet': None,
                'fine_abs_volume': None,
                'fine_volume': None,
                'fine_proportion': None
            },
            'coarse_aggregate': {
                'coarse_content_ssd': None,
                'coarse_content_wet': None,
                'coarse_abs_volume': None,
                'coarse_volume': None
            },
            'spec_strength': {
                'target_strength': {
                    'target_strength_value': None,
                    'std_dev_used': None,
                    'z_value': None,
                    'margin': None
                },
            },
            'water_cementitious_materials_ratio': {
                'w_cm': None,
                'w_cm_curve': None,
                'w_cm_by_strength': None,
                'w_cm_by_durability': None
            },
            'summation': {
                'total_abs_volume': None,
                'total_content': None
            }
        }

    def update_data(self, key_path, value):
        """
        Update a specific value using dot notation to access nested keys.

        :param str key_path: The key path to update, e.g. 'cementitious_material.cement.cement_content'.
        :param any value: The new value to update.
        """

        keys = key_path.split('.')
        data = self.doe_data

        try:
            for key in keys[:-1]:
                data = data[key]
            data[keys[-1]] = value
            self.logger.info(f"Updated {key_path} -> {value}")
        except KeyError as e:
            self.logger.error(f"Invalid key path: {key_path} ({str(e)})")
            raise

    def get_data(self, key_path):
        """
        Get the design value using dot notation (as key).

        :param str key_path: The key path to retrieve the value associated.
        :returns: Return the desired value.
        :rtype: any
        """

        keys = key_path.split('.')
        data = self.doe_data
        try:
            for key in keys:
                data = data[key]
            return data
        except KeyError as e:
            self.logger.error(f"Invalid key path: {key_path} ({str(e)})")
            raise

    # -------------------------------------------- Validation methods --------------------------------------------
    def add_calculation_error(self, section, message):
        """
        Add a calculation error with context.

        :param str section: Name of the section that failed.
        :param str message: Description of validation failure.
        """

        key = section.upper()
        # Only add the error if it is not already present
        if key not in self.calculation_errors:
            self.calculation_errors[key] = message
            self.logger.info(f"Calculation error: {key} -> {message}")

    def clear_calculation_errors(self, section=None):
        """
        Clear validation errors. If a section is provided, only the error associated with that section is cleared.

        :param str section: If provided, only the error associated with that section is cleared.
        """

        if section:
            key = section.upper()
            # Remove the error for the specified section if it exists
            self.calculation_errors.pop(key, None)
        else:
            # Clear all errors
            self.calculation_errors = {}

    # -------------------------------------------- Reset method --------------------------------------------

    def reset(self):
        """Reset all data while maintaining the structure."""

        self.doe_data = self.create_empty_doe_data()
        self.calculation_errors = {}
        self.logger.info("The data model for DoE method has been restored")