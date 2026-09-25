"""
Gesture recognition built on landmark geometry (no separate ML model needed
beyond what MediaPipe already gives us).

New vs. the original repo: thumbs-up/down gear shifting, and a held-open-palm
pause toggle, both with cooldowns/hold-timers so they don't fire every frame.
"""

import math
import time

from config import config
from hand_tracker import (
    WRIST, THUMB_TIP, THUMB_IP, THUMB_MCP,
    INDEX_TIP, INDEX_PIP, MIDDLE_TIP, MIDDLE_PIP,
    RING_TIP, RING_PIP, PINKY_TIP, PINKY_PIP,
)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_fist(points) -> bool:
    """True if enough of the four fingers (excluding thumb) are curled into the palm."""
    wrist = points[WRIST]
    finger_pairs = [
        (INDEX_TIP, INDEX_PIP),
        (MIDDLE_TIP, MIDDLE_PIP),
        (RING_TIP, RING_PIP),
        (PINKY_TIP, PINKY_PIP),
    ]
    curled = 0
    for tip_idx, pip_idx in finger_pairs:
        tip_dist = _dist(points[tip_idx], wrist)
        pip_dist = _dist(points[pip_idx], wrist)
        if tip_dist < pip_dist:  # tip closer to wrist than the knuckle = curled
            curled += 1

    threshold_fraction = config.get("gestures", "fist_curl_threshold", default=0.65)
    return (curled / len(finger_pairs)) >= threshold_fraction


def is_thumbs_up(points) -> bool:
    """Thumb extended upward (lower y = higher on screen), other four fingers curled."""
    if not is_fist(points):
        return False
    return points[THUMB_TIP][1] < points[THUMB_IP][1] < points[THUMB_MCP][1]


def is_thumbs_down(points) -> bool:
    if not is_fist(points):
        return False
    return points[THUMB_TIP][1] > points[THUMB_IP][1] > points[THUMB_MCP][1]


class GestureState:
    """Holds cross-frame state: gear number, pause hold timer, shift cooldown."""

    def __init__(self):
        self.gear = 1
        self.paused = False
        self._open_hold_start = None
        self._last_shift_time = 0.0

    def reset_gear(self):
        self.gear = 1

    def maybe_shift(self, thumbs_up: bool, thumbs_down: bool) -> bool:
        """Returns True if a shift happened this frame (for a UI flash / sound cue)."""
        cooldown = config.get("gestures", "gear_shift_cooldown_s", default=0.8)
        now = time.time()
        if now - self._last_shift_time < cooldown:
            return False
        if thumbs_up:
            self.gear = min(self.gear + 1, 6)
        elif thumbs_down:
            self.gear = max(self.gear - 1, 1)
        else:
            return False
        self._last_shift_time = now
        return True

    def update_pause_hold(self, both_hands_open: bool) -> bool:
        """Returns True the instant a pause/resume toggle fires (held-open long enough)."""
        hold_needed = config.get("gestures", "pause_hold_seconds", default=1.5)
        now = time.time()
        if both_hands_open:
            if self._open_hold_start is None:
                self._open_hold_start = now
            elif now - self._open_hold_start >= hold_needed:
                self.paused = not self.paused
                self._open_hold_start = None  # require releasing+re-holding to toggle again
                return True
        else:
            self._open_hold_start = None
        return False

    def pause_hold_progress(self, both_hands_open: bool) -> float:
        """0..1 progress toward the pause-hold threshold, for a UI progress ring."""
        if self._open_hold_start is None or not both_hands_open:
            return 0.0
        hold_needed = config.get("gestures", "pause_hold_seconds", default=1.5)
        return min(1.0, (time.time() - self._open_hold_start) / hold_needed)
