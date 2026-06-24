import cv2
import numpy as np

from config import (
    CURSOR_MINT_RGB,
    CURSOR_MINT_TOLERANCE,
    WHITE_MIN_VALUE,
    WHITE_MAX_SATURATION,
    MIN_CURSOR_MINT_RATIO,
    MIN_CURSOR_WHITE_RATIO,
    MIN_RADIUS_CURSOR,
    MAX_RADIUS_CURSOR,
    MIN_CIRCULARITY_CURSOR,
)
from utils import circularity, to_full_coords


def detect_cursor_circle(frame_bgr, process_scale, offset_x, offset_y):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    lower_mint = np.clip(
        CURSOR_MINT_RGB - CURSOR_MINT_TOLERANCE,
        0,
        255
    ).astype(np.uint8)

    upper_mint = np.clip(
        CURSOR_MINT_RGB + CURSOR_MINT_TOLERANCE,
        0,
        255
    ).astype(np.uint8)

    mint_mask_rgb = cv2.inRange(frame_rgb, lower_mint, upper_mint)

    mint_mask_hsv = cv2.inRange(
        hsv,
        np.array([68, 100, 140]),
        np.array([92, 255, 255])
    )

    mint_mask = cv2.bitwise_and(mint_mask_rgb, mint_mask_hsv)

    white_mask = cv2.inRange(
        hsv,
        np.array([0, 0, WHITE_MIN_VALUE]),
        np.array([179, WHITE_MAX_SATURATION, 255])
    )

    mask = cv2.bitwise_or(mint_mask, white_mask)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)
        estimated_full_area = area / max(process_scale * process_scale, 0.001)

        if estimated_full_area < 100:
            continue

        circ = circularity(contour)

        if circ < MIN_CIRCULARITY_CURSOR:
            continue

        (x, y), radius = cv2.minEnclosingCircle(contour)

        full = to_full_coords(
            x,
            y,
            radius,
            process_scale,
            offset_x,
            offset_y
        )

        if not (MIN_RADIUS_CURSOR <= full["radius"] <= MAX_RADIUS_CURSOR):
            continue

        circle_area_mask = np.zeros(mask.shape, dtype=np.uint8)
        cv2.circle(
            circle_area_mask,
            (int(x), int(y)),
            max(int(radius), 2),
            255,
            -1
        )

        mint_pixels = cv2.countNonZero(
            cv2.bitwise_and(mint_mask, mint_mask, mask=circle_area_mask)
        )

        white_pixels = cv2.countNonZero(
            cv2.bitwise_and(white_mask, white_mask, mask=circle_area_mask)
        )

        total_pixels = max(cv2.countNonZero(circle_area_mask), 1)

        mint_ratio = mint_pixels / total_pixels
        white_ratio = white_pixels / total_pixels

        if mint_ratio < MIN_CURSOR_MINT_RATIO:
            continue

        if white_ratio < MIN_CURSOR_WHITE_RATIO:
            continue

        full["type"] = "curseur"
        full["score"] = (
            circ * 3.0
            + mint_ratio * 2.0
            + white_ratio * 2.0
        )

        candidates.append(full)

    if not candidates:
        return None

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[0]
