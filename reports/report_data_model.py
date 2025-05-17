from abc import abstractmethod

from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from core.regular_concrete.models.aci_data_model import ACIDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from logger import Logger


class ReportDataModel:
    """Abstract base class for mix design reporting data models."""

    # Define a clear prefix for the key_paths
    KEY_PATH_MARKER = "RESOLVE@"

    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model):
        # Initialize the logger
        self.logger = Logger(__name__)
        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model
        # Connect to the data model of each method
        self.mce_data_model: MCEDataModel = mce_data_model
        self.aci_data_model: ACIDataModel = aci_data_model
        self.doe_data_model: DOEDataModel = doe_data_model

        # These dictionaries will be populated by _initialize_dictionaries() in the subclass
        self.input_data = {} # Basic input data
        self.dosage_data = {} # Dosage data per cubic meter
        self.adjusted_dosage_data = {} # Adjusted dosage data (after testing)
        self.adjustment_notes = {} # Adjustments made
        self.calculation_details = {} # Details of calculations by stages (for full report)

        # Initialization complete
        self.logger.info('Report data model initialized')

    @abstractmethod
    def _initialize_dictionaries(self, stress_units, scm_type=None):
        """
        Abstract method to be implemented by subclasses.
        You must initialize self.input_data, self.dosage_data, self.adjusted_dosage_data, self.adjustment_notes,
        and self.calculation_details with your specific structures and key_paths, or literal values.
        """
        pass

    @abstractmethod
    def _get_specific_data_retrieval_func(self):
        """
        Abstract method to be implemented by subclasses.
        It must return the specific get_data function of the corresponding data model
        (e.g., self.mce_data_model.get_data, self.aci_data_model.get_data or self.doe_data_model.get_data)
        for the dosage_data and calculation_details dictionaries.
        """
        pass

    def _recursive_fill_values(self, current_item, data_retrieval_func):
        """
        Recursively traverses a dictionary or list, identifying and resolving string
        values that are marked as key paths.

        This method iterates through the `current_item`. If `current_item` is a dictionary,
        it checks each value. If `current_item` is a list, it checks each element.

        - If a string value (in a dictionary or list) starts with the class attribute
          `KEY_PATH_MARKER`, the marker is stripped, and the remaining part of the string is treated as a `key_path`.
        - This `key_path` is then passed to the `data_retrieval_func` (which is typically a method from a data model
          like `get_design_value` or `get_data`) to obtain the actual data.
        - The original marked string is replaced with the value returned by `data_retrieval_func`.
        - If `data_retrieval_func` raises an exception (e.g., `KeyError`, `AttributeError`, `TypeError`)
          when trying to resolve the `key_path` (indicating an invalid or non-existent path), a warning is logged,
          and the value is set to `None`. This `None` will typically be converted to "-"
          by the `_recursive_replace_none` method in a subsequent pass.

        - String values that do *not* start with `KEY_PATH_MARKER` are treated as literal string data
          and are left unchanged.
        - Non-string values (e.g., numbers, booleans, pre-existing `None` values, or already resolved
          complex objects like dictionaries/lists) are also left unchanged by this specific lookup logic.
        - If a value or list item is itself a dictionary or list, the method recurses into that structure
          to continue the process.

        :param current_item: The dictionary or list to process. This item will be modified in place.
        :param data_retrieval_func: The function to call to resolve a key_path string.
                                    It should accept a string (the key_path) and return the resolved value.
        """

        if isinstance(current_item, dict):
            # Iterate over a copy of items if modifying the dict during iteration (list(current_item.items()))
            for key, value in list(current_item.items()):
                if isinstance(value, dict):
                    self._recursive_fill_values(value, data_retrieval_func)
                elif isinstance(value, list):
                    self._recursive_fill_values(value, data_retrieval_func)
                elif isinstance(value, str) and value.startswith(self.KEY_PATH_MARKER):
                    actual_key_path = value[len(self.KEY_PATH_MARKER):]
                    try:
                        resolved_value = data_retrieval_func(actual_key_path)
                        current_item[key] = resolved_value
                    except (KeyError, AttributeError, TypeError) as e:
                        # If the marked key_path cannot be resolved, it is logged and set to None.
                        # This allows _recursive_replace_none to convert it to "-".
                        self.logger.warning(
                            f"Could not resolve key_path '{actual_key_path}' "
                            f"(for dictionary key '{key}'). Error: {e}. Setting to None."
                        )
                        current_item[key] = None
                # Literal strings (not starting with marker), numbers, etc., are left as is.
        elif isinstance(current_item, list):
            for i, item_in_list in enumerate(current_item):
                if isinstance(item_in_list, dict) or isinstance(item_in_list, list):
                    self._recursive_fill_values(item_in_list, data_retrieval_func)
                elif isinstance(item_in_list, str) and item_in_list.startswith(self.KEY_PATH_MARKER):
                    actual_key_path = item_in_list[len(self.KEY_PATH_MARKER):]
                    try:
                        resolved_value = data_retrieval_func(actual_key_path)
                        current_item[i] = resolved_value
                    except (KeyError, AttributeError, TypeError) as e:
                        # If the marked key_path cannot be resolved, it is logged and set to None.
                        # This allows _recursive_replace_none to convert it to "-".
                        self.logger.warning(
                            f"Could not resolve key_path '{actual_key_path}' "
                            f"(in a list at index {i}). Error: {e}. Setting to None."
                        )
                        current_item[i] = None
                # Literal strings in lists (not starting with marker) are left as is.

    def _recursive_replace_none(self, current_item):
        """
        Recursively iterates through a dictionary or list. If a None value is found,
        it's replaced by "-". This is called after _recursive_fill_values.
        """

        if isinstance(current_item, dict):
            for key, value in list(current_item.items()):
                if isinstance(value, dict) or isinstance(value, list):
                    self._recursive_replace_none(value)
                elif value is None:
                    current_item[key] = "-"
        elif isinstance(current_item, list):
            for i, item_in_list in enumerate(current_item):
                if isinstance(item_in_list, dict) or isinstance(item_in_list, list):
                    self._recursive_replace_none(item_in_list)
                elif item_in_list is None:
                    current_item[i] = "-"

    def process_data_values(self):
        """Processes the data dictionaries:
        1. Fills values by resolving key_paths using appropriate data model methods.
           The values can be strings, dicts, or lists. Numeric literals are preserved.
        2. Replaces any None values with "-" throughout the possibly nested structure.
        """

        # --- First Pass: Fill values from key_paths ---

        # Dictionaries that always use self.data_model.get_design_value()
        general_data_dicts_to_fill = [
            self.input_data,
            self.adjusted_dosage_data,
            self.adjustment_notes
        ]
        for d_dict in general_data_dicts_to_fill:
            if d_dict:
                self._recursive_fill_values(d_dict, self.data_model.get_design_value)

        # Dictionaries that use the subclass-specific function
        specific_data_retrieval_func = self._get_specific_data_retrieval_func()
        specific_model_dicts_to_fill = [
            self.dosage_data,
            self.calculation_details
        ]
        for d_dict in specific_model_dicts_to_fill:
            if d_dict:
                self._recursive_fill_values(d_dict, specific_data_retrieval_func)

        # --- Second Pass: Replace None with "-" ---
        all_dictionaries = [
            self.input_data,
            self.dosage_data,
            self.adjusted_dosage_data,
            self.adjustment_notes,
            self.calculation_details
        ]
        for d_dict in all_dictionaries:
            if d_dict:
                self._recursive_replace_none(d_dict)

    def get_input_data(self):
        """Return the input data"""
        return self.input_data

    def get_dosage_data(self):
        """Return dosage data"""
        return self.dosage_data

    def get_adjusted_dosage_data(self):
        """Return the adjusted dosage data if it exists"""
        return self.adjusted_dosage_data

    def has_trial_mix_adjustments(self, structure):
        """
        Check whether trial mixes have been performed that have led to adjustments in the final design.
        To do this, check if a processed data structure, typically representing trial mix adjustments
        (self.get_adjustment_notes) is not "effectively empty".

        A structure is considered "effectively empty" if:
        1. It's an empty dictionary ({}) or an empty list ([]).
        2. It's a dictionary where all its values are recursively effectively empty.
        3. It's a list where all its items are recursively effectively empty.
        4. It's a string value equal to "-".
        Any other scalar value (numbers, other strings, booleans, None that wasn't replaced)
        is NOT considered effectively empty.

        This method is intended to be called AFTER the dictionary has been processed
        by _recursive_fill_values and _recursive_replace_none.

        :param structure: The data structure (dictionary, list, or scalar value) to check if is not "effectively empty".
        :return: False if the structure is effectively empty, True otherwise.
        :rtype: bool
        """

        if isinstance(structure, dict):
            if not structure:  # The empty dictionary {} is considered empty
                return False
            # If ANY value in the dictionary HAS meaningful data, then the dictionary has it
            return any(self.has_trial_mix_adjustments(value) for value in structure.values())
        elif isinstance(structure, list):
            if not structure:  # The empty list [] is considered empty
                return False
            # If ANY item in the list HAS meaningful data, then the list has it
            return any(self.has_trial_mix_adjustments(item) for item in structure)
        elif isinstance(structure, str):
            # A string is only considered "empty" if it is exactly "-"
            return structure != "-"
        else:
            # Any other data type (numbers, booleans, unreplaced None, etc.)
            # means that the structure is not "effectively empty" at that point.
            return True

    def get_adjustment_notes(self):
        """Return notes on adjustments made"""
        return self.adjustment_notes

    def get_calculation_details(self):
        """Return the calculation details for the full report"""
        return self.calculation_details


class MCEReportModel(ReportDataModel):
    """Report model for the MCE method"""

    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model):
        super().__init__(data_model, mce_data_model, aci_data_model, doe_data_model)
        # Stress units
        if self.data_model.units == "MKS":
            stress_units = "kgf/cm²"
        elif self.data_model.units == "SI":
            stress_units = "MPa"
        else:
            stress_units = None

        # Defines MCE-specific dictionaries
        self._initialize_dictionaries(stress_units=stress_units, scm_type=None)
        # Legacy common processing logic
        self.process_data_values()

    def _initialize_dictionaries(self, stress_units, scm_type=None):
        """
        Initializes all the data dictionaries with their key_paths or literal values.

        :param str stress_units: Stress unit (e.g. "kgf/cm²" or "MPa") according to the unit system used.
        :param str | None scm_type: Type of supplementary cementitious material used if any.
        """

        # Basic input data (method to access data -> self.data_model.get_design_value())
        self.input_data = {
            "Información general": {
                "Nombre del proyecto": ReportDataModel.KEY_PATH_MARKER + 'general_info.project_name',
                "Ubicación": ReportDataModel.KEY_PATH_MARKER + 'general_info.location',
                "Solicitante": ReportDataModel.KEY_PATH_MARKER + 'general_info.purchaser',
                "Fecha": ReportDataModel.KEY_PATH_MARKER + 'general_info.date',
            },
            "Condiciones de la obra": {
                "Asentamiento": {
                    "Valor (mm)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.slump_value',
                },
                "Clase de exposición": {
                    "Exposición al agua": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_1',
                    "Exposición a sulfatos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_2',
                    "Humedad relativa": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_3',
                    "Condición ambiental": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_4',
                },
                "Contenido de aire incorporado": {
                    "Diseño con aire incorporado": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.is_checked',
                    "Contenido de aire objetivo (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.user_defined',
                    "Contenido de aire estimado según exposición": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.exposure_defined',
                },
                "Resistencia promedio a la compresión requerida": {
                    f"Resistencia de cálculo especificada ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength',
                    "Días esperados para alcanzar la resistencia": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength_time',
                },
                "Desviación estándar conocida": {
                    "La desviación estándar es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_known_enabled',
                    f"Valor ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_value',
                    "Número de ensayos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.test_nro',
                    "Fracción defectiva (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.defective_level',
                },
                "Desviación estándar desconocida": {
                    "La desviación estándar no es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled',
                    "Control de calidad": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_unknown.quality_control',
                },
            },
            "Materiales cementantes": {
                "Cemento Portland": {
                    "Marca": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_seller',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_type',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_relative_density',
                },
                "Material cementante suplementario": {
                    "Uso de material cementante suplementario": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_checked',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_type',
                    "Contenido (%)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_content',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_relative_density',
                },
            },
            "Agregado fino": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.relative_density_SSD',
                    "Peso unitario suelto (kgf/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUS',
                    "Peso unitario compactado (kgf/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.gradation.passing', # This will be replaced by a dict
                    "Módulo de finura": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fineness_modulus'
                },
            },
            "Agregado grueso": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.relative_density_SSD',
                    "Peso unitario suelto (kgf/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUS',
                    "Peso unitario compactado (kgf/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.gradation.passing',
                    "Tamaño máximo nominal (mm)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.NMS'
                },
            },
            "Agua": {
                "Tipo": ReportDataModel.KEY_PATH_MARKER + 'water.water_type',
                "Lugar": ReportDataModel.KEY_PATH_MARKER + 'water.water_source',
                "Densidad (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'water.water_density',
            },
            "Aditivos": {
                "Reductor de agua": {
                    "Uso de reductor de agua": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_checked',
                    "¿Actúa como plastificante?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.plasticizer',
                    "¿Actúa como reductor de agua?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.water_reducer',
                    "¿Actúa como economizador de cemento?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.cement_economizer',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_type',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_dosage',
                    "Efectividad (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_effectiveness',
                },
                "Incorporador de aire": {
                    "Uso de incorporador de aire": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_checked',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_dosage',
                }
            },
        }
        # Dosage data per cubic meter (method to access data -> self.mce_data_model.get_data())
        self.dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume'
            },
        }
        # Adjusted dosage data (after testing) (method to access data -> self.data_model.get_design_value())
        self.adjusted_dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume'
            },
        }
        # Notes on adjustments made (method to access data -> self.data_model.get_design_value())
        self.adjustment_notes = {
            "Agua": {
                "Cantidad de agua utilizada (L)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.water_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_fine_agg',
            },
            "Material cementante": {
                "Cantidad de material cementante utilizado (kgf)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.cementitious_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_fine_agg',
            },
            "Proporción entre los agregados": {
                "Nueva proporción de agregado grueso (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_coarse_proportion',
                "Nueva proporción de agregado fino (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_fine_proportion',
            },
        }
        # Details of calculations by stages (for full report) (method to access data -> self.mce_data_model.get_data())
        self.calculation_details = {
            "1. Resistencia promedio requerida (f_cr)": {
                "Factor de modificación para la desviación estándar": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.k_factor',
                "Valor de z": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.z_value',
                "f_cr - 1 (kgf/cm²)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.f_cr_1',
                "f_cr - 2 (kgf/cm²)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.f_cr_2',
                "Margen (kgf/cm²)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.margin',
                "f_cr (kgf/cm²)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.target_strength_value',
            },
            "2. Proporción entre agregados finos y gruesos (relación beta)": {
                "Beta mínimo (%)": ReportDataModel.KEY_PATH_MARKER + 'beta.beta_min',
                "Beta máximo (%)": ReportDataModel.KEY_PATH_MARKER + 'beta.beta_max',
                "Beta promedio (%)": ReportDataModel.KEY_PATH_MARKER + 'beta.beta_mean',
                "Beta económico (%)": ReportDataModel.KEY_PATH_MARKER + 'beta.beta_economic',
                "Beta utilizado": ReportDataModel.KEY_PATH_MARKER + 'beta.beta',
            },
            "3. Relación agua-cemento (a/c)": {
                "Constante m": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.m',
                "Constante n": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.n',
                "Relación a/c por resistencia": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.design_alpha',
                "Factor Kr (corrección por tamaño máximo)": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.correction_factor_1',
                "Factor Ka (corrección por tipo de agregado)": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.correction_factor_2',
                "Relación a/c corregida": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.corrected_alpha',
                "Relación a/c por durabilidad": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.min_alpha',
                "Relación a/c final": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.fina_alpha',
                "Relación a/c reducida (Reductor de agua)": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.reduced_alpha',
                "Relación a/c utilizada": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm',
            },
            "4. Contenido y volumen absoluto del cemento": {
                "Relación a/c ficticia (Economizador de cemento)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.fictitious_alpha_wra_action_cement_economizer',
                "Relación a/c ficticia (Reductor de agua)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.fictitious_alpha_wra_action_water_reducer',
                "Constante k": 117.2,  # Numeric literal, will be preserved
                "Constante n": 0.16,   # Numeric literal, will be preserved
                "Constante m": 1.3,    # Numeric literal, will be preserved
                "Contenido base de cemento (kgf)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.design_cement_content',
                "Factor C1 (corrección por tamaño máximo)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.correction_factor_1',
                "Factor C2 (corrección por tipo de agregado)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.correction_factor_2',
                "Contenido corregido de cemento (kgf)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.corrected_cement_content',
                "Contenido mínimo de cemento (kgf)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.min_cement_content',
                "Contenido utilizado de cemento (kgf)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                "Volumen absoluto de cemento (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
            },
            "5. Volumen de aire atrapado": {
                "Volumen (absoluto) de aire atrapado (L)": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
            },
            "6. Contenido y volumen de agua (SSS)": {
                "Contenido de agua (kgf)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content',
                "Volumen (absoluto) de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
            },
            "7. Contenido y volumen absoluto de los agregados (SSS)": {
                "Contenido de agregado fino (kgf)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_ssd',
                "Contenido de agregado grueso (kgf)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_ssd',
                "Volumen absoluto de agregado fino (L)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "Volumen absoluto de agregado grueso (L)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
            },
            "8. Corrección por humedad": {
                "Contenido de agregado fino (kgf)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "Contenido de agregado grueso (kgf)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "Contenido de agua (kgf)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "Volumen de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume',
            },
        }

    def _get_specific_data_retrieval_func(self):
        return self.mce_data_model.get_data


class ACIReportModel(ReportDataModel):
    """Report model for the ACI method"""

    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model):
        super().__init__(data_model, mce_data_model, aci_data_model, doe_data_model)
        # Stress units
        if self.data_model.units == "MKS":
            stress_units = "kgf/cm²"
        elif self.data_model.units == "SI":
            stress_units = "MPa"
        else:
            stress_units = None

        # Type of air content in use
        if self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked'):
            air_type = "Aire incorporado"
        else:
            air_type = "Aire atrapado"

        # SCM in use
        is_scm_used = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')

        # Defines ACI-specific dictionaries
        self._initialize_dictionaries(stress_units=stress_units, scm_type=scm_type)

        # Conditionally delete keys
        if not is_scm_used and scm_type in self.dosage_data:
            del self.dosage_data[scm_type]
        if not is_scm_used and scm_type in self.adjusted_dosage_data:
            del self.adjusted_dosage_data[scm_type]
        if not is_scm_used:
            del self.calculation_details["4. Contenido y volumen absoluto del material cementante"][
                f"Contenido utilizado de {scm_type.lower()} (kg)"]
            del self.calculation_details["4. Contenido y volumen absoluto del material cementante"][
                f"Volumen absoluto de {scm_type.lower()} (L)"]
        if air_type == "Aire incorporado" and "Aire atrapado" in self.dosage_data:
            del self.dosage_data["Aire atrapado"]
        if air_type == "Aire incorporado" and "Aire atrapado" in self.adjusted_dosage_data:
            del self.adjusted_dosage_data["Aire atrapado"]
        if air_type == "Aire incorporado" and "6. Volumen de aire atrapado" in self.calculation_details:
            del self.calculation_details["6. Volumen de aire atrapado"]
        if air_type == "Aire atrapado" and "Aire incorporado" in self.dosage_data:
            del self.dosage_data["Aire incorporado"]
        if air_type == "Aire atrapado" and "Aire incorporado" in self.adjusted_dosage_data:
            del self.adjusted_dosage_data["Aire incorporado"]
        if air_type == "Aire atrapado" and "6. Volumen de aire incorporado" in self.calculation_details:
            del self.calculation_details["6. Volumen de aire incorporado"]

        # Legacy common processing logic
        self.process_data_values()

    def _initialize_dictionaries(self, stress_units, scm_type=None):
        """
        Initializes all the data dictionaries with their key_paths or literal values.

        :param str stress_units: Stress unit (e.g. "kgf/cm²" or "MPa") according to the unit system used.
        :param str | None scm_type: Type of supplementary cementitious material used if any.
        """

        # Basic input data (method to access data -> self.data_model.get_design_value())
        self.input_data = {
            "Información general": {
                "Nombre del proyecto": ReportDataModel.KEY_PATH_MARKER + 'general_info.project_name',
                "Ubicación": ReportDataModel.KEY_PATH_MARKER + 'general_info.location',
                "Solicitante": ReportDataModel.KEY_PATH_MARKER + 'general_info.purchaser',
                "Fecha": ReportDataModel.KEY_PATH_MARKER + 'general_info.date',
            },
            "Condiciones de la obra": {
                "Asentamiento": {
                    "Rango (mm)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.slump_range',
                },
                "Clase de exposición": {
                    "Exposición a sulfatos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_1',
                    "Exposición a ciclos de congelación y deshielo": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_2',
                    "Exposición al contacto con agua": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_3',
                    "Exposición a la corrosión": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_4',
                },
                "Contenido de aire incorporado": {
                    "Diseño con aire incorporado": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.is_checked',
                    "Contenido de aire objetivo (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.user_defined',
                    "Contenido de aire estimado según exposición": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.exposure_defined',
                },
                "Resistencia promedio a la compresión requerida": {
                    f"Resistencia de cálculo especificada ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength',
                    "Días esperados para alcanzar la resistencia": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength_time',
                },
                "Desviación estándar conocida": {
                    "La desviación estándar es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_known_enabled',
                    f"Valor ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_value',
                    "Número de ensayos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.test_nro',
                    "Fracción defectiva (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.defective_level',
                },
                "Desviación estándar desconocida": {
                    "La desviación estándar no es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled',
                },
            },
            "Materiales cementantes": {
                "Cemento Portland": {
                    "Marca": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_seller',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_type',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_relative_density',
                },
                "Material cementante suplementario": {
                    "Uso de material cementante suplementario": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_checked',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_type',
                    "Contenido (%)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_content',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_relative_density',
                },
            },
            "Agregado fino": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.relative_density_SSD',
                    "Masa unitaria suelta (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUS',
                    "Masa unitaria compactada (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.gradation.passing',
                    # This will be replaced by a dict
                    "Módulo de finura": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fineness_modulus'
                },
            },
            "Agregado grueso": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.relative_density_SSD',
                    "Masa unitaria suelta (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUS',
                    "Masa unitaria compactada (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.gradation.passing',
                    "Tamaño máximo nominal (mm)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.NMS'
                },
            },
            "Agua": {
                "Tipo": ReportDataModel.KEY_PATH_MARKER + 'water.water_type',
                "Lugar": ReportDataModel.KEY_PATH_MARKER + 'water.water_source',
                "Densidad (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'water.water_density',
            },
            "Aditivos": {
                "Reductor de agua": {
                    "Uso de reductor de agua": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_checked',
                    "¿Actúa como plastificante?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.plasticizer',
                    "¿Actúa como reductor de agua?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.water_reducer',
                    "¿Actúa como economizador de cemento?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.cement_economizer',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_type',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_dosage',
                    "Efectividad (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_effectiveness',
                },
                "Incorporador de aire": {
                    "Uso de incorporador de aire": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_checked',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_dosage',
                }
            },
        }
        # Dosage data per cubic meter (method to access data -> self.aci_data_model.get_data())
        self.dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_volume'
            },
            f"{scm_type}": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content'
            },
            "Aire incorporado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume'
            },
            "Incorporador de aire": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_volume'
            },
        }
        # Adjusted dosage data (after testing) (method to access data -> self.data_model.get_design_value())
        self.adjusted_dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_volume'
            },
            f"{scm_type}": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content'
            },
            "Aire incorporado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrained_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrained_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume'
            },
            "Incorporador de aire": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_volume'
            },
        }
        # Notes on adjustments made (method to access data -> self.data_model.get_design_value())
        self.adjustment_notes = {
            "Agua": {
                "Cantidad de agua utilizada (L)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.water_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_fine_agg',
            },
            "Material cementante": {
                "Cantidad de material cementante utilizado (kg)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.cementitious_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_fine_agg',
            },
            "Proporción entre los agregados": {
                "Nueva proporción de agregado grueso (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_coarse_proportion',
                "Nueva proporción de agregado fino (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_fine_proportion',
            },
        }
        # Details of calculations by stages (for full report) (method to access data -> self.aci_data_model.get_data())
        self.calculation_details = {
            "1. Resistencia promedio requerida (f_cr)": {
                "Factor de modificación para la desviación estándar": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.k_factor',
                "Valor de z": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.z_value',
                "f_cr - 1 (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.f_cr_1',
                "f_cr - 2 (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.f_cr_2',
                "Margen (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.margin',
                "f_cr (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.target_strength_value',
            },
            "2. Contenido y volumen de agua (SSS)": {
                "Contenido base de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.base',
                "Corrección por agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.coarse_aggregate_correction',
                "Corrección por agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.fine_aggregate_correction',
                "Corrección por material cementante suplementario (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.scm_correction',
                "Corrección por aditivo reductor de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.wra_correction',
                "Contenido utilizado de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.final_content',
                "Volumen (absoluto) de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
            },
            "3. Relación agua-material cementante (a/cm)": {
                "Relación a/cm por resistencia": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_by_strength',
                "Relación a/cm por durabilidad": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_by_durability',
                "Relación a/cm utilizado": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_previous',
            },
            "4. Contenido y volumen absoluto del material cementante": {
                "Contenido ficticio de agua (Reductor de agua)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.without_wra_correction',
                "Contenido base de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.base_content',
                "Contenido mínimo de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.min_content',
                "Contenido utilizado de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.final_content',
                "Contenido utilizado de cemento (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                f"Contenido utilizado de {scm_type.lower()} (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_content',
                "Volumen absoluto de cemento (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
                f"Volumen absoluto de {scm_type.lower()} (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_abs_volume',
            },
            "5. Revisión de la relación agua-material cementante (a/cm)": {
                "Relación a/cm recalculada (real)": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm',
            },
            "6. Volumen de aire atrapado": {
                "Volumen (absoluto) de aire atrapado (L)": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
            },
            "6. Volumen de aire incorporado": {
                "Volumen (absoluto) de aire incorporado (L)": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content',
            },
            "7. Contenido y volumen absoluto de los agregados (SSS)": {
                "Volumen de agregado grueso seco compactado con varilla": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.oven_dry_rodded_bulk_volume',
                "Contenido de agregado grueso seco (kg)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_oven_dry',
                "Contenido de agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_ssd',
                "Contenido de agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_ssd',
                "Volumen absoluto de agregado fino (L)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "Volumen absoluto de agregado grueso (L)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
            },
            "8. Corrección por humedad": {
                "Contenido de agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "Contenido de agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "Contenido de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "Volumen de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume',
            },
        }

    def _get_specific_data_retrieval_func(self):
        return self.aci_data_model.get_data


class DOEReportModel(ReportDataModel):
    """Report model for the DoE method"""

    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model):
        super().__init__(data_model, mce_data_model, aci_data_model, doe_data_model)
        # Stress units
        if self.data_model.units == "MKS":
            stress_units = "kgf/cm²"
        elif self.data_model.units == "SI":
            stress_units = "MPa"
        else:
            stress_units = None

        # Type of air content in use
        if self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked'):
            air_type = "Aire incorporado"
        else:
            air_type = "Aire atrapado"

        # SCM in use
        is_scm_used = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')

        # Defines ACI-specific dictionaries
        self._initialize_dictionaries(stress_units=stress_units, scm_type=scm_type)

        # Conditionally delete keys
        if not is_scm_used and scm_type in self.dosage_data:
            del self.dosage_data[scm_type]
        if not is_scm_used and scm_type in self.adjusted_dosage_data:
            del self.adjusted_dosage_data[scm_type]
        if not is_scm_used:
            del self.calculation_details["5. Contenido y volumen absoluto del material cementante"][
                f"Contenido utilizado de {scm_type.lower()} (kg)"]
            del self.calculation_details["5. Contenido y volumen absoluto del material cementante"][
                f"Volumen absoluto de {scm_type.lower()} (L)"]
            del self.calculation_details["6. Revisión de la relación agua-material cementante (a/cm)"][
                f"Contenido recalculado de {scm_type.lower()} (kg)"]
            del self.calculation_details["6. Revisión de la relación agua-material cementante (a/cm)"][
                f"Volumen absoluto recalculado de {scm_type.lower()} (L)"]
        if air_type == "Aire incorporado" and "Aire atrapado" in self.dosage_data:
            del self.dosage_data["Aire atrapado"]
        if air_type == "Aire incorporado" and "Aire atrapado" in self.adjusted_dosage_data:
            del self.adjusted_dosage_data["Aire atrapado"]
        if air_type == "Aire incorporado" and "1. Volumen de aire atrapado" in self.calculation_details:
            del self.calculation_details["1. Volumen de aire atrapado"]
        if air_type == "Aire atrapado" and "Aire incorporado" in self.dosage_data:
            del self.dosage_data["Aire incorporado"]
        if air_type == "Aire atrapado" and "Aire incorporado" in self.adjusted_dosage_data:
            del self.adjusted_dosage_data["Aire incorporado"]
        if air_type == "Aire atrapado" and "1. Volumen de aire incorporado" in self.calculation_details:
            del self.calculation_details["1. Volumen de aire incorporado"]

        # Legacy common processing logic
        self.process_data_values()

    def _initialize_dictionaries(self, stress_units, scm_type=None):
        """
        Initializes all the data dictionaries with their key_paths or literal values.

        :param str stress_units: Stress unit (e.g. "kgf/cm²" or "MPa") according to the unit system used.
        :param str | None scm_type: Type of supplementary cementitious material used if any.
        """

        # Basic input data (method to access data -> self.data_model.get_design_value())
        self.input_data = {
            "Información general": {
                "Nombre del proyecto": ReportDataModel.KEY_PATH_MARKER + 'general_info.project_name',
                "Ubicación": ReportDataModel.KEY_PATH_MARKER + 'general_info.location',
                "Solicitante": ReportDataModel.KEY_PATH_MARKER + 'general_info.purchaser',
                "Fecha": ReportDataModel.KEY_PATH_MARKER + 'general_info.date',
            },
            "Condiciones de la obra": {
                "Asentamiento": {
                    "Rango (mm)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.slump_range',
                },
                "Clase de exposición": {
                    "Corrosión inducida por carbonatación": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_1',
                    "Corrosión inducida por cloruros": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_2',
                    "Ataque por congelación y deshielo": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_3',
                    "Exposición a ambientes químicos agresivos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.exposure_class.items_4',
                },
                "Contenido de aire incorporado": {
                    "Diseño con aire incorporado": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.is_checked',
                    "Contenido de aire objetivo (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.user_defined',
                    "Contenido de aire estimado según exposición": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.entrained_air_content.exposure_defined',
                },
                "Resistencia promedio a la compresión requerida": {
                    f"Resistencia de cálculo especificada ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength',
                    "Días esperados para alcanzar la resistencia": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.spec_strength_time',
                },
                "Desviación estándar conocida": {
                    "La desviación estándar es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_known_enabled',
                    f"Valor ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.std_dev_value',
                    "Número de ensayos": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.test_nro',
                    "Fracción defectiva (%)": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_known.defective_level',
                },
                "Desviación estándar desconocida": {
                    "La desviación estándar no es conocida": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled',
                    f"Margen ({stress_units})": ReportDataModel.KEY_PATH_MARKER + 'field_requirements.strength.std_dev_unknown.margin',
                },
            },
            "Materiales cementantes": {
                "Cemento Portland": {
                    "Marca": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_seller',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_type',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.cement_relative_density',
                },
                "Material cementante suplementario": {
                    "Uso de material cementante suplementario": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_checked',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_type',
                    "Contenido (%)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_content',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'cementitious_materials.SCM.SCM_relative_density',
                },
            },
            "Agregado fino": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.relative_density_SSD',
                    "Masa unitaria suelta (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUS',
                    "Masa unitaria compactada (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.gradation.passing',
                    # This will be replaced by a dict
                    "Módulo de finura": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fineness_modulus'
                },
            },
            "Agregado grueso": {
                "Información general": {
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.name',
                    "Lugar": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.source',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.info.type',
                },
                "Propiedades físicas": {
                    "Densidad relativa (SSS)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.relative_density_SSD',
                    "Masa unitaria suelta (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUS',
                    "Masa unitaria compactada (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.physical_prop.PUC',
                },
                "Humedad": {
                    "Contenido de humedad (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.moisture_content',
                    "Capacidad de absorción (%)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.moisture.absorption_content',
                },
                "Granulometría": {
                    "Porcentaje acumulado pasante": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.gradation.passing',
                    "Tamaño máximo nominal (mm)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.NMS'
                },
            },
            "Agua": {
                "Tipo": ReportDataModel.KEY_PATH_MARKER + 'water.water_type',
                "Lugar": ReportDataModel.KEY_PATH_MARKER + 'water.water_source',
                "Densidad (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'water.water_density',
            },
            "Aditivos": {
                "Reductor de agua": {
                    "Uso de reductor de agua": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_checked',
                    "¿Actúa como plastificante?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.plasticizer',
                    "¿Actúa como reductor de agua?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.water_reducer',
                    "¿Actúa como economizador de cemento?": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_action.cement_economizer',
                    "Tipo": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_type',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_dosage',
                    "Efectividad (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_effectiveness',
                },
                "Incorporador de aire": {
                    "Uso de incorporador de aire": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_checked',
                    "Nombre": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_name',
                    "Densidad relativa": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_relative_density',
                    "Dosis (%)": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_dosage',
                }
            },
        }
        # Dosage data per cubic meter (method to access data -> self.doe_data_model.get_data())
        self.dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_volume'
            },
            f"{scm_type}": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content'
            },
            "Aire incorporado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.WRA.WRA_volume'
            },
            "Incorporador de aire": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'chemical_admixtures.AEA.AEA_volume'
            },
        }
        # Adjusted dosage data (after testing) (method to access data -> self.data_model.get_design_value())
        self.adjusted_dosage_data = {
            "Agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_content_correction',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.water.water_volume'
            },
            "Cemento": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.cement.cement_volume'
            },
            f"{scm_type}": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.cementitious_material.scm.scm_volume'
            },
            "Agregado fino": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.fine_aggregate.fine_volume'
            },
            "Agregado grueso": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_abs_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_content_wet',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.coarse_aggregate.coarse_volume'
            },
            "Aire atrapado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrapped_air_content'
            },
            "Aire incorporado": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrained_air_content',
                "content": '-',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.air.entrained_air_content'
            },
            "Reductor de agua": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.WRA.WRA_volume'
            },
            "Incorporador de aire": {
                "abs_vol": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_volume',
                "content": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_content',
                "volume": ReportDataModel.KEY_PATH_MARKER + 'trial_mix.adjustments.chemical_admixtures.AEA.AEA_volume'
            },
        }
        # Notes on adjustments made (method to access data -> self.data_model.get_design_value())
        self.adjustment_notes = {
            "Agua": {
                "Cantidad de agua utilizada (L)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.water_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.water.keep_fine_agg',
            },
            "Material cementante": {
                "Cantidad de material cementante utilizado (kg)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.cementitious_used',
                "Cantidad de aire medido (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.air_measured',
                "Relación agua-material cementante final": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.w_cm',
                "Mantener proporción de agregado grueso": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_coarse_agg',
                "Mantener proporción de agregado fino": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.cementitious_material.keep_fine_agg',
            },
            "Proporción entre los agregados": {
                "Nueva proporción de agregado grueso (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_coarse_proportion',
                "Nueva proporción de agregado fino (%)": ReportDataModel.KEY_PATH_MARKER + 'adjustments_trial_mix.aggregate_proportion.new_fine_proportion',
            },
        }
        # Details of calculations by stages (for full report) (method to access data -> self.aci_data_model.get_data())
        self.calculation_details = {
            "1. Volumen de aire atrapado": {
                "Volumen (absoluto) de aire atrapado (L)": ReportDataModel.KEY_PATH_MARKER + 'air.entrapped_air_content',
            },
            "1. Volumen de aire incorporado": {
                "Volumen (absoluto) de aire incorporado (L)": ReportDataModel.KEY_PATH_MARKER + 'air.entrained_air_content',
            },
            "2. Resistencia promedio requerida (f_cr)": {
                "Valor de z": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.z_value',
                "Desviación estándar - 1 (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.std_dev_value_1',
                "Desviación estándar - 2 (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.std_dev_value_2',
                "Desviación estándar utilizada (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.std_dev_used',
                "Margen (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.margin',
                "f_cr (MPa)": ReportDataModel.KEY_PATH_MARKER + 'spec_strength.target_strength.target_strength_value',
            },
            "3. Relación agua-material cementante (a/cm)": {
                "Relación a/cm por resistencia": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_by_strength',
                "Relación a/cm por durabilidad": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_by_durability',
                "Relación a/cm utilizado": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm_previous',
            },
            "4. Contenido y volumen de agua (SSS)": {
                "Contenido base de agua por agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.base_agg_fine',
                "Contenido base de agua por agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.base_agg_coarse',
                "Contenido base de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.base',
                "Corrección por material cementante suplementario (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.scm_correction',
                "Corrección por aditivo reductor de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.wra_correction',
                "Contenido utilizado de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.final_content',
                "Volumen (absoluto) de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_abs_volume',
            },
            "5. Contenido y volumen absoluto del material cementante": {
                "Contenido ficticio de agua (Reductor de agua)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content.without_wra_correction',
                "Contenido base de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.base_content',
                "Contenido mínimo de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.min_content',
                "Contenido utilizado de material cementante (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.final_content',
                "Contenido utilizado de cemento (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content_temp',
                f"Contenido utilizado de {scm_type.lower()} (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_content_temp',
                "Volumen absoluto de cemento (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume_temp',
                f"Volumen absoluto de {scm_type.lower()} (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_abs_volume_temp',
            },
            "6. Revisión de la relación agua-material cementante (a/cm)": {
                "Relación a/cm recalculada (real)": ReportDataModel.KEY_PATH_MARKER + 'water_cementitious_materials_ratio.w_cm',
                "Contenido recalculado de cemento (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_content',
                f"Contenido recalculado de {scm_type.lower()} (kg)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_content',
                "Volumen absoluto recalculado de cemento (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.cement.cement_abs_volume',
                f"Volumen absoluto recalculado de {scm_type.lower()} (L)": ReportDataModel.KEY_PATH_MARKER + 'cementitious_material.scm.scm_abs_volume',
            },
            "7. Contenido y volumen absoluto de los agregados (SSS)": {
                "Densidad relativa del agregado combinado (SSS)": ReportDataModel.KEY_PATH_MARKER + 'concrete.combined_relative_density',
                "Densidad húmeda del concreto normal (kg/m³)": ReportDataModel.KEY_PATH_MARKER + 'concrete.wet_density',
                "Contenido total de los agregados (kg)": ReportDataModel.KEY_PATH_MARKER + 'concrete.total_aggregate_content',
                "Proporción de agregado fino (%)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_proportion',
                "Contenido de agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_ssd',
                "Contenido de agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_ssd',
                "Volumen absoluto de agregado fino (L)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_abs_volume',
                "Volumen absoluto de agregado grueso (L)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_abs_volume',
            },
            "8. Corrección por humedad": {
                "Contenido de agregado fino (kg)": ReportDataModel.KEY_PATH_MARKER + 'fine_aggregate.fine_content_wet',
                "Contenido de agregado grueso (kg)": ReportDataModel.KEY_PATH_MARKER + 'coarse_aggregate.coarse_content_wet',
                "Contenido de agua (kg)": ReportDataModel.KEY_PATH_MARKER + 'water.water_content_correction',
                "Volumen de agua (L)": ReportDataModel.KEY_PATH_MARKER + 'water.water_volume',
            },
        }

    def _get_specific_data_retrieval_func(self):
        return self.doe_data_model.get_data