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
)

MOUSEEVENTF_MOVE = 0x0001


class MouseAssist:
    """
    Déplace doucement la souris vers le cercle cible seulement si le curseur
    se déplace déjà dans la direction de ce cercle.
    """

    def __init__(self):
        self.previous_cursor = None
        self.last_move_time = 0.0
        self.user32 = ctypes.windll.user32

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

    def update(self, cursor, target_circles):
        status = {
            "enabled": ENABLE_MOUSE_ASSIST,
            "active": False,
            "target": None,
            "alignment": 0.0,
            "step": 0.0,
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
            return status

        now = time.perf_counter()
        min_interval = 1.0 / max(ASSIST_UPDATE_HZ, 1)

        if now - self.last_move_time < min_interval:
            status["reason"] = "rate_limited"
            return status

        # Vecteur de mouvement actuel du curseur.
        move_x = cursor["x"] - self.previous_cursor["x"]
        move_y = cursor["y"] - self.previous_cursor["y"]
        move_len = math.hypot(move_x, move_y)

        self.previous_cursor = cursor

        if move_len < ASSIST_MIN_CURSOR_SPEED:
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
        alignment = (
            (move_x * to_target_x + move_y * to_target_y)
            / max(move_len * distance, 0.0001)
        )
        status["alignment"] = alignment

        if alignment < ASSIST_ACTIVATION_DOT:
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

        self.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)

        self.last_move_time = now
        status["active"] = True
        status["step"] = step
        status["reason"] = "moving"
        return status
