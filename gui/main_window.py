from PyQt6.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget, QHeaderView
from PyQt6.QtGui import QActionGroup

from Concretus.gui.ui_main_window import Ui_main_window
from Concretus.gui.ui_about import Ui_dialog_about
from Concretus.gui.ui_regular_concrete import Ui_regular_concrete_widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Create an instance of the GUI
        self.ui = Ui_main_window()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Set up a few things for the MainWindow
        self.set_up_main_window()
        # Default unit system
        self.units = 'MKS'
        # Default concrete mixture procedure
        self.method = 'MCE'
        # Initialize the regular_concrete_widget (initially None)
        self.regular_concrete = None

    def set_up_main_window(self):
        """Set up some logic for the application's GUI."""
        # Set up a QActionGroup for the Method menu
        method_group = QActionGroup(self)
        method_group.addAction(self.ui.action_MCE)
        method_group.addAction(self.ui.action_ACI)
        method_group.addAction(self.ui.action_DoE)

        # Set up a QActionGroup for the Unit sub-menu
        unit_group = QActionGroup(self)
        unit_group.addAction(self.ui.action_MKS)
        unit_group.addAction(self.ui.action_SI)

        # Add signal/slot connections for Method menu
        # Connect the .triggered() signal with the .***() slot
        self.ui.action_MCE.triggered.connect(self.procedures)
        self.ui.action_ACI.triggered.connect(self.procedures)
        self.ui.action_DoE.triggered.connect(self.procedures)

        # Add signal/slot connections for Report menu
        # Connect the .triggered() signal with the .***() slot
        self.ui.action_basic_report.triggered.connect(lambda: print('Basic report clicked'))
        self.ui.action_full_report.triggered.connect(lambda: print('Full report clicked'))

        # Add signal/slot connections for Unit sub-menu
        # Connect the .triggered() signal with the .***() slot
        self.ui.action_MKS.triggered.connect(self.system_of_units)
        self.ui.action_SI.triggered.connect(self.system_of_units)

        # Prevent accidentally exits
        # Connect the .triggered() signal with the .closeEvent() slot
        self.ui.action_quit.triggered.connect(self.close)

        # Initialize the About Dialog
        # Connect the .triggered() signal with the .launch_about() slot
        self.ui.action_about.triggered.connect(self.launch_about)

        # Initialize the Regular Concrete design
        # Connect the .triggered() signal with the .regular_concrete() slot
        self.ui.action_regular_concrete.triggered.connect(self.regular_concrete)

    def regular_concrete(self):
        """Initialize the design for Regular Concrete only when required by the user."""
        if not self.regular_concrete:
            self.regular_concrete = RegularConcrete()
        # Set up the center widget when the Regular Concrete design has been selected
        self.setCentralWidget(self.regular_concrete)
        # Update the system of units
        self.regular_concrete.update_units(self.units, self.method)
        # Update the method
        self.regular_concrete.update_methods(self.units, self.method)

    def system_of_units(self):
        """Changing the default unit system."""
        if self.sender().text() == 'Sistema Internacional de Unidades':
            print('SI units clicked')
            self.units = 'SI'
            if self.regular_concrete:
                self.regular_concrete.update_units(self.units, self.method)
        elif self.sender().text() == 'Sistema Técnico de Unidades':
            print('MKS units clicked')
            self.units = 'MKS'
            if self.regular_concrete:
                self.regular_concrete.update_units(self.units, self.method)

    def procedures(self):
        """Changing the default method."""
        if self.sender().text() == 'ACI':
            print('ACI method clicked')
            self.method = 'ACI'
            if self.regular_concrete:
                self.regular_concrete.update_methods(self.units, self.method)
        elif self.sender().text() == 'DoE':
            print('DoE method clicked')
            self.method = 'DoE'
            if self.regular_concrete:
                self.regular_concrete.update_methods(self.units, self.method)
        elif self.sender().text() == 'MCE':
            print('MCE method clicked')
            self.method = 'MCE'
            if self.regular_concrete:
                self.regular_concrete.update_methods(self.units, self.method)

    def launch_about(self):
        """Creating a slot for launching the About dialogLaunch the About dialog."""
        dlg_about = AboutDialog(self)
        dlg_about.exec()

    def closeEvent(self, event):
        """Reimplement the closing event to display a QMessageBox before closing."""
        reply = QMessageBox.question(self, 'Confirmación', "¿Estás seguro de que deseas salir?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


class RegularConcrete(QWidget):
    def __init__(self):
        super().__init__()
        # Create an instance of the GUI
        self.ui_regular_concrete = Ui_regular_concrete_widget()
        # Run the .setupUi() method to show the GUI
        self.ui_regular_concrete.setupUi(self)
        # Center the table headers for fine and coarse aggregate grading
        self.ui_regular_concrete.tableWidget_fine.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui_regular_concrete.tableWidget_coarse.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def update_units(self, units, method):
        """Implementing the logic to update the system units."""
        # Initialize the variables
        unit_suffix = None
        min_spec_strength = None
        max_spec_strength = None
        default_spec_strength = None

        if units == 'SI':
            unit_suffix = 'MPa'
            min_spec_strength = {'MCE': 18, 'ACI': 15, 'DoE': 12}
            max_spec_strength = {'MCE': 43, 'ACI': 45, 'DoE': 75}
            default_spec_strength = 21
        elif units == 'MKS':
            unit_suffix = 'kgf/cm²'
            min_spec_strength = {'MCE': 180, 'ACI': 150, 'DoE': 120}
            max_spec_strength = {'MCE': 430, 'ACI': 450, 'DoE': 750}
            default_spec_strength = 210

        # Update the labels
        self.ui_regular_concrete.label_spec_strength.setText(f"Resistencia de cálculo especificada ({unit_suffix})")
        self.ui_regular_concrete.label_value.setText(f"Valor ({unit_suffix})")
        self.ui_regular_concrete.label_margin.setText(f"Margen ({unit_suffix})")

        # Update default values based on the selected unit system
        self.ui_regular_concrete.doubleSpinBox_value.setMaximum(10 if units == 'SI' else 100)
        self.ui_regular_concrete.spinBox_slump.setMinimum(25 if method == 'ACI' else 10)
        self.ui_regular_concrete.spinBox_slump.setMaximum(175 if method == 'ACI' else 210)
        self.ui_regular_concrete.spinBox_slump.setValue(25 if method == 'ACI' else 10)

        # Update ranges for Specified strength
        self.ui_regular_concrete.spinBox_spec_strength.setMinimum(min_spec_strength.get(method, 0))
        self.ui_regular_concrete.spinBox_spec_strength.setMaximum(max_spec_strength.get(method, 0))
        self.ui_regular_concrete.spinBox_spec_strength.setValue(default_spec_strength)

    def update_methods(self, units, method):
        """Implementing the logic to update the fields for the selected method."""
        # Run the .update_units() method
        self.update_units(units, method)
        # Assign the self.ui_regular_concrete object reference to a local variable named ui
        ui = self.ui_regular_concrete

        if method == "MCE":
            # Setting the Method ComboBox
            ui.comboBox_method.setCurrentText("MCE")

            # Setting the Exposure class ComboBox
            ui.comboBox_exposure.clear()
            ui.comboBox_exposure.addItems([
                "(Estanqueidad) Concreto expuesto a agua dulce",
                "(Estanqueidad) Concreto expuesto a agua salobre o de mar",
                "(Exposición a sulfatos) Moderada",
                "(Exposición a sulfatos) Severa",
                "(Exposición a sulfatos) Muy severa",
                "Atmósfera común",
                "Alta humedad relativa",
                "Litoral"
            ])
            # Enabling/disabling controls for the Air content GroupBox
            ui.groupBox_air.setEnabled(False)
            # Setting the default value for the Defective level ComboBox
            ui.comboBox_defective_level.setCurrentIndex(10)
            # Enabling/disabling controls for the Unknown standard deviation GroupBox
            ui.label_qual_control.setEnabled(True)
            ui.comboBox_qual_control.setEnabled(True)
            ui.label_margin.setEnabled(False)
            ui.spinBox_margin.setEnabled(False)

            # Setting the Cement type ComboBox
            ui.comboBox_cement_type.clear()
            ui.comboBox_cement_type.addItems(["Tipo I", "Tipo II", "Tipo III", "Tipo IV", "Tipo V"])
            # Enabling/disabling controls for the Cement class ComboBox
            ui.label_cement_class.setEnabled(False)
            ui.comboBox_cement_class.setEnabled(False)
            # Setting the default value for the Cement relative density DoubleSpinBox
            ui.doubleSpinBox_cement_relative_density.setValue(3.33)
            # Enabling/disabling controls for SCM GroupBox
            ui.groupBox_SCM.setEnabled(False)

            # Setting the aggregate types
            ui.comboBox_fine_type.clear()
            ui.comboBox_fine_type.addItems(["Natural", "Triturada"])
            ui.comboBox_coarse_type.clear()
            ui.comboBox_coarse_type.addItems(["Triturado", "Semitriturado", "Grava natural"])

            # Enabling/disabling controls for Chemical admixtures Widget
            ui.chemical_admixtures.setEnabled(False)

        elif method == "ACI":
            # Setting the Method ComboBox
            ui.comboBox_method.setCurrentText("ACI")

            # Setting the Exposure class ComboBox
            ui.comboBox_exposure.clear()
            ui.comboBox_exposure.addItems([
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
            ])
            # Enabling/disabling controls for the Air content GroupBox
            ui.groupBox_air.setEnabled(True)
            # Setting the default value for the Defective level ComboBox
            ui.comboBox_defective_level.setCurrentIndex(10)
            # Enabling/disabling controls for the Unknown standard deviation GroupBox
            ui.label_qual_control.setEnabled(False)
            ui.comboBox_qual_control.setEnabled(False)
            ui.label_margin.setEnabled(False)
            ui.spinBox_margin.setEnabled(False)

            # Setting the Cement type ComboBox
            ui.comboBox_cement_type.clear()
            ui.comboBox_cement_type.addItems(
                ["Tipo I", "Tipo IA", "Tipo II", "Tipo IIA", "Tipo III", "Tipo IIIA", "Tipo IV", "Tipo V"])
            # Enabling/disabling controls for the Cement class ComboBox
            ui.label_cement_class.setEnabled(False)
            ui.comboBox_cement_class.setEnabled(False)
            # Setting the default value for the Cement relative density DoubleSpinBox
            ui.doubleSpinBox_cement_relative_density.setValue(3.15)
            # Enabling/disabling controls for SCM GroupBox
            ui.groupBox_SCM.setEnabled(True)
            ui.comboBox_SCM_type.clear()
            ui.comboBox_SCM_type.addItems(["Cenizas volantes", "Cemento de escoria", "Humo de sílice"])

            # Setting the aggregate types
            ui.comboBox_fine_type.clear()
            ui.comboBox_fine_type.addItems(["Natural", "Manufacturada"])
            ui.comboBox_coarse_type.clear()
            ui.comboBox_coarse_type.addItems(["Redondeada", "Angular"])

            # Enabling/disabling controls for Chemical admixtures Widget
            ui.chemical_admixtures.setEnabled(True)

        elif method == "DoE":
            # Setting the Method ComboBox
            ui.comboBox_method.setCurrentText("DoE")

            # Setting the Exposure class ComboBox
            ui.comboBox_exposure.clear()
            ui.comboBox_exposure.addItems([
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
            ])

            # Enabling/disabling controls for the Air content GroupBox
            ui.groupBox_air.setEnabled(True)
            # Setting the default value for the Defective level ComboBox
            ui.comboBox_defective_level.setCurrentIndex(6)
            # Enabling/disabling controls for the Unknown standard deviation GroupBox
            ui.label_qual_control.setEnabled(False)
            ui.comboBox_qual_control.setEnabled(False)
            ui.label_margin.setEnabled(True)
            ui.spinBox_margin.setEnabled(True)

            # Setting the Cement type ComboBox
            ui.comboBox_cement_type.clear()
            ui.comboBox_cement_type.addItems(["CEM I", "CEM II", "CEM III", "CEM VI", "CEM V"])
            # Enabling/disabling controls for the Cement class ComboBox
            ui.label_cement_class.setEnabled(True)
            ui.comboBox_cement_class.setEnabled(True)
            # Setting the default value for the Cement relative density DoubleSpinBox
            ui.doubleSpinBox_cement_relative_density.setValue(3.15)
            # Enabling/disabling controls for SCM GroupBox
            ui.groupBox_SCM.setEnabled(True)
            ui.comboBox_SCM_type.clear()
            ui.comboBox_SCM_type.addItems(["Cenizas volantes"])

            # Setting the aggregate types
            ui.comboBox_fine_type.clear()
            ui.comboBox_fine_type.addItems(["Triturada", "No triturada"])
            ui.comboBox_coarse_type.clear()
            ui.comboBox_coarse_type.addItems(["Triturada", "No triturada"])

            # Enabling/disabling controls for Chemical admixtures Widget
            ui.chemical_admixtures.setEnabled(True)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui_about = Ui_dialog_about()
        # Run the .setupUi() method to show the GUI
        self.ui_about.setupUi(self)