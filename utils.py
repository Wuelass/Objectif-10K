import cv2
import numpy as np
import mss


def circularity(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    if perimeter == 0:
        return 0

    return 4 * np.pi * area / (perimeter * perimeter)


def to_full_coords(x, y, radius, process_scale, offset_x, offset_y):
    return {
        "x": int(x / process_scale) + offset_x,
        "y": int(y / process_scale) + offset_y,
        "radius": int(radius / process_scale),
    }


def get_monitors():
    with mss.mss() as sct:
        return [dict(m) for m in sct.monitors]


def map_to_window(x, y, radius, win_w, win_h, screen_w, screen_h):
    margin = 30
    info_height = 90

    available_w = max(win_w - margin * 2, 1)
    available_h = max(win_h - margin * 2 - info_height, 1)

    scale = min(
        available_w / screen_w,
        available_h / screen_h
    )

    rect_w = screen_w * scale
    rect_h = screen_h * scale

    rect_x = (win_w - rect_w) / 2
    rect_y = 30

    mapped_x = rect_x + x * scale
    mapped_y = rect_y + y * scale
    mapped_r = max(radius * scale, 4)

    return mapped_x, mapped_y, mapped_r, rect_x, rect_y, rect_w, rect_h
