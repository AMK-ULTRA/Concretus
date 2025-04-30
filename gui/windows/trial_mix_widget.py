from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QMessageBox

from gui.ui.ui_trial_mix_widget import Ui_TrialMixWidget
from core.regular_concrete.models.data_model import RegularConcreteDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from core.regular_concrete.models.aci_data_model import ACIDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from core.regular_concrete.design_methods.mce import MCE
from core.regular_concrete.design_methods.aci import ACI
from core.regular_concrete.design_methods.doe import DOE
from logger import Logger


class TrialMix(QWidget):
    # Define a custom signal
    regular_concrete_requested = pyqtSignal()

    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_TrialMixWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model
        # Connect to the data model of each method
        self.mce_data_model = MCEDataModel()
        self.aci_data_model = ACIDataModel()
        self.doe_data_model = DOEDataModel()

        # Create an empty reference to the calculation engines
        self.mce = None
        self.aci = None
        self.doe = None

        # Set up the main connections
        self.table_connections()

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Trial mix widget initialized')

    def on_enter(self):
        """Prepare widget when it becomes visible."""

        self.data_model.current_step = 4

        method = self.data_model.method # Get the used method
        unit = self.data_model.units # and the current unit system

        if self.data_model.method == "MCE":
            self.mce_calculation_engine()
        elif self.data_model.method == "ACI":
            self.aci_calculation_engine()
        elif self.data_model.method == "DoE":
            self.doe_calculation_engine()

        self.create_table_columns(unit)
        self.create_table_rows(method)
        self.adjust_table_height()
        self.load_results(method)

    def on_exit(self):
        """Clean up widget when navigating away."""

        self.mce_data_model.reset()
        self.aci_data_model.reset()
        self.doe_data_model.reset()

    def table_connections(self):
        """Set up signal/slot connections for the tables."""

        # Calculate the proportion for the trial mix
        self.ui.pushButton_trial_mix.clicked.connect(self.sample_mixture)

    def create_table_columns(self, unit):
        """
        Create table columns based on selected unit system.
        Dynamically configures vertical headers according to the current unit system (MKS/SI).

        :param str unit: The current unit system (e.g., "MKS", "SI")
        """

        # Define column headers based on the current unit system.
        if unit == "MKS":
            column_headers = [
                "Volumen absoluto (L)",
                "Peso (kgf/m³)",
                "Volumen (L/m³)",
                "Peso de prueba (kgf)",
                "Volumen de prueba (L)"
            ]
        elif unit == "SI":
            column_headers = [
                "Volumen absoluto (L)",
                "Masa (kg/m³)",
                "Volumen (L/m³)",
                "Masa de prueba (kg)",
                "Volumen de prueba (L)"
            ]
        else:
            column_headers = []

        # Set the number of columns and assign horizontal headers
        self.ui.tableWidget.setColumnCount((len(column_headers)))
        self.ui.tableWidget.setHorizontalHeaderLabels(column_headers)

        # Center align and stretch horizontal headers
        self.ui.tableWidget.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def create_table_rows(self, method):
        """
        Create table rows based on selected calculation method and material options.

        Dynamically configures vertical headers according to the active calculation method (MCE/ACI/DoE)
        and material selections (SCM, air entrained).

        :param str method: The active method (e.g., "MCE", "ACI", "DoE")
        """

        # Retrieve needed values from the data model
        scm_is_enabled = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')
        entrained_air_is_enabled = self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked')

        # Define row headers based on the method and enabled flags
        if method == "MCE":
            row_headers = [
                "Agua",
                "Cemento",
                "Agregado fino",
                "Agregado grueso",
                "Aire atrapado",
                "Total"
            ]
        elif method in ("ACI", "DoE"):
            row_headers = [
                "Agua",
                "Cemento",
                scm_type,
                "Agregado fino",
                "Agregado grueso",
                "Aire atrapado",
                "Aire incorporado",
                "Total"
            ]
            # If scm_is_enabled is False, delete the row corresponding to SCM
            if not scm_is_enabled:
                if scm_type in row_headers:
                    row_headers.remove(scm_type)
            # if entrained_air_is_enabled is False or its entrained air content is zero, delete "Aire incorporado"
            if not entrained_air_is_enabled:
                for label in ["Aire incorporado"]:
                    if label in row_headers:
                        row_headers.remove(label)
            # Otherwise, delete "Aire atrapado"
            else:
                for label in ["Aire atrapado"]:
                    if label in row_headers:
                        row_headers.remove(label)

        else:
            row_headers = []

        # Clean table
        self.ui.tableWidget.setRowCount(0)

        # Set the number of rows and assign vertical headers
        self.ui.tableWidget.setRowCount(len(row_headers))
        self.ui.tableWidget.setVerticalHeaderLabels(row_headers)

    def adjust_table_height(self):
        """
        Adjust the vertical size of the table so that it fits exactly the number of rows,
        keeping each row at its predetermined height.
        """

        # Get the default height of each row
        row_height = self.ui.tableWidget.verticalHeader().defaultSectionSize()
        # Get the height of the horizontal header
        header_height = self.ui.tableWidget.horizontalHeader().height()
        # Calculate the total number of rows
        num_rows = self.ui.tableWidget.rowCount()

        # Calculate total height:
        # total height = header height + (number of rows * height of each row) + margin
        extra_margin = 2  # 2px margin to prevent scrollbar appearance
        total_height = header_height + num_rows * row_height + extra_margin

        # Adjust the height of the table
        self.ui.tableWidget.setFixedHeight(total_height)

    def mce_calculation_engine(self):
        """
        Initialize and run the MCE calculation engine.

        This method instantiates the MCE calculation engine with the current data models,
        executes the calculation process, and if any errors occur during the calculations,
        retrieves and formats the errors from the MCE data model, and displays them in a critical message box.
        After the message box is closed, it triggers the get_back_regular_concrete_widget method.
        """

        self.mce = MCE(self.data_model, self.mce_data_model)

        # Execute the calculations; if any step fails, run() returns False
        if not self.mce.run():
            # Retrieve the errors from the MCE data model and format them as "key: value" per line
            errors_dict = self.mce_data_model.calculation_errors
            errors_message = "\n".join(f"{key}: {value}" for key, value in errors_dict.items())

            # Create a QMessageBox instance
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error de Cálculo")
            msg_box.setText(f"Se produjeron errores durante los cálculos:\n{errors_message}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # Connect the finished signal to call get_back_button_clicked regardless of how the box is closed
            msg_box.finished.connect(self.get_back_regular_concrete_widget)
            # Execute the message box (modal)
            msg_box.exec()

    def aci_calculation_engine(self):
        """
        Initialize and run the ACI calculation engine.

        This method instantiates the ACI calculation engine with the current data models,
        executes the calculation process, and if any errors occur during the calculations,
        retrieves and formats the errors from the ACI data model, and displays them in a critical message box.
        After the message box is closed, it triggers the get_back_regular_concrete_widget method.
        """

        self.aci = ACI(self.data_model, self.aci_data_model)

        # Execute the calculations; if any step fails, run() returns False
        if not self.aci.run():
            # Retrieve the errors from the ACI data model and format them as "key: value" per line
            errors_dict = self.aci_data_model.calculation_errors
            errors_message = "\n".join(f"{key}: {value}" for key, value in errors_dict.items())

            # Create a QMessageBox instance
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error de Cálculo")
            msg_box.setText(f"Se produjeron errores durante los cálculos:\n{errors_message}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # Connect the finished signal to call get_back_button_clicked regardless of how the box is closed
            msg_box.finished.connect(self.get_back_regular_concrete_widget)
            # Execute the message box (modal)
            msg_box.exec()

    def doe_calculation_engine(self):
        """
        Initialize and run the DoE calculation engine.

        This method instantiates the DoE calculation engine with the current data models,
        executes the calculation process, and if any errors occur during the calculations,
        retrieves and formats the errors from the DoE data model, and displays them in a critical message box.
        After the message box is closed, it triggers the get_back_regular_concrete_widget method.
        """

        self.doe = DOE(self.data_model, self.doe_data_model)

        # Execute the calculations; if any step fails, run() returns False
        if not self.doe.run():
            # Retrieve the errors from the DoE data model and format them as "key: value" per line
            errors_dict = self.doe_data_model.calculation_errors
            errors_message = "\n".join(f"{key}: {value}" for key, value in errors_dict.items())

            # Create a QMessageBox instance
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error de Cálculo")
            msg_box.setText(f"Se produjeron errores durante los cálculos:\n{errors_message}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # Connect the finished signal to call get_back_button_clicked regardless of how the box is closed
            msg_box.finished.connect(self.get_back_regular_concrete_widget)
            # Execute the message box (modal)
            msg_box.exec()

    def get_back_regular_concrete_widget(self):
        """Emit a signal to go to the RegularConcrete widget."""

        self.regular_concrete_requested.emit()

    def load_results(self, method):
        """
        Load trial mix results into the QTableWidget based on the specified design method.

        This method selects the appropriate data model (MCE, ACI, or DoE) based on the provided method
        and retrieves three sets of data:

        1. Absolute volumes (e.g., water_abs_volume, cement_abs_volume, etc.).
        2. Contents (e.g., water_content, cement_content, etc.).
        3. Volumes (e.g., water_volume, cement_volume, etc.).

        These values are stored in three separate lists (col1, col2, and col3) corresponding to the three
        columns of the table. Since the maximum number of rows is fixed (8), but not all rows are valid for
        every method (i.e., some values may be None), the method filters out any row where at least one value
        (from any column) is None.

        :param str method: The design method for which to load results ("MCE", "ACI", or "DoE").
        """

        # Select the corresponding data model according to the method
        if method == "MCE":
            current_method_data_model: MCEDataModel = self.mce_data_model
        elif method == "ACI":
            current_method_data_model: ACIDataModel = self.aci_data_model
        elif method == "DoE":
            current_method_data_model: DOEDataModel = self.doe_data_model
        else:
            self.logger.error(f"Unknown method: {method}")
            return

        # Column 1 values: Absolute volumes
        col1 = [
            current_method_data_model.get_data('water.water_abs_volume'),
            current_method_data_model.get_data('cementitious_material.cement.cement_abs_volume'),
            current_method_data_model.get_data('cementitious_material.scm.scm_abs_volume'),
            current_method_data_model.get_data('fine_aggregate.fine_abs_volume'),
            current_method_data_model.get_data('coarse_aggregate.coarse_abs_volume'),
            current_method_data_model.get_data('air.entrapped_air_content'),
            current_method_data_model.get_data('air.entrained_air_content'),
            current_method_data_model.get_data('summation.total_abs_volume')
        ]

        # Column 2 values: Contents
        col2 = [
            current_method_data_model.get_data('water.water_content_correction'),
            current_method_data_model.get_data('cementitious_material.cement.cement_content'),
            current_method_data_model.get_data('cementitious_material.scm.scm_content'),
            current_method_data_model.get_data('fine_aggregate.fine_content_wet'),
            current_method_data_model.get_data('coarse_aggregate.coarse_content_wet'),
            "-",  # For entrapped air
            "-",  # For entrained air
            current_method_data_model.get_data('summation.total_content')
        ]

        # Column 3 values: Volumes
        col3 = [
            current_method_data_model.get_data('water.water_volume'),
            current_method_data_model.get_data('cementitious_material.cement.cement_volume'),
            current_method_data_model.get_data('cementitious_material.scm.scm_volume'),
            current_method_data_model.get_data('fine_aggregate.fine_volume'),
            current_method_data_model.get_data('coarse_aggregate.coarse_volume'),
            current_method_data_model.get_data('air.entrapped_air_content'),
            current_method_data_model.get_data('air.entrained_air_content'),
            "-" # For total volume
        ]

        # Filter out rows where any column value is None
        # If ANY of the three columns at a given index is None, that row is not valid
        valid_indices = [i for i in range(len(col1)) if not any([col1[i] is None, col2[i] is None, col3[i] is None])]

        # Populate each cell by creating a QTableWidgetItem and marking it as non-editable
        for new_row, i in enumerate(valid_indices): # Fill the table using the valid indices
            for j, col in enumerate([col1, col2, col3]):
                value = col[i]
                # Since we already filtered, value should not be None
                if value is None:
                    text = ""
                else:
                    if isinstance(value, (float, int)):
                        if j == 0:
                            text = f"{value:.2f}"
                        else:
                            text = f"{value:.0f}"
                    else:
                        text = str(value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Align text to center
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Make the cell non-editable
                self.ui.tableWidget.setItem(new_row, j, item)

    def sample_mixture(self):
        """
        Provide the material content for the mix per cubic meter at a volume specified by the user.
        Also consider a waste factor if required by the user.

        Process all rows of the QTableWidget (except the last row) as follows:
              - Extract values from the second (index 1) and third (index 2) columns.
              - Attempt to convert these values to float. If successful, multiply the value by the first factor
                (retrieved from doubleSpinBox_volume) and, if radioButton_waste is checked, by an additional factor
                (retrieved from spinBox_waste). If conversion fails, the value is left as is.
              - Update the fourth (index 3) and fifth (index 4) columns with the new values.
              - Sum up all the (numeric) values written in the fourth column and, in the last row, set that cell to
                the total sum; in the fifth column, place a dash ("-").
        """

        # Access the table widget
        table = self.ui.tableWidget
        row_count = table.rowCount()

        # Get the primary factor from the volume specified by th user
        factor = self.ui.doubleSpinBox_volume.value()

        # Check if waste adjustment is active, and get the additional factor if so
        if self.ui.radioButton_waste.isChecked():
            waste = self.ui.spinBox_waste.value()
            # Convert percentage to decimal form
            waste = (waste / 100) + 1
        else:
            waste = 1  # No additional multiplication if the radio button is not checked

        total_sum = 0  # This will accumulate the sum of numeric values (after multiplications) in column 4

        # Process all rows except the last one
        for row in range(row_count - 1):
            # Get items from the second (index 1) and third (index 2) columns
            item_col_2 = table.item(row, 1)
            item_col_3 = table.item(row, 2)

            text_2 = item_col_2.text() if item_col_2 is not None else ""
            text_3 = item_col_3.text() if item_col_3 is not None else ""

            # Try converting text to float; if it fails, retain the original text
            try:
                value_2 = float(text_2)
                is_numeric_2 = True
            except ValueError:
                is_numeric_2 = False
                value_2 = text_2

            try:
                value_3 = float(text_3)
                is_numeric_3 = True
            except ValueError:
                is_numeric_3 = False
                value_3 = text_3

            # Multiply the value by the factor (and by the waste if applicable) if it is numeric; otherwise, leave it as is
            if is_numeric_2:
                new_value_2 = value_2 * factor * waste
                new_value_2 = round(new_value_2, 1)
                # Accumulate the numeric value for the total sum
                total_sum += new_value_2
            else:
                new_value_2 = value_2

            if is_numeric_3:
                new_value_3 = value_3 * factor * waste
                new_value_3 = round(new_value_3, 1)
            else:
                new_value_3 = value_3

            # Update the fourth (index 3) and fifth (index 4) columns for this row
            item_2 = QTableWidgetItem(str(new_value_2))
            item_3 = QTableWidgetItem(str(new_value_3))

            # Align text to center
            item_2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_3.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Make the cell non-editable
            item_2.setFlags(item_2.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_3.setFlags(item_3.flags() & ~Qt.ItemFlag.ItemIsEditable)

            table.setItem(row, 3, item_2)
            table.setItem(row, 4, item_3)

        # Now update the last row
        last_row = row_count - 1
        # In the fourth column, place the total sum of the numeric values
        item_total_sum = QTableWidgetItem(str(round(total_sum, 1)))
        table.setItem(last_row, 3, item_total_sum)
        # In the fifth column, place a dash ("-")
        item_last_row = QTableWidgetItem("-")
        table.setItem(last_row, 4, item_last_row)

        # Align text to center
        item_total_sum.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_last_row.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Make the cell non-editable
        item_total_sum.setFlags(item_total_sum.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_last_row.setFlags(item_last_row.flags() & ~Qt.ItemFlag.ItemIsEditable)