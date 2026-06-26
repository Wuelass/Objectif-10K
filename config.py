import numpy as np

# ==================================================
# PERFORMANCE / AFFICHAGE
# ==================================================

TARGET_RENDER_FPS = 360

# 0.5 = plus rapide, 1.0 = plus précis mais plus lent
PROCESS_SCALE = 0.5

# None = analyse tout l'écran principal
# Pour booster les FPS, limite une zone :
# ROI = (x, y, largeur, hauteur)
ROI = None

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 460

PLACE_ON_SECOND_MONITOR = True


# ==================================================
# PARAMÈTRES DÉTECTION CURSEUR
# ==================================================

CURSOR_MINT_RGB = np.array([67, 255, 193])
CURSOR_MINT_TOLERANCE = 28

WHITE_MIN_VALUE = 225
WHITE_MAX_SATURATION = 55

MIN_CURSOR_MINT_RATIO = 0.08
MIN_CURSOR_WHITE_RATIO = 0.08

MIN_RADIUS_CURSOR = 8
MAX_RADIUS_CURSOR = 70

MIN_CIRCULARITY_CURSOR = 0.65


# ==================================================
# PARAMÈTRES DÉTECTION CERCLES
# ==================================================

TARGET_RING_MIN_VALUE = 155
TARGET_RING_MAX_SATURATION = 95

MIN_RADIUS_TARGET_CIRCLE = 22
MAX_RADIUS_TARGET_CIRCLE = 110

MIN_TARGET_CIRCLE_AREA = 120
MIN_CIRCULARITY_TARGET_CIRCLE = 0.50

MIN_TARGET_RING_RATIO = 0.18
MAX_TARGET_CENTER_WHITE_RATIO = 0.38


# ==================================================
# ASSISTANCE SOURIS
# ==================================================

ENABLE_MOUSE_ASSIST = True

ASSIST_INPUT_MODE = "tablet_pulse"
ASSIST_TABLET_REQUIRE_MOTION = False
ASSIST_TABLET_PULSE_ENABLED = True
ASSIST_TABLET_PULSE_MS = 35
ASSIST_TABLET_PULSE_COOLDOWN_MS = 140
ASSIST_TABLET_INTERRUPT_DOT = 0.10
ASSIST_TABLET_MAX_TARGET_SHIFT = 80

ASSIST_FORCE = 0.40
ASSIST_MAX_STEP = 12
ASSIST_MIN_CURSOR_SPEED = 2.0
ASSIST_ACTIVATION_DOT = 0.55
ASSIST_MIN_DISTANCE = 4
ASSIST_DEADZONE_RADIUS_FACTOR = 0.35
ASSIST_UPDATE_HZ = 360
ASSIST_TARGET_MODE = "nearest"
