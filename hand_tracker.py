"""
MediaPipe Hand Landmarker wrapper — built on the Tasks API.

Important: mediapipe pip releases from roughly 0.10.31 onward removed the
legacy `mediapipe.solutions` module entirely. Code written against
`mp.solutions.hands` (a very common pattern in older tutorials/repos) now
raises `AttributeError: module 'mediapipe' has no attribute 'solutions'`
on a fresh `pip install mediapipe`. This wraps the replacement — the
Tasks API — which needs an explicit model file (bundled at
assets/hand_landmarker.task) instead of a built-in model.

Returns plain-Python structures (dicts of pixel-space landmark points keyed
by handedness) so the rest of the app doesn't need to know which
hand-tracking API is in use.
"""

import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision

WRIST = 0
THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18

# Standard 21-point hand skeleton edges. This layout is stable across
# mediapipe versions/APIs, so it's hardcoded here rather than pulled from
# a drawing-utils module that may or may not exist in a given release.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
_DEFAULT_MODEL_PATH = Path(__file__).parent / "assets" / "hand_landmarker.task"


def _ensure_model(model_path: Path):
    """Downloads the model file if it's missing (it's bundled by default, so
    this is only a safety net if someone deletes the assets folder)."""
    if model_path.exists():
        return
    model_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(_MODEL_URL, model_path)


class HandTracker:
    def __init__(self, max_hands: int = 2, detection_conf: float = 0.6,
                 tracking_conf: float = 0.6, model_path: Path = _DEFAULT_MODEL_PATH):
        _ensure_model(model_path)

        base_options = mp_tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
        self._start_time = time.perf_counter()

    def process(self, rgb_frame, frame_width, frame_height):
        """
        Returns a dict like:
          {"Left": {"points": [(x, y), ...] (21 pts)},
           "Right": {...}}
        Handedness label is MediaPipe's, mirror-corrected relative to a
        typical front-facing webcam (i.e. it's the user's actual hand).
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.perf_counter() - self._start_time) * 1000)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        hands = {}
        if result.hand_landmarks and result.handedness:
            for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
                label = handedness[0].category_name  # "Left" | "Right"
                points = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in landmarks]
                hands[label] = {"points": points}
        return hands

    def draw(self, frame, points):
        """points: the pixel-space list from process()'s hand entry ["points"]."""
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, points[a], points[b], (60, 210, 255), 2)
        for x, y in points:
            cv2.circle(frame, (x, y), 3, (255, 220, 60), -1)

    def close(self):
        self._landmarker.close()
