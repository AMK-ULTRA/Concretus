import re

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QVBoxLayout
import pyqtgraph as pg

from core.regular_concrete.models.data_model import RegularConcreteDataModel
from logger import Logger
from settings import COARSE_RANGES, FINE_RANGES

class PlotDialog(QDialog):
    def __init__(self, data_model, aggregate_type, parent=None):
        """
        :param data_model: The data model of the application.
        :param str aggregate_type: "fine" or "coarse", to indicate which type of aggregate to graph.
        """

        super().__init__(parent)
        self.data_model: RegularConcreteDataModel = data_model # Connect to the data model
        self.aggregate_type = aggregate_type
        self.setWindowTitle("Curva granulométrica")
        self.resize(1000, 600)

        # Create a layout
        layout = QVBoxLayout(self)

        # Assign a unique object name to this QDialog
        self.setObjectName("PlotDialog")
        # Set a style sheet for this QDialog only
        self.setStyleSheet("QDialog#PlotDialog { background-color: black; }")

        # Create a PlotWidget from PyQtGraph
        self.plot_widget = pg.PlotWidget()
        # Set a background color
        self.plot_widget.setBackground('k') # Leave the default color
        # Set the x-axis in logarithmic mode.
        self.plot_widget.setLogMode(x=True, y=False)
        # Set axis labels: X as Sieve Opening (mm), Y as Cumulative Passing (%)
        self.plot_widget.getPlotItem().setLabels(bottom="Abertura del cedazo (mm)",
                                                 left="Porcentaje acumulado que pasa (%)")

        # Change axis colors
        # For the X axis
        left_axis = self.plot_widget.getPlotItem().getAxis('left')
        left_axis.setPen(pg.mkPen('w'))  # Change the color of the line and ticks
        left_axis.setTextPen(pg.mkPen('w'))  # Change the color of the labels
        # For the Y axis
        bottom_axis = self.plot_widget.getPlotItem().getAxis('bottom')
        bottom_axis.setPen(pg.mkPen('w')) # Change the color of the line and ticks
        bottom_axis.setTextPen(pg.mkPen('w')) # Change the color of the labels

        # Set the title for the plot
        self.plot_widget.getPlotItem().setTitle("Límites Granulométricos", color='w', size='15pt', bold=True)
        # Add a legend to the PlotItem
        self.plot_widget.getPlotItem().addLegend()
        # Show grid (default)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)  # Grid on both axis

        # Add the PlotWidget to the layout
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # Initialize the logger
        self.logger = Logger(__name__)
        self.logger.info('Plotting dialog initialized')

        # Call plot_curves passing the aggregate type ("fine" or "coarse")
        self.plot_curves(self.aggregate_type)

    @staticmethod
    def get_limits(limits):
        """
        Unpack a dictionary with upper and lower ranges for a specific aggregate denomination into two new dictionaries,
        one with the upper bounds and the other with the lower bounds.

        :param limits: A dictionary with allowed ranges for the passing percentage (grading limits). The values can be
                       either a tuple (upper, lower) or a single numeric value (interpreted as both upper and lower).
        :return: Two dictionaries, one with the upper bounds and the other with the lower bounds.
        :rtype: tuple[dict[str, int], dict[str, int]]
        """

        # Dictionaries to be returned
        upper_limits = {}
        lower_limits = {}

        for sieve, value in limits.items():
            if value is None:
                continue  # Skip null values

            # Handling simple values and tuples
            if isinstance(value, tuple):
                upper_limits[sieve] = value[0]
                lower_limits[sieve] = value[1]
            else:
                upper_limits[sieve] = value
                lower_limits[sieve] = value

        return upper_limits, lower_limits

    @staticmethod
    def parse_sieve_opening(key):
        """
        Extract the numeric sieve opening from the key string.

        :param str key: The sieve designation, as a string (e.g. '3/8" (9,5 mm)').
        :return: The sieve size, in mm. (e.g. '3/8" (9,5 mm)' -> 9.5).
        :rtype: float | None
        """

        # This regex captures a number (with comma or dot) inside parentheses before "mm".
        match = re.search(r'\(.*?(\d+([,.]\d+)?)', key)
        if match:
            num_str = match.group(1).replace(',', '.')
            try:
                return float(num_str)
            except ValueError:
                return None
        return None

    def get_sorted_xy(self, curve):
        """
        Converts a dictionary of the form {"sieve size (mm)": "passing %"} into a tuple
        containing two lists:

        1. Sieves: A list of sieve sizes in millimeters as floats, sorted in ascending order.
        2. Passing percentages: A list of corresponding passing percentages as floats,
           sorted in ascending order.

        :param dict curve: A dictionary where keys are sieve sizes in the format "sieve size (mm)"
                           (e.g., '3/8" (9,5 mm)') and values are passing percentages (e.g., 25.5).
        :return: A tuple containing two lists:
                 [sieve_sizes (list of floats)], [passing_percentages (list of floats)]
        :rtype: tuple[list, list]
        """

        data = []
        for key, percent in curve.items():
            sieve_opening = self.parse_sieve_opening(key)
            if sieve_opening is not None and percent is not None:
                data.append((sieve_opening, percent))
        data.sort(key=lambda tup: tup[0])
        self.logger.debug(data)

        return zip(*data) if data else ([], [])

    def plot_curves(self, aggregate_type):
        """
        Plot curves for the given aggregate type. Reads data from the data model
        depending on whether aggregate_type is "fine" or "coarse".

        :param str aggregate_type: The type of aggregate to plot ("fine" or "coarse").
        """

        method = self.data_model.method

        # Retrieve data from the data model depending on aggregate type
        if aggregate_type == 'fine':
            passing_data = self.data_model.get_design_value('fine_aggregate.gradation.passing')
            scores = self.data_model.get_design_value('validation.fine_scores')
        elif aggregate_type == 'coarse':
            passing_data = self.data_model.get_design_value('coarse_aggregate.gradation.passing')
            scores = self.data_model.get_design_value('validation.coarse_scores')
        else:
            self.logger.error(f"Unknown aggregate type: {aggregate_type}")
            return

        # Ensure that scores and passing_data are available
        if not scores or not passing_data:
            self.logger.error("Missing scores or passing grading from the data model.")
            return

        # Determine the identifier with the highest score
        max_score = 0
        identifier = None
        for name, score in scores.items():
            if score >= max_score:
                max_score = score
                identifier = name

        if identifier is None:
            self.logger.error("No valid identifier found in scores.")
            return

        # Retrieve the limits dictionary according to the identifier
        if aggregate_type == 'fine':
            limits = FINE_RANGES.get(method, {}).get(identifier)
        elif aggregate_type == 'coarse':
            limits = COARSE_RANGES.get(method, {}).get(identifier)
        else:
            limits = None

        if limits is None:
            self.logger.error(f"No limits found for {method} and identifier {identifier}")
            return

        # Get upper and lower limits as separate dictionaries
        upper_limits, lower_limits = self.get_limits(limits)

        # Prepare the curves to plot: passing data and limits.
        curves = [passing_data, upper_limits, lower_limits]
        names = [identifier, f'{identifier} (límite superior)', f'{identifier} (límite inferior)']
        colors = ['g', 'r', 'r']
        styles = [QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenStyle.DotLine, QtCore.Qt.PenStyle.DotLine]

        # Plot each curve.
        for curve, name, color, style in zip(curves, names, colors, styles):
            self.logger.info('************PLOTTING************')

            x_vals, y_vals = self.get_sorted_xy(curve) # Convert a curve dictionary into sorted x and y lists
            if not x_vals:  # If the list is empty, the curve is skipped.
                continue
            self.plot_widget.plot(
                x=list(x_vals),
                y=list(y_vals),
                pen=pg.mkPen(color=color, width=2, style=style),
                symbol='+',
                symbolSize=12,
                symbolBrush='w',
                symbolPen='k',
                name=name
            )