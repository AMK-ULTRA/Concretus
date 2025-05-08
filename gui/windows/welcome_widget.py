from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap

from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from gui.ui.ui_welcome_widget import Ui_WelcomeWidget
from logger import Logger
from settings import IMAGE_PYQT_LOGO, IMAGE_ABOUT


class Welcome(QWidget):
    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_WelcomeWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Apply resource paths
        self.apply_resource_paths()

        # Initialization complete
        self.logger.info('Welcome widget initialized')

    def on_enter(self):
        """Prepare widget when it becomes visible."""

        self.data_model.current_step = 1

    def apply_resource_paths(self):
        """Apply resource paths for the images."""

        # Images
        self.ui.label_pyqt_logo.setPixmap(QPixmap(str(IMAGE_PYQT_LOGO)))
        self.ui.label_logo.setPixmap(QPixmap(str(IMAGE_ABOUT)))