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

# Cercles avec contour blanc/gris.
# Le centre peut changer de couleur, donc on détecte surtout le contour.
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

# Sécurité : mets True seulement quand tu veux activer le mouvement automatique.
ENABLE_MOUSE_ASSIST = True

# "mouse" = correction relative classique.
# "tablet" = correction absolue adaptée aux tablettes graphiques.
ASSIST_INPUT_MODE = "tablet"

# En mode tablette, False permet à l'assist d'agir même si le stylet ne produit
# pas un mouvement relatif de souris exploitable.
ASSIST_TABLET_REQUIRE_MOTION = False

# Force du recentrage.
# 0.02 = très doux, 0.08 = moyen, 0.15 = fort.
ASSIST_FORCE = 0.40

# Limite de déplacement par correction, en pixels.
# Évite les téléportations instantanées.
ASSIST_MAX_STEP = 12

# L'assistance se déclenche seulement si le curseur bouge déjà en mode souris.
ASSIST_MIN_CURSOR_SPEED = 2.0

# Direction nécessaire pour activer l'assistance en mode souris.
# 0.30 = permissif, 0.60 = strict, 0.80 = très strict.
ASSIST_ACTIVATION_DOT = 0.55

# Distance minimale avant d'arrêter l'assistance.
ASSIST_MIN_DISTANCE = 4

# Zone morte autour du centre du cercle selon son rayon.
ASSIST_DEADZONE_RADIUS_FACTOR = 0.35

# Fréquence max des corrections de souris.
ASSIST_UPDATE_HZ = 360

# "nearest" = cercle le plus proche du curseur
# "best_score" = cercle le mieux détecté
ASSIST_TARGET_MODE = "nearest"
