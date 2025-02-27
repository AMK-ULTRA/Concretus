from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem

from Concretus.gui.ui.ui_trial_mix_widget import Ui_TrialMixWidget
from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.core.regular_concrete.models.mce_data_model import MCEDataModel
from Concretus.core.regular_concrete.models.aci_data_model import ACIDataModel
from Concretus.core.regular_concrete.models.doe_data_model import DoEDataModel
from Concretus.core.regular_concrete.design_methods.mce import MCE
from Concretus.logger import Logger


class TrialMix(QWidget):
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
        self.aci_data_model = None
        self.doe_data_model = None

        # Create an empty reference to the calculation engines
        self.mce = None
        self.aci = None
        self.doe = None

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Trial mix widget initialized')

    def on_enter(self):
        """Prepare widget when it becomes visible."""

        # Get the used method
        method = self.data_model.method

        self.create_table_columns(method)
        self.create_table_rows(method)
        self.adjust_table_height()
        if self.data_model.method == "MCE":
            self.mce_calculation_engine()
        elif self.data_model.method == "ACI":
            self.aci_calculation_engine()
        elif self.data_model.method == "DoE":
            self.doe_calculation_engine()
        self.load_results(method)

    def on_exit(self):
        """Clean up widget when navigating away."""

        self.mce_data_model.reset()

    def create_table_columns(self, method):
        """
        Create table columns based on selected calculation method.
        Dynamically configures vertical headers according to the active calculation method (MCE/ACI/DoE).

        :param method: The active method (e.g., "MCE", "ACI", "DoE")
        """

        # Define column headers based on the method.
        if method == "MCE":
            column_headers = [
                "Volumen absoluto (L)",
                "Peso (kgf/m³)",
                "Volumen (L/m³)",
                "Peso para la prueba (kgf/m³)",
                "Volumen para la prueba (L/m³)"
            ]
        elif method in ("ACI", "DoE"):
            column_headers = [
                "Volumen absoluto (L)",
                "Masa (kg/m³)",
                "Volumen (L/m³)",
                "Masa para la prueba (kg/m³)",
                "Volumen para la prueba (L/m³)"
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
        entrained_air_is_enabled = self.data_model.get_design_value('field_requirements.air_content.air_content_checked')

        # Define row headers based on the method and enabled flags.
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
                "Incorporador de aire",
                "Total"
            ]
            # If scm_is_enabled is False, delete the row corresponding to SCM
            if not scm_is_enabled:
                if scm_type in row_headers:
                    row_headers.remove(scm_type)
            # if entrained_air_is_enabled is False, delete "Aire incorporado" and "Incorporador de aire"
            if not entrained_air_is_enabled:
                for label in ["Aire incorporado", "Incorporador de aire"]:
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
        """Run the MCE calculation engine."""

        self.mce = MCE(self.data_model, self.mce_data_model)
        self.mce.run()

    def aci_calculation_engine(self):
        pass

    def doe_calculation_engine(self):
        pass

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
            current_method_data_model: DoEDataModel = self.doe_data_model
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
            current_method_data_model.get_data('air.entrapped_air'),
            current_method_data_model.get_data('air.entrained_air'),
            "-", # For air-entraining admixture
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
            current_method_data_model.get_data('cementitious_material.scm.air_entraining_admixture_content'),
            current_method_data_model.get_data('summation.total_content')
        ]

        # Column 3 values: Volumes
        col3 = [
            current_method_data_model.get_data('water.water_volume'),
            current_method_data_model.get_data('cementitious_material.cement.cement_volume'),
            current_method_data_model.get_data('cementitious_material.scm.scm_volume'),
            current_method_data_model.get_data('fine_aggregate.fine_volume'),
            current_method_data_model.get_data('coarse_aggregate.coarse_volume'),
            current_method_data_model.get_data('air.entrapped_air'),
            current_method_data_model.get_data('air.entrained_air'),
            "-", # For air-entraining admixture
            "-" # For total volume
        ]

        # Filter out rows where any column value is None
        # If ANY of the three columns at a given index is None, that row is not valid.
        valid_indices = [i for i in range(len(col1)) if all([col1[i], col2[i], col3[i]])]

        # Populate each cell by creating a QTableWidgetItem and marking it as non-editable
        for new_row, i in enumerate(valid_indices): # Fill the table using the valid indices
            for j, col in enumerate([col1, col2, col3]):
                value = col[i]
                # Since we already filtered, value should not be None
                if value is None:
                    text = ""
                else:
                    if isinstance(value, (float, int)):
                        text = f"{value:.2f}"
                    else:
                        text = str(value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Align text to center
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Make the cell non-editable
                self.ui.tableWidget.setItem(new_row, j, item)