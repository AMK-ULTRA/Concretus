from functools import partial

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialog, QStackedWidget, QLabel
from PyQt6.QtGui import QActionGroup, QIcon

from Concretus.gui.ui.ui_main_window import Ui_MainWindow
from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.gui.windows.welcome_widget import Welcome
from Concretus.gui.windows.regular_concrete_widget import RegularConcrete
from Concretus.gui.windows.check_design_widget import CheckDesign
from Concretus.gui.windows.trial_mix_widget import TrialMix
from Concretus.gui.windows.about_dialog import AboutDialog
from Concretus.gui.windows.config_dialog import ConfigDialog
from Concretus.core.regular_concrete.plots.grading_curve import PlotDialog
from Concretus.logger import Logger
from Concretus.settings import ICON_SETTINGS, ICON_PRINT, ICON_EXIT, ICON_ABOUT, ICON_CHECK_DESIGN, ICON_TRIAL_MIX, \
    ICON_RESTART, ICON_HELP_MANUAL


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Create an instance of the GUI
        self.ui = Ui_MainWindow()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Create an instance of the data model
        self.data_model = RegularConcreteDataModel()

        # Group menu actions
        self.group_action()
        # Apply resource paths
        self.apply_resource_paths()
        # Set up the main connections
        self.setup_connections()

        # Create an empty reference to the widgets
        self.welcome = None
        self.regular_concrete = None
        self.check_design = None
        self.trial_mix = None

        # Set up a QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.init_components() # Initialize the components for the QStackedWidget

        # Global signal/slot connections
        self.global_connections()

        # Create a permanent label to display the current unit system on the right side
        self.units_label = QLabel(f"Unidades: {self.data_model.units}")
        self.ui.statusbar.addPermanentWidget(self.units_label)

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Main window initialized')

    def global_connections(self):
        """Set global signal/slot connections, i.e. the connections between different QWidgets."""

        # Enable the QActions according to the current step
        self.data_model.step_changed.connect(lambda current_step: self.enable_actions(current_step))
        # When requested, show the RegularWidget widget
        self.check_design.regular_concrete_requested.connect(partial(self.navigate_to, self.regular_concrete))
        # Show the plot (fine or coarse aggregate) when requested by the user
        self.check_design.plot_requested.connect(lambda aggregate_type: self.show_plot_dialog(aggregate_type))
        # Change the display of units when the current unit system changes
        self.data_model.units_changed.connect(lambda unit: self.update_unit_system(unit))

    def group_action(self):
        """Set up QActionGroup for multiple menu actions."""

        # Set up a QActionGroup for the Regular Concrete sub-menu
        method_group = QActionGroup(self)
        method_group.addAction(self.ui.action_MCE)
        method_group.addAction(self.ui.action_ACI)
        method_group.addAction(self.ui.action_DoE)

    def apply_resource_paths(self):
        """Apply resource paths for the icons."""

        # Paths are configured in the settings.py file
        self.ui.action_config.setIcon(QIcon(str(ICON_SETTINGS)))
        self.ui.action_report.setIcon(QIcon(str(ICON_PRINT)))
        self.ui.action_quit.setIcon(QIcon(str(ICON_EXIT)))
        self.ui.action_about.setIcon(QIcon(str(ICON_ABOUT)))
        self.ui.action_check_design.setIcon(QIcon(str(ICON_CHECK_DESIGN)))
        self.ui.action_trial_mix.setIcon(QIcon(str(ICON_TRIAL_MIX)))
        self.ui.action_restart.setIcon(QIcon(str(ICON_RESTART)))
        self.ui.action_manual.setIcon(QIcon(str(ICON_HELP_MANUAL)))

    def setup_connections(self):
        """Set up the menu connections."""

        # Initialize the dialogs (Config, Report & About) when requested by the user
        self.ui.action_config.triggered.connect(self.show_config_dialog)
        self.ui.action_report.triggered.connect(self.show_report_dialog)
        self.ui.action_about.triggered.connect(self.show_about_dialog)

        # Initialize the widgets (RegularConcrete, CheckDesign & TrialMix) when requested by the user
        self.ui.action_MCE.triggered.connect(partial(self.show_regular_concrete, "MCE"))
        self.ui.action_ACI.triggered.connect(partial(self.show_regular_concrete, "ACI"))
        self.ui.action_DoE.triggered.connect(partial(self.show_regular_concrete, "DoE"))
        self.ui.action_check_design.triggered.connect(self.show_check_design)
        self.ui.action_trial_mix.triggered.connect(self.show_trial_mix)

        # Restart the workflow
        self.ui.action_restart.triggered.connect(self.reset_system)

        # Initialize the Exit MessageBox when requested by the user
        self.ui.action_quit.triggered.connect(self.close)

    def init_components(self):
        """Initialize all widgets and add them to the QStackedWidget."""

        # Initialize all widgets
        self.welcome = Welcome(self.data_model, self)
        self.regular_concrete = RegularConcrete(self.data_model, self)
        self.check_design = CheckDesign(self.data_model, self)
        self.trial_mix = TrialMix(self.data_model, self)

        # Add each widget to the QStackedWidget
        self.stacked_widget.addWidget(self.welcome)
        self.stacked_widget.addWidget(self.regular_concrete)
        self.stacked_widget.addWidget(self.check_design)
        self.stacked_widget.addWidget(self.trial_mix)

        # Display the welcome widget
        self.show_welcome()

    def update_unit_system(self, new_units):
        """
        Update the units label when the unit system changes.

        :param str new_units: A string representing the new unit system.
        """

        self.units_label.setText(f"Unidades: {new_units}")

    def enable_actions(self, current_step):
        """
        Enables the appropriate actions based on the current step and that some validation error keys do not exist.

        :param int current_step: The current step in the workflow.
        """

        actions_to_enable = {
            2: self.ui.action_check_design,
            3: self.ui.action_trial_mix,
        }

        if current_step in actions_to_enable:
            action = actions_to_enable[current_step]

            # If the action is Trial Mix, check that the error keys does not exist
            if action == self.ui.action_trial_mix:
                method = self.data_model.method
                if method == "ACI":
                    required_keys = [
                        "FINENESS MODULUS",
                        "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                        "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                        "MINIMUM ENTRAINED AIR",
                        "DATA ENTRY"
                    ]
                elif method in ("MCE", "DoE"):
                    required_keys = [
                        "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
                        "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)",
                        "MINIMUM ENTRAINED AIR",
                        "DATA ENTRY"
                    ]
                else:
                    required_keys = []

                # Check if any the error keys exist in the validation errors dictionary
                missing_keys = [key for key in required_keys if key in self.data_model.validation_errors]
                if not missing_keys:
                    # If one or more error keys does not exist, enable the action
                    action.setEnabled(True)
                    return
                else:
                    # Keep the action disabled
                    action.setEnabled(False)
                    return

            # If all validations pass or the action is not Trial Mix, enable the action
            if action == self.ui.action_check_design:
                action.setEnabled(True)
                # Disable the Trial Mix widget
                self.ui.action_trial_mix.setEnabled(False)

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

    def show_config_dialog(self):
        """Launch the Configuration dialog."""

        self.logger.info('The configuration dialog has been selected')

        config_dialog = ConfigDialog(self.data_model, self)
        if config_dialog.exec() == QDialog.DialogCode.Accepted:
            config_dialog.save_config()

    def show_report_dialog(self):
        """Launch the Report dialog."""

        self.logger.info('The report dialog has been selected')

    def show_about_dialog(self):
        """Launch the About dialog."""

        self.logger.info('The about dialog has been selected')

        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def show_plot_dialog(self, aggregate_type):
        """
        Launch the About dialog.

        :param str aggregate_type: The type of aggregate to plot ("fine" or "coarse").
        """

        self.logger.info('The plot dialog has been selected')

        plot_dialog = PlotDialog(self.data_model, aggregate_type, self)
        plot_dialog.exec()

    def show_welcome(self):
        """Displays the Welcome widget."""

        self.navigate_to(self.welcome)

    def show_regular_concrete(self, method):
        """
        Displays the Regular Concrete widget.

        :param str method: The method to update the fields in the widget.
        """

        self.logger.info('The Regular Concrete design has been selected')
        self.data_model.method = method

        self.navigate_to(self.regular_concrete)

    def show_check_design(self):
        """Displays the Checking Design widget."""

        self.logger.info('The Check Design has been selected')

        self.navigate_to(self.check_design)

    def show_trial_mix(self):
        """Displays the Trial Mix widget."""

        self.logger.info('The Check Design has been selected')

        self.navigate_to(self.trial_mix)

    def reset_system(self):
        """Does nothing by now."""

        self.logger.info('The restart action has been selected')

    def confirm_exit(self):
        """Confirming the user's exit action by displaying a QMessageBox."""

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