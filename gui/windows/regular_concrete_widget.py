from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem

from Concretus.gui.ui.ui_regular_concrete_widget import Ui_RegularConcreteWidget
from Concretus.logger import Logger
from Concretus.settings import MIN_SPEC_STRENGTH, MAX_SPEC_STRENGTH, SIEVES, \
    FINE_RETAINED_COL_STATE, COARSE_RETAINED_COL_STATE


class RegularConcrete(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_RegularConcreteWidget()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)

        # Default "% Retained" column state for each table
        self.fine_retained_col_active = FINE_RETAINED_COL_STATE
        self.coarse_retained_col_active = COARSE_RETAINED_COL_STATE
        # Set the default settings
        self.default_settings()
        # Set up the main connections
        self.setup_connections()
        # Initialize the logger
        self.logger = Logger(name='RegularConcrete', log_file='concretus.log')
        self.logger.info('The regular concrete widget has been created')

    def default_settings(self):
        """Set the default settings for the grading tables"""
        # Enable "% Passing" and disable "% Retained" by default
        self.toggle_passing_retained(self.ui.tableWidget_fine, not self.fine_retained_col_active)
        self.toggle_passing_retained(self.ui.tableWidget_coarse, not self.coarse_retained_col_active)

    def setup_connections(self):
        """Set up additional signal/slot connections."""
        # Toggle between "% Passing" and "% Retained"
        # The lambda function catches the "toggled" signal and calls the method passing two arguments
        self.ui.radioButton_fine_retained.toggled.connect(
            lambda checked: self.on_radio_button_toggled(checked, self.ui.tableWidget_fine)
        )
        self.ui.radioButton_coarse_retained.toggled.connect(
            lambda checked: self.on_radio_button_toggled(checked, self.ui.tableWidget_coarse)
        )

    def on_radio_button_toggled(self, checked, table):
        """
        Method that is executed when the QRadioButton changes state.
        :param checked: True if the QRadioButton is enabled, False otherwise.
        :param table: The table associated with the QRadioButton.
        """
        # Enable or disable the corresponding columns
        self.toggle_passing_retained(table, not checked)

        # Record the change in the logger
        table_name = "fine" if table == self.ui.tableWidget_fine else "coarse"
        self.logger.info(f'QRadioButton for {table_name} table is active: {checked}')

    @staticmethod
    def toggle_passing_retained(table, passing_enabled):
        """
        Enables "% Passing" and disables "% Retained", or vice versa.
        :param table: The table to modify.
        :param passing_enabled: True to enable "% Passing", False to enable "% Retained".
        """
        for row in range(table.rowCount()):
            # Enable or disable "% Passing"
            item_passing = table.item(row, 1)
            if not item_passing:
                item_passing = QTableWidgetItem()
                table.setItem(row, 1, item_passing)
            item_passing.setFlags(
                item_passing.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                if passing_enabled
                else item_passing.flags() & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable
            )

            # Enable or disable "% Retained"
            item_retained = table.item(row, 2)
            if not item_retained:
                item_retained = QTableWidgetItem()
                table.setItem(row, 2, item_retained)
            item_retained.setFlags(
                item_retained.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                if not passing_enabled
                else item_retained.flags() & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable
            )

    def populate_tables(self, method):
        """
        Deletes all rows and generates a new set of rows according to the selected method.
        :param method: The method for selecting the set of corresponding rows.
        """
        # Clean tables
        self.ui.tableWidget_fine.setRowCount(0)
        self.ui.tableWidget_coarse.setRowCount(0)

        # Center the table headers for fine and coarse aggregate grading
        self.ui.tableWidget_fine.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.ui.tableWidget_coarse.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

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
        self.default_settings()
        self.on_radio_button_toggled(self.ui.radioButton_fine_retained.isChecked(),
                                     self.ui.tableWidget_fine)
        self.on_radio_button_toggled(self.ui.radioButton_coarse_retained.isChecked(),
                                     self.ui.tableWidget_coarse)
        self.logger.info(f'The set of sieves for the {method} method has been generated')

    def update_units(self, units, method):
        """
        Update fields that depend on the selected units and method.
        :param units: The system of units to update the fields.
        :param method: The method to update the fields.
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

        # Update the labels
        self.ui.label_spec_strength.setText(f"Resistencia de cálculo especificada ({unit_suffix})")
        self.ui.label_value.setText(f"Valor ({unit_suffix})")
        self.ui.label_margin.setText(f"Margen ({unit_suffix})")

        # Update ranges for specified compressive strength
        min_spec_strength = MIN_SPEC_STRENGTH[units][method]
        max_spec_strength = MAX_SPEC_STRENGTH[units][method]
        self.ui.spinBox_spec_strength.setMinimum(min_spec_strength)
        self.ui.spinBox_spec_strength.setMaximum(max_spec_strength)
        self.ui.spinBox_spec_strength.setValue(default_spec_strength)

        # Update default values
        self.ui.doubleSpinBox_value.setMaximum(10 if units == 'SI' else 100)

        self.logger.info('The .update_units() method has executed successfully')

    def update_method(self, method):
        """
        Update fields that depend on the selected method.
        :param method: The method to update the fields.
        """
        # Populate the grading table
        self.populate_tables(method)

        # Update default values
        self.ui.spinBox_slump.setMinimum(25 if method == 'ACI' else 10)
        self.ui.spinBox_slump.setMaximum(175 if method == 'ACI' else 210)
        self.ui.spinBox_slump.setValue(25 if method == 'ACI' else 10)

        # A dictionary to map all method configurations
        method_config = {
            "MCE": {
                "exposure_items": [
                    "(Estanqueidad) Concreto expuesto a agua dulce",
                    "(Estanqueidad) Concreto expuesto a agua salobre o de mar",
                    "(Exposición a sulfatos) Moderada",
                    "(Exposición a sulfatos) Severa",
                    "(Exposición a sulfatos) Muy severa",
                    "Atmósfera común",
                    "Alta humedad relativa",
                    "Litoral"
                ],
                "air_enabled": False,
                "defective_level_index": 10,
                "qual_control_enabled": True,
                "margin_enabled": False,
                "cement_types": ["Tipo I", "Tipo II", "Tipo III", "Tipo IV", "Tipo V"],
                "cement_class_enabled": False,
                "cement_relative_density": 3.33,
                "scm_enabled": False,
                "scm_types": [],
                "fine_types": ["Natural", "Triturada"],
                "coarse_types": ["Triturado", "Semitriturado", "Grava natural"],
                "chemical_admixtures_enabled": False
            },
            "ACI": {
                "exposure_items": [
                    "Exposición a sulfatos (S0)",
                    "Exposición a sulfatos (S1)",
                    "Exposición a sulfatos (S2)",
                    "Exposición a ciclos de congelación y deshielo (F0)",
                    "Exposición a ciclos de congelación y deshielo (F1)",
                    "Exposición a ciclos de congelación y deshielo (F2)",
                    "Exposición a ciclos de congelación y deshielo (F3)",
                    "Exposición al contacto con agua (W0)",
                    "Exposición al contacto con agua (W1)",
                    "Exposición al contacto con agua (W2)",
                    "Exposición a la corrosión (C0)",
                    "Exposición a la corrosión (C1)",
                    "Exposición a la corrosión (C2)"
                ],
                "air_enabled": True,
                "defective_level_index": 10,
                "qual_control_enabled": False,
                "margin_enabled": False,
                "cement_types": ["Tipo I", "Tipo IA", "Tipo II", "Tipo IIA", "Tipo III", "Tipo IIIA", "Tipo IV",
                                 "Tipo V"],
                "cement_class_enabled": False,
                "cement_relative_density": 3.15,
                "scm_enabled": True,
                "scm_types": ["Cenizas volantes", "Cemento de escoria", "Humo de sílice"],
                "fine_types": ["Natural", "Manufacturada"],
                "coarse_types": ["Redondeada", "Angular"],
                "chemical_admixtures_enabled": True
            },
            "DoE": {
                "exposure_items": [
                    "Sin riesgo de corrosión (X0)",
                    "Corrosión inducida por carbonatación (XC1)",
                    "Corrosión inducida por carbonatación (XC2)",
                    "Corrosión inducida por carbonatación (XC3)",
                    "Corrosión inducida por carbonatación (XC4)",
                    "Corrosión inducida por cloruros (XS1)",
                    "Corrosión inducida por cloruros (XS2)",
                    "Corrosión inducida por cloruros (XS3)",
                    "Corrosión inducida por cloruros (XD1)",
                    "Corrosión inducida por cloruros (XD2)",
                    "Corrosión inducida por cloruros (XD3)",
                    "Ataque por congelación y deshielo (XF1)",
                    "Ataque por congelación y deshielo (XF2)",
                    "Ataque por congelación y deshielo (XF3)",
                    "Ataque por congelación y deshielo (XF4)",
                    "Exposición a ambientes químicos agresivos (XA1)",
                    "Exposición a ambientes químicos agresivos (XA2)",
                    "Exposición a ambientes químicos agresivos (XA3)"
                ],
                "air_enabled": True,
                "defective_level_index": 6,
                "qual_control_enabled": False,
                "margin_enabled": True,
                "cement_types": ["CEM I", "CEM II", "CEM III", "CEM VI", "CEM V"],
                "cement_class_enabled": True,
                "cement_relative_density": 3.15,
                "scm_enabled": True,
                "scm_types": ["Cenizas volantes"],
                "fine_types": ["Triturada", "No triturada"],
                "coarse_types": ["Triturada", "No triturada"],
                "chemical_admixtures_enabled": True
            }
        }

        # Set the configurations for the selected method
        config = method_config.get(method, {})
        if config:
            self.ui.comboBox_method.setCurrentText(method)
            self.ui.comboBox_exposure.clear()
            self.ui.comboBox_exposure.addItems(config["exposure_items"])
            self.ui.groupBox_air.setEnabled(config["air_enabled"])
            self.ui.comboBox_defective_level.setCurrentIndex(config["defective_level_index"])
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
            self.ui.comboBox_coarse_type.clear()
            self.ui.comboBox_coarse_type.addItems(config["coarse_types"])
            self.ui.chemical_admixtures.setEnabled(config["chemical_admixtures_enabled"])

            self.logger.info('The .update_methods() method has executed successfully')
        else:
            self.logger.warning('An invalid configuration dictionary has been selected')