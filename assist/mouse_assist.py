import ctypes
import math
import time

from config import (
    ENABLE_MOUSE_ASSIST,
    ASSIST_FORCE,
    ASSIST_MAX_STEP,
    ASSIST_MIN_CURSOR_SPEED,
    ASSIST_ACTIVATION_DOT,
    ASSIST_MIN_DISTANCE,
    ASSIST_DEADZONE_RADIUS_FACTOR,
    ASSIST_UPDATE_HZ,
    ASSIST_TARGET_MODE,
    ASSIST_INPUT_MODE,
    ASSIST_TABLET_REQUIRE_MOTION,
)

MOUSEEVENTF_MOVE = 0x0001
TABLET_INPUT_MODE = "tablet"


class MouseAssist:
    """
    Déplace doucement le curseur vers le cercle cible.

    Mode souris : garde le comportement initial, avec une correction relative
    seulement si le curseur part déjà vers la cible.

    Mode tablette : utilise une correction absolue avec SetCursorPos, mieux
    adaptée aux tablettes graphiques qui positionnent le curseur en absolu.
    """

    def __init__(self):
        self.previous_cursor = None
        self.last_move_time = 0.0
        self.user32 = ctypes.windll.user32
        self.input_mode = str(ASSIST_INPUT_MODE).lower().strip()

    def is_tablet_mode(self):
        return self.input_mode == TABLET_INPUT_MODE

    def choose_target(self, cursor, target_circles):
        if not cursor or not target_circles:
            return None

        cx = cursor["x"]
        cy = cursor["y"]

        if ASSIST_TARGET_MODE == "best_score":
            return max(target_circles, key=lambda c: c.get("score", 0.0))

        # Par défaut : cercle le plus proche du curseur.
        return min(
            target_circles,
            key=lambda c: (c["x"] - cx) ** 2 + (c["y"] - cy) ** 2
        )

    def move_cursor(self, cursor, dx, dy):
        if self.is_tablet_mode():
            # Une tablette graphique envoie souvent une position absolue.
            # SetCursorPos applique donc directement la correction à la position
            # détectée à l'écran au lieu d'ajouter un mouvement relatif souris.
            target_x = int(round(cursor["x"] + dx))
            target_y = int(round(cursor["y"] + dy))
            self.user32.SetCursorPos(target_x, target_y)
            return "absolute"

        self.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        return "relative"

    def update(self, cursor, target_circles):
        status = {
            "enabled": ENABLE_MOUSE_ASSIST,
            "active": False,
            "target": None,
            "alignment": 0.0,
            "step": 0.0,
            "input_mode": self.input_mode,
            "move_method": None,
            "reason": "disabled" if not ENABLE_MOUSE_ASSIST else "idle",
        }

        if not ENABLE_MOUSE_ASSIST:
            self.previous_cursor = cursor
            return status

        if not cursor:
            self.previous_cursor = None
            status["reason"] = "cursor_missing"
            return status

        target = self.choose_target(cursor, target_circles)
        status["target"] = target

        if not target:
            self.previous_cursor = cursor
            status["reason"] = "target_missing"
            return status

        if self.previous_cursor is None:
            self.previous_cursor = cursor
            status["reason"] = "waiting_motion"

            # En mode tablette on peut déjà assister sans attendre un delta
            # souris, car le stylet contrôle directement une position absolue.
            if not self.is_tablet_mode() or ASSIST_TABLET_REQUIRE_MOTION:
                return status

        now = time.perf_counter()
        min_interval = 1.0 / max(ASSIST_UPDATE_HZ, 1)

        if now - self.last_move_time < min_interval:
            status["reason"] = "rate_limited"
            return status

        previous_cursor = self.previous_cursor or cursor

        # Vecteur de mouvement actuel du curseur.
        move_x = cursor["x"] - previous_cursor["x"]
        move_y = cursor["y"] - previous_cursor["y"]
        move_len = math.hypot(move_x, move_y)

        self.previous_cursor = cursor

        if move_len < ASSIST_MIN_CURSOR_SPEED:
            if not self.is_tablet_mode() or ASSIST_TABLET_REQUIRE_MOTION:
                status["reason"] = "not_moving"
                return status

        # Vecteur du curseur vers la cible.
        to_target_x = target["x"] - cursor["x"]
        to_target_y = target["y"] - cursor["y"]
        distance = math.hypot(to_target_x, to_target_y)

        deadzone = max(
            ASSIST_MIN_DISTANCE,
            target.get("radius", 0) * ASSIST_DEADZONE_RADIUS_FACTOR
        )

        if distance <= deadzone:
            status["reason"] = "inside_deadzone"
            return status

        if distance <= 0:
            status["reason"] = "distance_zero"
            return status

        # Vérifie si le curseur part déjà vers la cible.
        alignment = 1.0
        if move_len > 0:
            alignment = (
                (move_x * to_target_x + move_y * to_target_y)
                / max(move_len * distance, 0.0001)
            )
        status["alignment"] = alignment

        if (
            not self.is_tablet_mode()
            or ASSIST_TABLET_REQUIRE_MOTION
        ) and alignment < ASSIST_ACTIVATION_DOT:
            status["reason"] = "wrong_direction"
            return status

        dir_x = to_target_x / distance
        dir_y = to_target_y / distance

        # Mouvement doux : proportionnel à la distance, limité par ASSIST_MAX_STEP.
        step = min(distance * ASSIST_FORCE, ASSIST_MAX_STEP)

        dx = int(round(dir_x * step))
        dy = int(round(dir_y * step))

        if dx == 0 and dy == 0:
            status["reason"] = "step_too_small"
            return status

        status["move_method"] = self.move_cursor(cursor, dx, dy)

        self.last_move_time = now
        status["active"] = True
        status["step"] = step
        status["reason"] = "moving"
        return status
