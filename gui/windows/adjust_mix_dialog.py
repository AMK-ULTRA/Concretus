from PyQt6.QtWidgets import QDialog, QMessageBox

from gui.ui.ui_adjust_mix_dialog import Ui_AdjustMixDialog
from core.regular_concrete.models.regular_concrete_data_model import RegularConcreteDataModel
from core.regular_concrete.models.aci_data_model import ACIDataModel
from core.regular_concrete.models.doe_data_model import DOEDataModel
from core.regular_concrete.models.mce_data_model import MCEDataModel
from logger import Logger


class AdjustTrialMixDialog(QDialog):
    def __init__(self, data_model, mce_data_model, aci_data_model, doe_data_model, parent=None):
        super().__init__(parent)
        # Create an instance of the GUI
        self.ui = Ui_AdjustMixDialog()
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

        # Group all QGroupBoxes into two instance lists
        self.group_boxes_1 = [
            self.ui.groupBox_adjust_water,
            self.ui.groupBox_adjust_cementitious,
            self.ui.groupBox_adjust_agg
        ]
        self.group_boxes_2 = [
            self.ui.groupBox_coarse,
            self.ui.groupBox_fine
        ]

        # Display volume percentages
        self.display_volume_percentages()
        # Display fine and coarse aggregate proportions
        self.display_agg_info()
        # Display the water-to-cementitious material ratio
        self.display_w_cm()

        # Set up local signal/slot connections
        self.setup_connections()

        # Perform a unit system update
        self.handle_AdjustTrialMixDialog_units_changed(self.data_model.units)

        # Initialization complete
        self.logger.info('Adjust trial mix dialog initialized')

    def setup_connections(self):
        """Set local signal/slot connections, i.e. the connections within the same QWidget."""

        # Connect the toggled signals for each QGroupBox in both groups so that they act as mutually exclusive groups
        for box in self.group_boxes_1:
            box.toggled.connect(lambda checked, current=box: self.handle_groupBoxes_toggled(current, checked))
        for box in self.group_boxes_2:
            box.toggled.connect(lambda checked, current=box: self.handle_groupBoxes_toggled(current, checked))
        # Run the adjustments when the push button is clicked
        self.ui.pushButton_apply_adjustments.clicked.connect(self.handle_pushButton_apply_adjustments_clicked)

    def display_volume_percentages(self, decimals=2):
        """
        Calculate each component’s percentage of the total absolute volume
        and display them in the UI. Components with value None or 0 are shown as 0.0%.

        :param int decimals: Number of decimal places to format the percentages.
        """

        # Validate inputs
        if decimals < 0:
            raise ValueError("Decimals must be non-negative")

        # Connect to the main data model
        dm = self.data_model

        # Retrieve absolute volumes (L)
        water_vol = dm.get_design_value('trial_mix.adjustments.water.water_abs_volume') or 0
        cement_vol = dm.get_design_value('trial_mix.adjustments.cementitious_material.cement.cement_abs_volume') or 0
        scm_vol = dm.get_design_value('trial_mix.adjustments.cementitious_material.scm.scm_abs_volume') or 0
        fine_vol = dm.get_design_value('trial_mix.adjustments.fine_aggregate.fine_abs_volume') or 0
        coarse_vol = dm.get_design_value('trial_mix.adjustments.coarse_aggregate.coarse_abs_volume') or 0
        entrapped_air = dm.get_design_value('trial_mix.adjustments.air.entrapped_air_content') or 0
        entrained_air = dm.get_design_value('trial_mix.adjustments.air.entrained_air_content') or 0
        total_vol = dm.get_design_value('trial_mix.adjustments.summation.total_abs_volume') or 0

        if total_vol == 0:
            self.logger.warning("Total absolute volume is zero or missing; cannot compute percentages")
            # Clear all fields
            for line_edit in [
                self.ui.lineEdit_cementitious,
                self.ui.lineEdit_water,
                self.ui.lineEdit_air,
                self.ui.lineEdit_fine_agg,
                self.ui.lineEdit_coarse_agg
            ]:
                line_edit.setText("0.0%")
            return

        # Compute percentages
        pct = lambda v: (v / total_vol * 100) if v else 0.0

        cementitious_pct = pct(cement_vol + scm_vol)
        water_pct = pct(water_vol)
        air_pct = pct(entrapped_air + entrained_air)
        fine_pct = pct(fine_vol)
        coarse_pct = pct(coarse_vol)

        # Format string helper
        fmt = f"{{:.{decimals}f}}%"

        # Map results to the UI
        boxes = [
            (self.ui.lineEdit_cementitious, cementitious_pct),
            (self.ui.lineEdit_water, water_pct),
            (self.ui.lineEdit_air, air_pct),
            (self.ui.lineEdit_fine_agg, fine_pct),
            (self.ui.lineEdit_coarse_agg, coarse_pct),
        ]
        for widget, value in boxes:
            widget.setText(fmt.format(value))

    def display_agg_info(self, decimals=2):
        """
        Fetch and display fine and coarse aggregate proportions for the selected design method.

        :param int decimals: Number of decimal places to format the percentages.
        """

        # Validate inputs
        if decimals < 0:
            raise ValueError("Decimals must be non-negative")

        # Connect to the main data model
        dm = self.data_model

        # Retrieve absolute volumes (L)
        fine_abs_volume = dm.get_design_value('trial_mix.adjustments.fine_aggregate.fine_abs_volume')
        coarse_abs_volume = dm.get_design_value('trial_mix.adjustments.coarse_aggregate.coarse_abs_volume')

        total_abs_volume = fine_abs_volume + coarse_abs_volume
        if total_abs_volume <= 0:
            raise ValueError("Total aggregate absolute volume must be greater than zero")

        # Calculate percentages
        fine_ptc = (fine_abs_volume / total_abs_volume) * 100
        coarse_ptc = (coarse_abs_volume / total_abs_volume) * 100

        # Obtain recommended ranges (only for MCE)
        if self.data_model.method == "MCE":
            fine_min = self.mce_data_model.get_data('beta.beta_min')
            fine_max = self.mce_data_model.get_data('beta.beta_max')
            coarse_min = 100 - fine_min
            coarse_max = 100 - fine_max
            fine_range = f"{fine_min:.{decimals}f}% – {fine_max:.{decimals}f}%"
            coarse_range = f"{coarse_min:.{decimals}f}% – {coarse_max:.{decimals}f}%"
        else:
            fine_range = "N/A"
            coarse_range = "N/A"

        # Update UI fields
        self.ui.lineEdit_fine_prop_actual.setText(f"{fine_ptc:.{decimals}f}")
        self.ui.lineEdit_coarse_prop_actual.setText(f"{coarse_ptc:.{decimals}f}")
        self.ui.lineEdit_fine_prop_range.setText(fine_range)
        self.ui.lineEdit_coarse_prop_range.setText(coarse_range)

    def display_w_cm(self, decimals=3):
        """
        Display the actual water-to-cementitious ratio in used.

        :param int decimals: Number of decimal places to format the ratio.
        """

        # Validate inputs
        if decimals < 0:
            raise ValueError("Decimals must be non-negative")

        # Connect to the main data model
        dm = self.data_model

        # Retrieve the w/am
        w_cm = dm.get_design_value('trial_mix.adjustments.water_cementitious_materials_ratio.w_cm')

        # Load the value
        self.ui.lineEdit_w_cm_used.setText(f"{w_cm:.{decimals}f}")
        self.ui.lineEdit_w_cm_used_2.setText(f"{w_cm:.{decimals}f}")

    def admixture_dosage(self):
        """
        Calculate and update the content and volume for chemical admixtures (WRA and AEA).

        This method calculates the dosage of Water Reducing Admixture (WRA) and Air-Entraining Admixture (AEA)
        based on the current cementitious content and stores the results in the data model.
        """

        # Connect to the main data model
        dm = self.data_model

        # Get cementitious materials content
        cement_content = dm.get_design_value('trial_mix.adjustments.cementitious_material.cement.cement_content') or 0
        scm_content = dm.get_design_value('trial_mix.adjustments.cementitious_material.scm.scm_content') or 0
        cementitious_content = cement_content + scm_content

        # Get water properties
        water_density = dm.get_design_value('water.water_density')

        # Results dictionary to store calculated values
        results = {
            'WRA': {'content': 0, 'volume': 0},
            'AEA': {'content': 0, 'volume': 0}
        }

        # Process each admixture type
        admixture_types = ['WRA', 'AEA']

        for admixture_type in admixture_types:
            # Check if admixture is enabled
            is_enabled = dm.get_design_value(f'chemical_admixtures.{admixture_type}.{admixture_type}_checked')

            if is_enabled:
                # Get admixture properties
                dosage = dm.get_design_value(f'chemical_admixtures.{admixture_type}.{admixture_type}_dosage')
                relative_density = dm.get_design_value(
                    f'chemical_admixtures.{admixture_type}.{admixture_type}_relative_density')

                # Calculate content and volume
                content = cementitious_content * (dosage / 100)
                volume = (content / (relative_density * water_density)) * 1000

                # Store results in dictionary
                results[admixture_type]['content'] = content
                results[admixture_type]['volume'] = volume

                # Update data model
                dm.update_design_data(
                    f'trial_mix.adjustments.chemical_admixtures.{admixture_type}.{admixture_type}_content', content)
                dm.update_design_data(
                    f'trial_mix.adjustments.chemical_admixtures.{admixture_type}.{admixture_type}_volume', volume)

        self.logger.info('The new contents and volumes of the chemical admixtures have been calculated')

    def water_adjustment(self):
        """
        Adjust water content of the trial mix based on the volume of water added and update the data model.

        This method recalculates mix proportions after adjusting the water content, maintaining either
        the water-to-cementitious materials ratio or the cementitious content based on user preference.

        :return: True if the calculations were performed correctly, False otherwise.
        :rtype: bool
        """

        # Connect to the main data model
        dm = self.data_model

        # Retrieve input values from UI and data models
        water_added_liters = self.ui.doubleSpinBox_water_used.value()
        air_percentage = self.ui.doubleSpinBox_air_measured.value()
        water_density = dm.get_design_value('water.water_density') * 0.001 # Convert from kg/m³ to L/m³
        w_cm = dm.get_design_value('trial_mix.adjustments.water_cementitious_materials_ratio.w_cm')
        coarse_content_wet = dm.get_design_value('trial_mix.adjustments.coarse_aggregate.coarse_content_wet')
        fine_content_wet = dm.get_design_value('trial_mix.adjustments.fine_aggregate.fine_content_wet')

        # Moisture parameters
        moisture_params = self._get_moisture_parameters()

        # Cementitious material parameters
        cementitious_params = self._get_cementitious_parameters()

        # Trial mix parameters
        trial_mix_volume = dm.get_design_value('trial_mix_volume')
        trial_mix_waste = dm.get_design_value('trial_mix_waste')

        # Calculate water adjustment
        water_added_kg = water_added_liters * water_density  # convert water added from L to kg

        # Scale up the added water to account for the trial mix volume and waste
        water_added_scaled = water_added_kg / (trial_mix_volume * trial_mix_waste)

        # Calculate free water in aggregates
        agg_free_water = self._calculate_aggregate_free_water(moisture_params, coarse_content_wet, fine_content_wet)

        # Determine total free water in the mixture
        new_water_content = water_added_scaled + agg_free_water

        # Update mix proportions based on user preference
        if self.ui.checkBox_keep_a_cm.isChecked():
            # Keep water-to-cementitious ratio constant, adjust cementitious content
            new_cementitious_content = new_water_content / w_cm
            new_w_cm = w_cm
        else:
            # Keep cementitious content constant, calculate new w/cm ratio
            new_cementitious_content = cementitious_params['cementitious_content']
            new_w_cm = new_water_content / new_cementitious_content

        # Keep the coarse proportion
        keep_coarse_prop = self.ui.radioButton_keep_corase_agg.isChecked()

        # Calculate updated mix proportions
        mix_proportions = self._calculate_mix_proportions(
            new_water_content,
            new_cementitious_content,
            cementitious_params,
            moisture_params,
            air_percentage,
            water_density,
            new_w_cm,
            keep_coarse_prop
        )

        # Store adjustment results and capture the success status
        stored_successfully = self._store_adjustment_results(mix_proportions)
        if stored_successfully:
            # Record the adjustments made
            adjustments_made = {
                "water_used": water_added_scaled / water_density,
                "air_measured": air_percentage,
                "w_cm": new_w_cm,
                "keep_coarse_agg": keep_coarse_prop,
                "keep_fine_agg": not keep_coarse_prop,
            }
            self._record_adjustments_made("water", adjustments_made)

        return stored_successfully

    def cementitious_material_adjustment(self):
        """
        Adjust cementitious material content of the trial mix and update the data model.

        This method recalculates mix proportions after adjusting the cementitious content,
        maintaining either the water-to-cementitious materials ratio or the water content
        based on user preference.

        :return: True if the calculations were performed correctly, False otherwise.
        :rtype: bool
        """

        # Connect to the main data model
        dm = self.data_model

        # Retrieve input values from UI and data models
        new_cementitious_content = self.ui.doubleSpinBox_cementitious_used.value()
        air_percentage = self.ui.doubleSpinBox_air_measured_2.value()
        w_cm = dm.get_design_value('trial_mix.adjustments.water_cementitious_materials_ratio.w_cm')
        water_density = dm.get_design_value('water.water_density') * 0.001 # Convert from kg/m³ to L/m³
        water_content = dm.get_design_value('trial_mix.adjustments.water.water_content_correction')

        # Get moisture parameters
        moisture_params = self._get_moisture_parameters()

        # Get cementitious material parameters
        cementitious_params = self._get_cementitious_parameters()

        # Trial mix parameters
        trial_mix_volume = dm.get_design_value('trial_mix_volume')
        trial_mix_waste = dm.get_design_value('trial_mix_waste')

        # Scale up the added cementitious content
        new_cementitious_content_scaled = new_cementitious_content / (trial_mix_volume * trial_mix_waste)

        # Determine the new water content based on user preference
        if self.ui.checkBox_keep_a_cm_2.isChecked():
            # Keep water-to-cementitious ratio constant, adjust water content
            new_water_content = w_cm * new_cementitious_content_scaled
            new_w_cm = w_cm
        else:
            # Keep water content constant, calculate new w/cm ratio
            new_water_content = water_content
            new_w_cm = new_water_content / new_cementitious_content_scaled

        # Keep the coarse proportion
        keep_coarse_prop = self.ui.radioButton_keep_corase_agg_2.isChecked()

        # Calculate updated mix proportions
        mix_proportions = self._calculate_mix_proportions(
            new_water_content,
            new_cementitious_content_scaled,
            cementitious_params,
            moisture_params,
            air_percentage,
            water_density,
            new_w_cm,
            keep_coarse_prop
        )

        # Store adjustment results and capture the success status
        stored_successfully = self._store_adjustment_results(mix_proportions)
        if stored_successfully:
            # Record the adjustments made
            adjustments_made = {
                "cementitious_used": new_cementitious_content_scaled,
                "air_measured": air_percentage,
                "w_cm": new_w_cm,
                "keep_coarse_agg": keep_coarse_prop,
                "keep_fine_agg": not keep_coarse_prop,
            }
            self._record_adjustments_made("cementitious_material", adjustments_made)

        return stored_successfully

    def aggregates_adjustment(self, agg_type):
        """
        Adjust fine or coarse aggregate proportions in the trial mix.

        :param str agg_type: "coarse" to adjust coarse aggregate fraction,
                             "fine" to adjust fine aggregate fraction.
        :return: True if the calculations were performed correctly, False otherwise.
        :rtype: bool
        """

        # Validate inputs
        if agg_type not in ["coarse", "fine"]:
            raise ValueError(f"Invalid agg_type -> {agg_type}")

        # Connect to the main data model
        dm = self.data_model

        # Retrieve input values from UI and data models
        fine_pct = self.ui.doubleSpinBox_fine_prop.value()
        coarse_pct = self.ui.doubleSpinBox_coarse_prop.value()
        water_density = dm.get_design_value('water.water_density') * 0.001 # Convert from kg/m3 to L/m3
        water_abs_vol = dm.get_design_value('trial_mix.adjustments.water.water_abs_volume')
        fine_abs_vol = dm.get_design_value('trial_mix.adjustments.fine_aggregate.fine_abs_volume')
        coarse_abs_vol = dm.get_design_value('trial_mix.adjustments.coarse_aggregate.coarse_abs_volume')

        # Get aggregate parameters
        agg_params = self._get_aggregate_parameters()

        # Get moisture parameters
        moisture_params = self._get_moisture_parameters()

        # Calculate total aggregate absolute volume (L)
        agg_abs_vol = fine_abs_vol + coarse_abs_vol
        if agg_abs_vol <= 0:
            raise ValueError("Total aggregate volume must be greater than zero")

        # Calculate new absolute volumes based on selected adjustment type
        if self.ui.groupBox_coarse.isChecked() and agg_type == "coarse":
            new_coarse_abs_vol = agg_abs_vol * (coarse_pct / 100)
            new_fine_abs_vol = agg_abs_vol - new_coarse_abs_vol
            fine_pct = 100 - coarse_pct
        elif self.ui.groupBox_fine.isChecked() and agg_type == "fine":
            new_fine_abs_vol = agg_abs_vol * (fine_pct / 100)
            new_coarse_abs_vol = agg_abs_vol - new_fine_abs_vol
            coarse_pct = 100 - fine_pct
        else:
            # No changes if the corresponding group box isn't checked
            new_fine_abs_vol = fine_abs_vol
            new_coarse_abs_vol = coarse_abs_vol

        # Calculate contents
        water_content = water_abs_vol * (1 * water_density)
        fine_content_ssd = new_fine_abs_vol * (agg_params['fine_relative_density'] * water_density)
        coarse_content_ssd = new_coarse_abs_vol * (agg_params['coarse_relative_density'] * water_density)

        # Calculate wet aggregate contents
        coarse_content_wet = coarse_content_ssd * ((100 + moisture_params['coarse_moisture_content']) /
                                                   (100 + moisture_params['coarse_absorption_content']))
        fine_content_wet = fine_content_ssd * ((100 + moisture_params['fine_moisture_content']) /
                                               (100 + moisture_params['fine_absorption_content']))

        # Calculate water content correction
        water_content_correction = (water_content + (fine_content_ssd - fine_content_wet)
                                    + (coarse_content_ssd - coarse_content_wet))

        # Calculate apparent volumes
        coarse_volume = coarse_content_wet / (agg_params['coarse_loose_bulk_density'] / 1000) # Convert loose bulk densities
        fine_volume = fine_content_wet / (agg_params['fine_loose_bulk_density'] / 1000)       # from kg/m³ to L/m³

        # Update all values in the data model
        update_items = {
            'trial_mix.adjustments.fine_aggregate.fine_abs_volume': new_fine_abs_vol,
            'trial_mix.adjustments.coarse_aggregate.coarse_abs_volume': new_coarse_abs_vol,
            'trial_mix.adjustments.water.water_content_correction': water_content_correction,
            'trial_mix.adjustments.fine_aggregate.fine_content_ssd': fine_content_ssd,
            'trial_mix.adjustments.fine_aggregate.fine_content_wet': fine_content_wet,
            'trial_mix.adjustments.coarse_aggregate.coarse_content_ssd': coarse_content_ssd,
            'trial_mix.adjustments.coarse_aggregate.coarse_content_wet': coarse_content_wet,
            'trial_mix.adjustments.fine_aggregate.fine_volume': fine_volume,
            'trial_mix.adjustments.coarse_aggregate.coarse_volume': coarse_volume
        }

        # Update all values at once
        for key, value in update_items.items():
            dm.update_design_data(key, value)

        # Record the adjustments made
        adjustments_made = {
            "new_coarse_proportion": coarse_pct,
            "new_fine_proportion": fine_pct,
        }
        self._record_adjustments_made("aggregate_proportion", adjustments_made)

        return True

    def _get_moisture_parameters(self):
        """
        Get moisture-related parameters from the data model.

        :return: A dictionary containing moisture content and absorption values.
        :rtype: dict[str, float]
        """

        return {
            'coarse_moisture_content': self.data_model.get_design_value('coarse_aggregate.moisture.moisture_content'),
            'coarse_absorption_content': self.data_model.get_design_value('coarse_aggregate.moisture.absorption_content'),
            'fine_moisture_content': self.data_model.get_design_value('fine_aggregate.moisture.moisture_content'),
            'fine_absorption_content': self.data_model.get_design_value('fine_aggregate.moisture.absorption_content'),
        }

    def _get_aggregate_parameters(self):
        """
        Get aggregate parameters from the data model.

        :return: A dictionary containing the different aggregate densities..
        :rtype: dict[str, float]
        """

        return {
            'fine_relative_density': self.data_model.get_design_value('fine_aggregate.physical_prop.relative_density_SSD'),
            'coarse_relative_density': self.data_model.get_design_value('coarse_aggregate.physical_prop.relative_density_SSD'),
            'fine_loose_bulk_density': self.data_model.get_design_value('fine_aggregate.physical_prop.PUS'),
            'coarse_loose_bulk_density': self.data_model.get_design_value('coarse_aggregate.physical_prop.PUS'),
        }

    def _get_cementitious_parameters(self):
        """
        Get cementitious material parameters from the data model.

        :return: A dictionary containing cementitious material parameters.
        :rtype: dict[str, float]
        """

        # Get SCM parameters
        scm_percentage = self.data_model.get_design_value('cementitious_materials.SCM.SCM_content')
        scm_flag = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')

        # Get cement content
        cement_content = self.data_model.get_design_value(
            'trial_mix.adjustments.cementitious_material.cement.cement_content') or 0
        scm_content = self.data_model.get_design_value(
            'trial_mix.adjustments.cementitious_material.scm.scm_content') or 0

        # Calculate total cementitious content
        cementitious_content = cement_content + scm_content if scm_flag else cement_content

        # Get densities
        cement_relative_density = self.data_model.get_design_value('cementitious_materials.cement_relative_density')
        scm_relative_density = self.data_model.get_design_value('cementitious_materials.SCM.SCM_relative_density') or 0

        return {
            'cement_content': cement_content,
            'scm_content': scm_content,
            'scm_percentage': scm_percentage,
            'scm_flag': scm_flag,
            'cementitious_content': cementitious_content,
            'cement_relative_density': cement_relative_density,
            'scm_relative_density': scm_relative_density,
        }

    @staticmethod
    def _calculate_aggregate_free_water(moisture_params, coarse_content_wet, fine_content_wet):
        """
        Calculate the free water in the aggregates.

        :param dict moisture_params: Dictionary containing moisture content and absorption values.
        :param float coarse_content_wet: The wet content of coarse aggregate.
        :param float fine_content_wet: The wet content of fine aggregate.
        :return: The total free water in aggregates.
        :rtype: float
        """

        # Calculate moisture correction factors
        coarse_factor = (1 - (1 + moisture_params['coarse_absorption_content'] / 100)
                         / (1 + moisture_params['coarse_moisture_content'] / 100))
        fine_factor = (1 - (1 + moisture_params['fine_absorption_content'] / 100)
                       / (1 + moisture_params['fine_moisture_content'] / 100))

        # Calculate free water in each aggregate
        coarse_free_water = coarse_content_wet * coarse_factor
        fine_free_water = fine_content_wet * fine_factor

        # Return total free water
        return fine_free_water + coarse_free_water

    def _calculate_mix_proportions(self, water_content, cementitious_content, cementitious_params, moisture_params,
                                   air_percentage, water_density, w_cm, keep_coarse_prop):
        """
        Calculate mix proportions based on input parameters.

        :param float water_content: Water content in kg.
        :param float cementitious_content: Total cementitious content in kg.
        :param dict cementitious_params: Dictionary containing cementitious material parameters.
        :param dict moisture_params: Dictionary containing moisture content and absorption values.
        :param float air_percentage: Air content percentage.
        :param float water_density: Density of water.
        :param float w_cm: Water to cementitious material ratio.
        :param bool keep_coarse_prop: Flag to determine if coarse aggregate is kept.
        :return: A dictionary containing calculated mix proportions.
        :rtype: dict[str, float]
        """

        # Connect to the main data model
        dm = self.data_model

        # Get aggregate parameters
        agg_params = self._get_aggregate_parameters()

        # Recalculate cement and SCM contents based on total cementitious content
        if cementitious_params['scm_flag']:
            scm_content = cementitious_content * (cementitious_params['scm_percentage'] / 100)
            cement_content = cementitious_content - scm_content
        else:
            scm_content = 0
            cement_content = cementitious_content

        # Calculate absolute volumes for water and cementitious materials (L)
        water_abs_volume = water_content / (1 * water_density)
        cement_abs_volume = cement_content / (cementitious_params['cement_relative_density'] * water_density)
        if scm_content != 0:
            scm_abs_volume = scm_content / (cementitious_params['scm_relative_density'] * water_density)
        else:
            scm_abs_volume = 0
        air_volume = air_percentage * 10

        # Determine aggregate volumes based on user preference
        if keep_coarse_prop:
            coarse_abs_volume = dm.get_design_value('trial_mix.adjustments.coarse_aggregate.coarse_abs_volume')
            fine_abs_volume = 1000 - (
                        water_abs_volume + cement_abs_volume + scm_abs_volume + coarse_abs_volume + air_volume)
        else:
            fine_abs_volume = dm.get_design_value('trial_mix.adjustments.fine_aggregate.fine_abs_volume')
            coarse_abs_volume = 1000 - (
                        water_abs_volume + cement_abs_volume + scm_abs_volume + fine_abs_volume + air_volume)

        # Store absolute volumes (L)
        abs_volumes = {
            'water_abs_volume': water_abs_volume,
            'cement_abs_volume': cement_abs_volume,
            'scm_abs_volume': scm_abs_volume,
            'coarse_abs_volume': coarse_abs_volume,
            'fine_abs_volume': fine_abs_volume,
            'air_volume': air_volume,
        }

        # Calculate aggregate contents
        coarse_content_ssd = coarse_abs_volume * (agg_params['coarse_relative_density'] * water_density)
        fine_content_ssd = fine_abs_volume * (agg_params['fine_relative_density'] * water_density)

        # Calculate wet aggregate contents
        coarse_content_wet = coarse_content_ssd * ((100 + moisture_params['coarse_moisture_content']) /
                                                   (100 + moisture_params['coarse_absorption_content']))
        fine_content_wet = fine_content_ssd * ((100 + moisture_params['fine_moisture_content']) /
                                               (100 + moisture_params['fine_absorption_content']))

        # Calculate water content correction
        water_content_correction = (water_content + (fine_content_ssd - fine_content_wet)
                                    + (coarse_content_ssd - coarse_content_wet))
        
        # Store materials contents
        contents = {
            'water_content_correction': water_content_correction,
            'cement_content': cement_content,
            'scm_content': scm_content,
            'coarse_content_ssd': coarse_content_ssd,
            'coarse_content_wet': coarse_content_wet,
            'fine_content_ssd': fine_content_ssd,
            'fine_content_wet': fine_content_wet,
        }

        # Calculate apparent volumes
        coarse_volume = coarse_content_wet / (agg_params['coarse_loose_bulk_density'] / 1000) # Convert loose bulk densities
        fine_volume = fine_content_wet / (agg_params['fine_loose_bulk_density'] / 1000)       # from kg/m³ to L/m³
        water_volume = water_content_correction
        
        # Store apparent volumes
        volumes = {
            'coarse_volume': coarse_volume,
            'fine_volume': fine_volume,
            'water_volume': water_volume,
        }

        # Calculate totals
        total_abs_volume = sum([
            abs_volumes['water_abs_volume'],
            abs_volumes['cement_abs_volume'],
            abs_volumes['scm_abs_volume'],
            abs_volumes['fine_abs_volume'],
            abs_volumes['coarse_abs_volume'],
            abs_volumes['air_volume']
        ])
        total_content = sum([
            water_content_correction,
            cement_content,
            scm_content,
            fine_content_wet,
            coarse_content_wet
        ])

        # Return calculated values
        return {
            'abs_volumes': abs_volumes,
            'contents': contents,
            'volumes': volumes,
            'w_cm': w_cm,
            'total_abs_volume': total_abs_volume,
            'total_content': total_content,
        }

    def _store_adjustment_results(self, mix_proportions):
        """
        Store adjustment results in the data model.

        :param dict mix_proportions: Dictionary containing calculated mix proportions.
        :return: True if data was stored successfully, False otherwise.
        :rtype: bool
        """

        try:
            # Check if air is entrained or entrapped
            entrained_air_flag = self.data_model.get_design_value('field_requirements.entrained_air_content.is_checked')
            scm_flag = self.data_model.get_design_value('cementitious_materials.SCM.SCM_checked')

            # Get necessary values from mix_proportions with safer dictionary access
            abs_volumes = mix_proportions.get('abs_volumes', {})
            contents = mix_proportions.get('contents', {})
            volumes = mix_proportions.get('volumes', {})

            # Define mapping of results to data model paths
            map_results = [
                # Water to cementitious material ratio
                ("trial_mix.adjustments.water_cementitious_materials_ratio.w_cm", mix_proportions.get('w_cm')),

                # Absolute volumes
                ('trial_mix.adjustments.water.water_abs_volume', abs_volumes.get('water_abs_volume')),
                ('trial_mix.adjustments.cementitious_material.cement.cement_abs_volume',
                 abs_volumes.get('cement_abs_volume')),
                ('trial_mix.adjustments.cementitious_material.scm.scm_abs_volume',
                 abs_volumes.get('scm_abs_volume') if scm_flag else None),
                ('trial_mix.adjustments.fine_aggregate.fine_abs_volume', abs_volumes.get('fine_abs_volume')),
                ('trial_mix.adjustments.coarse_aggregate.coarse_abs_volume', abs_volumes.get('coarse_abs_volume')),
                ('trial_mix.adjustments.air.entrapped_air_content',
                 abs_volumes.get('air_volume') if not entrained_air_flag else None),
                ('trial_mix.adjustments.air.entrained_air_content',
                 abs_volumes.get('air_volume') if entrained_air_flag else None),
                ('trial_mix.adjustments.summation.total_abs_volume', mix_proportions.get('total_abs_volume')),

                # Contents
                ('trial_mix.adjustments.water.water_content_correction', contents.get('water_content_correction')),
                ('trial_mix.adjustments.cementitious_material.cement.cement_content', contents.get('cement_content')),
                ('trial_mix.adjustments.cementitious_material.scm.scm_content',
                 contents.get('scm_content') if scm_flag else None),
                ('trial_mix.adjustments.fine_aggregate.fine_content_ssd', contents.get('fine_content_ssd')),
                ('trial_mix.adjustments.fine_aggregate.fine_content_wet', contents.get('fine_content_wet')),
                ('trial_mix.adjustments.coarse_aggregate.coarse_content_ssd', contents.get('coarse_content_ssd')),
                ('trial_mix.adjustments.coarse_aggregate.coarse_content_wet', contents.get('coarse_content_wet')),
                ('trial_mix.adjustments.summation.total_content', mix_proportions.get('total_content')),

                # Volumes
                ('trial_mix.adjustments.water.water_volume', volumes.get('water_volume')),
                ('trial_mix.adjustments.cementitious_material.cement.cement_volume', '-'),
                ('trial_mix.adjustments.cementitious_material.scm.scm_volume', '-'),
                ('trial_mix.adjustments.fine_aggregate.fine_volume', volumes.get('fine_volume')),
                ('trial_mix.adjustments.coarse_aggregate.coarse_volume', volumes.get('coarse_volume')),
            ]

            # First, validate all values before updating the data model
            for key_path, value in map_results:
                # Skip None values (missing or deliberately skipped)
                if value is None:
                    continue

                # Check for invalid numeric values
                if isinstance(value, (int, float)) and value < 0:
                    self.logger.warning(f'Error detected: Value {value} for key "{key_path}" is negative')
                    return False

            # If all validations passed, now update the data model
            for key_path, value in map_results:
                # Skip None values
                if value is None:
                    continue

                # Update the model with valid values
                self.data_model.update_design_data(key_path, value)

            return True

        except Exception as e:
            self.logger.error(f"Failed to store adjustment results: {str(e)}")
            return False

    def _record_adjustments_made(self, adjust_type, adjustments):
        """
        Record all the trial-mix adjustments made by the user into the data model.
        Previous values are preserved by storing them as a list along with the new value.

        :param str adjust_type: Category of adjustment (e.g. "water", "cementitious_material", "aggregate_proportion").
        :param dict[str, any] adjustments: A mapping of field names to values. Values set to None will be skipped.
        """

        # Validate inputs
        valid_types = {
            "water",
            "cementitious_material",
            "aggregate_proportion"
        }
        if adjust_type not in valid_types:
            raise ValueError(
                f"Invalid adjust_type {adjust_type!r}; "
                f"must be one of {sorted(valid_types)}"
            )

        if not isinstance(adjustments, dict):
            raise ValueError("Adjustments must be store in a dict-like mapping of field names to values")

        # Write each non-None value into the data model
        base_path = "adjustments_trial_mix"
        for field_name, value in adjustments.items():
            if value is None:
                # Skip placeholders or missing values
                continue

            # Build the full key path
            key_path = f"{base_path}.{adjust_type}.{field_name}"

            # Get previous value from the data model
            previous_value = self.data_model.get_design_value(key_path)

            # Prepare the new value to store
            if previous_value is None:
                # If no previous value exists, start a new list with the current value
                new_value = [value]
            elif isinstance(previous_value, list):
                # If previous value is already a list, append the new value
                new_value = previous_value + [value]
            else:
                # If previous value exists but is not a list, convert to list with both values
                new_value = [previous_value, value]

            # Record the updated list to the data model
            self.data_model.update_design_data(key_path, new_value)

    def handle_groupBoxes_toggled(self, toggled_box, checked):
        """
        When a group box is toggled on, uncheck all other group boxes in the same group.

        :param toggled_box: The QGroupBox that was toggled.
        :param bool checked: The new checked state.
        """

        if checked:
            # Determine the group to which toggled_box belongs
            if toggled_box in self.group_boxes_1:
                group = self.group_boxes_1
            elif toggled_box in self.group_boxes_2:
                group = self.group_boxes_2
            else:
                group = []

            # Uncheck all other boxes in the same group
            for box in group:
                if box is not toggled_box:
                    box.setChecked(False)

    def handle_pushButton_apply_adjustments_clicked(self):
        """Run the adjustments required by the user, and close the dialog on success."""

        self.logger.info("Applying adjustments...")

        # Read which adjustment group is active
        water_adjustment = self.ui.groupBox_adjust_water.isChecked()
        cementitious_adjustment = self.ui.groupBox_adjust_cementitious.isChecked()
        aggregates_adjustment = self.ui.groupBox_adjust_agg.isChecked()
        coarse_agg_adjustment = self.ui.groupBox_coarse.isChecked()
        fine_agg_adjustment = self.ui.groupBox_fine.isChecked()

        # Read input values
        water_added = self.ui.doubleSpinBox_water_used.value()
        air_measured_1 = self.ui.doubleSpinBox_air_measured.value()
        cementitious_added = self.ui.doubleSpinBox_cementitious_used.value()
        air_measured_2 = self.ui.doubleSpinBox_air_measured_2.value()
        coarse_pct = self.ui.doubleSpinBox_coarse_prop.value()
        fine_pct = self.ui.doubleSpinBox_fine_prop.value()

        # Water adjustment flow
        if water_adjustment:
            # Validate inputs
            if water_added <= 0 or air_measured_1 <= 0:
                QMessageBox.critical(
                    self,
                    "Error al ingresar datos",
                    "La cantidad de agua y el contenido de aire deben ser distintos de cero."
                )
                return

            # Call the adjustment method
            adjustment_applied = self.water_adjustment()

        # Cementitious material adjustment flow
        elif cementitious_adjustment:
            # Validate inputs
            if cementitious_added <= 0 or air_measured_2 <= 0:
                QMessageBox.critical(
                    self,
                    "Error al ingresar datos",
                    "La cantidad de material cementante y el contenido de aire deben ser distintos de cero."
                )
                return

            # Call the adjustment method
            adjustment_applied = self.cementitious_material_adjustment()

        # Aggregate proportion adjustment flow
        elif aggregates_adjustment:
            # Coarse aggregate branch
            if coarse_agg_adjustment:
                if coarse_pct <= 0 or coarse_pct >= 100:
                    QMessageBox.critical(
                        self,
                        "Error al ingresar datos",
                        "El porcentaje de agregado grueso debe ser un valor entre 0 y 100."
                    )
                    return

                # Call the adjustment method
                adjustment_applied = self.aggregates_adjustment("coarse")

            # Fine aggregate branch
            elif fine_agg_adjustment:
                if fine_pct <= 0 or fine_pct >= 100:
                    QMessageBox.critical(
                        self,
                        "Error al ingresar datos",
                        "El porcentaje de agregado fino debe ser un valor entre 0 y 100."
                    )
                    return

                # Call the adjustment method
                adjustment_applied = self.aggregates_adjustment("fine")

            else:
                QMessageBox.critical(
                    self,
                    "Error de selección",
                    "Elija el tipo de agregado a ajustar."
                )
                return

        # No adjustment selected
        else:
            QMessageBox.critical(
                self,
                "Error de selección",
                "Debe seleccionar un tipo de ajuste."
            )
            return

        # Close the dialog if any adjustments were applied successfully
        if adjustment_applied:
            # Calculate the dosages of the chemical admixtures before close the dialog
            self.admixture_dosage()

            self.accept()
            self.logger.info("Adjustments applied successfully. Closing dialog.")
        else:
            QMessageBox.critical(
                self,
                "Error en el ajuste",
                "No fue posible realizar el ajuste del diseño con los datos proporcionados debido a un error de cálculo. "
                "Verifique los valores ingresados y vuelva a intentar el ajuste."
            )
            self.logger.info("An error occurred, adjustments were not applied successfully. Try again")

    def handle_AdjustTrialMixDialog_units_changed(self, units):
        """
        Update fields that depend on the selected unit system.

        :param str units: The system of units to update the fields.
        """

        # Initialize the variables
        unit_suffix = None

        if units == 'SI':
            unit_suffix = 'kg'
        elif units == 'MKS':
            unit_suffix = 'kgf'

        # Update the labels
        self.ui.label_cementitious_used.setText(f"Nueva cantidad ({unit_suffix})")

        self.logger.info(f'A complete update of the unit system to {units} has been made')