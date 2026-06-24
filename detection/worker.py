import time

import cv2
import mss
import numpy as np

from assist.mouse_assist import MouseAssist
from config import PROCESS_SCALE, ROI
from detection.cursor import detect_cursor_circle
from detection.target_circles import detect_target_circles
from state import data_lock, shared_data, stop_event


def detection_worker():
    cv2.setUseOptimized(True)

    mouse_assist = MouseAssist()

    frame_counter = 0
    fps_timer = time.perf_counter()
    current_detect_fps = 0.0

    with mss.mss() as sct:
        primary_monitor = sct.monitors[1]

        if ROI is None:
            grab_region = {
                "left": primary_monitor["left"],
                "top": primary_monitor["top"],
                "width": primary_monitor["width"],
                "height": primary_monitor["height"],
            }

            offset_x = 0
            offset_y = 0
        else:
            roi_x, roi_y, roi_w, roi_h = ROI

            grab_region = {
                "left": primary_monitor["left"] + roi_x,
                "top": primary_monitor["top"] + roi_y,
                "width": roi_w,
                "height": roi_h,
            }

            offset_x = roi_x
            offset_y = roi_y

        while not stop_event.is_set():
            screenshot = np.array(sct.grab(grab_region))
            frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

            if PROCESS_SCALE != 1.0:
                frame_bgr = cv2.resize(
                    frame_bgr,
                    None,
                    fx=PROCESS_SCALE,
                    fy=PROCESS_SCALE,
                    interpolation=cv2.INTER_AREA
                )

            cursor = detect_cursor_circle(
                frame_bgr,
                PROCESS_SCALE,
                offset_x,
                offset_y
            )

            target_circles = detect_target_circles(
                frame_bgr,
                PROCESS_SCALE,
                offset_x,
                offset_y
            )

            assist_status = mouse_assist.update(cursor, target_circles)

            frame_counter += 1
            now = time.perf_counter()
            elapsed = now - fps_timer

            if elapsed >= 1.0:
                current_detect_fps = frame_counter / elapsed
                frame_counter = 0
                fps_timer = now

            with data_lock:
                shared_data["cursor"] = cursor
                shared_data["target_circles"] = target_circles
                shared_data["detect_fps"] = current_detect_fps
                shared_data["assist"] = assist_status
