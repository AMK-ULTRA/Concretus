import os

# =======================
# General Settings
# =======================

APP_NAME = "Concretus"
VERSION = "1.0.0"
AUTHOR = "Jesús Rivas"

# =======================
# GUI Settings
# =======================
WINDOW_TITLE = "Concretus - Diseño y Dosificación de Mezclas de Concreto"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_ICON = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')  # Path to the application icon


# =======================
# Application Styles
# =======================
# STYLE_FILE = os.path.join(os.path.dirname(__file__), 'assets', 'style.qss')  # PyQt style file

# =======================
# Concrete Mix Design Settings
# =======================
# DEFAULT_METHOD = "ACI"
# MAX_WATER_CEMENT_RATIO = 0.5
# DEFAULT_AGGREGATE_SIZE = 20

# =======================
# File and Path Settings
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Project base route
# DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'concretus.db')  # Ruta al archivo de base de datos

# =======================
# Log Settings
# =======================
LOG_FILE_CORE = os.path.join(BASE_DIR, 'logs', 'app.log')  # Log file path
print(BASE_DIR)
print(LOG_FILE_CORE)
print(__file__)
print(os.path.abspath(__file__))
print(os.path.dirname(os.path.abspath(__file__)))
