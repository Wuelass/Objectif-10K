import cv2
import numpy as np

from config import (
    TARGET_RING_MIN_VALUE,
    TARGET_RING_MAX_SATURATION,
    MIN_RADIUS_TARGET_CIRCLE,
    MAX_RADIUS_TARGET_CIRCLE,
    MIN_TARGET_CIRCLE_AREA,
    MIN_CIRCULARITY_TARGET_CIRCLE,
    MIN_TARGET_RING_RATIO,
    MAX_TARGET_CENTER_WHITE_RATIO,
)
from utils import circularity, to_full_coords


def detect_target_circles(frame_bgr, process_scale, offset_x, offset_y):
    """
    Détecte les cercles avec un contour blanc/gris.
    Le centre peut changer de couleur : violet, vert, bleu, etc.
    """

    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    ring_mask = cv2.inRange(
        hsv,
        np.array([0, 0, TARGET_RING_MIN_VALUE]),
        np.array([179, TARGET_RING_MAX_SATURATION, 255])
    )

    kernel = np.ones((3, 3), np.uint8)

    ring_mask = cv2.morphologyEx(
        ring_mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=1
    )

    ring_mask = cv2.morphologyEx(
        ring_mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    contours, _ = cv2.findContours(
        ring_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    results = []

    for contour in contours:
        area = cv2.contourArea(contour)
        estimated_full_area = area / max(process_scale * process_scale, 0.001)

        if estimated_full_area < MIN_TARGET_CIRCLE_AREA:
            continue

        circ = circularity(contour)

        if circ < MIN_CIRCULARITY_TARGET_CIRCLE:
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

        if not (MIN_RADIUS_TARGET_CIRCLE <= full["radius"] <= MAX_RADIUS_TARGET_CIRCLE):
            continue

        circle_mask = np.zeros(ring_mask.shape, dtype=np.uint8)
        cv2.circle(
            circle_mask,
            (int(x), int(y)),
            max(int(radius), 2),
            255,
            -1
        )

        inner_mask = np.zeros(ring_mask.shape, dtype=np.uint8)
        cv2.circle(
            inner_mask,
            (int(x), int(y)),
            max(int(radius * 0.58), 1),
            255,
            -1
        )

        inner_ring_cut = np.zeros(ring_mask.shape, dtype=np.uint8)
        cv2.circle(
            inner_ring_cut,
            (int(x), int(y)),
            max(int(radius * 0.72), 1),
            255,
            -1
        )

        ring_area = cv2.subtract(circle_mask, inner_ring_cut)

        ring_pixels = cv2.countNonZero(
            cv2.bitwise_and(ring_mask, ring_mask, mask=ring_area)
        )

        ring_area_pixels = max(cv2.countNonZero(ring_area), 1)
        ring_ratio = ring_pixels / ring_area_pixels

        center_white_pixels = cv2.countNonZero(
            cv2.bitwise_and(ring_mask, ring_mask, mask=inner_mask)
        )

        center_pixels = max(cv2.countNonZero(inner_mask), 1)
        center_white_ratio = center_white_pixels / center_pixels

        if ring_ratio < MIN_TARGET_RING_RATIO:
            continue

        if center_white_ratio > MAX_TARGET_CENTER_WHITE_RATIO:
            continue

        full["type"] = "cercle"
        full["score"] = (
            circ * 2.0
            + ring_ratio * 3.0
            - center_white_ratio
        )

        results.append(full)

    results.sort(key=lambda c: c["score"], reverse=True)
    return results
