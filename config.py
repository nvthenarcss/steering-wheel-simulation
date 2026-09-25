"""
Central configuration for Gaming Steering.

Everything that used to be a hardcoded constant scattered across the old
app.py now lives here, persisted to a JSON file so users can tweak behavior
without touching code. Falls back to sane defaults if the file is missing
or partially filled in (so upgrading defaults later never crashes on an
old config file).
"""

import json
import copy
from pathlib import Path

CONFIG_DIR = Path.home() / ".gaming_steering"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    "camera": {
        "index": None,          # None = auto-detect on first working camera
        "backend": None,        # None = auto-detect (platform-appropriate)
        "flip_horizontal": True,
        "width": 1280,
        "height": 720,
    },
    "steering": {
        "dead_zone_degrees": 6,
        "max_angle_degrees": 45,
        "release_center_degrees": 3,
        "smoothing": "ema",         # "ema" | "none"
        "smoothing_factor": 0.35,   # higher = snappier, lower = smoother
        "response_curve": "linear",  # "linear" | "exponential"
        "curve_exponent": 1.6,
        "calibration_offset": 0.0,  # set live via the 'c' key, persisted
    },
    "controller": {
        "mode": "auto",  # "auto" | "gamepad" | "keyboard"
        "keymap": {
            "steer_left": "left",
            "steer_right": "right",
            "accelerate": "up",
            "brake": "down",
            "gear_up": "e",
            "gear_down": "q",
            "boost": "space",
        },
    },
    "gestures": {
        "fist_curl_threshold": 0.65,   # fraction of fingers curled to count as a fist
        "gear_shift_cooldown_s": 0.8,
        "pause_hold_seconds": 1.5,
    },
    "voice": {
        "enabled": False,
        "commands": {
            "pause": "pause",
            "resume": "resume",
            "calibrate": "calibrate",
            "reset gear": "reset_gear",
        },
    },
    "analytics": {
        "enabled": False,
        "sample_every_n_frames": 10,
        "export_dir": str(Path.home() / ".gaming_steering" / "sessions"),
    },
    "gui": {
        "theme": {
            "background": [20, 20, 20],
            "primary": [255, 210, 60],
            "text": [230, 230, 230],
            "muted": [110, 110, 110],
            "accel": [80, 220, 120],
            "brake": [60, 60, 240],
            "panel_alpha": 0.55,
        },
        "show_hand_skeleton": True,
        "show_fps": True,
    },
    "logging": {
        "level": "INFO",
        "file": str(Path.home() / ".gaming_steering" / "app.log"),
    },
}


def _deep_merge(base, override):
    """Merge override into base, recursively, without dropping unknown base keys."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class ConfigManager:
    """Loads, saves, and provides dotted-path access to settings."""

    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data = copy.deepcopy(DEFAULTS)
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    on_disk = json.load(f)
                self.data = _deep_merge(DEFAULTS, on_disk)
            except (json.JSONDecodeError, OSError):
                # Corrupt or unreadable config: fall back to defaults rather
                # than crashing the whole app.
                self.data = copy.deepcopy(DEFAULTS)
        else:
            self.save()
        return self.data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, *keys, default=None):
        """config.get('steering', 'dead_zone_degrees')"""
        node = self.data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, *keys_and_value, save=True):
        """config.set('steering', 'dead_zone_degrees', 8)"""
        *keys, value = keys_and_value
        node = self.data
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value
        if save:
            self.save()

    def color(self, name):
        """Returns a gui theme color as a BGR tuple for OpenCV."""
        rgb = self.get("gui", "theme", name, default=[255, 255, 255])
        # Stored as RGB for human-readability in the JSON; OpenCV wants BGR.
        return tuple(int(c) for c in reversed(rgb))


# Module-level singleton so every file can just `from config import config`
config = ConfigManager()
