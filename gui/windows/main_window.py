from functools import partial

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialog, QStackedWidget, QLabel
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
                      ICON_ADJUST_ADMIXTURES)

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

    def setup_connections(self):
        """Set local signal/slot connections, i.e. the connections within the same QWidget."""

        # Initialize the dialogs when requested by the user
        self.ui.action_config.triggered.connect(self.handle_action_config_triggered)
        self.ui.action_report.triggered.connect(self.handle_action_report_triggered)
        self.ui.action_about.triggered.connect(self.handle_action_about_triggered)
        self.ui.action_adjust_materials.triggered.connect(self.handle_action_adjust_materials_triggered)
        self.ui.action_adjust_admixtures.triggered.connect(self.handle_action_adjust_admixtures_triggered)

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
        Enable the appropriate actions based on the current step and if some validation error keys do not exist.

        :param int current_step: The current step in the workflow.
        """

        actions_to_enable = {
            2: self.ui.action_check_design,
            3: self.ui.action_trial_mix,
            4: self.ui.menu_adjust_trial_mix,
        }

        if current_step in actions_to_enable:
            action = actions_to_enable[current_step]

            if action == self.ui.action_check_design:
                action.setEnabled(True)
                # Disable the other actions
                self.ui.action_trial_mix.setEnabled(False)
                self.ui.menu_adjust_trial_mix.setEnabled(False)

            elif action == self.ui.action_trial_mix:
                method = self.data_model.method

                # Define error keys for each method
                if method == "ACI":
                    required_keys = [
                        "GRADING REQUIREMENTS FOR FINE AGGREGATE",
                        "FINENESS MODULUS",
                        "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                        "CEMENTITIOUS MATERIAL REQUIRED DUE TO SULFATE EXPOSURE",
                        "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                        "MINIMUM ENTRAINED AIR",
                        "DATA ENTRY"
                    ]
                elif method in ("MCE", "DoE"):
                    required_keys = [
                        "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                        "CEMENTITIOUS MATERIAL REQUIRED DUE TO SULFATE EXPOSURE",
                        "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                        "MINIMUM ENTRAINED AIR",
                        "DATA ENTRY"
                    ]
                else:
                    required_keys = []

                # Check if any the error keys exist in the validation errors dictionary
                missing_keys = [key for key in required_keys if key in self.data_model.validation_errors]

                if method == "ACI":
                    has_fineness_modulus_error = "FINENESS MODULUS" in self.data_model.validation_errors
                    has_grading_requirements_error = "GRADING REQUIREMENTS FOR FINE AGGREGATE" in self.data_model.validation_errors

                    if has_fineness_modulus_error and not has_grading_requirements_error:
                        missing_keys.remove("FINENESS MODULUS")
                    elif has_grading_requirements_error and not has_fineness_modulus_error:
                        missing_keys.remove("GRADING REQUIREMENTS FOR FINE AGGREGATE")

                if not missing_keys:
                    # If no critical error keys exist, enable the action
                    action.setEnabled(True)
                else:
                    # Keep the action disabled
                    action.setEnabled(False)

            elif action == self.ui.menu_adjust_trial_mix:
                action.setEnabled(True)

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

    def handle_action_adjust_materials_triggered(self):
        """Launch the Adjust Trial Mix dialog."""

        self.logger.info('The adjust trial mix dialog has been selected')

        adjust_trial_mix = AdjustTrialMixDialog(self.data_model, self.mce_data_model, self.aci_data_model,
                                                self.doe_data_model, self)
        adjust_trial_mix.exec()

    def handle_action_adjust_admixtures_triggered(self):
        """Return to the Chemical Admixtures widget."""

        self.logger.info('The adjust admixture action has been selected')

        # partial(lambda data_model: self.show_regular_concrete(data_model.method, 6), self.data_model)
        # lambda: self.show_regular_concrete(self.data_model.method, 6)
        self.handle_show_regular_concrete_triggered(self.data_model.method, 6)

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

        self.logger.info('The check design has been selected')

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