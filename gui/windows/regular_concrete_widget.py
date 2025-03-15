from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QItemDelegate, QLineEdit

from Concretus.gui.ui.ui_regular_concrete_widget import Ui_RegularConcreteWidget
from Concretus.core.regular_concrete.models.data_model import RegularConcreteDataModel
from Concretus.logger import Logger
from Concretus.settings import MIN_SPEC_STRENGTH, MAX_SPEC_STRENGTH, SIEVES, FINE_RETAINED_STATE, COARSE_RETAINED_STATE


class NumericDelegate(QItemDelegate):
    """Override the createEditor method of QItemDelegate (inherited by QAbstractItemDelegate)."""

    def createEditor(self, parent, option, index):
        # Create a QLineEdit and assign it a QDoubleValidator to allow numbers
        editor = QLineEdit(parent)
        validator = QDoubleValidator(editor)
        # Setting the validator range
        validator.setBottom(0)  # only positive numbers
        editor.setValidator(validator)
        return editor


class DeleteKeyEventFilter(QObject):
    """Override the eventFilter method of QObject (inherited by QTableWidget)."""

    def eventFilter(self, obj, event):
        # We are only interested in capturing keypress events
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete:
                # We check if the object is a QTableWidget (just in case)
                # and we delete the contents of the current cell
                current_item = obj.currentItem()
                if current_item is not None:
                    current_item.setText("")
                return True  # Indicates that the event was handled
        # For all other cases, the event is passed to the default processor
        return super().eventFilter(obj, event)


class RegularConcrete(QWidget):
    """Main logic of the Regular Concrete widget."""

    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_RegularConcreteWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Global signal/slot connections
        self.global_connections()

        # Create an instance of the event filter
        self.delete_key_filter = DeleteKeyEventFilter()

        # Install the event filter on both tables
        self.ui.tableWidget_fine.installEventFilter(self.delete_key_filter)
        self.ui.tableWidget_coarse.installEventFilter(self.delete_key_filter)

        # Set up the main connections
        self.table_connections()
        # Default "% Retained" state for each table
        self.fine_retained_state = FINE_RETAINED_STATE
        self.coarse_retained_state = COARSE_RETAINED_STATE

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Regular concrete widget initialized')

        # Run a method update
        self.update_units(self.data_model.units)

    def on_enter(self):
        """Prepare widget when it becomes visible."""
        pass

    def on_exit(self):
        """Clean up widget when navigating away."""

        self.save_data()
        self.save_table_data()

        # Save the QRadioButton state
        for aggregate, radio_button in zip(
                ['fine_aggregate', 'coarse_aggregate'],
                [self.ui.radioButton_fine_retained, self.ui.radioButton_coarse_retained]
        ):
            self.save_retained_states(aggregate, radio_button.isChecked())

    def global_connections(self):
        """Set global signal/slot connections, i.e. the connections between different QWidgets."""

        # Load current unit system and method whenever units/method changes
        self.data_model.units_changed.connect(lambda units: self.update_units(units))
        self.data_model.method_changed.connect(lambda method: self.update_method(method))

    def save_data(self):
        """Stores all form data in the data model."""

        # Map all widgets, key paths and methods to get the current value
        # Format: (self.ui.[objectName], 'key path in the design data', 'method (without parenthesis)')
        field_mappings = [
            # General Info
            (self.ui.lineEdit_name, 'general_info.project_name', 'text'),
            (self.ui.lineEdit_location, 'general_info.location', 'text'),
            (self.ui.comboBox_method, 'general_info.method', 'currentText'),
            (self.ui.lineEdit_purchaser, 'general_info.purchaser', 'text'),
            (self.ui.dateEdit_date, 'general_info.date', lambda de: de.date().toString("dd-MM-yyyy")),

            # Field Requirements
            (self.ui.spinBox_slump, 'field_requirements.slump', 'value'),
            (self.ui.label_1, 'field_requirements.exposure_class.group_1', 'text'),
            (self.ui.comboBox_1, 'field_requirements.exposure_class.items_1', 'currentText'),
            (self.ui.label_2, 'field_requirements.exposure_class.group_2', 'text'),
            (self.ui.comboBox_2, 'field_requirements.exposure_class.items_2', 'currentText'),
            (self.ui.label_3, 'field_requirements.exposure_class.group_3', 'text'),
            (self.ui.comboBox_3, 'field_requirements.exposure_class.items_3', 'currentText'),
            (self.ui.label_4, 'field_requirements.exposure_class.group_4', 'text'),
            (self.ui.comboBox_4, 'field_requirements.exposure_class.items_4', 'currentText'),
            (self.ui.groupBox_air, 'field_requirements.entrained_air_content.is_checked', 'isChecked'),
            (self.ui.doubleSpinBox_user_defined, 'field_requirements.entrained_air_content.user_defined', 'value'),
            (self.ui.radioButton_exposure_defined, 'field_requirements.entrained_air_content.exposure_defined', 'isChecked'),
            (self.ui.spinBox_spec_strength, 'field_requirements.strength.spec_strength', 'value'),
            (self.ui.comboBox_spec_strength_time, 'field_requirements.strength.spec_strength_time', 'currentText'),
            (self.ui.groupBox_std_dev_known, 'field_requirements.strength.std_dev_known.std_dev_known_enabled',
             'isChecked'),
            (self.ui.doubleSpinBox_std_dev_value, 'field_requirements.strength.std_dev_known.std_dev_value', 'value'),
            (self.ui.spinBox_test_nro, 'field_requirements.strength.std_dev_known.test_nro', 'value'),
            (self.ui.comboBox_defective_level, 'field_requirements.strength.std_dev_known.defective_level', 'currentText'),
            (self.ui.groupBox_std_dev_unknown, 'field_requirements.strength.std_dev_unknown.std_dev_unknown_enabled',
             'isEnabled'),
            (self.ui.comboBox_qual_control, 'field_requirements.strength.std_dev_unknown.quality_control', 'currentText'),
            (self.ui.spinBox_margin, 'field_requirements.strength.std_dev_unknown.margin', 'value'),

            # Cementitious Materials
            (self.ui.lineEdit_cement_seller, 'cementitious_materials.cement_seller', 'text'),
            (self.ui.comboBox_cement_type, 'cementitious_materials.cement_type', 'currentText'),
            (self.ui.comboBox_cement_class, 'cementitious_materials.cement_class', 'currentText'),
            (self.ui.doubleSpinBox_cement_relative_density, 'cementitious_materials.relative_density', 'value'),
            (self.ui.groupBox_SCM, 'cementitious_materials.SCM.SCM_checked', 'isChecked'),
            (self.ui.comboBox_SCM_type, 'cementitious_materials.SCM.SCM_type', 'currentText'),
            (self.ui.spinBox_SCM_content, 'cementitious_materials.SCM.SCM_content', 'value'),
            (self.ui.doubleSpinBox_SCM_relative_density, 'cementitious_materials.SCM.SCM_relative_density', 'value'),

            # Fine Aggregate
            (self.ui.lineEdit_fine_name, 'fine_aggregate.info.name', 'text'),
            (self.ui.lineEdit_fine_source, 'fine_aggregate.info.source', 'text'),
            (self.ui.comboBox_fine_type, 'fine_aggregate.info.type', 'currentText'),
            (self.ui.doubleSpinBox_fine_relative_density, 'fine_aggregate.physical_prop.relative_density_SSD', 'value'),
            (self.ui.doubleSpinBox_fine_pus, 'fine_aggregate.physical_prop.PUS', 'value'),
            (self.ui.doubleSpinBox_fine_puc, 'fine_aggregate.physical_prop.PUC', 'value'),
            (self.ui.doubleSpinBox_fine_mc, 'fine_aggregate.moisture.moisture_content', 'value'),
            (self.ui.doubleSpinBox_fine_abs, 'fine_aggregate.moisture.absorption_content', 'value'),

            # Coarse Aggregate
            (self.ui.lineEdit_coarse_name, 'coarse_aggregate.info.name', 'text'),
            (self.ui.lineEdit_coarse_source, 'coarse_aggregate.info.source', 'text'),
            (self.ui.comboBox_coarse_type, 'coarse_aggregate.info.type', 'currentText'),
            (self.ui.doubleSpinBox_coarse_relative_density, 'coarse_aggregate.physical_prop.relative_density_SSD',
             'value'),
            (self.ui.doubleSpinBox_coarse_pus, 'coarse_aggregate.physical_prop.PUS', 'value'),
            (self.ui.doubleSpinBox_coarse_puc, 'coarse_aggregate.physical_prop.PUC', 'value'),
            (self.ui.doubleSpinBox_coarse_mc, 'coarse_aggregate.moisture.moisture_content', 'value'),
            (self.ui.doubleSpinBox_coarse_abs, 'coarse_aggregate.moisture.absorption_content', 'value'),

            # Water
            (self.ui.comboBox_water_type, 'water.water_type', 'currentText'),
            (self.ui.lineEdit_water_source, 'water.water_source', 'text'),
            (self.ui.doubleSpinBox_water_density, 'water.water_density', 'value'),

            # Chemical Admixtures
            (self.ui.comboBox_admixture_type, 'chemical_admixtures.admixture_type', 'currentText'),
            (self.ui.lineEdit_admixture_name, 'chemical_admixtures.admixture_name', 'text'),
            (self.ui.doubleSpinBox_admixture_relative_density, 'chemical_admixtures.admixture_relative_density',
             'value'),
            (self.ui.doubleSpinBox_admixture_dosage, 'chemical_admixtures.admixture_dosage', 'value'),
            (self.ui.spinBox_admixture_effectiveness, 'chemical_admixtures.effectiveness', 'value')
        ]

        # Iterates through a list of tuples, where each tuple represents a mapping between
        # a widget, a data path, and a method to get the value from the widget.
        for widget, data_path, value_getter in field_mappings:
            try:
                # Checks if the value_getter is a callable object (e.g., a function)
                if callable(value_getter):
                    # If it is, call the function with the widget as an argument to get the value
                    value = value_getter(widget)
                # If value_getter is not a callable object, assume it's the name of a method of the widget
                else:
                    # Use getattr() to dynamically retrieve and call the method
                    value = getattr(widget, value_getter)()

                # Update the data model with the retrieved value
                self.data_model.update_design_data(data_path, value)

            except AttributeError as e:
                self.logger.warning(f"Error updating field {data_path}: {str(e)}")
                continue

    def save_table_data(self):
        """Stores all table data in the data model."""

        # Dictionaries for fine aggregate
        passing_fine = {}
        retained_fine = {}

        # Dictionaries for coarse aggregate
        passing_coarse = {}
        retained_coarse = {}

        # Retrieve the retained state for fine and coarse tables
        flag_fine_retained = self.ui.radioButton_fine_retained.isChecked()
        flag_coarse_retained = self.ui.radioButton_coarse_retained.isChecked()

        # List with tuples (table, passing dictionary, retained dictionary)
        # The first tuple corresponds to fine aggregate, the second to coarse aggregate.
        tables_info = [
            (self.ui.tableWidget_fine, passing_fine, retained_fine),
            (self.ui.tableWidget_coarse, passing_coarse, retained_coarse)
        ]

        # Loop over each table (fine and coarse)
        for index, (table, dict_passing, dict_retained) in enumerate(tables_info):
            # Determine the flag for the current table.
            # For fine aggregate (index 0)
            if index == 0:
                flag_retained = flag_fine_retained
            else:
                flag_retained = flag_coarse_retained

            row_count = table.rowCount()
            for row in range(row_count):
                # Obtain the sieve denomination from the first column (key)
                item_key = table.item(row, 0)
                if item_key is None:
                    continue  # Skip the row if no key is present
                key = item_key.text().strip()

                if not flag_retained:
                    # If the retained flag is False, get the "% Passing" value (column 1)
                    item_passing = table.item(row, 1)
                    if item_passing is not None and item_passing.text().strip() != "":
                        value_passing = item_passing.text().strip()
                    else:
                        value_passing = None
                    try:
                        value_passing = float(value_passing) if value_passing is not None else None
                    except ValueError:
                        value_passing = None
                    dict_passing[key] = value_passing
                    # Optionally, we can set the retained dictionary value to None:
                    # dict_retained[key] = None
                else:
                    # If the retained flag is True, get the "% Retained" value (column 2)
                    item_retained = table.item(row, 2)
                    if item_retained is not None and item_retained.text().strip() != "":
                        value_retained = item_retained.text().strip()
                    else:
                        value_retained = None
                    try:
                        value_retained = float(value_retained) if value_retained is not None else None
                    except ValueError:
                        value_retained = None
                    dict_retained[key] = value_retained
                    # Optionally, we can set the passing dictionary value to None:
                    # dict_passing[key] = None

        # Map all key paths and new dictionaries
        update_data = {
            'fine_aggregate.gradation.passing': passing_fine,
            'fine_aggregate.gradation.retained': retained_fine,
            'coarse_aggregate.gradation.passing': passing_coarse,
            'coarse_aggregate.gradation.retained': retained_coarse
        }

        # Update the data model with the dictionaries.
        for key_path, value in update_data.items():
            self.data_model.update_design_data(key_path, value)

    def save_retained_states(self, aggregate_type, retained_checked):
        """
        Saves the checked state of the fine and coarse aggregate retained radio buttons by updating
        the 'retained_checked' and 'passing_checked' flags in the data model.

        :param str aggregate_type: The type of aggregate ('fine_aggregate' or 'coarse_aggregate').
        :param bool retained_checked: True if the "Retained" radio button is checked, False otherwise.
        """

        self.data_model.update_design_data(f"{aggregate_type}.gradation.retained_checked", retained_checked)
        self.data_model.update_design_data(f"{aggregate_type}.gradation.passing_checked", not retained_checked)

    def table_config(self):
        """Set the default settings for the grading tables."""

        # Enable "% Passing" and disable "% Retained" by default
        self.toggle_passing_retained(self.ui.tableWidget_fine, self.fine_retained_state)
        self.toggle_passing_retained(self.ui.tableWidget_coarse, self.coarse_retained_state)

    def table_connections(self):
        """Set up signal/slot connections for the grading tables."""

        # Toggle between "% Passing" and "% Retained" state
        self.ui.radioButton_fine_retained.toggled.connect(
            lambda checked: self.toggle_passing_retained(self.ui.tableWidget_fine, checked)
        )
        self.ui.radioButton_coarse_retained.toggled.connect(
            lambda checked: self.toggle_passing_retained(self.ui.tableWidget_coarse, checked)
        )

    def table_item_delegate(self):
        """Set the item delegate for each grading table."""

        numeric_delegate = NumericDelegate()
        self.ui.tableWidget_fine.setItemDelegateForColumn(1, numeric_delegate)
        self.ui.tableWidget_fine.setItemDelegateForColumn(2, numeric_delegate)
        self.ui.tableWidget_coarse.setItemDelegateForColumn(1, numeric_delegate)
        self.ui.tableWidget_coarse.setItemDelegateForColumn(2, numeric_delegate)

    def toggle_passing_retained(self, table, retained_enabled):
        """
        Enables "% Passing" and disables "% Retained", or vice versa.

        :param table: The table to modify.
        :param bool retained_enabled: True to enable "% Retained", False to enable "% Passing".
        """

        # Record the change in the logger
        table_name = "fine" if table == self.ui.tableWidget_fine else "coarse"
        self.logger.info(f'QRadioButton for {table_name} table is active: {retained_enabled}')

        for row in range(table.rowCount()):
            # Enable or disable "% Passing"
            item_passing = table.item(row, 1)
            if not item_passing:
                item_passing = QTableWidgetItem()
                table.setItem(row, 1, item_passing)
            item_passing.setFlags(
                item_passing.flags() & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable
                if retained_enabled
                else item_passing.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )

            # Enable or disable "% Retained"
            item_retained = table.item(row, 2)
            if not item_retained:
                item_retained = QTableWidgetItem()
                table.setItem(row, 2, item_retained)
            item_retained.setFlags(
                item_retained.flags() & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable
                if not retained_enabled
                else item_retained.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )

    def populate_tables(self, method):
        """
        Deletes all rows and generates a new set of rows according to the selected method.

        :param str method: The method for selecting the set of corresponding rows.
        """

        # Clean tables
        self.ui.tableWidget_fine.setRowCount(0)
        self.ui.tableWidget_coarse.setRowCount(0)

        # Center the table headers for fine and coarse aggregate grading
        self.ui.tableWidget_fine.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.tableWidget_coarse.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Sieve set according to the selected method
        sieves_fine = SIEVES[method]["fine_sieves"]
        sieves_coarse = SIEVES[method]["coarse_sieves"]

        # Fill in the "Sieve, in (mm)" column in each table
        for sieve in sieves_fine:
            row = self.ui.tableWidget_fine.rowCount()
            self.ui.tableWidget_fine.insertRow(row)
            item = QTableWidgetItem(sieve)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # Not editable, not selectable
            self.ui.tableWidget_fine.setItem(row, 0, item)

        for sieve in sieves_coarse:
            row = self.ui.tableWidget_coarse.rowCount()
            self.ui.tableWidget_coarse.insertRow(row)
            item = QTableWidgetItem(sieve)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # Not editable, not selectable
            self.ui.tableWidget_coarse.setItem(row, 0, item)

        # Reset default settings
        self.ui.radioButton_fine_retained.setChecked(FINE_RETAINED_STATE)
        self.ui.radioButton_coarse_retained.setChecked(COARSE_RETAINED_STATE)
        self.table_config()
        self.table_item_delegate()
        self.logger.info(f'The set of sieves for the {method} method has been generated')

    def update_units(self, units):
        """
        Update fields that depend on the selected unit system.

        :param str units: The system of units to update the fields.
        """

        # Initialize the variables
        unit_suffix = None
        default_spec_strength = None

        if units == 'SI':
            unit_suffix = 'MPa'
            default_spec_strength = 21
        elif units == 'MKS':
            unit_suffix = 'kgf/cm²'
            default_spec_strength = 210

        # Update ranges for specified compressive strength
        min_spec_strength = MIN_SPEC_STRENGTH[units][
            # "MCE" acts as a placeholder since the default value of "method" property in the data model is "None"
            "MCE" if not self.data_model.method else self.data_model.method
        ]
        max_spec_strength = MAX_SPEC_STRENGTH[units][
            # Avoid an error when accessing the dictionary
            "MCE" if not self.data_model.method else self.data_model.method
        ]
        self.ui.spinBox_spec_strength.setMinimum(min_spec_strength)
        self.ui.spinBox_spec_strength.setMaximum(max_spec_strength)

        # Update default value for specified compressive strength
        self.ui.spinBox_spec_strength.setValue(default_spec_strength)

        # Update default value for known standard deviation
        self.ui.doubleSpinBox_std_dev_value.setMaximum(10 if units == 'SI' else 100)

        # Update the labels
        self.ui.label_spec_strength.setText(f"Resistencia de cálculo especificada ({unit_suffix})")
        self.ui.label_std_dev_value.setText(f"Valor ({unit_suffix})")
        self.ui.label_margin.setText(f"Margen ({unit_suffix})")

        self.logger.info(f'A complete update of the unit system to {units} has been made')

    def update_method(self, method):
        """
        Update fields that depend on the selected method.

        :param str method: The method to update the fields.
        """

        # Populate the grading table
        self.populate_tables(method)

        # Update ranges for specified compressive strength
        min_spec_strength = MIN_SPEC_STRENGTH[self.data_model.units][
            # "MCE" acts as a placeholder since the default value of "method" property in the data model is "None"
            "MCE" if not method else method
        ]
        max_spec_strength = MAX_SPEC_STRENGTH[self.data_model.units][
            # Avoid an error when accessing the dictionary
            "MCE" if not method else method
        ]
        self.ui.spinBox_spec_strength.setMinimum(min_spec_strength)
        self.ui.spinBox_spec_strength.setMaximum(max_spec_strength)

        # Update default values
        self.ui.spinBox_slump.setMinimum(25 if method == 'ACI' else 10)
        self.ui.spinBox_slump.setMaximum(175 if method == 'ACI' else 210)
        self.ui.spinBox_slump.setValue(25 if method == 'ACI' else 10)

        # A dictionary to map all method configurations
        method_config = {
            "MCE": {
                "exposure_class": {
                    "group_1": "Exposición al agua",
                    "items_1": ("Despreciable", "Agua dulce", "Agua salobre o de mar"),
                    "group_2": "Exposición a sulfatos",
                    "items_2": ("Despreciable", "Moderada", "Severa", "Muy severa"),
                    "group_3": "Humedad relativa",
                    "items_3": ("Despreciable", "Alta"),
                    "group_4": "Condición ambiental",
                    "items_4": ("Atmósfera común", "Litoral")
                },
                "air_enabled": False,
                "defective_level_index": 10,
                "spec_strength_time_enabled": True,
                "spec_strength_time": ("7 días", "28 días", "90 días"),
                "spec_strength_time_index": 1,
                "qual_control_enabled": True,
                "margin_enabled": False,
                "cement_types": ("Tipo I", "Tipo II", "Tipo III", "Tipo IV", "Tipo V"),
                "cement_class_enabled": False,
                "cement_relative_density": 3.33,
                "scm_enabled": False,
                "scm_types": None,
                "fine_types": ("Natural", "Triturada"),
                "fine_pus": "Peso unitario suelto (kgf/m³)",
                "fine_puc": "Peso unitario compactado (kgf/m³)",
                "coarse_types": ("Triturado", "Semitriturado", "Grava natural"),
                "coarse_pus": "Peso unitario suelto (kgf/m³)",
                "coarse_puc": "Peso unitario compactado (kgf/m³)",
                "chemical_admixtures_enabled": False
            },
            "ACI": {
                "exposure_class": {
                    "group_1": "Exposición a sulfatos",
                    "items_1": ("S0", "S1", "S2", "S3"),
                    "group_2": "Exposición a ciclos de congelación y deshielo",
                    "items_2": ("F0", "F1", "F2", "F3"),
                    "group_3": "Exposición al contacto con agua",
                    "items_3": ("W0", "W1", "W2"),
                    "group_4": "Exposición a la corrosión",
                    "items_4": ("C0", "C1", "C2")
                },
                "air_enabled": True,
                "defective_level_index": 10,
                "spec_strength_time_enabled": False,
                "spec_strength_time": ["28 días"],
                "spec_strength_time_index": 0,
                "qual_control_enabled": False,
                "margin_enabled": False,
                "cement_types": ("Tipo I", "Tipo IA", "Tipo II", "Tipo IIA",
                                 "Tipo III", "Tipo IIIA", "Tipo IV", "Tipo V"),
                "cement_class_enabled": False,
                "cement_relative_density": 3.15,
                "scm_enabled": True,
                "scm_types": ("Cenizas volantes", "Cemento de escoria", "Humo de sílice"),
                "fine_types": ("Natural", "Manufacturada"),
                "fine_pus": "Masa unitaria suelta (kg/m³)",
                "fine_puc": "Masa unitaria compactada (kg/m³)",
                "coarse_types": ("Redondeada", "Angular"),
                "coarse_pus": "Masa unitaria suelta (kg/m³)",
                "coarse_puc": "Masa unitaria compactada (kg/m³)",
                "chemical_admixtures_enabled": True
            },
            "DoE": {
                "exposure_class": {
                    "group_1": "Corrosión inducida por carbonatación",
                    "items_1": ("N/A", "XC1", "XC2", "XC3", "XC4"),
                    "group_2": "Corrosión inducida por cloruros",
                    "items_2": ("N/A", "XS1", "XS2", "XS3", "XD1", "XD2", "XD3"),
                    "group_3": "Ataque por congelación y deshielo",
                    "items_3": ("N/A", "XF1", "XF2", "XF3", "XF4"),
                    "group_4": "Exposición a ambientes químicos agresivos",
                    "items_4": ("N/A", "XA1", "XA2", "XA3")
                },
                "air_enabled": True,
                "defective_level_index": 6,
                "spec_strength_time_enabled": True,
                "spec_strength_time": ("3 días", "7 días", "28 días", "91 días"),
                "spec_strength_time_index": 2,
                "qual_control_enabled": False,
                "margin_enabled": True,
                "cement_types": ("CEM I", "CEM II", "CEM III", "CEM VI", "CEM V"),
                "cement_class_enabled": True,
                "cement_relative_density": 3.15,
                "scm_enabled": True,
                "scm_types": ["Cenizas volantes"],
                "fine_types": ("Triturada", "No triturada"),
                "fine_pus": "Masa unitaria suelta (kg/m³)",
                "fine_puc": "Masa unitaria compactada (kg/m³)",
                "coarse_types": ("Triturada", "No triturada"),
                "coarse_pus": "Masa unitaria suelta (kg/m³)",
                "coarse_puc": "Masa unitaria compactada (kg/m³)",
                "chemical_admixtures_enabled": True
            }
        }

        # Set the configurations for the selected method
        config = method_config.get(method, {})
        if config:
            self.ui.comboBox_method.setCurrentText(method)
            self.ui.label_1.setText(config["exposure_class"]["group_1"])
            self.ui.label_2.setText(config["exposure_class"]["group_2"])
            self.ui.label_3.setText(config["exposure_class"]["group_3"])
            self.ui.label_4.setText(config["exposure_class"]["group_4"])
            self.ui.comboBox_1.clear()
            self.ui.comboBox_1.addItems(config["exposure_class"]["items_1"])
            self.ui.comboBox_2.clear()
            self.ui.comboBox_2.addItems(config["exposure_class"]["items_2"])
            self.ui.comboBox_3.clear()
            self.ui.comboBox_3.addItems(config["exposure_class"]["items_3"])
            self.ui.comboBox_4.clear()
            self.ui.comboBox_4.addItems(config["exposure_class"]["items_4"])
            self.ui.groupBox_air.setEnabled(config["air_enabled"])
            self.ui.comboBox_defective_level.setCurrentIndex(config["defective_level_index"])
            self.ui.comboBox_spec_strength_time.setEnabled(config["spec_strength_time_enabled"])
            self.ui.comboBox_spec_strength_time.clear()
            self.ui.comboBox_spec_strength_time.addItems(config["spec_strength_time"])
            self.ui.comboBox_spec_strength_time.setCurrentIndex(config["spec_strength_time_index"])
            self.ui.label_qual_control.setEnabled(config["qual_control_enabled"])
            self.ui.comboBox_qual_control.setEnabled(config["qual_control_enabled"])
            self.ui.label_margin.setEnabled(config["margin_enabled"])
            self.ui.spinBox_margin.setEnabled(config["margin_enabled"])
            self.ui.comboBox_cement_type.clear()
            self.ui.comboBox_cement_type.addItems(config["cement_types"])
            self.ui.label_cement_class.setEnabled(config["cement_class_enabled"])
            self.ui.comboBox_cement_class.setEnabled(config["cement_class_enabled"])
            self.ui.doubleSpinBox_cement_relative_density.setValue(config["cement_relative_density"])
            self.ui.groupBox_SCM.setEnabled(config["scm_enabled"])
            if config["scm_enabled"]:
                self.ui.comboBox_SCM_type.clear()
                self.ui.comboBox_SCM_type.addItems(config.get("scm_types", []))
            self.ui.comboBox_fine_type.clear()
            self.ui.comboBox_fine_type.addItems(config["fine_types"])
            self.ui.label_fine_pus.setText(config["fine_pus"])
            self.ui.label_fine_puc.setText(config["fine_puc"])
            self.ui.label_coarse_pus.setText(config["coarse_pus"])
            self.ui.label_coarse_puc.setText(config["coarse_puc"])
            self.ui.comboBox_coarse_type.clear()
            self.ui.comboBox_coarse_type.addItems(config["coarse_types"])
            self.ui.chemical_admixtures.setEnabled(config["chemical_admixtures_enabled"])

            self.logger.info(f'A complete update of the current method "{method}" has been made')
        else:
            self.logger.warning('An invalid configuration dictionary has been selected')