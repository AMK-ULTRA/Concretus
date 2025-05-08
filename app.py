import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.windows.main_window import MainWindow
from settings import ICON_LOGO
from logger import Logger

# Initialize the logger
logger = Logger(__name__)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_LOGO)))
    logger.info("The application has just started")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())