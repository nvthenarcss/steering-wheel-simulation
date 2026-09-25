"""
Turns two wrist positions into a steering angle, then into a continuous
analog strength (-1.0 full left .. +1.0 full right) that a gamepad can use
directly. Also derives the old binary LEFT/RIGHT/STRAIGHT label for
display and for the keyboard fallback controller.

This replaces both the inline math duplicated in the old app.py *and* the
separate, never-imported steering/steering_math.py that expected a
different landmark format.
"""

import math

from config import config
from smoothing import EMA


class SteeringProcessor:
    def __init__(self):
        self._smoother = EMA(factor=config.get("steering", "smoothing_factor", default=0.35))
        self.calibration_offset = config.get("steering", "calibration_offset", default=0.0)
        self._last_raw_angle = 0.0

    def calibrate(self):
        """Call while the user is holding their hands in the 'straight' position."""
        self.calibration_offset = self._last_raw_angle
        config.set("steering", "calibration_offset", self.calibration_offset)

    def process(self, left_wrist, right_wrist):
        """
        left_wrist / right_wrist: (x, y) pixel tuples.
        Returns dict: angle_degrees, strength (-1..1), direction ("LEFT"/"RIGHT"/"STRAIGHT")
        """
        dx = right_wrist[0] - left_wrist[0]
        dy = right_wrist[1] - left_wrist[1]
        raw_angle = math.degrees(math.atan2(dy, dx))
        self._last_raw_angle = raw_angle

        angle = raw_angle - self.calibration_offset

        dead_zone = config.get("steering", "dead_zone_degrees", default=6)
        max_angle = config.get("steering", "max_angle_degrees", default=45)

        if abs(angle) <= dead_zone:
            effective = 0.0
        else:
            sign = 1 if angle > 0 else -1
            effective = sign * (abs(angle) - dead_zone)

        max_effective = max(max_angle - dead_zone, 1)
        normalized = max(-1.0, min(1.0, effective / max_effective))

        curve = config.get("steering", "response_curve", default="linear")
        if curve == "exponential":
            exponent = config.get("steering", "curve_exponent", default=1.6)
            normalized = math.copysign(abs(normalized) ** exponent, normalized)

        if config.get("steering", "smoothing", default="ema") == "ema":
            normalized = self._smoother.update(normalized)

        if normalized > 0.05:
            direction = "RIGHT"
        elif normalized < -0.05:
            direction = "LEFT"
        else:
            direction = "STRAIGHT"

        return {
            "angle_degrees": angle,
            "strength": normalized,   # -1.0 .. 1.0, ready for an analog stick axis
            "direction": direction,
        }
