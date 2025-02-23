from functools import partial

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

from Concretus.gui.ui.ui_check_design_widget import Ui_CheckDesignWidget
from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.core.regular_concrete.models.validation import Validation
from Concretus.logger import Logger
from Concretus.settings import VALID_STYLE, INVALID_STYLE, FINENESS_MODULUS_LIMITS


class CheckDesign(QWidget):
    # Define custom signals
    regular_concrete_requested = pyqtSignal()
    plot_requested = pyqtSignal(str)

    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        self.ui = Ui_CheckDesignWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Create an instance of the validation module
        self.validation = Validation(self.data_model)

        # Global signal/slot connections
        self.global_connections()

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Check design widget initialized')

    def on_enter(self):
        """Prepare widget when it becomes visible."""

        self.validation.calculate_grading_percentages()
        self.grading_requirements()
        self.show_nms()
        self.allowed_fineness_modulus()
        self.minimum_spec_strength()

        # Check if necessary calculations should be performed
        if self.data_model.method != 'MCE':
            if self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked'):
                self.ui.groupBox_SCM.setEnabled(True)
                self.maximum_scm_content()
            if self.data_model.get_design_value(
                    'field_requirements.air_content.air_content_checked') and not self.data_model.get_design_value(
                    'field_requirements.air_content.exposure_defined'):
                self.ui.groupBox_air_content.setEnabled(True)
                self.minimum_entrained_air()

        # Update the progress bar
        self.update_progress_bar()

    def on_exit(self):
        """Clean up widget when navigating away."""

        self.data_model.clear_validation_errors()
        self.clean_up_fields()

        # Disable these fields
        self.ui.groupBox_SCM.setEnabled(False)
        self.ui.groupBox_air_content.setEnabled(False)

    def global_connections(self):
        """Set global signal/slot connections, i.e. the connections between different QWidgets."""

        # Minimum GUI update every time units change
        self.data_model.units_changed.connect(lambda units: self.update_units(units))
        # Go to Regular Concrete widget when requested by the user
        self.ui.pushButton_review_design.clicked.connect(self.get_back_button_clicked)
        # Show the plot (fine or coarse aggregate) when requested by the user
        self.ui.pushButton_fine_graph.clicked.connect(partial(self.display_plot_button_clicked, "fine"))
        self.ui.pushButton_coarse_graph.clicked.connect(partial(self.display_plot_button_clicked, "coarse"))

    @staticmethod
    def load_style(style_file):
        """
        Loads the contents of a CSS file.

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
        """Clears the text content of specified line edits and resets their styles."""

        # Fields to clean
        clear_fields = [
            self.ui.lineEdit_SCM_type,
            self.ui.lineEdit_SCM_actual,
            self.ui.lineEdit_SCM_max,
            self.ui.lineEdit_exposure_class_2,
            self.ui.lineEdit_air_NMS,
            self.ui.lineEdit_NMS,
            self.ui.lineEdit_air_actual,
            self.ui.lineEdit_air_min
        ]

        for field in clear_fields:
            field.clear()
            self.apply_validation_style(field, None)

    def update_progress_bar(self):
        """
        Updates the progress bar based on the number of validation errors.
        0 errors correspond to 100% progress and 6 errors to 0% progress.
        """

        # Retrieve the dictionary with all errors
        validation_errors = self.data_model.validation_errors

        # Define error keys and assign 1 if key exists in validation_errors, otherwise 0
        error_keys = [
            "GRADING REQUIREMENTS FOR COARSE AGGREGATE",
            "GRADING REQUIREMENTS FOR FINE AGGREGATE",
            "FINENESS MODULUS",
            "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
            "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
            "MINIMUM ENTRAINED AIR",
        ]
        errors = {key: 1 if key in validation_errors else 0 for key in error_keys}

        # Retrieve the scores for coarse and fine gradings
        coarse_scores = self.data_model.get_design_value('validation.coarse_scores')
        fine_scores = self.data_model.get_design_value('validation.fine_scores')

        # Determine the maximum score for coarse and fine; use 0 if empty
        k_1 = max(coarse_scores.values(), default=0)
        k_2 = max(fine_scores.values(), default=0)

        # Multiply the first two error values by their respective maximum scores
        weighted_error_1 = errors["GRADING REQUIREMENTS FOR COARSE AGGREGATE"] * k_1
        weighted_error_2 = errors["GRADING REQUIREMENTS FOR FINE AGGREGATE"] * k_2

        # Create a list of all errors, using the weighted values for the first two
        error_list = [
            weighted_error_1,
            weighted_error_2,
            errors["FINENESS MODULUS"],
            errors["MINIMUM SPECIFIED COMPRESSIVE STRENGTH"],
            errors["MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)"],
            errors["MINIMUM ENTRAINED AIR"],
        ]
        error_count = sum(error_list)
        max_errors = 6  # Total number of error categories

        # Calculate the progress percentage
        progress_value = 100 - (error_count * 100 / max_errors)

        # Update the progress bar with the computed value
        self.ui.progressBar.setValue(int(round(progress_value)))

    def get_back_button_clicked(self):
        """Pressing the button emits a signal to go to the RegularConcrete widget."""

        # When the button is pressed, the signal is emitted
        self.regular_concrete_requested.emit()

    def display_plot_button_clicked(self, aggregate_type):
        """
        Pressing the button emits a signal to go show the plotted grading curve.

        :param str aggregate_type: The aggregate to be plotted.
        """

        # When the button is pressed, the signal is emitted along with the type of aggregate to be plotted.
        self.plot_requested.emit(aggregate_type)

    def update_units(self, units):
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

    def grading_requirements(self):
        """
        Verify whether the sieve analysis given for fine and coarse aggregate are valid.
        Then updates the corresponding GUI fields.
        """

        # Retrieve the current method
        method = self.data_model.method
        # and passing percentage dictionaries for fine and coarse aggregate from the data model
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

        # Retrieve the grading list from the data model
        grading_list = self.data_model.get_design_value('coarse_aggregate.gradation.passing')

        # Calculate the nominal maximum size
        nms = self.validation.calculate_nominal_maximum_size(grading_list)

        # Update the data model
        self.data_model.update_design_data('coarse_aggregate.NMS', nms)

        # Update the fields in the GUI
        if nms is None:
            self.ui.lineEdit_NMS.setText('No hay granulometría')
        else:
            self.ui.lineEdit_NMS.setText(str(nms))

    def allowed_fineness_modulus(self):
        """
        Check whether the fineness modulus meets regulatory requirements.
        Then updates the corresponding GUI fields.
        """

        # Retrieve the current method and retained percentage dictionary for fine aggregate from the data model
        method = self.data_model.method
        cumulative_retained = self.data_model.get_design_value('fine_aggregate.gradation.cumulative_retained')

        # Obtain the fineness modulus and if it is value passed the requirements
        fineness_modulus, valid = self.validation.required_fineness_modulus(method, cumulative_retained)

        # Update the fineness modulus in the data model
        self.data_model.update_design_data('fine_aggregate.fineness_modulus', fineness_modulus)

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

        # Retrieve the method and current specified compressive strength from the data model
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

    def maximum_scm_content(self):
        """
        Check whether the given SCM content is lower than the maximum SCM content  permitted according
        to the exposure class. Then updates the corresponding GUI fields.
        """

        # Retrieve the method, exposure classes, scm type and its content from the data model
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

        # Retrieve values from the data model
        method = self.data_model.method
        exposure_classes = self.data_model.get_design_value('validation.exposure_classes')
        nms = self.data_model.get_design_value('coarse_aggregate.NMS')
        coarse_category = self.data_model.get_design_value('validation.coarse_category')
        entrained_air = self.data_model.get_design_value('field_requirements.air_content.user_defined')

        # Get the required minimum entrained air content and associated parameters.
        valid, minimum_entrained_air, exp_class, nms_val = self.validation.required_entrained_air(
            method,
            list(exposure_classes.values()),
            nms,
            coarse_category,
            entrained_air
        )

        # Format the exposure class string for display:
        if isinstance(exp_class, list):
            exp_class_text = ", ".join(exp_class)
        else:
            exp_class_text = str(exp_class)

        # Update the UI fields
        self.ui.lineEdit_exposure_class_2.setText(exp_class_text)
        if nms_val is None:
            self.ui.lineEdit_air_NMS.setText("No hay granulometría")
        else:
            self.ui.lineEdit_air_NMS.setText(nms_val)

        self.ui.lineEdit_air_actual.setText(str(entrained_air))
        self.ui.lineEdit_air_min.setText(str(minimum_entrained_air))

        # Apply validation style only if valid is not None (i.e., True or False)
        if valid is not None:
            self.apply_validation_style(self.ui.lineEdit_air_actual, valid)