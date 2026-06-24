import threading

from detection.worker import detection_worker
from state import stop_event
from ui.pygame_window import run_window


def main():
    worker = threading.Thread(target=detection_worker, daemon=True)
    worker.start()

    try:
        run_window()
    finally:
        stop_event.set()
        worker.join(timeout=1.0)


if __name__ == "__main__":
    main()
