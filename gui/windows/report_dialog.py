from PyQt6.QtWidgets import QDialog

from gui.ui.ui_report_dialog import Ui_ReportDialog
from logger import Logger


class ReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_ReportDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Initialization complete
        self.logger.info('Report dialog initialized')

    def get_options(self):
        """
        Get the report type and decimals options from the UI

        :return: The type of report and the number of decimal places to use.
        :rtype: tuple[str, int]
        """

        report_type = "summary" if self.ui.radioButton_basic_report.isChecked() else "full"
        decimal_places = self.ui.spinBox_decimals.value()

        return report_type, decimal_places