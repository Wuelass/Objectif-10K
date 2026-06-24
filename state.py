import threading

shared_data = {
    "cursor": None,
    "target_circles": [],
    "detect_fps": 0.0,
    "assist": {
        "enabled": False,
        "active": False,
        "target": None,
        "alignment": 0.0,
        "step": 0.0,
        "reason": "idle",
    },
}

data_lock = threading.Lock()
stop_event = threading.Event()
