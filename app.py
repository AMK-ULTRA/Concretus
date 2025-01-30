import sys
from PyQt6.QtWidgets import QApplication
from Concretus.gui.windows.main_window import MainWindow
from Concretus.logger import Logger

# Initialize the logger
logger = Logger(name='App')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    logger.info("The application has just started")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())