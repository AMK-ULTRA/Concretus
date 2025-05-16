from functools import partial

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QMessageBox

from gui.ui.ui_check_design_widget import Ui_CheckDesignWidget
from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.validation import Validation
from logger import Logger
from settings import VALID_STYLE, INVALID_STYLE, FINENESS_MODULUS_LIMITS, NMS_VALID, ERROR_KEYS


class CheckDesign(QWidget):
    # Define custom signals
    request_regular_concrete_from_check = pyqtSignal()
    plot_requested = pyqtSignal(str)

    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        self.ui = Ui_CheckDesignWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Create an instance of the validation module
        self.validation = Validation(self.data_model)

        # Global signal/slot connections
        self.global_connections()

        # Initialization complete
        self.logger.info('Check design widget initialized')

    def on_enter(self):
        """Prepare widget when it becomes visible."""

        self.validation.calculate_grading_percentages()
        self.grading_requirements()
        self.show_nms()
        self.allowed_fineness_modulus()
        self.minimum_spec_strength()
        self.cement_type_required()

        # Check if necessary calculations should be performed
        if self.data_model.method != 'MCE':
            if self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked'):
                self.ui.groupBox_SCM.setEnabled(True)
                self.maximum_scm_content()
            if (self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked')
                    and not self.data_model.get_design_value('field_requirements.entrained_air_content.exposure_defined')):
                self.ui.groupBox_air_content.setEnabled(True)
                self.minimum_entrained_air()

        # Update the progress bar
        self.update_progress_bar()
        # Check the inputs
        if self.validate_inputs():
            self.data_model.current_step = 3 # Update de current step if the validation pass

    def on_exit(self):
        """Clean up widget when navigating away."""

        for section in ERROR_KEYS:
            self.data_model.clear_validation_errors(section)
        self.clean_up_fields()

        # Disable these fields
        self.ui.groupBox_SCM.setEnabled(False)
        self.ui.groupBox_air_content.setEnabled(False)

    def global_connections(self):
        """Set global signal/slot connections, i.e. the connections between different QWidgets."""

        # Change the display of units when the current system of units changes
        self.data_model.units_changed.connect(lambda units: self.handle_CheckDesign_units_changed(units))
        # Show the regular concrete widget when requested by the user
        self.ui.pushButton_review_design.clicked.connect(self.handle_CheckDesign_regular_concrete_requested_MainWindow)
        # Show the plot dialog when requested by the user
        self.ui.pushButton_fine_graph.clicked.connect(
            partial(self.handle_CheckDesign_plot_requested_MainWindow, "fine"))
        self.ui.pushButton_coarse_graph.clicked.connect(
            partial(self.handle_CheckDesign_plot_requested_MainWindow, "coarse"))

    @staticmethod
    def load_style(style_file):
        """
        Load the contents of a CSS file.

        :param str style_file: The path to the CSS file.
        :returns: The sheet style.
        :rtype: str
        """

        with open(style_file, 'r') as f:
            return f.read()

    def apply_validation_style(self, line_edit, is_valid):
        """
        Apply a sheet style for validation fields.

        :param any line_edit: The QLineEdit widget to apply the sheet style (e.g. self.ui.lineEdit_SCM_max).
        :param bool | None is_valid: Is True, a valid sheet style is applied; is False, an invalid sheet style
                                     is applied; is None, clear any sheet style previously applied.
        """

        # Load the style
        valid_sheet_style = self.load_style(VALID_STYLE)
        invalid_sheet_style = self.load_style(INVALID_STYLE)
        clear_sheet_style = ""

        if is_valid is True:
            line_edit.setStyleSheet(valid_sheet_style)
        elif is_valid is False:
            line_edit.setStyleSheet(invalid_sheet_style)
        elif is_valid is None:
            line_edit.setStyleSheet(clear_sheet_style)

    def clean_up_fields(self):
        """Clear the text content of specified line edits and reset their styles."""

        # Fields to clean
        clear_fields = [
            self.ui.lineEdit_SCM_type,
            self.ui.lineEdit_SCM_actual,
            self.ui.lineEdit_SCM_max,
            self.ui.lineEdit_exposure_class_2,
            self.ui.lineEdit_air_NMS,
            self.ui.lineEdit_NMS,
            self.ui.lineEdit_air_actual,
            self.ui.lineEdit_air_min,
            self.ui.lineEdit_cement_used
        ]

        for field in clear_fields:
            field.clear()
            self.apply_validation_style(field, None)

    def update_progress_bar(self):
        """
        Update the progress bar based on the number of validation errors.
        0 errors correspond to 100% progress and 7 errors to 0% progress.
        """

        # Retrieve the dictionary with all errors
        validation_errors = self.data_model.validation_errors

        # Using the ERROR_KEYS dictionary, assign 0 if key exists in validation_errors, otherwise 1
        errors = {key: 0 if key in validation_errors else 1 for key in ERROR_KEYS}

        # Retrieve the scores for coarse and fine gradings
        coarse_scores = self.data_model.get_design_value('validation.coarse_scores')
        fine_scores = self.data_model.get_design_value('validation.fine_scores')

        # Determine the maximum score for coarse and fine; use 1 if empty
        weighted_error_1 = max(coarse_scores.values(), default=1)
        weighted_error_2 = max(fine_scores.values(), default=1)

        # Update the errors dictionary with the weighted values for coarse and fine grading requirements
        errors["GRADING REQUIREMENTS FOR COARSE AGGREGATE"] = weighted_error_1
        errors["GRADING REQUIREMENTS FOR FINE AGGREGATE"] = weighted_error_2

        # Determine the validations that were passed
        validation_passed = sum(errors.values())

        # Total number of validation categories
        max_validation = 7

        # Calculate the progress percentage
        progress_value = (validation_passed / max_validation) * 100

        # Update the progress bar with the computed value
        self.ui.progressBar.setValue(int(round(progress_value)))

    def validate_inputs(self):
        """
        Validate the input data from the data model. If any critical errors are detected,
        a warning message box will be shown and the get_back_button_clicked() method will be triggered.

        :return bool: True if validation passes, False otherwise.
        """

        # Retrieve inputs from the data model
        fine_relative_density = self.data_model.get_design_value('fine_aggregate.physical_prop.relative_density_SSD')
        coarse_relative_density = self.data_model.get_design_value('coarse_aggregate.physical_prop.relative_density_SSD')
        cement_relative_density = self.data_model.get_design_value('cementitious_materials.cement_relative_density')
        scm_relative_density = self.data_model.get_design_value('cementitious_materials.SCM.SCM_relative_density')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')
        scm_checked = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')
        fine_loose_bulk_density = self.data_model.get_design_value('fine_aggregate.physical_prop.PUS')
        coarse_loose_bulk_density = self.data_model.get_design_value('coarse_aggregate.physical_prop.PUS')
        coarse_compacted_bulk_density = self.data_model.get_design_value('coarse_aggregate.physical_prop.PUC')
        entrained_air = self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked')
        entrained_air_exposure_defined = self.data_model.get_design_value('field_requirements.entrained_air_content.exposure_defined')
        std_dev_known = self.data_model.get_design_value('field_requirements.strength.std_dev_known.std_dev_known_enabled')
        std_dev_value = self.data_model.get_design_value('field_requirements.strength.std_dev_known.std_dev_value')
        doe_margin = self.data_model.get_design_value('field_requirements.strength.std_dev_unknown.margin')
        aea_checked = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_checked')
        aea_relative_density = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_relative_density')
        aea_dosage = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_dosage')
        exposure_class_aci = self.data_model.get_design_value('field_requirements.exposure_class.items_2')
        exposure_class_doe = self.data_model.get_design_value('field_requirements.exposure_class.items_3')
        nominal_max_size = self.data_model.get_design_value('coarse_aggregate.NMS')
        passing_600 = self.data_model.get_design_value('fine_aggregate.gradation.passing')
        coarse_moisture = self.data_model.get_design_value('coarse_aggregate.moisture.moisture_content')
        coarse_absorption = self.data_model.get_design_value('coarse_aggregate.moisture.absorption_content')
        fine_moisture = self.data_model.get_design_value('fine_aggregate.moisture.moisture_content')
        fine_absorption = self.data_model.get_design_value('fine_aggregate.moisture.absorption_content')
        wra_checked = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_checked')
        wra_plasticizer = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_action.plasticizer')
        wra_water_reducer = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_action.water_reducer')
        wra_cement_economizer = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_action.cement_economizer')
        wra_relative_density = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_relative_density')
        wra_dosage = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_dosage')
        wra_effectiveness = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_effectiveness')

        # Get the design method
        method = self.data_model.method

        warnings = []

        # Check zero relative density
        if fine_relative_density == 0:
            warnings.append("La densidad relativa del agregado fino no puede ser cero.")
        if coarse_relative_density == 0:
            warnings.append("La densidad relativa del agregado grueso no puede ser cero.")
        if cement_relative_density == 0:
            warnings.append("La densidad relativa del cemento no puede ser cero.")
        if scm_relative_density == 0 and scm_checked:
            warnings.append(f"La densidad relativa del SCM ({scm_type}) no puede ser cero.")
        if wra_relative_density == 0 and wra_checked:
            warnings.append("La densidad relativa del aditivo reductor de agua no puede ser cero.")
        if aea_relative_density == 0 and aea_checked:
            warnings.append("La densidad relativa del aditivo incorporador de aire no puede ser cero.")

        # Check standard deviation values
        if std_dev_known and std_dev_value == 0.0:
            warnings.append("La desviación estándar a usar no puede ser cero.")
        if method == "DoE" and doe_margin == 0:
            warnings.append("El margen de seguridad a usar no puede ser cero.")

        # Check bulk density with method-specific messages
        if fine_loose_bulk_density == 0:
            if method == "MCE":
                warnings.append("El peso unitario suelto del agregado fino no puede ser cero.")
            else:
                warnings.append("La masa unitaria suelta del agregado fino no puede ser cero.")
        if coarse_loose_bulk_density == 0:
            if method == "MCE":
                warnings.append("El peso unitario compactado del agregado fino no puede ser cero.")
            else:
                warnings.append("La masa unitaria compactada del agregado fino no puede ser cero.")
        if coarse_compacted_bulk_density == 0 and method == "ACI":
            warnings.append("La masa unitaria compactada del agregado grueso no puede ser cero.")

        # Validate entrained air requirements
        if entrained_air and entrained_air_exposure_defined:
            if method == "ACI" and exposure_class_aci not in ["F1", "F2", "F3"]:
                warnings.append("La clase de exposición indicada no requiere de aire incorporado.")
            if method == "DoE" and exposure_class_doe not in ["XF2", "XF3", "XF4"]:
                warnings.append("La clase de exposición indicada no requiere de aire incorporado.")
        if not entrained_air:
            if method == "ACI" and exposure_class_aci in ["F1", "F2", "F3"]:
                warnings.append("La clase de exposición indicada requiere de aire incorporado.")
            if method == "DoE" and exposure_class_doe in ["XF2", "XF3", "XF4"]:
                warnings.append("La clase de exposición indicada requiere de aire incorporado.")

        # Validate AEA requirements
        if entrained_air and not aea_checked:
            warnings.append("Aditivo incorporador de aire requerido (diseño con aire incorporado).")
        if aea_checked and not entrained_air:
            warnings.append("Aditivo incorporador de aire no requerido (diseño sin aire incorporado).")
        if aea_dosage == 0 and aea_checked:
            warnings.append("La dosis del aditivo incorporador de aire no puede ser cero.")

        # Validate WRA requirements
        if wra_checked and not any([wra_plasticizer, wra_water_reducer, wra_cement_economizer]):
            warnings.append("Seleccione el efecto deseado del aditivo reductor de agua.")
        if wra_checked and not wra_plasticizer and not wra_effectiveness:
            warnings.append("Ingrese la efectividad del aditivo reductor de agua.")
        if wra_checked and not wra_dosage:
            warnings.append("La dosis del aditivo reductor de agua no puede ser cero.")

        # Validate nominal maximum size
        if nominal_max_size is None:
            nominal_max_size = "Indeterminado"
        if method == "MCE" and nominal_max_size not in NMS_VALID["MCE"]:
            warnings.append(f"Los calculos no son aplicables con este tamaño máximo nominal: {nominal_max_size}")
        if method == "ACI" and nominal_max_size not in NMS_VALID["ACI"]:
            warnings.append(f"Los calculos no son aplicables con este tamaño máximo nominal: {nominal_max_size}")
        if method == "DoE" and nominal_max_size not in NMS_VALID["DoE"]:
            warnings.append(f"Los calculos no son aplicables con este tamaño máximo nominal: {nominal_max_size}")

        # Validate grading limits
        if method == "DoE" and passing_600.get("No. 30 (0,600 mm)", 1) is None:
            warnings.append("El celda para el cedazo No. 30 (0,600 mm) no puede estar vacía.")

        # Validate the absorption and moisture percentage
        if coarse_moisture == 0:
            warnings.append("El porcentaje de humedad del agregado grueso no pueden ser cero.")
        if coarse_absorption == 0:
            warnings.append("El porcentaje de absorción del agregado grueso no pueden ser cero.")
        if fine_moisture == 0:
            warnings.append("El porcentaje de humedad del agregado fino no pueden ser cero.")
        if fine_absorption == 0:
            warnings.append("El porcentaje de absorción del agregado fino no pueden ser cero.")

        # If there are warnings, display them in a QMessageBox and connect the signals
        if warnings:
            # Add a validation error to the data model
            self.data_model.add_validation_error("Data entry", "Some inputs are not valid")

            # Construct the message text
            message = "Se encontraron los siguientes errores en el ingreso de los datos:\n\n" + "\n".join(warnings)

            # Create the QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Errores en datos de diseño")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.finished.connect(self.handle_CheckDesign_regular_concrete_requested_MainWindow)
            msg_box.exec()

            return False  # Indicate that validation did not pass

        else:
            # Remove the validation error from the data model (if it fails the first time)
            self.data_model.clear_validation_errors("DATA ENTRY")

            return True # Indicate that validation pass

    def grading_requirements(self):
        """
        Verify whether the sieve analysis given for fine and coarse aggregate are valid.
        Then updates the corresponding GUI fields.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        measured_coarse = self.data_model.get_design_value('coarse_aggregate.gradation.passing')
        measured_fine = self.data_model.get_design_value('fine_aggregate.gradation.passing')

        # Get the classification for each sieve analysis
        fine_category, coarse_category = self.validation.classify_grading(method, measured_coarse, measured_fine)

        # Update the fields in the GUI
        for line_edit, category in zip(
                [self.ui.lineEdit_fine_check, self.ui.lineEdit_coarse_check],
                [fine_category, coarse_category]
        ):
            if category is None:
                line_edit.setText('Sin coincidencia')
                self.apply_validation_style(line_edit, False)
            else:
                line_edit.setText(category)
                self.apply_validation_style(line_edit, True)

    def show_nms(self):
        """Display the nominal maximum size of the coarse aggregate."""

        # Retrieve design parameters from the data model
        method = self.data_model.method
        coarse_category = self.data_model.get_design_value('validation.coarse_category')
        grading_list = self.data_model.get_design_value('coarse_aggregate.gradation.passing')

        # Calculate the nominal maximum size
        nms = self.validation.calculate_nominal_maximum_size(grading_list, method, coarse_category)

        # Update the fields in the GUI
        if nms is None:
            self.ui.lineEdit_NMS.setText('Indeterminado')
        else:
            self.ui.lineEdit_NMS.setText(str(nms))

    def allowed_fineness_modulus(self):
        """
        Check whether the fineness modulus meets regulatory requirements. Then updates the corresponding GUI fields.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        cumulative_retained = self.data_model.get_design_value('fine_aggregate.gradation.cumulative_retained')

        # Obtain the fineness modulus and if it is value passed the requirements
        fineness_modulus, valid = self.validation.required_fineness_modulus(method, cumulative_retained)

        # Retrieve the limits according to the method
        fm_limits = FINENESS_MODULUS_LIMITS.get(method, {})
        fm_max = fm_limits.get("FM_MAXIMUM")
        fm_min = fm_limits.get("FM_MINIMUM")

        # Update the fields in the GUI
        self.ui.lineEdit_FM_actual.setText(str(fineness_modulus))
        self.apply_validation_style(self.ui.lineEdit_FM_actual, valid)

        if fm_max is None and fm_min is None:
            self.ui.lineEdit_FM_max.setText("N/A")
            self.ui.lineEdit_FM_min.setText("N/A")
        else:
            self.ui.lineEdit_FM_max.setText(str(fm_max))
            self.ui.lineEdit_FM_min.setText(str(fm_min))

    def minimum_spec_strength(self):
        """
        Check whether the specified compressive strength is sufficient for the given exposure classes.
        Then updates the corresponding GUI fields.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        current_spec_strength = self.data_model.get_design_value('field_requirements.strength.spec_strength')

        # Get exposure classes
        exposure_classes = {}
        for groups, items in {'group_1': 'items_1', 'group_2': 'items_2', 'group_3': 'items_3',
                             'group_4': 'items_4'}.items():
            group = self.data_model.get_design_value(f'field_requirements.exposure_class.{groups}')
            item = self.data_model.get_design_value(f'field_requirements.exposure_class.{items}')
            exposure_classes[group] = item

        # Update de the data model
        self.data_model.update_design_data('validation.exposure_classes', exposure_classes)

        # Check if the given specified compressive strength is sufficient
        valid, minimum_value, exposure_class = self.validation.required_spec_strength(method, current_spec_strength, list(exposure_classes.values()))

        # Update the fields in the GUI
        for groups, items in exposure_classes.items():
            if items == exposure_class:
                self.ui.lineEdit_exposure_class.setText(f'{groups}: {exposure_class}')
                break # If it is already found, there is no need to continue

        self.ui.lineEdit_spec_strength_actual.setText(str(current_spec_strength))
        self.ui.lineEdit_spec_strength_min.setText(str(minimum_value))
        self.apply_validation_style(self.ui.lineEdit_spec_strength_actual, valid)

    def cement_type_required(self):
        """
        Validate the selected cement type against sulfate exposure requirements and update the GUI.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        exposure_classes = self.data_model.get_design_value('validation.exposure_classes')
        cement_type = self.data_model.get_design_value('cementitious_materials.cement_type')

        # Validate if the selected cement type meets sulfate exposure requirements
        sulfate_exposure, required_cement_types, valid = self.validation.required_cement_type(method, list(
            exposure_classes.values()), cement_type)

        # Update the GUI field for the cement type used
        self.ui.lineEdit_cement_used.setText(cement_type)

        # Update exposure class and required cement types in the GUI
        if sulfate_exposure is None and required_cement_types is None:
            self.ui.lineEdit_exposure_class_3.setText("N/A")
            self.ui.lineEdit_cement_required.setText("N/A")
        else:
            self.ui.lineEdit_exposure_class_3.setText(sulfate_exposure)
            self.ui.lineEdit_cement_required.setText(", ".join(required_cement_types))
            self.apply_validation_style(self.ui.lineEdit_cement_used, valid)

    def maximum_scm_content(self):
        """
        Check whether the given SCM content is lower than the maximum SCM content permitted according to
        the exposure class. Then updates the corresponding GUI fields.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        exposure_classes = self.data_model.get_design_value('validation.exposure_classes')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')
        scm_content = self.data_model.get_design_value('cementitious_materials.SCM.SCM_content')

        # Check if the provided SCM content meets the requirements
        valid, threshold_value = self.validation.required_scm_content(method, list(exposure_classes.values()), scm_type, scm_content)

        # Update the fields in the GUI
        self.ui.lineEdit_SCM_type.setText(scm_type)
        self.ui.lineEdit_SCM_actual.setText(str(scm_content))
        self.apply_validation_style(self.ui.lineEdit_SCM_actual, valid)

        if valid is None and threshold_value == 0:
            self.ui.lineEdit_SCM_max.setText('N/A')
        else:
            self.ui.lineEdit_SCM_max.setText(str(threshold_value))

    def minimum_entrained_air(self):
        """
        Verify if the specified entrained air content meets the minimum requirement based on exposure classes,
        nominal maximum size (NMS) and coarse aggregate category. Then updates the corresponding GUI fields.
        """

        # Retrieve design parameters from the data model
        method = self.data_model.method
        exposure_classes = self.data_model.get_design_value('validation.exposure_classes')
        nms = self.data_model.get_design_value('coarse_aggregate.NMS')
        entrained_air = self.data_model.get_design_value('field_requirements.entrained_air_content.user_defined')

        # Get the required minimum entrained air content and associated parameters
        valid, minimum_entrained_air, exp_class = self.validation.required_entrained_air(
            method,
            list(exposure_classes.values()),
            nms,
            entrained_air
        )

        # Format the exposure class string for display:
        if isinstance(exp_class, list):
            exp_class_text = ", ".join(exp_class)
        else:
            exp_class_text = str(exp_class)

        # Update the UI fields
        self.ui.lineEdit_exposure_class_2.setText(exp_class_text)
        if nms is None:
            self.ui.lineEdit_air_NMS.setText("Indeterminado")
        else:
            self.ui.lineEdit_air_NMS.setText(nms)

        self.ui.lineEdit_air_actual.setText(str(entrained_air))
        self.ui.lineEdit_air_min.setText(str(minimum_entrained_air))

        # Apply validation style only if valid is not None (i.e., True or False)
        if valid is not None:
            self.apply_validation_style(self.ui.lineEdit_air_actual, valid)

    def handle_CheckDesign_regular_concrete_requested_MainWindow(self):
        """Pressing the button emits a signal to go to the RegularConcrete widget."""

        # When the button is clicked, the signal is emitted
        self.request_regular_concrete_from_check.emit()

    def handle_CheckDesign_plot_requested_MainWindow(self, aggregate_type):
        """
        Pressing the button emits a signal to go show the plotted grading curve.

        :param str aggregate_type: The aggregate to be plotted.
        """

        # When the button is clicked, the signal is emitted along with the type of aggregate to be plotted
        self.plot_requested.emit(aggregate_type)

    def handle_CheckDesign_units_changed(self, units):
        """
        Update fields that depend on the selected unit system (only for the specified compressive strength fields).

        :param str units: The system of units to update the fields.
        """

        # Initialize the variables
        unit_suffix = None

        if units == 'SI':
            unit_suffix = 'MPa'
        elif units == 'MKS':
            unit_suffix = 'kgf/cm²'

        # Update the labels
        self.ui.label_spec_strength_actual.setText(f"Valor actual ({unit_suffix})")
        self.ui.label_spec_strength_min.setText(f"Valor mínimo ({unit_suffix})")