from PyQt6.QtCore import QObject, pyqtSignal

from settings import DEFAULT_UNITS_KEY, DEFAULT_LANGUAGE_KEY, INITIAL_STEP, LANGUAGES, UNIT_SYSTEM
from logger import Logger

class RegularConcreteDataModel(QObject):
    """
    Central data model for the concrete regular procedure.
    Manages all workflow and notifies components of changes.
    """

    # Create the main custom signals
    language_changed = pyqtSignal(str)  # Emit when the system language changes
    units_changed = pyqtSignal(str)     # Emit when the system of units changes
    method_changed = pyqtSignal(str)    # Emit when the design method changes
    step_changed = pyqtSignal(int)      # Emit when the workflow step changes

    def __init__(self):
        super().__init__()

        # Initialize the logger
        self.logger = Logger(__name__)

        # Default state
        self._current_step = INITIAL_STEP
        self._language = DEFAULT_LANGUAGE_KEY # Underlying variable
        self._units = DEFAULT_UNITS_KEY # Underlying variable
        self._method = None # Underlying variable

        # Data structure
        self.design_data = self.create_empty_design_data() # data model
        self.validation_errors: dict[str, str] = {} # dictionary with all the errors

        # Initialization complete
        self.logger.info("Data model initialized")

    # -------------------------------------------- Principal properties --------------------------------------------
    @property
    def language(self) -> str:
        return self._language # Access the underlying variable

    @language.setter
    def language(self, lang: str):
        if lang not in LANGUAGES.keys():
            raise ValueError("Unsupported language")
        if lang != self._language:
            self._language = lang # Modify the underlying variable
            self.language_changed.emit(lang)
            self.logger.info(f"Language changed to: {lang}")

    @property
    def units(self) -> str:
        return self._units # Access the underlying variable

    @units.setter
    def units(self, unit: str):
        if unit not in UNIT_SYSTEM.keys():
            raise ValueError("Invalid unit system")
        if unit != self._units:
            self._units = unit # Modify the underlying variable
            self.units_changed.emit(unit)
            self.logger.info(f"Unit system changed to: {unit}")

    @property
    def method(self) -> str:
        return self._method # Access the underlying variable

    @method.setter
    def method(self, method: str):
        if method != self._method:
            self._method = method # Modify the underlying variable
            self.method_changed.emit(method)
            self.logger.info(f"Regular concrete method changed to: {method}")

    @property
    def current_step(self) -> int:
        return self._current_step # Access the underlying variable

    @current_step.setter
    def current_step(self, step: int):
        if step != self._current_step:
            self._current_step = step # Modify the underlying variable
            self.step_changed.emit(step)
            self.logger.info(f"The current step is: {step}")

    # -------------------------------------------- Design data --------------------------------------------
    @staticmethod
    def create_empty_design_data():
        """Create the empty design data."""

        return {
            'general_info': {
                'project_name': None,
                'location': None,
                'method': None,
                'purchaser': None,
                'date': None
            },
            'field_requirements': {
                'slump_value': None,
                'slump_range': None,
                'exposure_class': {
                    'group_1': None,
                    "items_1": None,
                    'group_2': None,
                    "items_2": None,
                    'group_3': None,
                    "items_3": None,
                    'group_4': None,
                    "items_4": None,
                },
                'entrained_air_content': {
                    'is_checked': None,
                    'user_defined': None,
                    'exposure_defined': None
                },
                'strength': {
                    'spec_strength': None,
                    'spec_strength_time': None,
                    'std_dev_known': {
                        'std_dev_known_enabled': None,
                        'std_dev_value': None,
                        'test_nro': None,
                        'defective_level': None
                    },
                    'std_dev_unknown': {
                        'std_dev_unknown_enabled': None,
                        'quality_control': None,
                        'margin': None
                    }
                }

            },
            'cementitious_materials': {
                'cement_seller': None,
                'cement_type': None,
                'cement_class': None,
                'cement_relative_density': None,
                'SCM': {
                    'SCM_checked': None,
                    'SCM_type': None,
                    'SCM_content': None,
                    'SCM_relative_density': None
                }
            },
            'fine_aggregate': {
                'info': {
                    'name': None,
                    'source': None,
                    'type': None
                },
                'physical_prop': {
                    'relative_density_SSD': None,
                    'PUS': None,
                    'PUC': None
                },
                'moisture': {
                    'moisture_content': None,
                    'absorption_content': None
                },
                'gradation': {
                    'passing_checked': None,
                    'passing': None,
                    'retained_checked': None,
                    'retained': None,
                    'cumulative_retained': None
                },
                'fineness_modulus': None
            },
            'coarse_aggregate': {
                'info': {
                    'name': None,
                    'source': None,
                    'type': None
                },
                'physical_prop': {
                    'relative_density_SSD': None,
                    'PUS': None,
                    'PUC': None
                },
                'moisture': {
                    'moisture_content': None,
                    'absorption_content': None
                },
                'gradation': {
                    'passing_checked': None,
                    'passing': None,
                    'retained_checked': None,
                    'retained': None,
                    'cumulative_retained': None
                },
                'NMS': None
            },
            'water': {
                'water_type': None,
                'water_source': None,
                'water_density': None
            },
            'chemical_admixtures': {
                'WRA': {
                'WRA_checked': None,
                'WRA_action': {
                    'plasticizer': None,
                    'water_reducer': None,
                    'cement_economizer': None,
                },
                'WRA_type': None,
                'WRA_name': None,
                'WRA_relative_density': None,
                'WRA_dosage': None,
                'WRA_effectiveness': None
            },
                'AEA': {
                'AEA_checked': None,
                'AEA_name': None,
                'AEA_relative_density': None,
                'AEA_dosage': None
            }
            },
            'validation': {
                'coarse_category': None,
                'coarse_scores': None,
                'fine_category': None,
                'fine_scores': None,
                'exposure_classes': None,
            },
            'trial_mix': {
                'adjustments': {
                    'water': {
                        'water_abs_volume': None,
                        'water_content_correction': None,
                        'water_volume': None,
                    },
                    'cementitious_material': {
                        'cement': {
                            'cement_abs_volume': None,
                            'cement_content': None,
                            'cement_volume': None,
                        },
                        'scm': {
                            'scm_abs_volume': None,
                            'scm_content': None,
                            'scm_volume': None,
                        },
                    },
                    'fine_aggregate': {
                        'fine_abs_volume': None,
                        'fine_content_ssd': None,
                        'fine_content_wet': None,
                        'fine_volume': None,
                    },
                    'coarse_aggregate': {
                        'coarse_abs_volume': None,
                        'coarse_content_ssd': None,
                        'coarse_content_wet': None,
                        'coarse_volume': None,
                    },
                    'air': {
                        'entrapped_air_content': None,
                        'entrained_air_content': None,
                    },
                    'water_cementitious_materials_ratio': {
                        'w_cm': None
                    },
                    'chemical_admixtures': {
                        'WRA': {
                            'WRA_content': None,
                            'WRA_volume': None,
                        },
                        'AEA': {
                            'AEA_content': None,
                            'AEA_volume': None,
                        },
                    },
                    'summation': {
                        'total_abs_volume': None,
                        'total_content': None,
                    },
                },
                'trial_mix_volume': None,
                'trial_mix_waste': None
            },
            'adjustments_trial_mix': {
                "water": {
                    "water_used": None,
                    "air_measured": None,
                    "w_cm": None,
                    "keep_coarse_agg": None,
                    "keep_fine_agg": None,
                },
                "cementitious_material": {
                    "cementitious_used": None,
                    "air_measured": None,
                    "w_cm": None,
                    "keep_coarse_agg": None,
                    "keep_fine_agg": None,
                },
                "aggregate_proportion": {
                    "new_coarse_proportion": None,
                    "new_fine_proportion": None,
                },
            }
        }

    def update_design_data(self, key_path, value):
        """
        Update a specific value using dot notation to access nested keys.

        :param str key_path: The key path to update, e.g. 'cementitious_materials.SCM.SCM_type'.
        :param any value: The new value to update.
        """

        keys = key_path.split('.')
        data = self.design_data

        try:
            for key in keys[:-1]:
                data = data[key]
            data[keys[-1]] = value
            self.logger.info(f"Updated {key_path} -> {value}")
        except KeyError as e:
            self.logger.error(f"Invalid key path: {key_path} ({str(e)})")
            raise

    def get_design_value(self, key_path):
        """
        Get the design value using dot notation (as key).

        :param str key_path: The key path to retrieve the value associated.
        :returns: Return the desired value.
        :rtype: any
        """

        keys = key_path.split('.')
        data = self.design_data
        try:
            for key in keys:
                data = data[key]
            return data
        except KeyError as e:
            self.logger.error(f"Invalid key path: {key_path} ({str(e)})")
            raise

    # -------------------------------------------- Validation methods --------------------------------------------
    def add_validation_error(self, section, message):
        """
        Add a validation error with context.

        :param str section: Name of the section that failed.
        :param str message: Description of validation failure.
        """

        key = section.upper()
        # Only add the error if it is not already present
        if key not in self.validation_errors:
            self.validation_errors[key] = message
            self.logger.info(f"Validation error: {key} -> {message}")

    def clear_validation_errors(self, section = None):
        """
        Clear validation errors. If a section is provided, only the error associated with that section is cleared.

        :param str section: If provided, only the error associated with that section is cleared.
        """

        if section:
            key = section.upper()
            # Remove the error for the specified section if it exists
            self.validation_errors.pop(key, None)
        else:
            # Clear all errors
            self.validation_errors = {}

    # -------------------------------------------- Reset method --------------------------------------------
    def reset(self):
        """Reset all data while maintaining the structure."""

        self.design_data = self.create_empty_design_data()
        self.validation_errors = {}
        self.current_step = 0
        self.logger.info("All data has been restored")