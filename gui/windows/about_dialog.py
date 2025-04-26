from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog

from gui.ui.ui_about_dialog import Ui_AboutDialog
from logger import Logger
from settings import IMAGE_ABOUT


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_AboutDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Apply resource paths
        self.apply_resource_paths()

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('About dialog initialized')

    def apply_resource_paths(self):
        """Apply resource paths (images and icons) from settings.py."""

        # Logo image
        self.ui.label_logo.setPixmap(QPixmap(str(IMAGE_ABOUT)))