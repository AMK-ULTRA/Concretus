from PyQt6.QtWidgets import QDialog

from gui.ui.ui_config_dialog import Ui_ConfigDialog
from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from logger import Logger
from settings import LANGUAGES, UNIT_SYSTEM


class ConfigDialog(QDialog):
    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_ConfigDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Set initial values
        self.ui.comboBox_lang.addItems(list(LANGUAGES.values()))
        self.ui.comboBox_units.addItems(list(UNIT_SYSTEM.values()))

        # Load the previous configuration
        self.load_config()

        # Initialization complete
        self.logger.info('Configuration dialog initialized')

    def get_lang_key(self):
        """Get the key associated with the current language from the "LANGUAGES" dictionary."""

        language = self.ui.comboBox_lang.currentText()
        for key, value in LANGUAGES.items():
            if value == language:
                return key

    def get_units_key(self):
        """Get the key associated with the current unit system from the "LANGUAGES" dictionary."""

        units = self.ui.comboBox_units.currentText()
        for key, value in UNIT_SYSTEM.items():
            if value == units:
                return key

    def save_config(self):
        """Save current language and unit system to data model."""

        lang_key, units_key = self.get_lang_key(), self.get_units_key()
        self.data_model.language = lang_key
        self.data_model.units = units_key

    def load_config(self):
        """Load the previous language and unit system."""

        lang_key, units_key = self.data_model.language, self.data_model.units
        self.ui.comboBox_lang.setCurrentText(LANGUAGES[lang_key])
        self.ui.comboBox_units.setCurrentText(UNIT_SYSTEM[units_key])