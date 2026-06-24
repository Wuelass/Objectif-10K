import os
import time

from config import (
    PLACE_ON_SECOND_MONITOR,
    TARGET_RENDER_FPS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    PROCESS_SCALE,
)
from state import data_lock, shared_data
from utils import get_monitors, map_to_window


def draw_text(surface, font, text, x, y, color):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))


def run_window():
    monitors = get_monitors()
    primary = monitors[1]

    screen_w = primary["width"]
    screen_h = primary["height"]

    if PLACE_ON_SECOND_MONITOR and len(monitors) >= 3:
        second = monitors[2]
        os.environ["SDL_VIDEO_WINDOW_POS"] = (
            f"{second['left'] + 50},{second['top'] + 50}"
        )

    import pygame

    pygame.init()

    window = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.RESIZABLE
    )

    pygame.display.set_caption("Détection - curseur et cercles")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)
    font_bold = pygame.font.SysFont("Arial", 16, bold=True)

    background = (18, 18, 18)
    screen_rect_color = (180, 180, 180)
    text_color = (230, 230, 230)

    cursor_color = (67, 255, 193)
    circle_color = (196, 138, 90)

    render_frame_counter = 0
    render_fps = 0.0
    render_timer = time.perf_counter()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        win_w, win_h = window.get_size()

        with data_lock:
            cursor = shared_data["cursor"]
            target_circles = list(shared_data["target_circles"])
            detect_fps = shared_data["detect_fps"]
            assist = dict(shared_data.get("assist", {}))

        window.fill(background)

        _, _, _, rect_x, rect_y, rect_w, rect_h = map_to_window(
            0,
            0,
            1,
            win_w,
            win_h,
            screen_w,
            screen_h
        )

        pygame.draw.rect(
            window,
            screen_rect_color,
            pygame.Rect(rect_x, rect_y, rect_w, rect_h),
            width=2
        )

        draw_text(
            window,
            font_small,
            f"Écran principal : {screen_w}x{screen_h}",
            int(rect_x + 8),
            int(rect_y + 8),
            screen_rect_color
        )

        if cursor:
            cx, cy, r, *_ = map_to_window(
                cursor["x"],
                cursor["y"],
                cursor["radius"],
                win_w,
                win_h,
                screen_w,
                screen_h
            )

            pygame.draw.circle(
                window,
                cursor_color,
                (int(cx), int(cy)),
                int(r),
                width=3
            )

            pygame.draw.circle(
                window,
                cursor_color,
                (int(cx), int(cy)),
                4
            )

            draw_text(
                window,
                font_bold,
                "CURSEUR",
                int(cx + 10),
                int(cy - 12),
                cursor_color
            )

        for i, circle in enumerate(target_circles, start=1):
            cx, cy, r, *_ = map_to_window(
                circle["x"],
                circle["y"],
                circle["radius"],
                win_w,
                win_h,
                screen_w,
                screen_h
            )

            pygame.draw.circle(
                window,
                circle_color,
                (int(cx), int(cy)),
                int(r),
                width=2
            )

            pygame.draw.circle(
                window,
                circle_color,
                (int(cx), int(cy)),
                3
            )

            draw_text(
                window,
                font_small,
                f"CERCLE {i}",
                int(cx + 8),
                int(cy - 10),
                circle_color
            )

        assist_target = assist.get("target")
        if cursor and assist_target:
            c_x, c_y, _, *_ = map_to_window(
                cursor["x"],
                cursor["y"],
                1,
                win_w,
                win_h,
                screen_w,
                screen_h
            )

            t_x, t_y, t_r, *_ = map_to_window(
                assist_target["x"],
                assist_target["y"],
                assist_target["radius"],
                win_w,
                win_h,
                screen_w,
                screen_h
            )

            pygame.draw.line(
                window,
                cursor_color,
                (int(c_x), int(c_y)),
                (int(t_x), int(t_y)),
                width=1
            )

            pygame.draw.circle(
                window,
                cursor_color,
                (int(t_x), int(t_y)),
                int(t_r + 4),
                width=2
            )

        info_y = win_h - 98

        draw_text(
            window,
            font,
            f"Affichage cible : {TARGET_RENDER_FPS} Hz | Affichage réel : {render_fps:.1f} FPS",
            20,
            info_y,
            text_color
        )

        draw_text(
            window,
            font,
            f"Détection réelle : {detect_fps:.1f} FPS | PROCESS_SCALE={PROCESS_SCALE}",
            20,
            info_y + 22,
            text_color
        )

        if cursor:
            cursor_text = (
                f"Curseur : x={cursor['x']} "
                f"y={cursor['y']} "
                f"r={cursor['radius']}"
            )
        else:
            cursor_text = "Curseur : non détecté"

        draw_text(
            window,
            font_bold,
            cursor_text,
            20,
            info_y + 44,
            cursor_color
        )

        draw_text(
            window,
            font_bold,
            f"Cercles détectés : {len(target_circles)}",
            430,
            info_y + 44,
            circle_color
        )

        assist_text = (
            f"Assist : {'ON' if assist.get('enabled') else 'OFF'} | "
            f"actif={assist.get('active', False)} | "
            f"align={assist.get('alignment', 0.0):.2f} | "
            f"raison={assist.get('reason', 'idle')}"
        )

        draw_text(
            window,
            font_small,
            assist_text,
            20,
            info_y + 68,
            cursor_color if assist.get("active") else text_color
        )

        pygame.display.flip()

        render_frame_counter += 1
        now = time.perf_counter()

        if now - render_timer >= 1.0:
            render_fps = render_frame_counter / (now - render_timer)
            render_frame_counter = 0
            render_timer = now

        clock.tick(TARGET_RENDER_FPS)

    pygame.quit()
