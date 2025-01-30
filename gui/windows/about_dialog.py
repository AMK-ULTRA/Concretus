from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog

from Concretus.gui.ui.ui_about_dialog import Ui_AboutDialog
from Concretus.logger import Logger
from Concretus.settings import IMAGE_ABOUT


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_AboutDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(name='AboutDialog', log_file='concretus.log')
        self.logger.info('The about dialog has been created')

        # Apply resource paths
        self.apply_resource_paths()

    def apply_resource_paths(self):
        """Apply resource paths (images and icons) from settings.py."""
        # Logo image
        self.ui.label_logo.setPixmap(QPixmap(str(IMAGE_ABOUT)))