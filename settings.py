from pathlib import Path

# -----------------------------------------------------------------------------
# Base Directory
# -----------------------------------------------------------------------------
# Get the project base path (where settings.py file is located)
BASE_DIR = Path(__file__).resolve().parent

# -----------------------------------------------------------------------------
# Log Settings
# -----------------------------------------------------------------------------
LOG_LEVEL = "DEBUG"  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Format of log messages
LOG_FILE = "concretus.log"  # Log file

# -----------------------------------------------------------------------------
# File and Path Settings
# -----------------------------------------------------------------------------
ASSETS_DIR = BASE_DIR / "assets"  # Resources directory (images, icons, etc.)
CORE_DIR = BASE_DIR / "core"  # Core directory
REPORTS_DIR = BASE_DIR / "reports"  # Reports directory
GUI_DIR = BASE_DIR / "gui"  # Graphical interface files directory
TESTS_DIR = BASE_DIR / "tests"  # Tests directory

# Visual media files path
IMAGES_DIR = BASE_DIR / "assets" / "images"

# Icons
ICON_SETTINGS = IMAGES_DIR / "settings.png"
ICON_PRINT = IMAGES_DIR / "print.png"
ICON_EXIT = IMAGES_DIR / "exit.png"
ICON_ABOUT = IMAGES_DIR / "about.png"
ICON_CHECK_DESIGN = IMAGES_DIR / "check_design.png"
ICON_TRIAL_MIX = IMAGES_DIR / "trial_mix.png"

# Images
# IMAGE_LOGO = IMAGES_DIR / "logo.png"
IMAGE_PYQT_LOGO = IMAGES_DIR / "pyqt_logo.png"
IMAGE_ABOUT = IMAGES_DIR / "about_logo.png"

# Styles path
STYLE_PATH = ASSETS_DIR / "styles" / "style.css" # Not implemented yet

# -----------------------------------------------------------------------------
# GUI Settings
# -----------------------------------------------------------------------------
# Application language (es, en, etc.)
LANGUAGES = {
    "es": "Español"
}

# System of units
UNITS_SYSTEM = {
    "MKS": "Sistema Técnico de Unidades",
    "SI": "Sistema Internacional de Unidades"
}

DEFAULT_LANG = "es"
DEFAULT_UNITS = "MKS"

# Default state of the retained percentage column for the grading tables
FINE_RETAINED_COL_STATE = False
COARSE_RETAINED_COL_STATE = False

# -----------------------------------------------------------------------------
# Concrete Mix Design Settings
# -----------------------------------------------------------------------------
# Default ranges for specified concrete strength
MIN_SPEC_STRENGTH = {
    "MKS": {"MCE": 180, "ACI": 150, "DoE": 120},
    "SI": {"MCE": 18, "ACI": 15, "DoE": 12}
}
MAX_SPEC_STRENGTH = {
    "MKS": {"MCE": 430, "ACI": 450, "DoE": 750},
    "SI": {"MCE": 43, "ACI": 45, "DoE": 75}
}

# Default sieves designation (in, mm) for the available methods
SIEVES = {
    "MCE": {
        "fine_sieves": [
            "3/8\" (9,5)",
            "No. 4 (4,75)",
            "No. 8 (2,36)",
            "No. 16 (1,18)",
            "No. 30 (0,600)",
            "No. 50 (0,300)",
            "No. 100 (0,150)",
            "No. 200 (0,075)"
        ],
        "coarse_sieves": [
            "3\" (75)",
            "2-1/2\" (63)",
            "2\" (50)",
            "1-1/2\" (37,5)",
            "1\" (25,0)",
            "3/4\" (19,0)",
            "1/2\" (12,5)",
            "3/8\" (9,5)",
            "1/4\" (6,3)",
            "No. 4 (4,75)",
            "No. 8 (2,36)",
            "No. 16 (1,18)",
            "No. 30 (0,600)",
            "No. 50 (0,300)"
        ]
    },
    "ACI": {
        "fine_sieves": [
            "3/8\" (9,5)",
            "No. 4 (4,75)",
            "No. 8 (2,36)",
            "No. 16 (1,18)",
            "No. 30 (0,600)",
            "No. 50 (0,300)",
            "No. 100 (0,150)",
            "No. 200 (0,075)"
        ],
        "coarse_sieves": [
            "4\" (100)",
            "3-1/2\" (90)",
            "3\" (75)",
            "2-1/2\" (63)",
            "2\" (50)",
            "1-1/2\" (37,5)",
            "1\" (25,0)",
            "3/4\" (19,0)",
            "1/2\" (12,5)",
            "3/8\" (9,5)",
            "No. 4 (4,75)",
            "No. 8 (2,36)",
            "No. 16 (1,18)",
            "No. 50 (0,300)"
        ]
    },
    "DoE": {
        "fine_sieves": [
            "5/16\" (8,0)",
            "1/4\" (6,3)",
            "No. 5 (4,0)",
            "No. 7 (2,8)",
            "No. 10 (2,0)",
            "No. 18 (1,00)",
            "No. 35 (0,500)",
            "No. 60 (0,250)",
            "No. 230 (0,063)"
        ],
        "coarse_sieves": [
            "N/A (80)",
            "2-1/2\" (63)",
            "N/A (40)",
            "1-1/4\" (31,5)",
            "N/A (20,0)",
            "5/8\" (16,0)",
            "N/A (14,0)",
            "N/A (10,0)",
            "5/16\" (8,0)",
            "1/4\" (6,3)",
            "No. 5 (4,00)",
            "No. 7 (2,80)",
            "No. 10 (2,00)",
            "No. 18 (1,00)"
        ]
    }
}

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
# DEBUG_MODE = True  # Debug mode (True or False)
# LANGUAGE = "es"  # Application language (es, en, etc.)