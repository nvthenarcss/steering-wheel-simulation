"""
Cross-platform camera discovery and opening.

The original repo hardcoded cv2.CAP_DSHOW (Windows-only) in app.py and kept
a *separate*, never-integrated debug script (canera.py) that actually did
the useful cross-backend probing. This module merges the two: it does the
probing for real, at startup, and remembers what worked in config.json so
subsequent launches are instant.
"""

import platform
import cv2

from config import config
from logger_setup import get_logger

log = get_logger(__name__)

_BACKENDS_BY_OS = {
    "Windows": [("MSMF", cv2.CAP_MSMF), ("DSHOW", cv2.CAP_DSHOW), ("DEFAULT", cv2.CAP_ANY)],
    "Darwin": [("AVFOUNDATION", cv2.CAP_AVFOUNDATION), ("DEFAULT", cv2.CAP_ANY)],
    "Linux": [("V4L2", cv2.CAP_V4L2), ("DEFAULT", cv2.CAP_ANY)],
}


def _candidate_backends():
    return _BACKENDS_BY_OS.get(platform.system(), [("DEFAULT", cv2.CAP_ANY)])


def probe_cameras(max_index: int = 5):
    """Returns a list of (backend_name, backend_flag, index) that actually opened + read a frame."""
    working = []
    for backend_name, backend_flag in _candidate_backends():
        for index in range(max_index):
            cap = cv2.VideoCapture(index, backend_flag)
            if cap.isOpened():
                ok, _ = cap.read()
                if ok:
                    working.append((backend_name, backend_flag, index))
            cap.release()
    return working


def open_camera():
    """
    Opens a camera using, in order of preference:
      1. A previously-saved working backend/index from config.json
      2. The first backend/index that actually opens AND returns a frame
    Persists whichever one works so next launch skips the probing.
    """
    saved_index = config.get("camera", "index")
    saved_backend = config.get("camera", "backend")

    if saved_index is not None and saved_backend is not None:
        backend_flag = getattr(cv2, f"CAP_{saved_backend}", cv2.CAP_ANY)
        cap = cv2.VideoCapture(saved_index, backend_flag)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                log.info(f"Reusing saved camera: index={saved_index} backend={saved_backend}")
                _apply_resolution(cap)
                return cap
        cap.release()
        log.warning("Saved camera config no longer works, re-probing...")

    working = probe_cameras()
    if not working:
        raise RuntimeError(
            "No working camera found. Check that a webcam is connected and not in use "
            "by another application."
        )

    backend_name, backend_flag, index = working[0]
    log.info(f"Selected camera: index={index} backend={backend_name}")
    config.set("camera", "index", index, save=False)
    config.set("camera", "backend", backend_name, save=True)

    cap = cv2.VideoCapture(index, backend_flag)
    _apply_resolution(cap)
    return cap


def _apply_resolution(cap):
    width = config.get("camera", "width", default=1280)
    height = config.get("camera", "height", default=720)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
