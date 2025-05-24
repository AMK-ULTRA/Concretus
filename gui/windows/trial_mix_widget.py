from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QMessageBox

from gui.ui.ui_trial_mix_widget import Ui_TrialMixWidget
from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from core.regular_concrete.models.aci_data_model import ACIDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from core.regular_concrete.design_methods.mce import MCE
from core.regular_concrete.design_methods.aci import ACI
from core.regular_concrete.design_methods.doe import DOE
from logger import Logger


class TrialMix(QWidget):
    # Define a custom signal
    request_regular_concrete_from_trial = pyqtSignal()
    adjust_mix_dialog_enabled = pyqtSignal(float)
    adjust_admixtures_action_enabled = pyqtSignal()

    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_TrialMixWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Initialize the logger
        self.logger = Logger(__name__)

        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model
        # Connect to the data model of each method
        self.mce_data_model: MCEDataModel = mce_data_model
        self.aci_data_model: ACIDataModel = aci_data_model
        self.doe_data_model: DOEDataModel = doe_data_model

        # Create an empty reference to the calculation engines
        self.mce = None
        self.aci = None
        self.doe = None

        # Set up local signal/slot connections
        self.setup_connections()

        # Initialization complete
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

        self.save_trial_mix_results()
        self.create_table_columns(unit)
        self.create_table_rows(method)
        self.adjust_table_height()
        self.load_results(method)
        self.handle_adjust_admixtures_action_enabled()

    def on_exit(self):
        """Clean up widget when navigating away."""

        self.mce_data_model.reset()
        self.aci_data_model.reset()
        self.doe_data_model.reset()

    def setup_connections(self):
        """Set local signal/slot connections, i.e. the connections within the same QWidget."""

        # Calculate the proportion for the trial mix when requested by the user
        self.ui.pushButton_trial_mix.clicked.connect(self.handle_pushButton_trial_mix_clicked)

    def create_table_columns(self, unit):
        """
        Configure the table's column headers for two QTableWidgets based on the selected unit system
        and any admixtures used.

        :param str unit: The current unit system (e.g., "MKS", "SI")
        """

        # ------------------------------------------------------
        # Process Materials Table (self.ui.tableWidget)
        # ------------------------------------------------------
        if unit == "MKS":
            column_headers_1 = [
                "Volumen absoluto (L)",
                "Peso (kgf/m³)",
                "Volumen (L/m³)",
                "Peso de prueba (kgf)",
                "Volumen de prueba (L)"
            ]
        elif unit == "SI":
            column_headers_1 = [
                "Volumen absoluto (L)",
                "Masa (kg/m³)",
                "Volumen (L/m³)",
                "Masa de prueba (kg)",
                "Volumen de prueba (L)"
            ]
        else:
            column_headers_1 = []

        # ----------------------------
        # Process Admixture Table (self.ui.tableWidget_2)
        # ----------------------------
        wra_is_enabled = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_checked')
        aea_is_enabled = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_checked')

        if wra_is_enabled or aea_is_enabled:
            column_headers_2 = [
                # "Volumen absoluto (L)",
                "Cantidad (kg/m³)",
                "Volumen (L/m³)",
                "Cantidad de prueba (g)",
                "Volumen de prueba (mL)"
            ]
        else:
            column_headers_2 = []

        tables = (self.ui.tableWidget, self.ui.tableWidget_2)
        column_headers = (column_headers_1, column_headers_2)

        for table, column_header in zip(tables, column_headers):
            # Set the number of columns and assign horizontal headers
            table.setColumnCount((len(column_header)))
            table.setHorizontalHeaderLabels(column_header)

            # Center align and stretch horizontal headers
            table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def create_table_rows(self, method):
        """
        Configure the row headers for two QTableWidgets based on the selected design method,
        material options, and chemical admixture flags.

        For self.ui.tableWidget:
        - The vertical headers are set based on the active calculation method (e.g., "MCE", "ACI", "DoE")
          and additional material options such as SCM and entrained air content.

        For self.ui.tableWidget_2:
        - The vertical headers are set based on chemical admixture selections:
            * If WRA is enabled (water-reducing admixture), a row labeled "Reductor de agua" is added.
            * If AEA is enabled (air-entraining admixture), a row labeled "Incorporador de aire" is added.

        :param str method: The active method (e.g., "MCE", "ACI", "DoE")
        """

        # Retrieve needed values from the data model
        scm_is_enabled = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')
        scm_type = self.data_model.get_design_value('cementitious_materials.SCM.SCM_type')
        entrained_air_is_enabled = self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked')
        wra_is_enabled = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_checked')
        aea_is_enabled = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_checked')

        # ------------------------
        # Process Materials Table (self.ui.tableWidget)
        # ------------------------

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
            # If SCM is not enabled, remove the SCM type row
            if not scm_is_enabled:
                if scm_type in row_headers:
                    row_headers.remove(scm_type)
            # If entrained air is not enabled (or its content is zero), remove "Aire incorporado";
            if not entrained_air_is_enabled:
                for label in ["Aire incorporado"]:
                    if label in row_headers:
                        row_headers.remove(label)
            # otherwise, remove "Aire atrapado".
            else:
                for label in ["Aire atrapado"]:
                    if label in row_headers:
                        row_headers.remove(label)

        else:
            row_headers = []
        # Clear and update tableWidget for design method rows
        self.ui.tableWidget.setRowCount(0)
        self.ui.tableWidget.setRowCount(len(row_headers))
        self.ui.tableWidget.setVerticalHeaderLabels(row_headers)

        # ------------------------
        # Process Materials Table (self.ui.tableWidget)
        # ------------------------

        # Create row headers based on the admixture flags
        admixture_rows = []
        if wra_is_enabled:
            admixture_rows.append("Reductor de agua")
        if aea_is_enabled:
            admixture_rows.append("Incorporador de aire")

        # Clear and update tableWidget_2 for admixture rows.
        self.ui.tableWidget_2.setRowCount(0)
        self.ui.tableWidget_2.setRowCount(len(admixture_rows))
        self.ui.tableWidget_2.setVerticalHeaderLabels(admixture_rows)

    def adjust_table_height(self):
        """
        Adjust the vertical size of two tables (the materials table and the admixture table) so that
        each table exactly fits its number of rows with each row retaining its predetermined height.
        """

        # Adjust both tables using the helper method
        self._adjust_single_table_height(self.ui.tableWidget)
        self._adjust_single_table_height(self.ui.tableWidget_2)

    @staticmethod
    def _adjust_single_table_height(table_widget):
        """
        Adjusts the vertical size of a single QTableWidget to fit its content exactly.

        :param table_widget: A QTableWidget instance to adjust.
        """
        # Get the default height of each row.
        row_height = table_widget.verticalHeader().defaultSectionSize()
        # Get the height of the horizontal header.
        header_height = table_widget.horizontalHeader().height()
        # Obtain the total number of rows in the table.
        num_rows = table_widget.rowCount()

        # Calculate the total table height:
        #   total height = header height + (number of rows * row height) + extra margin.
        extra_margin = 2  # A small margin (in pixels) to prevent the appearance of a scrollbar.
        total_height = header_height + (num_rows * row_height) + extra_margin

        # Set the fixed height of the table.
        table_widget.setFixedHeight(total_height)

    def run_engine(self, engine_class, data_model_attr, instance_attr):
        """
        Instantiate and run a calculation engine, then display any errors.

        :param engine_class: The engine class to instantiate (MCE, ACI or DOE).
        :param str data_model_attr: Name of the data-model attribute (e.g. "mce_data_model").
        :param str instance_attr: Name of the instance attribute to assign the engine to (e.g. "mce").
        """

        # Instantiate and store
        engine = engine_class(self.data_model, getattr(self, data_model_attr))
        setattr(self, instance_attr, engine)

        # Run and check for failure
        if not engine.run():
            # Gather errors
            data_model = getattr(self, data_model_attr)
            errors = data_model.calculation_errors
            message = "\n".join(f"{k}: {v}" for k, v in errors.items())

            # Show modal critical box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error de cálculo")
            msg_box.setText(f"Se produjeron errores durante los cálculos:\n{message}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.finished.connect(self.handle_TrialMix_regular_concrete_requested_MainWindow)
            msg_box.exec()

    def mce_calculation_engine(self):
        """Run the MCE calculation engine."""

        self.run_engine(MCE, "mce_data_model", "mce")

    def aci_calculation_engine(self):
        """Run the ACI calculation engine."""

        self.run_engine(ACI, "aci_data_model", "aci")

    def doe_calculation_engine(self):
        """Run the DoE calculation engine."""

        self.run_engine(DOE, "doe_data_model", "doe")

    def save_trial_mix_results(self):
        """
        Save the trial mix’s absolute volumes, contents, and volumes from the current data model into
        the main data model (RegularConcreteDataModel).
        """

        # Validate current design method
        method = self.data_model.method
        if method not in ["MCE", "ACI", "DoE"]:
            raise ValueError(f"Invalid method: {method}. Must be one of: MCE, ACI, DoE")
        self.logger.info(f"Saving the trial mix’s absolute volumes, contents, and volumes from the {method} data model "
                         f"into the main data model (RegularConcreteDataModel).")

        # Select the appropriate data model
        data_models = {
            "MCE": self.mce_data_model,
            "ACI": self.aci_data_model,
            "DoE": self.doe_data_model,
        }
        source_dm = data_models[method]

        # Define a mapping of (destination_key, source_key)
        mappings = [
            # Water to cementitious material ratio
            ("trial_mix.adjustments.water_cementitious_materials_ratio.w_cm", "water_cementitious_materials_ratio.w_cm"),

            # Absolute volumes
            ("trial_mix.adjustments.water.water_abs_volume", "water.water_abs_volume"),
            ("trial_mix.adjustments.cementitious_material.cement.cement_abs_volume",
             "cementitious_material.cement.cement_abs_volume"),
            ("trial_mix.adjustments.cementitious_material.scm.scm_abs_volume",
             "cementitious_material.scm.scm_abs_volume"),
            ("trial_mix.adjustments.fine_aggregate.fine_abs_volume", "fine_aggregate.fine_abs_volume"),
            ("trial_mix.adjustments.coarse_aggregate.coarse_abs_volume", "coarse_aggregate.coarse_abs_volume"),
            ("trial_mix.adjustments.air.entrapped_air_content", "air.entrapped_air_content"),
            ("trial_mix.adjustments.air.entrained_air_content", "air.entrained_air_content"),
            ("trial_mix.adjustments.summation.total_abs_volume", "summation.total_abs_volume"),

            # Contents
            ("trial_mix.adjustments.water.water_content_correction", "water.water_content_correction"),
            ("trial_mix.adjustments.cementitious_material.cement.cement_content",
             "cementitious_material.cement.cement_content"),
            ("trial_mix.adjustments.cementitious_material.scm.scm_content", "cementitious_material.scm.scm_content"),
            ("trial_mix.adjustments.fine_aggregate.fine_content_wet", "fine_aggregate.fine_content_wet"),
            ("trial_mix.adjustments.fine_aggregate.fine_content_ssd", "fine_aggregate.fine_content_ssd"),
            ("trial_mix.adjustments.coarse_aggregate.coarse_content_wet", "coarse_aggregate.coarse_content_wet"),
            ("trial_mix.adjustments.coarse_aggregate.coarse_content_ssd", "coarse_aggregate.coarse_content_ssd"),
            ("trial_mix.adjustments.summation.total_content", "summation.total_content"),

            # Volumes
            ("trial_mix.adjustments.water.water_volume", "water.water_volume"),
            ("trial_mix.adjustments.cementitious_material.cement.cement_volume",
             "cementitious_material.cement.cement_volume"),
            ("trial_mix.adjustments.cementitious_material.scm.scm_volume", "cementitious_material.scm.scm_volume"),
            ("trial_mix.adjustments.fine_aggregate.fine_volume", "fine_aggregate.fine_volume"),
            ("trial_mix.adjustments.coarse_aggregate.coarse_volume", "coarse_aggregate.coarse_volume"),
        ]

        # Loop through mappings, fetch and save each value
        for dest_key, src_key in mappings:
            try:
                value = source_dm.get_data(src_key)
            except (AttributeError, KeyError) as e:
                raise ValueError(f"Could not retrieve '{src_key}' from {method} model: {e}")
            self.data_model.update_design_data(dest_key, value)

    def load_results(self, method):
        """
        Load trial mix results into two QTableWidgets based on the specified design method.

        For the materials table (self.ui.tableWidget):
        - Retrieves three data sets:
            * Column 1: Absolute volumes (e.g., water_abs_volume, cement_abs_volume, etc.).
            * Column 2: Contents (e.g., water_content, cement_content, etc.).
            * Column 3: Volumes (e.g., water_volume, cement_volume, etc.).
        - Filters out any row where any of the three values is None.
        - Populates the table with the valid rows.

        For the admixture table (self.ui.tableWidget_2):
        - Retrieves two data sets:
            * Column 1: Chemical admixture contents (WRA_content and AEA_content).
            * Column 2: Chemical admixture volumes (WRA_volume and AEA_volume).
        - Filters out any row where any value is None.
        - Populates the table with the valid rows.

        :param str method: The design method for which to load results ("MCE", "ACI", "DoE" or "trial mix adjustments").
        """

        # Select the corresponding data model according to the method
        if method == "MCE":
            current_data_model = self.mce_data_model
        elif method == "ACI":
            current_data_model = self.aci_data_model
        elif method == "DoE":
            current_data_model = self.doe_data_model
        elif method == "trial mix adjustments":
            current_data_model = self.data_model
        else:
            self.logger.error(f"Unknown method: {method}")
            return

        # Determine which getter method and prefix to use based on the method
        if method == "trial mix adjustments":
            get_method = current_data_model.get_design_value
            prefix = "trial_mix.adjustments."
        else:
            get_method = current_data_model.get_data
            prefix = ""

        # ------------------------
        # Process Materials Table (self.ui.tableWidget)
        # ------------------------
        # Column 1 values: Absolute volumes
        col1 = [
            get_method(f'{prefix}water.water_abs_volume'),
            get_method(f'{prefix}cementitious_material.cement.cement_abs_volume'),
            get_method(f'{prefix}cementitious_material.scm.scm_abs_volume'),
            get_method(f'{prefix}fine_aggregate.fine_abs_volume'),
            get_method(f'{prefix}coarse_aggregate.coarse_abs_volume'),
            get_method(f'{prefix}air.entrapped_air_content'),
            get_method(f'{prefix}air.entrained_air_content'),
            get_method(f'{prefix}summation.total_abs_volume')
        ]

        # Column 2 values: Contents
        col2 = [
            get_method(f'{prefix}water.water_content_correction'),
            get_method(f'{prefix}cementitious_material.cement.cement_content'),
            get_method(f'{prefix}cementitious_material.scm.scm_content'),
            get_method(f'{prefix}fine_aggregate.fine_content_wet'),
            get_method(f'{prefix}coarse_aggregate.coarse_content_wet'),
            "-",  # For entrapped air
            "-",  # For entrained air
            get_method(f'{prefix}summation.total_content')
        ]

        # Column 3 values: Volumes
        col3 = [
            get_method(f'{prefix}water.water_volume'),
            get_method(f'{prefix}cementitious_material.cement.cement_volume'),
            get_method(f'{prefix}cementitious_material.scm.scm_volume'),
            get_method(f'{prefix}fine_aggregate.fine_volume'),
            get_method(f'{prefix}coarse_aggregate.coarse_volume'),
            get_method(f'{prefix}air.entrapped_air_content'),
            get_method(f'{prefix}air.entrained_air_content'),
            "-"  # For total volume
        ]

        # Filter out rows where any column value is None
        # If ANY of the three columns at a given index is None, that row is not valid
        valid_indices = [
            i for i in range(len(col1))
            if not any(value is None for value in (col1[i], col2[i], col3[i]))
        ]

        # Populate each cell in the materials table
        for new_row, i in enumerate(valid_indices):
            for j, col in enumerate([col1, col2, col3]):
                value = col[i]
                # Value should not be None after filtering
                if isinstance(value, (float, int)):
                    if j == 0:
                        text = f"{value:.2f}"
                    else:
                        text = f"{value:.1f}"
                else:
                    text = str(value)
                item = QTableWidgetItem(text)  # Create a QTableWidgetItem
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Align text to center
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make the cell non-editable
                self.ui.tableWidget.setItem(new_row, j, item)

        # ------------------------------------------------------
        # Process Admixture Table (self.ui.tableWidget_2)
        # ------------------------------------------------------
        # Column 1: Chemical admixture contents
        admixture_col1 = [
            get_method(f'{prefix}chemical_admixtures.WRA.WRA_content'),
            get_method(f'{prefix}chemical_admixtures.AEA.AEA_content')
        ]

        # Column 2: Chemical admixture volumes
        admixture_col2 = [
            get_method(f'{prefix}chemical_admixtures.WRA.WRA_volume'),
            get_method(f'{prefix}chemical_admixtures.AEA.AEA_volume')
        ]

        # Filter out rows where any column value is None
        valid_indices_adm = [
            i for i in range(len(admixture_col1))
            if not any(value is None for value in (admixture_col1[i], admixture_col2[i]))
        ]

        # Populate each cell in the admixture table
        for new_row, i in enumerate(valid_indices_adm):
            for j, col in enumerate([admixture_col1, admixture_col2]):
                value = col[i]
                if isinstance(value, (float, int)):
                    text = f"{value:.3f}"
                else:
                    text = str(value)
                item = QTableWidgetItem(text)  # Create a QTableWidgetItem
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Align text to center
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make the cell non-editable
                self.ui.tableWidget_2.setItem(new_row, j, item)

    def clear_last_two_columns(self, table_widget):
        """
        Clear data from the last two columns of a QTableWidget.

        This method preserves data in all columns except the last two.
        Useful for cleaning certain data before updates or when refreshing only part of a table's content.
        For our case, clean up the proportions from the previous trial mix.

        Also, clear the value of the trial mix volume and the percentage of waste.

        :param str table_widget: The key associated with the QTableWidget object from which data will be deleted.
        """

        # Get the table to clean up
        tables = {
            'materials_table': self.ui.tableWidget,
            'admixture_table': self.ui.tableWidget_2,
        }
        table = tables[table_widget]

        # Get table dimensions
        row_count = table.rowCount()
        column_count = table.columnCount()

        # Check if table has at least two columns
        if column_count < 2:
            self.logger.warning("Table has fewer than 2 columns, nothing to clear")
            return

        # Calculate which columns to clear (last two)
        first_column_to_clear = column_count - 2

        # Clear data from the last two columns
        for row in range(row_count):
            for col in range(first_column_to_clear, column_count):
                # Remove item from this cell
                table.setItem(row, col, None)

        # Reset these UI fields
        self.ui.doubleSpinBox_volume.setValue(0.0)
        self.ui.spinBox_waste.setValue(0)

        self.logger.debug(
            f"Cleared last two columns of table -> {table}, columns {first_column_to_clear} and {first_column_to_clear + 1}")

    def handle_TrialMix_regular_concrete_requested_MainWindow(self):
        """Emit a signal to go to the RegularConcrete widget."""

        # When the button is clicked, the signal is emitted
        self.request_regular_concrete_from_trial.emit()

    def handle_pushButton_trial_mix_clicked(self):
        """
        Calculate the material content for the mix per cubic meter at a volume specified by the user.
        Also consider a waste factor if required by the user. This method processes two tables with different logic:

        For self.ui.tableWidget:
        - Process all rows except the last row.
        - Extract values from the second (index 1) and third (index 2) columns.
        - Attempt to convert these values to float. If successful, multiply the numeric value by:
                * A primary factor (from doubleSpinBox_volume).
                * An additional waste factor (if radioButton_waste is checked, using spinBox_waste; otherwise, 1).
        - Update the fourth (index 3) and fifth (index 4) columns with the new values.
        - Accumulate the numeric values from the fourth column and, in the last row, set that cell to the total sum;
            in the fifth column, place a dash ("-").

        For self.ui.tableWidget_2:
        - Process all rows (without a dedicated total row).
        - Extract values from the first (index 0) and second (index 1) columns.
        - Convert the value from the first column (assumed to be in kg) to grams by multiplying by 1000.
        - Convert the value from the second column (assumed to be in Liters) to milliliters by multiplying by 1000.
        - Update the third (index 2) and fourth (index 3) columns with these converted values.

        At the end, it sends a signal to enable the test mix adjustments if the test mix volume is non-zero.
        """

        # ------------------------
        # Process Materials Table (self.ui.tableWidget)
        # ------------------------

        # Access the table widget
        table = self.ui.tableWidget
        row_count = table.rowCount()

        # Get the primary factor from the volume specified by the user
        factor = self.ui.doubleSpinBox_volume.value()

        # Check if waste adjustment is active, and get the additional factor if so
        if self.ui.radioButton_waste.isChecked():
            waste = self.ui.spinBox_waste.value()
            waste = (waste / 100) + 1 # Convert percentage to decimal form
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

            # Multiply the value by the factor (and by the waste) if is numeric; otherwise, leave it as is
            if is_numeric_2:
                new_value_2 = round(value_2 * factor * waste, 1)
                # Accumulate the numeric value for the total sum
                total_sum += new_value_2
            else:
                new_value_2 = value_2

            if is_numeric_3:
                new_value_3 = round(value_3 * factor * waste, 1)
            else:
                new_value_3 = value_3

            # Create QTableWidgetItems for the updated values
            item_2 = QTableWidgetItem(str(new_value_2))
            item_3 = QTableWidgetItem(str(new_value_3))

            # Align text to center and make the cell non-editable
            item_2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_3.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_2.setFlags(item_2.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_3.setFlags(item_3.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Update columns: 4th (index 3) and 5th (index 4)
            table.setItem(row, 3, item_2)
            table.setItem(row, 4, item_3)

        # Process the last row for the materials table
        last_row = row_count - 1
        # In the fourth column, place the total sum of the numeric values
        item_total_sum = QTableWidgetItem(str(round(total_sum, 1)))
        table.setItem(last_row, 3, item_total_sum)
        # In the fifth column, place a dash ("-")
        item_last_row = QTableWidgetItem("-")
        table.setItem(last_row, 4, item_last_row)

        # Align text to center and make the cell non-editable
        item_total_sum.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_last_row.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_total_sum.setFlags(item_total_sum.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_last_row.setFlags(item_last_row.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # ----------------------------
        # Process Admixture Table (self.ui.tableWidget_2)
        # ----------------------------
        table2 = self.ui.tableWidget_2
        row_count2 = table2.rowCount()

        # For the admixture table, process all rows (no summing of a total row)
        for row in range(row_count2):
            # Extract items from the first (index 0) and second (index 1) columns
            item_col_1 = table2.item(row, 0)
            item_col_2 = table2.item(row, 1)

            text_1 = item_col_1.text() if item_col_1 is not None else ""
            text_2 = item_col_2.text() if item_col_2 is not None else ""

            # Attempt to convert the extracted texts to float
            try:
                value_1 = float(text_1)
                is_numeric_1 = True
            except ValueError:
                is_numeric_1 = False
                value_1 = text_1

            try:
                value_2 = float(text_2)
                is_numeric_2 = True
            except ValueError:
                is_numeric_2 = False
                value_2 = text_2

            # Multiply the value by the factor if is numeric; otherwise, leave it as is
            if is_numeric_1: # For the first value (assumed kg), convert to grams (multiply by 1000) if numeric
                new_value_1 = round(value_1 * factor * 1000, 1)
            else:
                new_value_1 = value_1

            if is_numeric_2: # For the second value (assumed Liters), convert to milliliters (multiply by 1000) if numeric
                new_value_2 = round(value_2 * factor * 1000, 1)
            else:
                new_value_2 = value_2

            # Create QTableWidgetItems for the updated values
            item_new_1 = QTableWidgetItem(str(new_value_1))
            item_new_2 = QTableWidgetItem(str(new_value_2))

            # Align text to center and make the cell non-editable
            item_new_1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_new_2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_new_1.setFlags(item_new_1.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_new_2.setFlags(item_new_2.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Update columns for table2: third (index 2) and fourth (index 3)
            table2.setItem(row, 2, item_new_1)
            table2.setItem(row, 3, item_new_2)

        # Enable test mix adjustments if the test mix volume is non-zero
        self.adjust_mix_dialog_enabled.emit(factor)

        # Save the volume of the test mixture and the percentage of waste (as factors) in the data model
        self.data_model.update_design_data('trial_mix_volume', factor)
        self.data_model.update_design_data('trial_mix_waste', waste)

        self.logger.info("The proportioning process has been done successfully")

    def handle_adjust_admixtures_action_enabled(self):
        """Emit a signal to enable the admixture adjustment action."""

        wra_is_enabled = self.data_model.get_design_value('chemical_admixtures.WRA.WRA_checked')
        aea_is_enabled = self.data_model.get_design_value('chemical_admixtures.AEA.AEA_checked')

        if wra_is_enabled or aea_is_enabled:
            self.adjust_admixtures_action_enabled.emit()