import shutil
from functools import partial

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialog, QStackedWidget, QLabel, QFileDialog
from PyQt6.QtGui import QActionGroup, QIcon

from gui.ui.ui_main_window import Ui_MainWindow
from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from core.regular_concrete.models.aci_data_model import ACIDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from gui.windows.welcome_widget import Welcome
from gui.windows.regular_concrete_widget import RegularConcrete
from gui.windows.check_design_widget import CheckDesign
from gui.windows.trial_mix_widget import TrialMix
from gui.windows.adjust_mix_dialog import AdjustTrialMixDialog
from gui.windows.about_dialog import AboutDialog
from gui.windows.config_dialog import ConfigDialog
from core.regular_concrete.plots.grading_curve_plot_dialog import PlotDialog
from logger import Logger
from settings import (ICON_SETTINGS, ICON_PRINT, ICON_EXIT, ICON_ABOUT, ICON_CHECK_DESIGN, ICON_TRIAL_MIX, ICON_RESTART,
                      ICON_HELP_MANUAL, ICON_ADJUST_TRIAL_MIX, ICON_REGULAR_CONCRETE, ICON_ADJUST_MATERIALS,
                      ICON_ADJUST_ADMIXTURES, ICON_GET_BACK_DESIGN, USER_MANUAL)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Create an instance of the GUI
        self.ui = Ui_MainWindow()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Create an instance of the main data model
        self.data_model = RegularConcreteDataModel()
        # Create an instance for the data model of each method
        self.mce_data_model = MCEDataModel()
        self.aci_data_model = ACIDataModel()
        self.doe_data_model = DOEDataModel()

        # Group menu actions
        self.group_action()
        # Apply resource paths
        self.apply_resource_paths()

        # Create an empty reference to the widgets
        self.welcome = None
        self.regular_concrete = None
        self.check_design = None
        self.trial_mix = None

        # Set up a QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.init_components() # Initialize the components for the QStackedWidget

        # Create a permanent label to display the current unit system on the right side
        self.units_label = QLabel(f"Unidades: {self.data_model.units}")
        self.ui.statusbar.addPermanentWidget(self.units_label)

        # Set up local signal/slot connections
        self.setup_connections()
        # Set up global signal/slot connections
        self.global_connections()

        # Initialization complete
        self.logger.info('Main window initialized')

    def global_connections(self):
        """Set global signal/slot connections, i.e. the connections between different QWidgets."""

        # Enable the QActions according to the current step
        self.data_model.step_changed.connect(lambda current_step: self.handle_MainWindow_step_changed(current_step))
        # Change the display of units when the current system of units changes
        self.data_model.units_changed.connect(lambda units: self.handle_MainWindow_units_changed(units))
        # Show the regular concrete widget when requested by the user
        self.check_design.request_regular_concrete_from_check.connect(partial(self.navigate_to, self.regular_concrete))
        self.trial_mix.request_regular_concrete_from_trial.connect(partial(self.navigate_to, self.regular_concrete))
        # Show the plot dialog when requested by the user
        self.check_design.plot_requested.connect(lambda agg_type: self.handle_CheckDesign_plot_requested(agg_type))
        # Enable test mix adjustments if the test mix volume is non-zero
        self.trial_mix.adjust_mix_dialog_enabled.connect(lambda factor: self.handle_TrialMix_adjust_mix_dialog_enabled(factor))
        # Enable the admixture adjustment action if a chemical admixture has been used
        self.trial_mix.adjust_admixtures_action_enabled.connect(self.handle_TrialMix_adjust_admixtures_action_enabled)

    def setup_connections(self):
        """Set local signal/slot connections, i.e. the connections within the same QWidget."""

        # Initialize the dialogs when requested by the user
        self.ui.action_config.triggered.connect(self.handle_action_config_triggered)
        self.ui.action_report.triggered.connect(self.handle_action_report_triggered)
        self.ui.action_about.triggered.connect(self.handle_action_about_triggered)
        self.ui.action_adjust_materials.triggered.connect(self.handle_action_adjust_materials_triggered)
        self.ui.action_manual.triggered.connect(self.handle_action_manual_triggered)

        # Set the Regular Concrete widget as the current widget
        self.ui.action_adjust_admixtures.triggered.connect(self.handle_action_adjust_admixtures_triggered)
        self.ui.action_get_back_design.triggered.connect(self.handle_action_get_back_design_triggered)

        # Initialize the widgets (RegularConcrete, CheckDesign & TrialMix) when requested by the user
        self.ui.action_MCE.triggered.connect(partial(self.handle_show_regular_concrete_triggered, "MCE", None))
        self.ui.action_ACI.triggered.connect(partial(self.handle_show_regular_concrete_triggered, "ACI", None))
        self.ui.action_DoE.triggered.connect(partial(self.handle_show_regular_concrete_triggered, "DoE", None))
        self.ui.action_check_design.triggered.connect(self.handle_show_check_design_triggered)
        self.ui.action_trial_mix.triggered.connect(self.handle_show_trial_mix_triggered)

        # Restart the workflow
        self.ui.action_restart.triggered.connect(self.handle_action_restart_triggered)

        # Initialize the Exit MessageBox when requested by the user
        self.ui.action_quit.triggered.connect(self.close)

    def apply_resource_paths(self):
        """Apply resource paths for the icons."""

        # Paths are configured in the settings.py file
        self.ui.action_config.setIcon(QIcon(str(ICON_SETTINGS)))
        self.ui.action_report.setIcon(QIcon(str(ICON_PRINT)))
        self.ui.action_quit.setIcon(QIcon(str(ICON_EXIT)))
        self.ui.action_about.setIcon(QIcon(str(ICON_ABOUT)))
        self.ui.menu_regular_concrete.setIcon(QIcon(str(ICON_REGULAR_CONCRETE)))
        self.ui.action_check_design.setIcon(QIcon(str(ICON_CHECK_DESIGN)))
        self.ui.action_trial_mix.setIcon(QIcon(str(ICON_TRIAL_MIX)))
        self.ui.menu_adjust_trial_mix.setIcon(QIcon(str(ICON_ADJUST_TRIAL_MIX)))
        self.ui.action_adjust_materials.setIcon(QIcon(str(ICON_ADJUST_MATERIALS)))
        self.ui.action_adjust_admixtures.setIcon(QIcon(str(ICON_ADJUST_ADMIXTURES)))
        self.ui.action_get_back_design.setIcon(QIcon(str(ICON_GET_BACK_DESIGN)))
        self.ui.action_restart.setIcon(QIcon(str(ICON_RESTART)))
        self.ui.action_manual.setIcon(QIcon(str(ICON_HELP_MANUAL)))

    def group_action(self):
        """Set up QActionGroup for multiple menu actions."""

        # Set up a QActionGroup for the Regular Concrete sub-menu
        method_group = QActionGroup(self)
        method_group.addAction(self.ui.action_MCE)
        method_group.addAction(self.ui.action_ACI)
        method_group.addAction(self.ui.action_DoE)

    def init_components(self):
        """Initialize all widgets and add them to the QStackedWidget."""

        # Initialize all widgets
        self.welcome = Welcome(self.data_model, self)
        self.regular_concrete = RegularConcrete(self.data_model, self)
        self.check_design = CheckDesign(self.data_model, self)
        self.trial_mix = TrialMix(self.data_model,self.mce_data_model, self.aci_data_model, self.doe_data_model, self)

        # Add each widget to the QStackedWidget
        self.stacked_widget.addWidget(self.welcome)
        self.stacked_widget.addWidget(self.regular_concrete)
        self.stacked_widget.addWidget(self.check_design)
        self.stacked_widget.addWidget(self.trial_mix)

        # Display the welcome widget
        self.handle_show_welcome_triggered()

    def navigate_to(self, widget):
        """
        Navigate to the selected widget by updating the current widget in QStackedWidget.

        :param object widget: The widget to display.
        """

        current_widget = self.stacked_widget.currentWidget()

        if current_widget != widget:
            # Execute exit logic of the current widget
            if hasattr(current_widget, 'on_exit'):
                current_widget.on_exit()

            # Update widget
            self.stacked_widget.setCurrentWidget(widget)

            # Execute enter logic of the new widget
            if hasattr(widget, 'on_enter'):
                widget.on_enter()

    def handle_MainWindow_step_changed(self, current_step):
        """
        Enable the appropriate actions based on the current step and validation status.

        :param int current_step: The current step in the workflow.
        """

        # Disable all the actions
        self._disable_all_actions()

        # Mapping the steps and their corresponding actions
        actions_map = {
            2: self._handle_step_2_actions,
            3: self._handle_step_3_actions,
            4: self._handle_step_4_actions,
        }

        if current_step in actions_map:
            actions_map[current_step]()

    def _disable_all_actions(self):
        """Disable all relevant actions to maintain a clean state."""

        self.ui.action_check_design.setEnabled(False)
        self.ui.action_trial_mix.setEnabled(False)
        self.ui.menu_adjust_trial_mix.setEnabled(False)
        self.ui.action_get_back_design.setEnabled(False)

    def _handle_step_2_actions(self):
        """Configure the actions for step 2."""

        self.ui.action_check_design.setEnabled(True)

    def _handle_step_3_actions(self):
        """Configure the actions for step 3 based on method-specific validations."""

        method = self.data_model.method

        # Define the error keys required according to the method
        required_keys = self._get_required_keys_for_method(method)

        # Check if error keys exist in the validation error dictionary
        missing_keys = self._get_missing_validation_keys(required_keys, method)

        # Enable action if there are no critical errors
        self.ui.action_trial_mix.setEnabled(not missing_keys)

    @staticmethod
    def _get_required_keys_for_method(method):
        """
        Return the error keys required by the method.

        :param str method: The current method in used.
        """

        if method == "ACI":
            return [
                "GRADING REQUIREMENTS FOR FINE AGGREGATE",
                "FINENESS MODULUS",
                "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                "CEMENTITIOUS MATERIAL REQUIRED DUE TO SULFATE EXPOSURE",
                "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                "MINIMUM ENTRAINED AIR",
                "DATA ENTRY"
            ]
        elif method in ("MCE", "DoE"):
            return [
                "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                "CEMENTITIOUS MATERIAL REQUIRED DUE TO SULFATE EXPOSURE",
                "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                "MINIMUM ENTRAINED AIR",
                "DATA ENTRY"
            ]
        else:
            return []

    def _get_missing_validation_keys(self, required_keys, method):
        """
        Determine which validation keys are missing, considering special cases.

        :param list[str] required_keys: The keys required by the method.
        :param str method: The current method in used.
        """

        missing_keys = [key for key in required_keys if key in self.data_model.validation_errors]

        # Special handling for the ACI method
        if method == "ACI":
            self._handle_special_aci_validation(missing_keys)

        return missing_keys

    def _handle_special_aci_validation(self, missing_keys):
        """
        Handles special validation for the ACI method related to "FINENESS MODULUS" and "GRADING REQUIREMENTS".

        :param list[str] missing_keys: A list containing all missing validation keys required by the method.
        """

        has_fineness_modulus_error = "FINENESS MODULUS" in self.data_model.validation_errors
        has_grading_requirements_error = "GRADING REQUIREMENTS FOR FINE AGGREGATE" in self.data_model.validation_errors

        # If only one of the two errors is present, we remove it from the critical errors
        if has_fineness_modulus_error and not has_grading_requirements_error:
            if "FINENESS MODULUS" in missing_keys:
                missing_keys.remove("FINENESS MODULUS")
        elif has_grading_requirements_error and not has_fineness_modulus_error:
            if "GRADING REQUIREMENTS FOR FINE AGGREGATE" in missing_keys:
                missing_keys.remove("GRADING REQUIREMENTS FOR FINE AGGREGATE")

    def _handle_step_4_actions(self):
        """Configure the actions for step 4."""

        self.ui.menu_adjust_trial_mix.setEnabled(True)
        self.ui.action_get_back_design.setEnabled(True)

    def handle_MainWindow_units_changed(self, new_units):
        """
        Update the units label when the unit system changes.

        :param str new_units: A string representing the new unit system.
        """

        self.units_label.setText(f"Unidades: {new_units}")

    def handle_CheckDesign_plot_requested(self, aggregate_type):
        """
        Launch the Grading Curve Plotting dialog.

        :param str aggregate_type: The type of aggregate to plot ("fine" or "coarse").
        """

        self.logger.info('The grading curve plotting dialog has been selected')

        plot_dialog = PlotDialog(self.data_model, aggregate_type, self)
        plot_dialog.exec()

    def handle_TrialMix_adjust_mix_dialog_enabled(self, factor):
        """
        Enable the trial mix adjustment dialog if the trial mix volume (or factor) is greater than 0,
        otherwise, disable it.

        :param factor: Trial mix volume selected by the user.
        """

        if factor > 0:
            self.ui.action_adjust_materials.setEnabled(True)
        else:
            self.ui.action_adjust_materials.setEnabled(False)

    def handle_TrialMix_adjust_admixtures_action_enabled(self):
        """Enable the admixture adjustment if any chemical admixture has been used."""

        self.ui.action_adjust_admixtures.setEnabled(True)

    def handle_action_config_triggered(self):
        """Launch the Configuration dialog."""

        self.logger.info('The configuration dialog has been selected')

        config_dialog = ConfigDialog(self.data_model, self)
        if config_dialog.exec() == QDialog.DialogCode.Accepted:
            config_dialog.save_config()

    def handle_action_report_triggered(self):
        """Launch the Report dialog."""

        self.logger.info('The report dialog has been selected')

    def handle_action_about_triggered(self):
        """Launch the About dialog."""

        self.logger.info('The about dialog has been selected')

        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def handle_action_manual_triggered(self):
        """Allow the user to save a copy of the user manual in PDF format"""

        self.logger.info('The user manual has been selected')

        try:
            # Verify that the manual exists
            if not USER_MANUAL.exists():
                QMessageBox.critical(self, "Error", "No se pudo encontrar el manual de usuario.")
                return

            # Open dialog to select where to save the file
            destination_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Manual de Usuario",
                "Manual de Usuario - Concretus.pdf",
                "Archivos PDF (*.pdf)"
            )

            # If the user cancels the dialog, destination_path will be an empty string
            if destination_path:
                # Force .pdf extension
                if not destination_path.lower().endswith('.pdf'):
                    destination_path += '.pdf'

                # Copy the PDF file to the selected location
                shutil.copy(str(USER_MANUAL), destination_path)
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"El Manual de Usuario se guardó correctamente en:\n{destination_path}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el manual: {str(e)}")

    def handle_action_adjust_materials_triggered(self):
        """Launch the Adjust Trial Mix dialog."""

        self.logger.info('The adjust trial mix dialog has been selected')

        adjust_trial_mix = AdjustTrialMixDialog(self.data_model, self.mce_data_model, self.aci_data_model,
                                                self.doe_data_model, self)
        if adjust_trial_mix.exec() == QDialog.DialogCode.Accepted:
            # Load the results in the trial mix widget
            self.trial_mix.load_results("trial mix adjustments")
            # Clean up the proportions from the previous trial mix
            self.trial_mix.clear_last_two_columns("materials_table")
            self.trial_mix.clear_last_two_columns("admixture_table")

        # Disable the action
        self.ui.action_adjust_materials.setEnabled(False)

    def handle_action_adjust_admixtures_triggered(self):
        """Return to the Chemical Admixtures widget."""

        self.logger.info('The adjust admixture action has been selected')

        self.handle_show_regular_concrete_triggered(self.data_model.method, 6)

    def handle_action_get_back_design_triggered(self):
        """Return to the first widget in the Regular Concrete widget."""

        self.logger.info('The get back design action has been selected')

        self.handle_show_regular_concrete_triggered(self.data_model.method, 0)

    def handle_action_restart_triggered(self):
        """Restart the workflow."""

        self.logger.info('The restart action has been selected')

    def handle_show_welcome_triggered(self):
        """Display the Welcome widget."""

        self.navigate_to(self.welcome)

    def handle_show_regular_concrete_triggered(self, method, index=None):
        """
        Display the Regular Concrete widget.

        :param str method: The method to update the fields in the widget.
        :param int index: The index of the widget to display when the regular concrete widget is called.
        """

        self.logger.info('The regular concrete design has been selected')
        self.data_model.method = method
        if index:
            self.regular_concrete.set_index(index)

        self.navigate_to(self.regular_concrete)

    def handle_show_check_design_triggered(self):
        """Display the Checking Design widget."""

        self.logger.info('The check design has been selected')

        self.navigate_to(self.check_design)

    def handle_show_trial_mix_triggered(self):
        """Display the Trial Mix widget."""

        self.logger.info('The trial mix has been selected')

        self.navigate_to(self.trial_mix)

    def confirm_exit(self):
        """Confirm the user's exit action by displaying a QMessageBox."""

        reply = QMessageBox.question(self, 'Confirmación', "¿Estás seguro de que deseas salir?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def closeEvent(self, event):
        """Reimplement the close event based on the .confirm_exit() method."""

        self.logger.info('Exit dialog has been opened')
        if self.confirm_exit():
            self.logger.info('Exit dialog has been accepted')
            event.accept()
        else:
            self.logger.info('Exit dialog has been denied')
            event.ignore()