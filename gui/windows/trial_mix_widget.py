from PyQt6.QtWidgets import QWidget

from Concretus.gui.ui.ui_trial_mix_widget import Ui_TrialMixWidget
from Concretus.logger import Logger


class TrialMix(QWidget):
    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_TrialMixWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Connect to the data model
        self.data_model = data_model

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Trial mix widget initialized')