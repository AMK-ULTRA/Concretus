from PyQt6.QtWidgets import QDialog

from gui.ui.ui_conversion_dialog import Ui_ConversionDialog
from core.regular_concrete.models.data_model import RegularConcreteDataModel
from logger import Logger

class ConversionDialog(QDialog):
    def __init__(self, data_model, admixture_type, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_ConversionDialog()
        # Run the .setupUi() method to show the GUI
        self.ui.setupUi(self)
        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model
        # Save the admixture type
        self.admixture_type = admixture_type

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Conversion dialog initialized')

    def conversion_tool(self):
        """
        Convert admixture dosages to a dosage percentage relative to the total cementitious material.

        This method retrieves the input dosage, relative density, and cement bag weight from the UI,
        determines which dosage type (radio button selection) is active, then calculates the corresponding
        dosage percentage. Finally, it updates the data model based on the admixture type (WRA or AEA).

        Dosage Calculation Details:
            - If 'dosage type 1' is selected:
                1. Calculate the dosage weight: dosage * relative_density.
                2. Convert the cement bag weight from kg to grams: cement_bag_weight * 1000.
                3. Compute the percentage: (dosage_weight / adjusted_cement_bag_weight) * 100.

            - If 'dosage type 2' is selected:
                1. Calculate the dosage weight: dosage * relative_density.
                2. Using one kilogram (1000 grams) of cement as a reference.
                3. Compute the percentage: (dosage_weight / 1000) * 100.
        """

        # Check which dosage type is selected from the radio buttons
        dosage_type_1_selected = self.ui.radioButton_1.isChecked()
        dosage_type_2_selected = self.ui.radioButton_2.isChecked()

        # Retrieve input values from UI
        dosage = self.ui.doubleSpinBox_dosage.value()
        relative_density = self.ui.doubleSpinBox_dosage_relative_density.value()
        cement_bag_weight = self.ui.doubleSpinBox_bag_weight.value()

        dosage_percentage = None

        # Calculation based on the selected dosage type
        if dosage_type_1_selected:
            # Validate that cement bag weight is not zero
            if cement_bag_weight == 0:
                self.logger.error('Cement bag weight cannot be zero for dosage type 1 conversion')
                return

            dosage_weight = dosage * relative_density
            # Convert the cement bag weight from kg to grams
            adjusted_cement_bag_weight = 1000 * cement_bag_weight
            dosage_percentage = (dosage_weight / adjusted_cement_bag_weight) * 100
        elif dosage_type_2_selected:
            dosage_weight = dosage * relative_density
            # Here, one kilogram of cement is used as a reference.
            dosage_percentage = (dosage_weight / 1000) * 100

        # Update the data model according to the admixture type
        if self.admixture_type == "WRA":
            self.data_model.update_design_data('chemical_admixtures.WRA.WRA_dosage', dosage_percentage)
            self.logger.info('Conversion process for WRA completed successfully')
        elif self.admixture_type == "AEA":
            self.data_model.update_design_data('chemical_admixtures.AEA.AEA_dosage', dosage_percentage)
            self.logger.info('Conversion process for AEA completed successfully')
        else:
            self.logger.warning(f'Unsupported admixture type: {self.admixture_type}. No conversion performed')