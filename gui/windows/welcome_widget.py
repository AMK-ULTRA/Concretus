from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap

from Concretus.gui.ui.ui_welcome_widget import Ui_WelcomeWidget
from Concretus.logger import Logger
from Concretus.settings import IMAGE_PYQT_LOGO, IMAGE_ABOUT


class Welcome(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_WelcomeWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Apply resource paths
        self.apply_resource_paths()

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Welcome widget initialized')

    def apply_resource_paths(self):
        """Apply resource paths for the images."""

        # Images
        self.ui.label_pyqt_logo.setPixmap(QPixmap(str(IMAGE_PYQT_LOGO)))
        self.ui.label_logo.setPixmap(QPixmap(str(IMAGE_ABOUT)))