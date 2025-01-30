from PyQt6.QtWidgets import QDialog

from Concretus.gui.ui.ui_config_dialog import Ui_ConfigDialog
from Concretus.logger import Logger
from Concretus.settings import LANGUAGES, UNITS_SYSTEM


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_ConfigDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(name='ConfigDialog', log_file='concretus.log')
        self.logger.info('The configuration dialog has been created')

        # Set initial values
        self.ui.comboBox_lang.addItems(list(LANGUAGES.values()))
        self.ui.comboBox_units.addItems(list(UNITS_SYSTEM.values()))

    def get_lang_settings(self):
        """Get the current language."""
        language = self.ui.comboBox_lang.currentText()
        for key, value in LANGUAGES.items():
            if value == language:
                return key

    def get_units_settings(self):
        """Get the current unit system."""
        units = self.ui.comboBox_units.currentText()
        for key, value in UNITS_SYSTEM.items():
            if value == units:
                return key

    def set_current_settings(self, language, units):
        """Set the new language and unit system."""
        self.ui.comboBox_lang.setCurrentText(LANGUAGES[language])
        self.ui.comboBox_units.setCurrentText(UNITS_SYSTEM[units])