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
STYLE_PATH = ASSETS_DIR / "styles" # Style directory

# Visual media files path
IMAGES_DIR = BASE_DIR / "assets" / "images"

# Icons
ICON_LOGO = IMAGES_DIR / "logo.ico"
ICON_SETTINGS = IMAGES_DIR / "settings.png"
ICON_PRINT = IMAGES_DIR / "print.png"
ICON_RESTART = IMAGES_DIR / "restart.png"
ICON_EXIT = IMAGES_DIR / "exit.png"
ICON_REGULAR_CONCRETE = IMAGES_DIR / "regular_concrete.png"
ICON_CHECK_DESIGN = IMAGES_DIR / "check_design.png"
ICON_TRIAL_MIX = IMAGES_DIR / "trial_mix.png"
ICON_ADJUST_TRIAL_MIX = IMAGES_DIR / "adjust_trial_mix.png"
ICON_ADJUST_MATERIALS = IMAGES_DIR / "adjust_materials.png"
ICON_ADJUST_ADMIXTURES = IMAGES_DIR / "adjust_admixtures.png"
ICON_GET_BACK_DESIGN = IMAGES_DIR / "get_back_design"
ICON_HELP_MANUAL = IMAGES_DIR / "help_manual.png"
ICON_ABOUT = IMAGES_DIR / "about.png"

# Images
IMAGE_PYQT_LOGO = IMAGES_DIR / "pyqt_logo.png"
IMAGE_LOGO = IMAGES_DIR / "logo.png"

# Styles
VALID_STYLE = STYLE_PATH / "valid.css"
INVALID_STYLE = STYLE_PATH / "invalid.css"

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
# DEBUG_MODE = True  # Debug mode (True or False)
# LANGUAGE = "es"  # Application language (es, en, etc.)

# -----------------------------------------------------------------------------
# GUI Settings
# -----------------------------------------------------------------------------
# Application language (es, en, etc.)
LANGUAGES = {
    "es": "Español"
}

# System of units
UNIT_SYSTEM = {
    "MKS": "Sistema Técnico de Unidades",
    "SI": "Sistema Internacional de Unidades"
}

DEFAULT_LANGUAGE_KEY = "es"
DEFAULT_UNITS_KEY = "MKS"
INITIAL_STEP = 0

# Default ranges for entering the specified compressive strength
MIN_SPEC_STRENGTH = {
    "MKS": {"MCE": 180, "ACI": 170, "DoE": 120},
    "SI": {"MCE": 18, "ACI": 17, "DoE": 12}
}
MAX_SPEC_STRENGTH = {
    "MKS": {"MCE": 430, "ACI": 450, "DoE": 750},
    "SI": {"MCE": 43, "ACI": 45, "DoE": 75}
}

# -----------------------------------------------------------------------------
# Regular Concrete Design Settings
# -----------------------------------------------------------------------------
# Default sieves designation (in, mm) for the available methods
SIEVES = {
    "MCE": {
        "fine_sieves": [
            '3/8" (9,5 mm)',
            '1/4" (6,3 mm)',
            "No. 4 (4,75 mm)",
            "No. 8 (2,36 mm)",
            "No. 16 (1,18 mm)",
            "No. 30 (0,600 mm)",
            "No. 50 (0,300 mm)",
            "No. 100 (0,150 mm)",
            "No. 200 (0,075 mm)"
        ],
        "coarse_sieves": [
            '3-1/2" (90 mm)',
            '3" (75 mm)',
            '2-1/2" (63 mm)',
            '2" (50 mm)',
            '1-1/2" (37,5 mm)',
            '1" (25 mm)',
            '3/4" (19 mm)',
            '1/2" (12,5 mm)',
            '3/8" (9,5 mm)',
            '1/4" (6,3 mm)',
            "No. 4 (4,75 mm)",
            "No. 8 (2,36 mm)",
            "No. 16 (1,18 mm)",
            "No. 30 (0,600 mm)",
            "No. 50 (0,300 mm)"
        ]
    },
    "ACI": {
        "fine_sieves": [
            '3/8" (9,5 mm)',
            "No. 4 (4,75 mm)",
            "No. 8 (2,36 mm)",
            "No. 16 (1,18 mm)",
            "No. 30 (0,600 mm)",
            "No. 50 (0,300 mm)",
            "No. 100 (0,150 mm)",
            "No. 200 (0,075 mm)"
        ],
        "coarse_sieves": [
            '4" (100 mm)',
            '3-1/2" (90 mm)',
            '3" (75 mm)',
            '2-1/2" (63 mm)',
            '2" (50 mm)',
            '1-1/2" (37,5 mm)',
            '1" (25 mm)',
            '3/4" (19 mm)',
            '1/2" (12,5 mm)',
            '3/8" (9,5 mm)',
            "No. 4 (4,75 mm)",
            "No. 8 (2,36 mm)",
            "No. 16 (1,18 mm)",
            "No. 50 (0,300 mm)"
        ]
    },
    "DoE": {
        "fine_sieves": [
            '5/16" (8 mm)',
            '1/4" (6,3 mm)',
            "No. 5 (4 mm)",
            "No. 7 (2,8 mm)",
            "No. 10 (2 mm)",
            "No. 18 (1 mm)",
            "No. 30 (0,600 mm)",
            "No. 35 (0,500 mm)",
            "No. 60 (0,250 mm)",
            "No. 120 (0,125 mm)",
            "No. 230 (0,063 mm)"
        ],
        "coarse_sieves": [
            "N/A (80 mm)",
            '2-1/2" (63 mm)',
            "N/A (40 mm)",
            '1-1/4" (31,5 mm)',
            "N/A (20 mm)",
            '5/8" (16 mm)',
            "N/A (14 mm)",
            "N/A (10 mm)",
            '5/16" (8 mm)',
            '1/4" (6,3 mm)',
            "No. 5 (4 mm)",
            "No. 7 (2,8 mm)",
            "No. 10 (2 mm)",
            "No. 18 (1 mm)"
        ]
    }
}

# Default state of the retained percentage column for the grading tables
FINE_RETAINED_STATE = False
COARSE_RETAINED_STATE = False

# Minimum specified compressive strength according to the exposure class
MINIMUM_SPEC_STRENGTH = {
    "MCE": {
        "MKS": {
            "Agua dulce" : 260,
		    "Agua salobre o de mar": 300,
		    "Moderada": 260,
		    "Severa": 300,
		    "Muy severa": 300,
            "Alta": 180,
            "Atmósfera común": 180,
            "Litoral": 180,
        },
        "SI": {
            "Agua dulce" : 26,
		    "Agua salobre o de mar": 30,
		    "Moderada": 26,
		    "Severa": 30,
		    "Muy severa": 30,
            "Alta": 18,
            "Atmósfera común": 18,
            "Litoral": 18,
        }
    },
    "ACI": {
        "MKS": {
            "S0": 170,
            "S1": 280,
            "S2": 310,
            "S3": 350,
            "F0": 170,
            "F1": 240,
            "F2": 310,
            "F3": 350,
            "W0": 170,
            "W1": 170,
            "W2": 280,
            "C0": 170,
            "C1": 170,
            "C2": 350
        },
        "SI": {
            "S0": 17,
            "S1": 28,
            "S2": 31,
            "S3": 35,
            "F0": 17,
            "F1": 24,
            "F2": 31,
            "F3": 35,
            "W0": 17,
            "W1": 17,
            "W2": 28,
            "C0": 17,
            "C1": 17,
            "C2": 35
        }
    },
    "DoE": {
        "MKS": {
            "N/A": 120,
	        "XC1": 200,
	        "XC2": 250,
	        "XC3": 300,
	        "XC4": 300,
	        "XS1": 300,
	        "XS2": 350,
	        "XS3": 350,
	        "XD1": 300,
	        "XD2": 300,
	        "XD3": 350,
	        "XF1": 300,
	        "XF2": 250,
	        "XF3": 300,
	        "XF4": 300,
	        "XA1": 300,
	        "XA2": 300,
	        "XA3": 350
        },
        "SI": {
            "N/A": 12,
	        "XC1": 20,
	        "XC2": 25,
	        "XC3": 30,
	        "XC4": 30,
	        "XS1": 30,
	        "XS2": 35,
	        "XS3": 35,
	        "XD1": 30,
	        "XD2": 30,
	        "XD3": 35,
	        "XF1": 30,
	        "XF2": 25,
	        "XF3": 30,
	        "XF4": 30,
	        "XA1": 30,
	        "XA2": 30,
	        "XA3": 35
        }
    }
}

# Type of cement required according to sulfate exposure
CEMENT_TYPE = {
    "MCE": {
        "Moderada": ["Tipo II", "Tipo V"],
        "Severa": ["Tipo V"],
        "Muy severa": ["Tipo V"]
    },
    "ACI": {
        "S1": ["Tipo II", "Tipo IIA", "Tipo V"],
        "S2": ["Tipo V"],
        "S3": ["Tipo V"]
    },
    "DoE": {
        "XA2": ["CEM I (SR)", "CEM III (SR)", "CEM IV (SR)"],
        "XA3": ["CEM I (SR)", "CEM III (SR)", "CEM IV (SR)"]
    },
}

# Allowed ranges for the passing percentage (grading limits) according to COVENIN 0277-2021 (MCE),
# ASTM C33-C33M (23) (ACI) and PD 6682-1-2009 (DoE)
# KEEP THE FOLLOWING FORMAT -> (upper limit, lower limit) | When both limits are equal, simply write the number

COARSE_RANGES = {
    "MCE": {
        "Nro. 0": {
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': 100,
            '1/2" (12,5 mm)': (100, 80),
            '3/8" (9,5 mm)': (85, 50),
            '1/4" (6,3 mm)': (60, 25),
            "No. 4 (4,75 mm)": (40, 15),
            "No. 8 (2,36 mm)": (20, 5),
            "No. 16 (1,18 mm)": (10, 0),
            "No. 30 (0,600 mm)": (5, 0),
            "No. 50 (0,300 mm):": None
    },
        "Nro. 1": {
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': (100, 90),
            '3/4" (19 mm)': (90, 50),
            '1/2" (12,5 mm)': (45, 15),
            '3/8" (9,5 mm)': (20, 0),
            '1/4" (6,3 mm)': (7, 0),
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 50 (0,300 mm):": None
    },
        "Nro. 2": {
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': (100, 95),
            '1-1/2" (37,5 mm)': (90, 75),
            '1" (25 mm)': (70, 35),
            '3/4" (19 mm)': (30, 5),
            '1/2" (12,5 mm)': (10, 0),
            '3/8" (9,5 mm)': (5, 0),
            '1/4" (6,3 mm)': None,
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 50 (0,300 mm):": None
    },
        "Nro. 3": {
            '3" (75 mm)': 100,
            '2-1/2" (63 mm)': (100, 90),
            '2" (50 mm)': (95, 65),
            '1-1/2" (37,5 mm)': (60, 20),
            '1" (25 mm)': (10, 0),
            '3/4" (19 mm)': (5, 0),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 50 (0,300 mm):": None
    }
    },
    "ACI": {
        "1": {
            '4" (100 mm)': 100,
            '3-1/2" (90 mm)': (100, 90),
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': (60, 25),
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': (15, 0),
            '1" (25 mm)': None,
            '3/4" (19 mm)': (5, 0),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': None,
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "2": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': 100,
            '2-1/2" (63 mm)': (100, 90),
            '2" (50 mm)': (70, 35),
            '1-1/2" (37,5 mm)': (15, 0),
            '1" (25 mm)': None,
            '3/4" (19 mm)': (5, 0),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': None,
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "3": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': 100,
            '2" (50 mm)': (100, 90),
            '1-1/2" (37,5 mm)': (70, 35),
            '1" (25 mm)': (15, 0),
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': (5, 0),
            '3/8" (9,5 mm)': None,
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "357": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': 100,
            '2" (50 mm)': (100, 95),
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': (70, 35),
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': (30, 10),
            '3/8" (9,5 mm)': None,
            "No. 4 (4,75 mm)": (5, 0),
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "4": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': 100,
            '1-1/2" (37,5 mm)': (100, 90),
            '1" (25 mm)': (55, 20),
            '3/4" (19 mm)': (15, 0),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': (5, 0),
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "467": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': 100,
            '1-1/2" (37,5 mm)': (100, 95),
            '1" (25 mm)': None,
            '3/4" (19 mm)': (70, 35),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': (30, 10),
            "No. 4 (4,75 mm)": (5, 0),
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "5": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': (100, 90),
            '3/4" (19 mm)': (55, 20),
            '1/2" (12,5 mm)': (10, 0),
            '3/8" (9,5 mm)': (5, 0),
            "No. 4 (4,75 mm)": None,
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "56": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': (100, 90),
            '3/4" (19 mm)': (85, 40),
            '1/2" (12,5 mm)': (40, 10),
            '3/8" (9,5 mm)': (15, 0),
            "No. 4 (4,75 mm)": (5, 0),
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "57": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': 100,
            '1" (25 mm)': (100, 95),
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': (60, 25),
            '3/8" (9,5 mm)': None,
            "No. 4 (4,75 mm)": (10, 0),
            "No. 8 (2,36 mm)": (5, 0),
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "6": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': 100,
            '3/4" (19 mm)': (100, 90),
            '1/2" (12,5 mm)': (55, 20),
            '3/8" (9,5 mm)': (15, 0),
            "No. 4 (4,75 mm)": (5, 0),
            "No. 8 (2,36 mm)": None,
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "67": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': 100,
            '3/4" (19 mm)': (100, 90),
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': (55, 20),
            "No. 4 (4,75 mm)": (10, 0),
            "No. 8 (2,36 mm)": (5, 0),
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "7": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': 100,
            '1/2" (12,5 mm)': (100, 90),
            '3/8" (9,5 mm)': (70, 40),
            "No. 4 (4,75 mm)": (15, 0),
            "No. 8 (2,36 mm)": (5, 0),
            "No. 16 (1,18 mm)": None,
            "No. 50 (0,300 mm):": None
        },
        "8": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': 100,
            '3/8" (9,5 mm)': (100, 85),
            "No. 4 (4,75 mm)": (30, 10),
            "No. 8 (2,36 mm)": (10, 0),
            "No. 16 (1,18 mm)": (5, 0),
            "No. 50 (0,300 mm):": None
        },
        "89": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': 100,
            '3/8" (9,5 mm)': (100, 90),
            "No. 4 (4,75 mm)": (55, 20),
            "No. 8 (2,36 mm)": (30, 5),
            "No. 16 (1,18 mm)": (10, 0),
            "No. 50 (0,300 mm):": (5, 0)
        },
        "9": {
            '4" (100 mm)': None,
            '3-1/2" (90 mm)': None,
            '3" (75 mm)': None,
            '2-1/2" (63 mm)': None,
            '2" (50 mm)': None,
            '1-1/2" (37,5 mm)': None,
            '1" (25 mm)': None,
            '3/4" (19 mm)': None,
            '1/2" (12,5 mm)': None,
            '3/8" (9,5 mm)': 100,
            "No. 4 (4,75 mm)": (100 ,85),
            "No. 8 (2,36 mm)": (40, 10),
            "No. 16 (1,18 mm)": (10 , 0),
            "No. 50 (0,300 mm):": (5, 0)
        }
    },
    "DoE": {
        "4/40 (GC 90/15)": {
            "N/A (80 mm)": 100,
            '2-1/2" (63 mm)': (100, 98),
            "N/A (40 mm)": (99, 90),
            '1-1/4" (31,5 mm)': None,
            "N/A (20 mm)": (70, 25),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": None,
            "N/A (10 mm)": None,
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": (15, 0),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": (5, 0),
            "No. 18 (1 mm)": None
        },
        "4/20 (GC 90/15)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": 100,
            '1-1/4" (31,5 mm)': (100, 98),
            "N/A (20 mm)": (99, 90),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": None,
            "N/A (10 mm)": (70, 25),
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": (15, 0),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": (5, 0),
            "No. 18 (1 mm)": None
        },
        "2/14 (GC 90/15)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": None,
            '1-1/4" (31,5 mm)': 100,
            "N/A (20 mm)": (100, 98),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": (99, 90),
            "N/A (10 mm)": None,
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': (70, 25),
            "No. 5 (4 mm)": None,
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": (15, 0),
            "No. 18 (1 mm)": (5, 0)
        },
        "20/40 (GC 85/20)": {
            "N/A (80 mm)": 100,
            '2-1/2" (63 mm)': (100, 98),
            "N/A (40 mm)": (99, 85),
            '1-1/4" (31,5 mm)': None,
            "N/A (20 mm)": (20, 0),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": None,
            "N/A (10 mm)": (5, 0),
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": None,
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": None,
            "No. 18 (1 mm)": None
        },
        "10/20 (GC 85/20)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": 100,
            '1-1/4" (31,5 mm)': (100, 98),
            "N/A (20 mm)": (99, 85),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": None,
            "N/A (10 mm)": (20, 0),
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": (5, 0),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": None,
            "No. 18 (1 mm)": None
        },
        "6.3/14 (GC 85/20)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": None,
            '1-1/4" (31,5 mm)': 100,
            "N/A (20 mm)": (100, 98),
            '5/8" (16 mm)': None,
            "N/A (14 mm)": (99, 85),
            "N/A (10 mm)": None,
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': (20, 0),
            "No. 5 (4 mm)": None,
            "No. 7 (2,8 mm)": (5, 0),
            "No. 10 (2 mm)": None,
            "No. 18 (1 mm)": None
        },
        "4/10 (GC 85/20)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": None,
            '1-1/4" (31,5 mm)': None,
            "N/A (20 mm)": 100,
            '5/8" (16 mm)': None,
            "N/A (14 mm)": (100, 98),
            "N/A (10 mm)": (99, 85),
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": (20, 0),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": (5, 0),
            "No. 18 (1 mm)": None
        },
        "2/6.3 (GC 80/20)": {
            "N/A (80 mm)": None,
            '2-1/2" (63 mm)': None,
            "N/A (40 mm)": None,
            '1-1/4" (31,5 mm)': None,
            "N/A (20 mm)": None,
            '5/8" (16 mm)': None,
            "N/A (14 mm)": 100,
            "N/A (10 mm)": (100, 98),
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': (99, 80),
            "No. 5 (4 mm)": None,
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": (20, 0),
            "No. 18 (1 mm)": (5, 0)
        }
    }
} # Coarse aggregate
FINE_RANGES = {
    "MCE": {
        "Gruesa": {
            '3/8" (9,5 mm)': 100,
            '1/4" (6,3 mm)': (100, 85),
            "No. 4 (4,75 mm)": (95, 70),
            "No. 8 (2,36 mm)": (70, 40),
            "No. 16 (1,18 mm)": (50, 25),
            "No. 30 (0,600 mm)": (32, 15),
            "No. 50 (0,300 mm)": (20, 5),
            "No. 100 (0,150 mm)": (10, 0),
            "No. 200 (0,075 mm)": (2.5, 0)
        },
        "Media": {
            '3/8" (9,5 mm)': 100,
            '1/4" (6,3 mm)': (100, 85),
            "No. 4 (4,75 mm)": (100, 75),
            "No. 8 (2,36 mm)": (90, 55),
            "No. 16 (1,18 mm)": (75, 38),
            "No. 30 (0,600 mm)": (55, 20),
            "No. 50 (0,300 mm)": (35, 10),
            "No. 100 (0,150 mm)": (20, 6),
            "No. 200 (0,075 mm)": (5, 0)
        },
        "Fino": {
            '3/8" (9,5 mm)': 100,
            '1/4" (6,3 mm)': 100,
            "No. 4 (4,75 mm)": (100, 95),
            "No. 8 (2,36 mm)": (99, 85),
            "No. 16 (1,18 mm)": (95, 70),
            "No. 30 (0,600 mm)": (85, 48),
            "No. 50 (0,300 mm)": (60, 30),
            "No. 100 (0,150 mm)": (30, 12),
            "No. 200 (0,075 mm)": (5, 1)
        },
        "Muy finas": {
            '3/8" (9,5 mm)': 100,
            '1/4" (6,3 mm)': 100,
            "No. 4 (4,75 mm)": 100,
            "No. 8 (2,36 mm)": 100,
            "No. 16 (1,18 mm)": (100, 95),
            "No. 30 (0,600 mm)": (100, 85),
            "No. 50 (0,300 mm)": (85, 40),
            "No. 100 (0,150 mm)": (35, 8),
            "No. 200 (0,075 mm)": (8, 0)
        },
    },
    "ACI": {
        "ASTM C33": {
            '3/8" (9,5 mm)': 100,
            "No. 4 (4,75 mm)": (100, 95),
            "No. 8 (2,36 mm)": (100, 80),
            "No. 16 (1,18 mm)": (85, 50),
            "No. 30 (0,600 mm)": (60, 25),
            "No. 50 (0,300 mm)": (30, 5),
            "No. 100 (0,150 mm)": (10, 0),
            "No. 200 (0,075 mm)": (3, 0)
        }
    },
    "DoE": {
        "0/4 (CP) [GF 85]": {
            '5/16" (8 mm)': 100,
            '1/4" (6,3 mm)': (100, 95),
            "No. 5 (4 mm)": (99, 85),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": None,
            "No. 18 (1 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 35 (0,500 mm)": (45, 5),
            "No. 60 (0,250 mm)": None,
            "No. 230 (0,063 mm)": None
        },
        "0/4 (MP) [GF 85]": {
            '5/16" (8 mm)': 100,
            '1/4" (6,3 mm)': (100, 95),
            "No. 5 (4 mm)": (99, 85),
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": None,
            "No. 18 (1 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 35 (0,500 mm)": (70, 30),
            "No. 60 (0,250 mm)": None,
            "No. 230 (0,063 mm)": None
        },
        "0/2 (MP) [GF 85]": {
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": 100,
            "No. 7 (2,8 mm)": (100, 95),
            "No. 10 (2 mm)": (99, 85),
            "No. 18 (1 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 35 (0,500 mm)": (70, 30),
            "No. 60 (0,250 mm)": None,
            "No. 230 (0,063 mm)": None
        },
        "0/2 (FP) [GF 85]": {
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": 100,
            "No. 7 (2,8 mm)": (100, 95),
            "No. 10 (2 mm)": (99, 85),
            "No. 18 (1 mm)": None,
            "No. 30 (0,600 mm)": None,
            "No. 35 (0,500 mm)": (100, 55),
            "No. 60 (0,250 mm)": None,
            "No. 230 (0,063 mm)": None
        },
        "0/1 (FP) [GF 85]": {
            '5/16" (8 mm)': None,
            '1/4" (6,3 mm)': None,
            "No. 5 (4 mm)": None,
            "No. 7 (2,8 mm)": None,
            "No. 10 (2 mm)": 100,
            "No. 18 (1 mm)": (99, 85),
            "No. 30 (0,600 mm)": None,
            "No. 35 (0,500 mm)": (100, 55),
            "No. 60 (0,250 mm)": None,
            "No. 230 (0,063 mm)": None
        }
    }
} # Fine aggregate

# Threshold values for the fineness modulus
FINENESS_MODULUS_LIMITS = {
    "MCE": {
        "FM_MINIMUM": None,
        "FM_MAXIMUM": None
    },
    "ACI": {
        "FM_MINIMUM": 2.30,
        "FM_MAXIMUM": 3.10
    },
    "DoE": {
        "FM_MINIMUM": None,
        "FM_MAXIMUM": None
    },
}

# Sieves for calculating fineness modulus
FINENESS_MODULUS_SIEVES = {
    "MCE": [
        '3" (75 mm)',
        '1-1/2" (37,5 mm)',
        '3/4" (19 mm)',
        '3/8" (9,5 mm)',
        "No. 4 (4,75 mm)",
        "No. 8 (2,36 mm)",
        "No. 16 (1,18 mm)",
        "No. 30 (0,600 mm)",
        "No. 50 (0,300 mm)",
        "No. 100 (0,150 mm)"
    ],
    "ACI": [
        '3" (75 mm)',
        '1-1/2" (37,5 mm)',
        '3/4" (19 mm)',
        '3/8" (9,5 mm)',
        "No. 4 (4,75 mm)",
        "No. 8 (2,36 mm)",
        "No. 16 (1,18 mm)",
        "No. 30 (0,600 mm)",
        "No. 50 (0,300 mm)",
        "No. 100 (0,150 mm)"
    ],
    "DoE": [
        "No. 5 (4 mm)",
        "No. 10 (2 mm)",
        "No. 18 (1 mm)",
        "No. 35 (0,500 mm)",
        "No. 60 (0,250 mm)",
        "No. 120 (0,125 mm)"
    ],
}

# Maximum SCM content (by percentage) according to the exposure class and type of SCMs
MAXIMUM_SCM = {
    "MCE": None,
    "ACI": {
        "F3": {
            "Cenizas volantes": 25,
	        "Cemento de escoria": 50,
	        "Humo de sílice": 10
        }
    },
    "DoE": None
}

# Minimum entrained air content (by percentage) according to the exposure class
# Only applies to concrete exposed to cycles of freezing and thawing
ENTRAINED_AIR = {
    "MCE": None,
    "ACI": { # For ACI method, the maximum nominal aggregate size is required
        "F1": {
            '3-1/2" (90 mm)': 3.43, # It was not originally stipulated, it was obtained by interpolation
            '3" (75 mm)': 3.50,
            '2-1/2" (63 mm)': 3.74, # It was not originally stipulated, it was obtained by interpolation
            '2" (50 mm)': 4.00,
            '1-1/2" (37,5 mm)': 4.50,
            '1" (25 mm)': 4.50,
            '3/4" (19 mm)': 5.00,
            '1/2" (12,5 mm)': 5.50,
            '3/8" (9,5 mm)': 6.00
        },
        "F2": {
            '3-1/2" (90 mm)': 4.35, # It was not originally stipulated, it was obtained by interpolation
            '3" (75 mm)': 4.50,
            '2-1/2" (63 mm)': 4.74, # It was not originally stipulated, it was obtained by interpolation
            '2" (50 mm)': 5.00,
            '1-1/2" (37,5 mm)': 5.50,
            '1" (25 mm)': 6.00,
            '3/4" (19 mm)': 6.00,
            '1/2" (12,5 mm)': 7.00,
            '3/8" (9,5 mm)': 7.50
        },
        "F3": {
            '3-1/2" (90 mm)': 4.35, # It was not originally stipulated, it was obtained by interpolation
            '3" (75 mm)': 4.50,
            '2-1/2" (63 mm)': 4.74, # It was not originally stipulated, it was obtained by interpolation
            '2" (50 mm)': 5.00,
            '1-1/2" (37,5 mm)': 5.50,
            '1" (25 mm)': 6.00,
            '3/4" (19 mm)': 6.00,
            '1/2" (12,5 mm)': 7.00,
            '3/8" (9,5 mm)': 7.50
        }
    },
    "DoE": {
        "XF2": 4.00,
        "XF3": 4.00,
        "XF4": 4.00
    }
}

# Nominal maximum size of coarse aggregate according to its category (classification)
NMS_BY_CATEGORY = {
    "MCE": {
        "Nro. 0": '1/2" (12,5 mm)',
        "Nro. 1": '1" (25 mm)',
        "Nro. 2": '2" (50 mm)',
        "Nro. 3": '2" (50 mm)'
    },
    "ACI": {
        "1": '3-1/2" (90 mm)',
        "2": '2-1/2" (63 mm)',
        "3": '2" (50 mm)',
        "357": '2" (50 mm)',
        "4": '1-1/2" (37,5 mm)',
        "467": '1-1/2" (37,5 mm)',
        "5": '1" (25 mm)',
        "56": '1" (25 mm)',
        "57": '1" (25 mm)',
        "6": '3/4" (19 mm)',
        "67": '3/4" (19 mm)',
        "7": '1/2" (12,5 mm)',
        "8": '3/8" (9,5 mm)',
        "89": '3/8" (9,5 mm)',
        "9": "No. 4 (4,75 mm)"
    },
    "DoE": {
        "4/40 (GC 90/15)": "N/A (40 mm)",
        "4/20 (GC 90/15)": "N/A (20 mm)",
        "2/14 (GC 90/15)": "N/A (14 mm)",
        "20/40 (GC 85/20)": "N/A (40 mm)",
        "10/20 (GC 85/20)": "N/A (20 mm)",
        "6.3/14 (GC 85/20)": "N/A (14 mm)",
        "4/10 (GC 85/20)": "N/A (10 mm)",
        "2/6.3 (GC 80/20)": '1/4" (6,3 mm)'
    },
}

# Maximum nominal sizes valid by method
NMS_VALID = {
    "MCE": ['3" (75 mm)', '2-1/2" (63 mm)', '2" (50 mm)', '1-1/2" (37,5 mm)', '1" (25 mm)', '3/4" (19 mm)',
            '1/2" (12,5 mm)', '3/8" (9,5 mm)', '1/4" (6,3 mm)'],
    "ACI": ['3-1/2" (90 mm)', '3" (75 mm)', '2-1/2" (63 mm)', '2" (50 mm)', '1-1/2" (37,5 mm)', '1" (25 mm)',
            '3/4" (19 mm)', '1/2" (12,5 mm)', '3/8" (9,5 mm)'],
    "DoE": ["N/A (40 mm)", "N/A (20 mm)", "N/A (10 mm)"],
}

# Conversion factors according to the unit system
# The key is the target unit system
CONVERSION_FACTORS = {
    "MKS": {
        "stress": 0.1 # MPa -> kgf/cm^2 (real factor -> 0.0980665)
    },
    "SI": {
        "stress": 10.0 # kgf/cm^2 -> MPa (real factor -> 10.1972)
    }
}

# z values for preset quartiles
QUARTILES = {
    "0,5": -2.576,
    "1": -2.326,
    "2": -2.054,
    "2,5": -1.960,
    "3": -1.881,
    "4": -1.751,
    "5": -1.645,
    "6": -1.555,
    "7": -1.476,
    "8": -1.405,
    "9": -1.341,
    "10": -1.282,
    "15": -1.036,
    "20": -0.842,
    "25": -0.674
}

# k-factor for increasing sample standard deviation for number of strength tests
# considered in calculating standard deviation
K_FACTOR = {
    15: 1.16,
    16: 1.144,
    17: 1.128,
    18: 1.112,
    19: 1.096,
    20: 1.08,
    21: 1.07,
    22: 1.06,
    23: 1.05,
    24: 1.04,
    25: 1.03,
    26: 1.024,
    27: 1.018,
    28: 1.012,
    29: 1.006,
    30: 1.00
}

# List of error keys for progress bar update
ERROR_KEYS = ["GRADING REQUIREMENTS FOR COARSE AGGREGATE", "GRADING REQUIREMENTS FOR FINE AGGREGATE",
              "FINENESS MODULUS", "MINIMUM SPECIFIED COMPRESSIVE STRENGTH",
              "CEMENTITIOUS MATERIAL REQUIRED DUE TO SULFATE EXPOSURE",
              "MAXIMUM CONTENT OF SUPPLEMENTARY CEMENTITIOUS MATERIAL (SCM)", "MINIMUM ENTRAINED AIR"]

# -----------------------------------------------------------------------------
# MCE method settings
# -----------------------------------------------------------------------------

# Combined aggregate grading (passing percentage)
# KEEP THE FOLLOWING FORMAT -> (upper limit, lower limit)
COMBINED_GRADING = {
    '3-1/2" (90 mm)': {
        '3-1/2" (90 mm)': (100, 90),
        '3" (75 mm)': (95, 80),
        '2-1/2" (63 mm)': (92, 60),
        '2" (50 mm)': (85, 50),
        '1-1/2" (37,5 mm)': (76, 40),
        '1" (25 mm)': (68, 33),
        '3/4" (19 mm)': (63, 30),
        '1/2" (12,5 mm)': (57, 28),
        '3/8" (9,5 mm)': (53, 25),
        '1/4" (6,3 mm)': (45, 22),
        "No. 4 (4,75 mm)": (45, 22),
        "No. 8 (2,36 mm)": (40, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 7),
        "No. 100 (0,150 mm)": (8, 2)
    },
    '3" (75 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': (100, 90),
        '2-1/2" (63 mm)': (92, 70),
        '2" (50 mm)': (87, 55),
        '1-1/2" (37,5 mm)': (80, 45),
        '1" (25 mm)': (72, 38),
        '3/4" (19 mm)': (68, 35),
        '1/2" (12,5 mm)': (62, 32),
        '3/8" (9,5 mm)': (58, 30),
        '1/4" (6,3 mm)': (48, 25),
        "No. 4 (4,75 mm)": (48, 25),
        "No. 8 (2,36 mm)": (43, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 7),
        "No. 100 (0,150 mm)": (8, 2)
    },
    '2-1/2" (63 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': (100, 90),
        '2" (50 mm)': (87, 65),
        '1-1/2" (37,5 mm)': (80, 55),
        '1" (25 mm)': (73, 47),
        '3/4" (19 mm)': (68, 43),
        '1/2" (12,5 mm)': (62, 37),
        '3/8" (9,5 mm)': (60, 35),
        '1/4" (6,3 mm)': (58, 30),
        "No. 4 (4,75 mm)": (50, 28),
        "No. 8 (2,36 mm)": (45, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 7),
        "No. 100 (0,150 mm)": (8, 2)
    },
    '2" (50 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': (100, 90),
        '1-1/2" (37,5 mm)': (87, 73),
        '1" (25 mm)': (77, 59),
        '3/4" (19 mm)': (73, 53),
        '1/2" (12,5 mm)': (68, 44),
        '3/8" (9,5 mm)': (65, 40),
        '1/4" (6,3 mm)': (60, 35),
        "No. 4 (4,75 mm)": (55, 30),
        "No. 8 (2,36 mm)": (45, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 7),
        "No. 100 (0,150 mm)": (8, 2)
    },
    '1-1/2" (37,5 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': (100, 90),
        '1" (25 mm)': (84, 70),
        '3/4" (19 mm)': (77, 61),
        '1/2" (12,5 mm)': (70, 49),
        '3/8" (9,5 mm)': (65, 43),
        '1/4" (6,3 mm)': (60, 35),
        "No. 4 (4,75 mm)": (55, 30),
        "No. 8 (2,36 mm)": (45, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 7),
        "No. 100 (0,150 mm)": (8, 2)
    },
    '1" (25 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': None,
        '1" (25 mm)': (100, 90),
        '3/4" (19 mm)': (90, 70),
        '1/2" (12,5 mm)': (75, 55),
        '3/8" (9,5 mm)': (68, 45),
        '1/4" (6,3 mm)': (60, 35),
        "No. 4 (4,75 mm)": (55, 30),
        "No. 8 (2,36 mm)": (45, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 5),
        "No. 100 (0,150 mm)": (8, 1)
    },
    '3/4" (19 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': None,
        '1" (25 mm)': None,
        '3/4" (19 mm)': (100, 90),
        '1/2" (12,5 mm)': (85, 65),
        '3/8" (9,5 mm)': (75, 55),
        '1/4" (6,3 mm)': (65, 45),
        "No. 4 (4,75 mm)": (60, 38),
        "No. 8 (2,36 mm)": (45, 20),
        "No. 16 (1,18 mm)": (35, 15),
        "No. 30 (0,600 mm)": (25, 10),
        "No. 50 (0,300 mm)": (16, 5),
        "No. 100 (0,150 mm)": (8, 1)
    },
    '1/2" (12,5 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': None,
        '1" (25 mm)': None,
        '3/4" (19 mm)': None,
        '1/2" (12,5 mm)': (100, 90),
        '3/8" (9,5 mm)': (98, 90),
        '1/4" (6,3 mm)': (65, 51),
        "No. 4 (4,75 mm)": (58, 42),
        "No. 8 (2,36 mm)": (43, 37),
        "No. 16 (1,18 mm)": (31, 17),
        "No. 30 (0,600 mm)": (20, 10),
        "No. 50 (0,300 mm)": (11, 5),
        "No. 100 (0,150 mm)": (6, 1)
    },
    '3/8" (9,5 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': None,
        '1" (25 mm)': None,
        '3/4" (19 mm)': None,
        '1/2" (12,5 mm)': None,
        '3/8" (9,5 mm)': (100, 90),
        '1/4" (6,3 mm)': (73, 61),
        "No. 4 (4,75 mm)": (62, 48),
        "No. 8 (2,36 mm)": (40, 26),
        "No. 16 (1,18 mm)": (26, 14),
        "No. 30 (0,600 mm)": (13, 5),
        "No. 50 (0,300 mm)": (7, 3),
        "No. 100 (0,150 mm)": (5, 1)
    },
    '1/4" (6,3 mm)': {
        '3-1/2" (90 mm)': None,
        '3" (75 mm)': None,
        '2-1/2" (63 mm)': None,
        '2" (50 mm)': None,
        '1-1/2" (37,5 mm)': None,
        '1" (25 mm)': None,
        '3/4" (19 mm)': None,
        '1/2" (12,5 mm)': None,
        '3/8" (9,5 mm)': None,
        '1/4" (6,3 mm)': (100, 90),
        "No. 4 (4,75 mm)": (65, 52),
        "No. 8 (2,36 mm)": (38, 26),
        "No. 16 (1,18 mm)": (21, 9),
        "No. 30 (0,600 mm)": (8, 2),
        "No. 50 (0,300 mm)": (5, 1),
        "No. 100 (0,150 mm)": (2, 0)
    }
}

# Correction factor for cement content
CEMENT_FACTOR_1 = {
    '3" (75 mm)': 0.82,
    '2-1/2" (63 mm)': 0.85,
    '2" (50 mm)': 0.88,
    '1-1/2" (37,5 mm)': 0.93,
    '1" (25 mm)': 1.00,
    '3/4" (19 mm)': 1.05,
    '1/2" (12,5 mm)': 1.14,
    '3/8" (9,5 mm)': 1.20,
    '1/4" (6,3 mm)': 1.33
} # According to the nominal maximum size
CEMENT_FACTOR_2 = {
    "Triturado": {
        "Natural": 1.00,
        "Triturada": 1.28
    },
    "Semitriturado": {
        "Natural": 0.93,
        "Triturada": 1.23
    },
    "Grava natural": {
        "Natural": 0.90,
        "Triturada": 0.96
    }
} # According to aggregate type

# Minimum cement content according to exposure class
MIN_CEMENT_MCE = {
    "Despreciable": 270,
    "Agua dulce": 270,
    "Agua salobre o de mar": 350,
    "Moderada": 270,
    "Severa": 270,
    "Muy severa": 350,
    "Alta": 270,
    "Atmósfera común": 270,
    "Litoral": 350
}

# Constants values for M and N in the Abrams Law.
CONSTANTS = {
    "7 días": {
        "m": 861.3,
        "n": 13.1
    },
    "28 días": {
        "m": 902.5,
        "n": 8.69
    },
    "90 días": {
        "m": 973.1,
        "n": 7.71
    }
}

# Correction factor for water-cement ratio
ALFA_FACTOR_1 = {
    '3" (75 mm)': 0.74,
    '2-1/2" (63 mm)': 0.78,
    '2" (50 mm)': 0.82,
    '1-1/2" (37,5 mm)': 0.91,
    '1" (25 mm)': 1.00,
    '3/4" (19 mm)': 1.05,
    '1/2" (12,5 mm)': 1.10,
    '3/8" (9,5 mm)': 1.30,
    '1/4" (6,3 mm)': 1.60
} # According to the nominal maximum size
ALFA_FACTOR_2 = {
    "Triturado": {
        "Natural": 1.00,
        "Triturada": 1.14
    },
    "Semitriturado": {
        "Natural": 0.97,
        "Triturada": 1.10
    },
    "Grava natural": {
        "Natural": 0.91,
        "Triturada": 0.93
    }
} # According to aggregate type

# Maximum water-cement ratio according to exposure class
MAX_W_C_MCE = {
    "Despreciable": 1.00,
    "Agua dulce": 0.50,
    "Agua salobre o de mar": 0.40,
    "Moderada": 0.50,
    "Severa": 0.45,
    "Muy severa": 0.45,
    "Alta": 0.55,
    "Atmósfera común": 0.75,
    "Litoral": 0.60
}

# -----------------------------------------------------------------------------
# ACI method settings
# -----------------------------------------------------------------------------

# Approximate mixing water for different slumps and nominal maximum sizes of aggregate
WATER_CONTENT_NAE = {
    '25 mm - 50 mm': {
        '3-1/2" (90 mm)': 130,
        '3" (75 mm)': 130,
        '2-1/2" (63 mm)': 143,
        '2" (50 mm)': 154,
        '1-1/2" (37,5 mm)': 166,
        '1" (25 mm)': 179,
        '3/4" (19 mm)': 190,
        '1/2" (12,5 mm)': 199,
        '3/8" (9,5 mm)': 207
    },
    '75 mm - 100 mm': {
        '3-1/2" (90 mm)': 144,
        '3" (75 mm)': 145,
        '2-1/2" (63 mm)': 157,
        '2" (50 mm)': 169,
        '1-1/2" (37,5 mm)': 181,
        '1" (25 mm)': 193,
        '3/4" (19 mm)': 205,
        '1/2" (12,5 mm)': 216,
        '3/8" (9,5 mm)': 228
    },
    '125 mm - 150 mm': {
        '3-1/2" (90 mm)': 146,
        '3" (75 mm)': 151,
        '2-1/2" (63 mm)': 160,
        '2" (50 mm)': 172,
        '1-1/2" (37,5 mm)': 183,
        '1" (25 mm)': 196,
        '3/4" (19 mm)': 208,
        '1/2" (12,5 mm)': 222,
        '3/8" (9,5 mm)': 237
    },
    '150 mm - 175 mm': {
        '3-1/2" (90 mm)': 154,
        '3" (75 mm)': 160,
        '2-1/2" (63 mm)': 168,
        '2" (50 mm)': 178,
        '1-1/2" (37,5 mm)': 190,
        '1" (25 mm)': 202,
        '3/4" (19 mm)': 216,
        '1/2" (12,5 mm)': 228,
        '3/8" (9,5 mm)': 243
    }
} # Non-air-entrained
WATER_CONTENT_AE = {
    '25 mm - 50 mm': {
        '3-1/2" (90 mm)': 123,
        '3" (75 mm)': 122,
        '2-1/2" (63 mm)': 133,
        '2" (50 mm)': 142,
        '1-1/2" (37,5 mm)': 150,
        '1" (25 mm)': 160,
        '3/4" (19 mm)': 168,
        '1/2" (12,5 mm)': 175,
        '3/8" (9,5 mm)': 181
    },
    '75 mm - 100 mm': {
        '3-1/2" (90 mm)': 134,
        '3" (75 mm)': 133,
        '2-1/2" (63 mm)': 145,
        '2" (50 mm)': 157,
        '1-1/2" (37,5 mm)': 165,
        '1" (25 mm)': 175,
        '3/4" (19 mm)': 184,
        '1/2" (12,5 mm)': 193,
        '3/8" (9,5 mm)': 202
    },
    '125 mm - 150 mm': {
        '3-1/2" (90 mm)': 138,
        '3" (75 mm)': 142,
        '2-1/2" (63 mm)': 149,
        '2" (50 mm)': 160,
        '1-1/2" (37,5 mm)': 166,
        '1" (25 mm)': 178,
        '3/4" (19 mm)': 187,
        '1/2" (12,5 mm)': 199,
        '3/8" (9,5 mm)': 211
    },
    '150 mm - 175 mm': {
        '3-1/2" (90 mm)': 148,
        '3" (75 mm)': 154,
        '2-1/2" (63 mm)': 159,
        '2" (50 mm)': 166,
        '1-1/2" (37,5 mm)': 174,
        '1" (25 mm)': 184,
        '3/4" (19 mm)': 197,
        '1/2" (12,5 mm)': 205,
        '3/8" (9,5 mm)': 216
    }
} # Air-entrained

# Maximum water-cementitious materials ratio, by durability
MAX_W_CM_ACI = {
    "S0": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "S1": 0.50,
    "S2": 0.45,
    "S3": 0.40,
    "F0": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "F1": 0.55,
    "F2": 0.45,
    "F3": 0.40,
    "W0": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "W1": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "W2": 0.50,
    "C0": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "C1": 1.00, # It does not have minimum w_cm ratio; therefore, it is 1.00 by default
    "C2": 0.40
}

# Minimum requirements of cementing materials for concrete used in flatwork
MIN_CEMENTITIOUS_CONTENT_ACI = {
    '1-1/2" (37,5 mm)': 280,
    '1" (25 mm)': 310,
    '3/4" (19 mm)': 320,
    '1/2" (12,5 mm)': 350,
    '3/8" (9,5 mm)': 360
}

# Estimated amount of entrapped air (by percentage) in non-air-entrained concrete
ENTRAPPED_AIR = {
    '3-1/2" (90 mm)': 0.15, # It was not originally stipulated, it was obtained by interpolation
    '3" (75 mm)': 0.30,
    '2-1/2" (63 mm)': 0.40, # It was not originally stipulated, it was obtained by interpolation
    '2" (50 mm)': 0.50,
    '1-1/2" (37,5 mm)': 1.00,
    '1" (25 mm)': 1.50,
    '3/4" (19 mm)': 2.00,
    '1/2" (12,5 mm)': 2.50,
    '3/8" (9,5 mm)': 3.00
}

# Linear regression coefficients
COEFFICIENTS = {
    '3-1/2" (90 mm)': {
        'a': -0.1,
        'b': 1.1106
    },
    '3" (75 mm)': {
        'a': -0.1,
        'b': 1.06
    },
    '2-1/2" (63 mm)': {
        'a': -0.1,
        'b': 1.058
    },
    '2" (50 mm)': {
        'a': -0.1,
        'b': 1.02
    },
    '1-1/2" (37,5 mm)': {
        'a': -0.1,
        'b': 0.99
    },
    '1" (25 mm)': {
        'a': -0.1,
        'b': 0.95
    },
    '3/4" (19 mm)': {
        'a': -0.1,
        'b': 0.9
    },
    '1/2" (12,5 mm)': {
        'a': -0.1,
        'b': 0.83
    },
    '3/8" (9,5 mm)': {
        'a': -0.1,
        'b': 0.74
    }
}

# -----------------------------------------------------------------------------
# DoE method settings
# -----------------------------------------------------------------------------

# Approximate compressive strengths (N/mm2) of concrete mixes made with a free-water/cement ratio of 0.5
STARTING_STRENGTH = {
    "42.5": {
        "No triturada": {
            "3 días": 22,
            "7 días": 30,
            "28 días": 42,
            "91 días": 49
        },
        "Triturada": {
            "3 días": 27,
            "7 días": 36,
            "28 días": 49,
            "91 días": 56
        }
    },
    "52.5": {
        "No triturada": {
            "3 días": 29,
            "7 días": 37,
            "28 días": 48,
            "91 días": 54
        },
        "Triturada": {
            "3 días": 34,
            "7 días": 43,
            "28 días": 55,
            "91 días": 61
        }
    }
}

# Coefficients of a third-degree polynomial of the form ax³ + bx² + cx + d = 0
# Water-cementitious materials ratio
W_CM_COEFFICIENTS = {
    "Line 1": [52.591, -186.45, 231.87, -97.003], # The coefficients are in the ascending order [d, c, b, a]
    "Line 2": [72.12, -227.68, 257.04, -98.99],
    "Line 3": [112.93, -371.56, 440.46, -179.83],
    "Line 4": [133.43, -417.35, 475.38, -187.39],
    "Line 5": [139.1, -397.38, 413.46, -148.54],
    "Line 6": [155.65, -442.45, 469.06, -174.84],
    "Line 7": [145.73, -329.21, 277.12, -82.835],
    "Line 8": [149.82, -282.76, 181.17, -31.69],
    "Line 9": [142.99, -194.11, 41.43, 31.652],
    "Line 10": [162.07, -220.79, 62.71, 23.234]
}

# Maximum water-cementitious materials ratio, by durability
MAX_W_CM_DOE = {
    "XC1": 0.65,
    "XC2": 0.60,
    "XC3": 0.55,
    "XC4": 0.50,
    "XS1": 0.50,
    "XS2": 0.45,
    "XS3": 0.45,
    "XD1": 0.55,
    "XD2": 0.55,
    "XD3": 0.45,
    "XF1": 0.55,
    "XF2": 0.55,
    "XF3": 0.50,
    "XF4": 0.45,
    "XA1": 0.55,
    "XA2": 0.50,
    "XA3": 0.45
}

# Approximate free-water contents (kg/m3) required to give various levels of workability
WATER_CONTENT = {
    "N/A (10 mm)": {
        "No triturada": {
            "0 mm - 10 mm": 150,
            "10 mm - 30 mm": 180,
            "30 mm - 60 mm": 205,
            "60 mm - 180 mm": 225
        },
        "Triturada": {
            "0 mm - 10 mm": 180,
            "10 mm - 30 mm": 205,
            "30 mm - 60 mm": 230,
            "60 mm - 180 mm": 250
        }
    },
    "N/A (20 mm)": {
        "No triturada": {
            "0 mm - 10 mm": 135,
            "10 mm - 30 mm": 160,
            "30 mm - 60 mm": 180,
            "60 mm - 180 mm": 195
        },
        "Triturada": {
            "0 mm - 10 mm": 170,
            "10 mm - 30 mm": 190,
            "30 mm - 60 mm": 210,
            "60 mm - 180 mm": 225
        }
    },
    "N/A (40 mm)": {
        "No triturada": {
            "0 mm - 10 mm": 115,
            "10 mm - 30 mm": 140,
            "30 mm - 60 mm": 160,
            "60 mm - 180 mm": 175
        },
        "Triturada": {
            "0 mm - 10 mm": 155,
            "10 mm - 30 mm": 175,
            "30 mm - 60 mm": 190,
            "60 mm - 180 mm": 205
        }
    },
}

# Reductions in free-water content (kg/m3) due to SCM used
WATER_CONTENT_REDUCTION = {
    '10-20': {
        "0 mm - 10 mm": 5,
        "10 mm - 30 mm": 5,
        "30 mm - 60 mm": 5,
        "60 mm - 180 mm": 10
        },
    '20-30': {
        "0 mm - 10 mm": 10,
        "10 mm - 30 mm": 10,
        "30 mm - 60 mm": 10,
        "60 mm - 180 mm": 15
        },
    '30-40': {
        "0 mm - 10 mm": 15,
        "10 mm - 30 mm": 15,
        "30 mm - 60 mm": 20,
        "60 mm - 180 mm": 20
        },
    '40-50': {
        "0 mm - 10 mm": 20,
        "10 mm - 30 mm": 20,
        "30 mm - 60 mm": 25,
        "60 mm - 180 mm": 25
        },
    '50': {
        "0 mm - 10 mm": 25,
        "10 mm - 30 mm": 25,
        "30 mm - 60 mm": 30,
        "60 mm - 180 mm": 30
        }
}

# Minimum cement content, by durability
MIN_CEMENTITIOUS_CONTENT_DOE = {
    "XC1": 260,
    "XC2": 280,
    "XC3": 280,
    "XC4": 300,
    "XS1": 300,
    "XS2": 320,
    "XS3": 340,
    "XD1": 300,
    "XD2": 300,
    "XD3": 320,
    "XF1": 300,
    "XF2": 300,
    "XF3": 320,
    "XF4": 340,
    "XA1": 300,
    "XA2": 320,
    "XA3": 360
}

# Coefficients of a one-degree polynomial of the form ax + b = 0
# Wet density of fully compacted concrete
DENSITY_COEFFICIENTS = {
    2.40: [2403.75, -0.9375], # The coefficients are in the ascending order [b, a]
    2.50: [2496.25, -1.0625],
    2.60: [2605, -1.25],
    2.70: [2697.5, -1.375],
    2.80: [2812.5, -1.625],
    2.90: [2905, -1.75],
}

# Coefficients of a one-degree polynomial of the form ax + b = 0
# Fine proportion
FINE_PROPORTION = {
    "N/A (10 mm)": {
        "0 mm - 10 mm": {
            100: [20.1667, 12.1667], # The coefficients are in the ascending order [b, a]
            80: [22.8333, 14.3333],
            60: [28.4333, 16.3333],
            40: [31.7667, 24.6667],
            15: [42.6333, 27.3333]
        },
        "10 mm - 30 mm": {
            100: [21.1333, 11.8333],
            80: [24.9, 13.5],
            60: [29.2667, 17.6667],
            40: [33.0333, 25.8333],
            15: [44.6667, 27.1667]
        },
        "30 mm - 60 mm": {
            100: [22, 14],
            80: [26.9333, 13.8333],
            60: [32.8333, 15.8333],
            40: [37.1333, 22.8333],
            15: [49.2667, 26.1667]
        },
        "60 mm - 180 mm": {
            100: [25.7, 13],
            80: [30, 14.5],
            60: [36.3, 17.5],
            40: [43.7, 23],
            15: [55.0333, 28.8333]
        }
    },
    "N/A (20 mm)": {
        "0 mm - 10 mm": {
            100: [13.6, 12.5],
            80: [15.7, 15],
            60: [18.7333, 18.8333],
            40: [21.6333, 23.3333],
            15: [29, 27.5]
        },
        "10 mm - 30 mm": {
            100: [15.3667, 12.1667],
            80: [16.7333, 16.3333],
            60: [19.9, 19],
            40: [24.4, 23],
            15: [31.7333, 27.3333]
        },
        "30 mm - 60 mm": {
            100: [17.4667, 11.6667],
            80: [19.8333, 14.3333],
            60: [23.4333, 17.8333],
            40: [27.1333, 22.8333],
            15: [34.8667, 29.1667]
        },
        "60 mm - 180 mm": {
            100: [19.7333, 13.8333],
            80: [22.2, 16.5],
            60: [26.4, 20],
            40: [33.4667, 22.1667],
            15: [42, 28]
        }
    },
    "N/A (40 mm)": {
        "0 mm - 10 mm": {
            100: [9.9, 12.5],
            80: [12.1667, 14.6667],
            60: [13.9667, 18.1667],
            40: [16.1333, 24.8333],
            15: [22.3667, 27.1667]
        },
        "10 mm - 30 mm": {
            100: [12.4667, 11.1667],
            80: [13.9, 13.5],
            60: [15.7667, 17.6667],
            40: [18.5, 24],
            15: [23.9333, 28.3333]
        },
        "30 mm - 60 mm": {
            100: [14.4667, 11.1667],
            80: [17.2333, 11.8333],
            60: [19.5, 16.5],
            40: [24.4333, 19.8333],
            15: [28.8, 27.5]
        },
        "60 mm - 180 mm": {
            100: [16.9, 12.5],
            80: [19.6, 15],
            60: [22.5667, 18.6667],
            40: [28.1667, 22.1667],
            15: [35.2667, 28.1667]
        }
    },
}