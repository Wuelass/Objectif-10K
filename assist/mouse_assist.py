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
    ASSIST_TABLET_PULSE_ENABLED,
    ASSIST_TABLET_PULSE_MS,
    ASSIST_TABLET_PULSE_COOLDOWN_MS,
    ASSIST_TABLET_INTERRUPT_DOT,
    ASSIST_TABLET_MAX_TARGET_SHIFT,
)

MOUSEEVENTF_MOVE = 0x0001
TABLET_INPUT_MODE = "tablet"
TABLET_PULSE_INPUT_MODE = "tablet_pulse"


class MouseAssist:
    def __init__(self):
        self.previous_cursor = None
        self.last_move_time = 0.0
        self.user32 = ctypes.windll.user32
        self.input_mode = str(ASSIST_INPUT_MODE).lower().strip()

        self.tablet_armed = False
        self.tablet_target = None
        self.tablet_pulse_until = 0.0
        self.last_tablet_pulse_time = 0.0

    def is_tablet_mode(self):
        return self.input_mode in {TABLET_INPUT_MODE, TABLET_PULSE_INPUT_MODE}

    def is_tablet_pulse_mode(self):
        return self.input_mode == TABLET_PULSE_INPUT_MODE

    def choose_target(self, cursor, target_circles):
        if not cursor or not target_circles:
            return None

        cx = cursor["x"]
        cy = cursor["y"]

        if ASSIST_TARGET_MODE == "best_score":
            return max(target_circles, key=lambda c: c.get("score", 0.0))

        return min(
            target_circles,
            key=lambda c: (c["x"] - cx) ** 2 + (c["y"] - cy) ** 2
        )

    def reset_tablet_state(self):
        self.tablet_armed = False
        self.tablet_target = None
        self.tablet_pulse_until = 0.0

    def save_tablet_target(self, target):
        self.tablet_target = {
            "x": target["x"],
            "y": target["y"],
            "radius": target.get("radius", 0),
        }

    def is_same_tablet_target(self, target):
        if not self.tablet_target or not target:
            return False

        shift = math.hypot(
            target["x"] - self.tablet_target["x"],
            target["y"] - self.tablet_target["y"],
        )

        return shift <= ASSIST_TABLET_MAX_TARGET_SHIFT

    def set_cursor_pos(self, x, y):
        self.user32.SetCursorPos(int(round(x)), int(round(y)))

    def move_cursor(self, cursor, dx, dy):
        if self.is_tablet_mode():
            self.set_cursor_pos(cursor["x"] + dx, cursor["y"] + dy)
            return "absolute"

        self.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        return "relative"

    def update_tablet_pulse(self, status, target, distance, deadzone, alignment, move_len, now):
        status["tablet_armed"] = self.tablet_armed

        if not ASSIST_TABLET_PULSE_ENABLED:
            status["reason"] = "tablet_pulse_disabled"
            return status

        if self.tablet_target and now < self.tablet_pulse_until:
            self.set_cursor_pos(self.tablet_target["x"], self.tablet_target["y"])
            status["active"] = True
            status["move_method"] = "absolute_pulse"
            status["step"] = distance
            status["reason"] = "tablet_pulse_active"
            return status

        if self.tablet_armed and not self.is_same_tablet_target(target):
            self.reset_tablet_state()

        moving_enough = move_len >= ASSIST_MIN_CURSOR_SPEED
        moving_toward_target = moving_enough and alignment >= ASSIST_ACTIVATION_DOT

        if moving_toward_target:
            self.tablet_armed = True
            self.save_tablet_target(target)
            status["tablet_armed"] = True
            status["reason"] = "tablet_pulse_armed"
            return status

        movement_interrupted = (
            self.tablet_armed
            and distance > deadzone
            and (
                not moving_enough
                or alignment <= ASSIST_TABLET_INTERRUPT_DOT
            )
        )

        if not movement_interrupted:
            status["tablet_armed"] = self.tablet_armed
            status["reason"] = (
                "tablet_pulse_waiting_motion"
                if not self.tablet_armed
                else "tablet_pulse_waiting_interrupt"
            )
            return status

        cooldown = ASSIST_TABLET_PULSE_COOLDOWN_MS / 1000.0
        if now - self.last_tablet_pulse_time < cooldown:
            status["tablet_armed"] = self.tablet_armed
            status["reason"] = "tablet_pulse_cooldown"
            return status

        self.save_tablet_target(target)
        self.tablet_armed = False
        self.tablet_pulse_until = now + ASSIST_TABLET_PULSE_MS / 1000.0
        self.last_tablet_pulse_time = now
        self.set_cursor_pos(target["x"], target["y"])

        status["active"] = True
        status["tablet_armed"] = False
        status["move_method"] = "absolute_pulse"
        status["step"] = distance
        status["reason"] = "tablet_pulse_start"
        return status

    def update(self, cursor, target_circles):
        status = {
            "enabled": ENABLE_MOUSE_ASSIST,
            "active": False,
            "target": None,
            "alignment": 0.0,
            "step": 0.0,
            "input_mode": self.input_mode,
            "move_method": None,
            "tablet_armed": self.tablet_armed,
            "reason": "disabled" if not ENABLE_MOUSE_ASSIST else "idle",
        }

        if not ENABLE_MOUSE_ASSIST:
            self.previous_cursor = cursor
            self.reset_tablet_state()
            return status

        if not cursor:
            self.previous_cursor = None
            self.reset_tablet_state()
            status["reason"] = "cursor_missing"
            return status

        target = self.choose_target(cursor, target_circles)
        status["target"] = target

        if not target:
            self.previous_cursor = cursor
            self.reset_tablet_state()
            status["reason"] = "target_missing"
            return status

        now = time.perf_counter()

        if self.previous_cursor is None:
            self.previous_cursor = cursor
            status["reason"] = "waiting_motion"
            if self.is_tablet_pulse_mode() or not self.is_tablet_mode() or ASSIST_TABLET_REQUIRE_MOTION:
                return status

        min_interval = 1.0 / max(ASSIST_UPDATE_HZ, 1)

        if now - self.last_move_time < min_interval:
            status["reason"] = "rate_limited"
            return status

        previous_cursor = self.previous_cursor or cursor

        move_x = cursor["x"] - previous_cursor["x"]
        move_y = cursor["y"] - previous_cursor["y"]
        move_len = math.hypot(move_x, move_y)

        self.previous_cursor = cursor
        self.last_move_time = now

        if move_len < ASSIST_MIN_CURSOR_SPEED:
            if not self.is_tablet_mode() or ASSIST_TABLET_REQUIRE_MOTION:
                status["reason"] = "not_moving"
                return status

        to_target_x = target["x"] - cursor["x"]
        to_target_y = target["y"] - cursor["y"]
        distance = math.hypot(to_target_x, to_target_y)

        deadzone = max(
            ASSIST_MIN_DISTANCE,
            target.get("radius", 0) * ASSIST_DEADZONE_RADIUS_FACTOR
        )

        if distance <= deadzone:
            self.reset_tablet_state()
            status["tablet_armed"] = False
            status["reason"] = "inside_deadzone"
            return status

        if distance <= 0:
            self.reset_tablet_state()
            status["tablet_armed"] = False
            status["reason"] = "distance_zero"
            return status

        alignment = 1.0
        if move_len > 0:
            alignment = (
                (move_x * to_target_x + move_y * to_target_y)
                / max(move_len * distance, 0.0001)
            )
        status["alignment"] = alignment

        if self.is_tablet_pulse_mode():
            return self.update_tablet_pulse(
                status,
                target,
                distance,
                deadzone,
                alignment,
                move_len,
                now,
            )

        if (
            not self.is_tablet_mode()
            or ASSIST_TABLET_REQUIRE_MOTION
        ) and alignment < ASSIST_ACTIVATION_DOT:
            status["reason"] = "wrong_direction"
            return status

        dir_x = to_target_x / distance
        dir_y = to_target_y / distance
        step = min(distance * ASSIST_FORCE, ASSIST_MAX_STEP)

        dx = int(round(dir_x * step))
        dy = int(round(dir_y * step))

        if dx == 0 and dy == 0:
            status["reason"] = "step_too_small"
            return status

        status["move_method"] = self.move_cursor(cursor, dx, dy)
        status["active"] = True
        status["step"] = step
        status["reason"] = "moving"
        return status
