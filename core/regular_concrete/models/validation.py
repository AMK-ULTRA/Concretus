from core.regular_concrete.models.data_model import RegularConcreteDataModel
from logger import Logger
from settings import (COARSE_RANGES, FINE_RANGES, MINIMUM_SPEC_STRENGTH, FINENESS_MODULUS_SIEVES, MAXIMUM_SCM,
                      NMS_BY_CATEGORY, ENTRAINED_AIR, FINENESS_MODULUS_LIMITS)


class Validation:
    def __init__(self, data_model):
        # Connect to the data model
        self.data_model: RegularConcreteDataModel = data_model

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Validation logic is active')

    def calculate_grading_percentages(self):
        """
        Calculate the complementary percentages in the grading of the fine and coarse aggregate.

        If the 'passing_checked' flag is on (True), it calculates:
          - The cumulative retained percentage for each sieve as: 100 - cumulative passing.
          - The individual fraction retained as the difference between consecutive cumulative values.

        If the 'retained_checked' flag is on (True), it calculates:
          - The cumulative retained percentage by summing the individual retained percentages.
          - The cumulative passing percentage as: 100 - cumulative retained.

        It is assumed that the calculations for each aggregate (fine and coarse) are processed independently.
        """

        for aggregate_type in ['fine_aggregate', 'coarse_aggregate']:
            # Retrieve data and flags from the data model.
            passing_checked = self.data_model.get_design_value(f"{aggregate_type}.gradation.passing_checked")
            retained_checked = self.data_model.get_design_value(f"{aggregate_type}.gradation.retained_checked")
            passing_data = self.data_model.get_design_value(f"{aggregate_type}.gradation.passing")
            retained_data = self.data_model.get_design_value(f"{aggregate_type}.gradation.retained")

            # Use a temporary dictionary for cumulative retained values.
            cumulative_retained_data = {}

            # Mode A: If the passing flag is on, derive retained values from passing data.
            if passing_checked:
                # Calculate cumulative retained percentage: for each sieve, it's 100 - passing value.
                for key, passing_value in passing_data.items():
                    if passing_value is not None:
                        cumulative_retained_data[key] = 100 - passing_value
                    else:
                        cumulative_retained_data[key] = None

                # Update the cumulative retained data in the data model.
                self.data_model.update_design_data(f"{aggregate_type}.gradation.cumulative_retained",
                                                   cumulative_retained_data)

                # Calculate the individual fraction retained.
                keys = list(cumulative_retained_data.keys())
                new_retained_data = {}

                # Check that there is at least one key.
                if keys:
                    # Find the first key with a non-None value.
                    first_valid_index = None
                    for i, k in enumerate(keys):
                        if cumulative_retained_data[k] is not None:
                            first_valid_index = i
                            # Set the first valid value in the new dictionary.
                            new_retained_data[k] = cumulative_retained_data[k]
                            break

                    # If a valid value was found, process the subsequent keys.
                    if first_valid_index is not None:
                        # Iterate from the key immediately after the first valid one
                        for i in range(first_valid_index + 1, len(keys)):
                            current = cumulative_retained_data[keys[i]]
                            previous = cumulative_retained_data[keys[i - 1]]
                            # Compute the difference only if both values are valid; otherwise, assign None.
                            if current is not None and previous is not None:
                                new_retained_data[keys[i]] = current - previous
                            else:
                                new_retained_data[keys[i]] = None

                self.data_model.update_design_data(f"{aggregate_type}.gradation.retained", new_retained_data)

            # Mode B: If the retained flag is on, derive passing data from retained values.
            if retained_checked:
                # Calculate the cumulative retained percentage by summing the individual retained percentages.
                cumulative = 0
                new_cumulative_retained_data = {}
                for key, value in retained_data.items():
                    if value is not None:
                        cumulative += value
                        new_cumulative_retained_data[key] = cumulative
                    else:
                        new_cumulative_retained_data[key] = None
                self.data_model.update_design_data(f"{aggregate_type}.gradation.cumulative_retained",
                                                   new_cumulative_retained_data)

                # Calculate the cumulative passing percentage as 100 - cumulative retained.
                new_passing_data = {}
                for key, cum_value in new_cumulative_retained_data.items():
                    if cum_value is not None:
                        new_passing_data[key] = 100 - cum_value
                    else:
                        new_passing_data[key] = None
                self.data_model.update_design_data(f"{aggregate_type}.gradation.passing", new_passing_data)

    def calculate_nominal_maximum_size(self, grading, method=None, coarse_category=None, threshold=95):
        """
        Calculate the Nominal Maximum Size (NMS) of the aggregate based on its particle size distribution.

        This method determines the NMS through two potential approaches:
        1. Category-specific lookup: If a method and coarse category are provided, it checks for a predefined NMS value.
        2. Grading analysis: Finds the smallest sieve size where the specified percentage of particles pass through.

        :param dict[str, float | None] grading: Particle size distribution with sieve sizes as keys and passing
                                       percentages as values. Must be arranged in descending order (from largest to smallest sieve).
        :param str method: Design method used for NMS determination (e.g. "MCE", "ACI", "DoE").
        :param str coarse_category: Coarse aggregate category used for category-specific NMS lookup.
        :param int threshold: The minimum passing percentage that establishes the maximum nominal size (95% by default).
        :return: The nominal maximum size of the aggregate, either from category lookup or
                 the smallest sieve where the threshold percentage is met.
        :rtype: str | None
        """

        # Check for a category-specific NMS (highest priority)
        if method and coarse_category:
            nms_category = NMS_BY_CATEGORY.get(method, {}).get(coarse_category)
            if nms_category is not None:
                self.data_model.update_design_data('coarse_aggregate.NMS', nms_category)
                return nms_category

        # Find the smallest sieve meeting the threshold requirement
        smallest_sieve = None
        for sieve, percentage in grading.items():
            # Skip None values to handle potentially incomplete grading data
            if percentage is not None and percentage >= threshold:
                smallest_sieve = sieve

        # Update data model with the determined NMS
        self.data_model.update_design_data('coarse_aggregate.NMS', smallest_sieve)

        return smallest_sieve

    @staticmethod
    def classify_aggregate(measured_data, range_categories, threshold= 0.95):
        """
        Classify a sieve analysis (for an aggregate) by comparing the measured data with the allowable ranges.

        :param dict[str, float | None] measured_data: Dictionary with measured data (key = sieve name, value = % measured or None).
        :param dict[str, dict] range_categories: Dictionary where keys are categories (e.g. "#0", "#1", etc.)
                                                 and values are dictionaries mapping each sieve requirements.
        :param float threshold: Minimum threshold (between 0 and 1) to consider the category valid.
        :return: The best category (or None if none meet the criteria) and all the remaining categories with corresponding scores.
        :rtype: tuple[str | None, dict]
        """

        scores = {}
        for category, reqs in range_categories.items():
            total = 0  # sieves examined (other than None)
            matches = 0  # sieves approved the requirements

            for sieve, requirement in reqs.items():
                if requirement is None:
                    continue  # Skip the sieve
                total += 1 # Otherwise count it

                measured = measured_data.get(sieve) # Get the measured value for the sieve
                if measured is None:
                    # If there is no value (empty), it is considered to have failed
                    continue
                if isinstance(requirement, tuple):
                    max_val, min_val = requirement
                    if max_val >= measured >= min_val:
                        matches += 1
                else:
                    if measured == requirement:
                        matches += 1

            # Calculate the score for this category
            score = matches / total if total > 0 else 0
            scores[category] = score # Dictionary with the score for each category

        # Find and assign to best_category the key (category) with the highest score,
        # using the lambda function to extract the value of each key and compare them.
        best_category = max(scores, key=lambda c: scores[c])

        if scores[best_category] >= threshold:
            return best_category, scores
        else:
            return None, scores

    def classify_grading(self, method, measured_coarse, measured_fine, threshold=0.95):
        """
        Classify sieve analysis for coarse and fine aggregate, according to the method and predefined range dictionaries.

        :param str method: Design method ("MCE", "ACI", "DoE").
        :param dict measured_coarse: Measured data for coarse aggregate.
        :param dict measured_fine: Measured data for fine aggregate.
        :param float threshold: Minimum threshold to consider the category (default 0.95, i.e. 95%).
        :return: The corresponding category for each sieve analysis, "None" if no requirement was met.
        :rtype: tuple[str | None, str | None]
        """

        # Extract the range dictionaries for the given method
        coarse_ranges = COARSE_RANGES.get(method)
        fine_ranges = FINE_RANGES.get(method)

        if coarse_ranges is None or fine_ranges is None:
            self.logger.warning(f"No ranges were found for the {method} method")
            return None, None

        coarse_category, coarse_scores = self.classify_aggregate(measured_coarse, coarse_ranges, threshold)
        fine_category, fine_scores = self.classify_aggregate(measured_fine, fine_ranges, threshold)

        # Update the data model
        self.data_model.update_design_data('validation.coarse_category', coarse_category)
        self.data_model.update_design_data('validation.fine_category', fine_category)
        self.data_model.update_design_data('validation.coarse_scores', coarse_scores)
        self.data_model.update_design_data('validation.fine_scores', fine_scores)

        if coarse_category is None:
            # Add validation error
            self.data_model.add_validation_error('Grading requirements for coarse aggregate',
                                                 f'Did not meet any requirements: {coarse_scores}')

        if fine_category is None:
            # Add validation error
            self.data_model.add_validation_error('Grading requirements for fine aggregate',
                                                 f'Did not meet any requirements: {fine_scores}')

        if coarse_category and fine_category:
            self.logger.debug(f'The best category for the coarse aggregate grading is {coarse_category}. '
                              f'The calculated scores of all the sieves studied are as follows:')
            self.logger.debug(coarse_scores)
            self.logger.debug(f'The best category for the fine aggregate grading is {fine_category}. '
                              f'The calculated scores of all the sieves studied are as follows:')
            self.logger.debug(fine_scores)

        return fine_category, coarse_category

    @staticmethod
    def calculate_fineness_modulus(sieves, cumulative_retained_grading):
        """
        Calculates the fineness modulus of a fine aggregate based on sieve analysis data.

        :param list[str] sieves: A list of specified series of sieves according to regulations.
        :param dict[str, float | None] cumulative_retained_grading: A dictionary mapping each sieve
                                                                    with its cumulative retained percentage
        :return: The calculated fineness modulus.
        :rtype: float
        """

        # Create a list with the percentage of valid sieves, making sure that if the value is None, 0 is taken
        cumulative_retained = [cumulative_retained_grading.get(sieve, 0) or 0 for sieve in sieves]

        # The fineness modulus is calculated by adding the cumulative percentages (by mass) retained on each
        # of a specified series of sieves and dividing the sum by 100
        return sum(cumulative_retained) / 100

    def required_fineness_modulus(self, method, cumulative_retained_grading):
        """
        Checks if the calculated fineness modulus is within the required range.

        :param str method: The method used for the calculation.
        :param dict[str, float | None] cumulative_retained_grading: A dictionary containing the sieve analysis data
                                                                    (cumulative retained percentage).
        :return: The fineness modulus (rounded to 2 digits) and:
                 - True if the fineness modulus is within the range,
                 - False if the fineness modulus is not within the range,
                 - None if there were no limits for the fineness modulus for the given method.
        :rtype: tuple[float, bool | None]
        """

        # Predefined dictionary with all valid sieves for each method
        sieves = FINENESS_MODULUS_SIEVES.get(method, [])
        # Calculate the fineness modulus
        fineness_modulus = self.calculate_fineness_modulus(sieves, cumulative_retained_grading)

        # Update the data model
        self.data_model.update_design_data('fine_aggregate.fineness_modulus', fineness_modulus)

        # Retrieve the limits according to the method
        fm_max = FINENESS_MODULUS_LIMITS.get(method, {}).get("FM_MAXIMUM")
        fm_min = FINENESS_MODULUS_LIMITS.get(method, {}).get("FM_MINIMUM")

        # If there were no limits for the fineness modulus in the given method
        if fm_max is None and fm_min is None:
            self.logger.debug(f"No limits exits for the fineness modulus for the method {method}")
            return round(fineness_modulus, 2), None

        # Otherwise, check if the calculated fineness modulus is within the required ranges
        if fm_min <= fineness_modulus <= fm_max:
            self.logger.debug("Fineness modulus is within the required range")
            return round(fineness_modulus, 2), True
        else:
            error_message = (
                f"Fineness modulus out of range. "
                f"Minimum: {fm_min}, Maximum: {fm_max}, "
                f"Calculated: {fineness_modulus}"
            )
            # Add validation error
            self.data_model.add_validation_error("Fineness modulus", error_message)
            return round(fineness_modulus, 2), False

    @staticmethod
    def get_max_exposure_value(method, units, exposure_classes):
        """
        Get the most demanding exposure class with its specified minimum compressive strength at 28 days.

        :param str method: Design method ("MCE", "ACI", "DoE")
        :param str units: Unit system ("MKS", "SI")
        :param list exposure_classes: List of exposure classes (e.g. ["S0", "F1", ...])
        :return: The exposure class and its associated value.
        :rtype: tuple[str | None, int | None]
        """

        # Gets the range dictionary for the given method and unit system
        ranges = MINIMUM_SPEC_STRENGTH.get(method, {}).get(units, {})

        max_key = None
        max_value = None

        # Loop through each key and value in the range dictionary
        for key, value in ranges.items():
            # Only consider the keys that are in the list of exposure classes
            if key in exposure_classes:
                # Make sure the value is not None. Otherwise, skip it
                if value is not None:
                    # If a maximum value has not yet been set or the current value is greater
                    if max_value is None or value > max_value:
                        max_value = value
                        max_key = key

        return max_key, max_value

    def required_spec_strength(self, method, spec_strength, exposure_classes):
        """
        Checks if the specified compressive strength meets the minimum requirement
        based on the most demanding exposure class.

        :param str method: The method to retrieve the necessary requirements.
        :param int spec_strength: The specified compressive strength to evaluate.
        :param list exposure_classes: List with the given exposure classes.
        :return: A tuple (boolean_value, required_strength, exposure_class) where:
                 - boolean_value is True if the specified compressive strength is sufficient, False otherwise.
                 - required_strength is the minimum required compressive strength.
                 - exposure_class is the associated exposure class.
        :rtype: tuple[bool | None, int | None, str | None]
        """

        # Retrieve the current unit system from the data model
        units = self.data_model.units

        # Get the most demanding exposure class and its required strength
        exposure_class , required_strength = self.get_max_exposure_value(method, units, exposure_classes)

        if exposure_class is None or required_strength is None:
            self.logger.warning(f"No method is configured or does not exist -> method = {method}")
            return None, None, None

        if spec_strength is None:
            self.logger.warning("Specified compressive strength is None")
            return False, required_strength, exposure_class

        # Check if the current strength meets the requirement
        if spec_strength <  required_strength:
            # Add validation error
            self.data_model.add_validation_error(
                'Minimum specified compressive strength',
                f'The minimum value must be {required_strength} for the exposure class ({exposure_class})')
            return False, required_strength, exposure_class
        else:
            self.logger.debug('The specified compressive strength is greater than the minimum required by regulations')
            return True, required_strength, exposure_class

    @staticmethod
    def get_max_scm_content(method, exposure_classes, scm_type):
        """
        Retrieve the maximum allowed content for a supplementary cementitious material (SCM)

        for a given design method, among a list of exposure classes.
        :param str method: Design method ("MCE", "ACI", "DoE").
        :param list[str] exposure_classes: List of exposure classes (e.g. ["S0", "F0", "W0", "C0"]).
        :param str scm_type: The type of supplementary cementitious material (e.g. "Cemento de escoria").
        :return: The exposure class with the highest SCM content along with that content if found, otherwise None.
        :rtype: tuple[str , int] | None
        """

        # Retrieve the dictionary for the specified design method
        method_data = MAXIMUM_SCM.get(method)
        if method_data is None:
            return None

        max_exposure_class = None
        max_value = None

        # Iterate over each exposure class provided in the list
        for ec in exposure_classes:
            # Retrieve the exposure data for the current exposure class
            exposure_data = method_data.get(ec)
            if exposure_data is None:
                continue  # If the current exposure class is not present, skip it

            # Retrieve the SCM content for the specified SCM type
            value = exposure_data.get(scm_type)
            if value is None:
                continue  # If there's no value for this SCM type, skip it

            # Update the maximum if needed
            if max_value is None or value > max_value:
                max_value = value
                max_exposure_class = ec

        if max_exposure_class is None or max_value is None:
            return None

        return max_exposure_class, max_value

    def required_scm_content(self, method, exposure_classes, scm_type, scm_content):
        """
        Checks if the provided SCM content meets the maximum allowed content for the specified
        design method, a list of exposure classes, and SCM type.

        :param str method: Design method ("MCE", "ACI", "DoE").
        :param list[str] exposure_classes: List of exposure classes (e.g. ["S0", "F0", "W0", "C0"]).
        :param str scm_type: The type of supplementary cementitious material.
        :param int scm_content: The content value to evaluate.
        :return: A tuple (valid, threshold_value) where:
                 - valid is True if scm_content is within the allowed range,
                   False if it exceeds the allowed maximum,
                   or None if no threshold was found.
                 - threshold_value is the maximum allowed SCM content (or 0 if not found).
        :rtype: tuple[bool | None, int]
        """

        result = self.get_max_scm_content(method, exposure_classes, scm_type)
        if result is None:
            self.logger.debug(
                f"There is no required SCM content for method '{method}' with the provided exposure classes.")
            return None, 0

        max_exposure_class = result[0]
        threshold_value = result[1]
        if scm_content > threshold_value:
            # Add validation error
            self.data_model.add_validation_error(
                'Maximum content of supplementary cementitious material (SCM)',
                f"The maximum allowed SCM must be: {threshold_value}% for the given exposure class ({max_exposure_class})."
            )
            return False, threshold_value
        else:
            self.logger.debug("The given SCM content meets the requirements.")
            return True, threshold_value

    @staticmethod
    def get_entrained_air(method, exposure_classes, nms):
        """
        Determine the required minimum entrained air content based on the design method, a list of exposure classes,
        and a given nominal maximum size (NMS).

        :param str method: Design method (e.g. "MCE", "ACI", "DoE").
        :param list[str] exposure_classes: List of exposure classes (e.g. ["S1", "F2", "W0", "S0"] for ACI,
                                           or ["XC1", "XD2", "XF4", "XA2"] for DoE).
        :param str nms: The nominal maximum size used to look up the required value (only for the ACI method).
        :return: A tuple (minimum_entrained_air, exposure_class) where:
                 - minimum_entrained_air is the required entrained air content as a percentage or None if none found.
                 - exposure_class is the governing exposure class or the full list of exposure classes if none have requirements.
        :rtype: tuple[float | None, str | list[str]]
        """

        max_value = None
        max_exposure = None

        # Iterate through the list of exposure classes
        for exposure_class in exposure_classes:
            # Get the entry from ENTRAINED_AIR for the given method and exposure class
            entry = ENTRAINED_AIR.get(method, {}).get(exposure_class)
            if entry is None:
                continue

            # Handle dictionary entries (NMS-based lookup)
            if isinstance(entry, dict):
                result = entry.get(nms)
                if result is not None and (max_value is None or result > max_value):
                    max_value = result
                    max_exposure = exposure_class
            # Handle numeric entries (direct values)
            elif isinstance(entry, (float, int)):
                if max_value is None or entry > max_value:
                    max_value = float(entry)
                    max_exposure = exposure_class

        # Return the result, defaulting to the full exposure list if no matching criteria found
        return (max_value, max_exposure) if max_value is not None else (None, exposure_classes)

    def required_entrained_air(self, method, exposure_classes, nms, entrained_air):
        """
        Checks whether the provided entrained air content meets the required minimum value based on
        the design method, a list of exposure classes, and a given nominal maximum size.

        :param str method: Design method (e.g. "MCE", "ACI", "DoE").
        :param list[str] exposure_classes: List of exposure classes (e.g. ["S1", "F2", "W0", "S0"] for ACI,
                                           or ["XC1", "XD2", "XF4", "XA2"] for DoE).
        :param str nms: The nominal maximum size used to look up the required value (only for the ACI method).
        :param float entrained_air: The entrained air content (in %) to evaluate.
        :return: A tuple (valid, minimum_entrained_air, exposure_class) where:
                 - valid is True if entrained_air meets or exceeds the required minimum,
                   False if it is below the required minimum,
                   or None if no minimum requirement was found.
                 - minimum_entrained_air is the required entrained air content.
                 - exposure_class is the exposure class (or list of exposure classes) associated with the requirement.
        :rtype: tuple[bool | None, float | str, str | list[str]]
        """

        minimum_entrained_air, exposure_used = self.get_entrained_air(method, exposure_classes, nms)

        if minimum_entrained_air is None:
            self.logger.debug(
                f"There is no minimum requirement for entrained air for these exposure classes: {exposure_classes}"
            )
            return None, "N/A", exposure_classes

        if entrained_air < minimum_entrained_air:
            self.data_model.add_validation_error(
                'Minimum entrained air',
                f"Does not meet the minimum for the given exposure class ({exposure_used}). "
                f"Required: {minimum_entrained_air}%."
            )
            return False, minimum_entrained_air, exposure_used
        else:
            self.logger.debug("The given entrained air meets the minimum requirement of the exposure class.")
            return True, minimum_entrained_air, exposure_used