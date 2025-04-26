import sys
from PyQt6.QtWidgets import QApplication
from gui.windows.main_window import MainWindow
from logger import Logger

# Initialize the logger
logger = Logger(__name__)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    logger.info("The application has just started")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())