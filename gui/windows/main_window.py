from functools import partial

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialog
from PyQt6.QtGui import QActionGroup, QPixmap, QIcon

from Concretus.gui.ui.ui_main_window import Ui_MainWindow
from Concretus.gui.windows.about_dialog import AboutDialog
from Concretus.gui.windows.config_dialog import ConfigDialog
from Concretus.gui.windows.regular_concrete_widget import RegularConcrete
from Concretus.logger import Logger
from Concretus.settings import DEFAULT_UNITS, IMAGE_PYQT_LOGO, ICON_SETTINGS, ICON_PRINT, ICON_EXIT, \
    ICON_ABOUT, ICON_CHECK_DESIGN, ICON_TRIAL_MIX, DEFAULT_LANG, IMAGE_ABOUT


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Create an instance of the GUI
        self.ui = Ui_MainWindow()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Default system language
        self.lang = DEFAULT_LANG
        # Default system of units
        self.units = DEFAULT_UNITS
        # Create a reference to the object (initially None)
        self.method = None
        self.about_dialog = None
        self.config_dialog = None
        self.report_dialog = None

        # Group the QAction
        self.group_action()
        # Apply resource paths
        self.apply_resource_paths()
        # Set up the main connections
        self.setup_connections()
        # Initialize the Regular Concrete design (initially None)
        self.regular_concrete = None
        # Initialize the logger
        self.logger = Logger(name='MainWindow', log_file='concretus.log')
        self.logger.info('The main window has been created')

    def group_action(self):
        """Set up QActionGroup for multiple menu actions."""
        # Set up a QActionGroup for the Regular Concrete sub-menu
        method_group = QActionGroup(self)
        method_group.addAction(self.ui.action_MCE)
        method_group.addAction(self.ui.action_ACI)
        method_group.addAction(self.ui.action_DoE)

    def apply_resource_paths(self):
        """Apply resource paths (images and icons) from settings.py."""
        # Images
        self.ui.label_pyqt_logo.setPixmap(QPixmap(str(IMAGE_PYQT_LOGO)))
        self.ui.label_logo.setPixmap(QPixmap(str(IMAGE_ABOUT)))

        # Icons
        self.ui.action_config.setIcon(QIcon(str(ICON_SETTINGS)))
        self.ui.action_report.setIcon(QIcon(str(ICON_PRINT)))
        self.ui.action_quit.setIcon(QIcon(str(ICON_EXIT)))
        self.ui.action_about.setIcon(QIcon(str(ICON_ABOUT)))
        self.ui.action_check_design.setIcon(QIcon(str(ICON_CHECK_DESIGN)))
        self.ui.action_trial_mix.setIcon(QIcon(str(ICON_TRIAL_MIX)))

    def setup_connections(self):
        """Set up the principal signal/slot connections."""
        # Initialize the Configuration Dialog
        self.ui.action_config.triggered.connect(self.show_config_dialog)

        # Initialize the Report Dialog
        self.ui.action_report.triggered.connect(self.show_report_dialog)

        # Initialize the Exit MessageBox
        self.ui.action_quit.triggered.connect(self.close)

        # Initialize the Concrete Regular Widget
        self.ui.action_MCE.triggered.connect(partial(self.show_regular_concrete, "MCE"))
        self.ui.action_ACI.triggered.connect(partial(self.show_regular_concrete, "ACI"))
        self.ui.action_DoE.triggered.connect(partial(self.show_regular_concrete, "DoE"))

        # Initialize the About Dialog
        self.ui.action_about.triggered.connect(self.show_about_dialog)

    def show_config_dialog(self):
        """Launch the Configuration dialog."""
        self.logger.info('The configuration dialog has been selected')

        if not self.config_dialog: # Create an instance only once
            self.config_dialog = ConfigDialog(self)
            # Set the default system of units and language
            self.config_dialog.set_current_settings(self.lang, self.units)

        if self.config_dialog.exec() == QDialog.DialogCode.Accepted:
            self.lang = self.config_dialog.get_lang_settings()
            self.logger.info(f'The actual language is: {self.lang}')
            self.units = self.config_dialog.get_units_settings()
            self.logger.info(f'The actual system of units is: {self.units}')

        # Run unit system update on Regular Concrete Widget only if it has already been instantiated
        if self.regular_concrete:
            self.regular_concrete.update_units(self.units, self.method)

    def show_report_dialog(self):
        self.logger.info('The report dialog has been selected')

    def show_regular_concrete(self, method):
        """
        Initialize the design for Regular Concrete.
        :param method: The method to update the fields.
        """
        self.logger.info('The Regular Concrete design has been selected')
        self.method = method
        self.logger.info(f'The {self.method} units has been selected')

        if not self.regular_concrete: # Create an instance only once
            self.regular_concrete = RegularConcrete(self)

        # Update the selected method on the Regular Concrete Widget
        self.regular_concrete.update_method(self.method)
        # Update the selected system of units on the Regular Concrete Widget
        self.regular_concrete.update_units(self.units, self.method)
        # Set the new center widget
        self.setCentralWidget(self.regular_concrete)

    def show_about_dialog(self):
        """Launch the About dialog."""
        self.logger.info('The about dialog has been selected')
        if not self.about_dialog:
            self.about_dialog = AboutDialog(self)
        self.about_dialog.exec()

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