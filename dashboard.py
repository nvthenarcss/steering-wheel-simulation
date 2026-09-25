"""
On-screen HUD. Colors come from config so users can re-theme without
touching code. The old repo's speedometer showed a number with no real
game telemetry behind it; this version is upfront about what it actually
knows: gesture state, steering strength, gear, and system status.
"""

import math
import cv2

from config import config

FONT = cv2.FONT_HERSHEY_SIMPLEX


def _theme():
    return {
        "bg": config.color("background"),
        "primary": config.color("primary"),
        "text": config.color("text"),
        "muted": config.color("muted"),
        "accel": config.color("accel"),
        "brake": config.color("brake"),
    }


def draw_status_bar(frame, fps, camera_ok, tracking_ok, controller_mode, gear, paused):
    theme = _theme()
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 40), theme["bg"], -1)

    cv2.putText(frame, f"FPS: {int(fps)}", (10, 26), FONT, 0.55, theme["primary"], 1)

    def dot(label, ok, x):
        color = theme["accel"] if ok else theme["brake"]
        cv2.putText(frame, label, (x, 26), FONT, 0.55, theme["text"], 1)
        cv2.circle(frame, (x + len(label) * 11 + 12, 20), 5, color, -1)

    dot("Camera", camera_ok, 140)
    dot("Tracking", tracking_ok, 300)
    dot(f"Controller ({controller_mode})", True, 470)

    cv2.putText(frame, f"GEAR {gear}", (w - 160, 26), FONT, 0.55, theme["primary"], 1)
    if paused:
        cv2.putText(frame, "PAUSED", (w // 2 - 50, 26), FONT, 0.6, theme["brake"], 2)
    return frame


def draw_pause_progress(frame, progress: float):
    """A small filling ring near the top center showing pause-hold progress."""
    if progress <= 0:
        return frame
    theme = _theme()
    h, w = frame.shape[:2]
    center = (w // 2, 60)
    cv2.ellipse(frame, center, (18, 18), -90, 0, int(360 * progress), theme["primary"], 3)
    return frame


def draw_steering_wheel(frame, center, angle_degrees, direction, strength):
    theme = _theme()
    radius = 55
    cv2.circle(frame, center, radius, theme["muted"], 2)
    cv2.circle(frame, center, 6, theme["primary"], -1)
    for spoke_angle in (90, 210, 330):
        rad = math.radians(spoke_angle + angle_degrees)
        x2 = int(center[0] + radius * math.cos(rad))
        y2 = int(center[1] + radius * math.sin(rad))
        cv2.line(frame, center, (x2, y2), theme["primary"], 3)

    color = theme["accel"] if direction == "STRAIGHT" else theme["primary"]
    cv2.putText(frame, "STEERING", (center[0] - 32, center[1] + 40), FONT, 0.35, theme["muted"], 1)
    cv2.putText(frame, direction, (center[0] - 26, center[1] + 55), FONT, 0.4, color, 1)
    cv2.putText(frame, f"angle {int(angle_degrees)} deg  |  strength {strength:+.2f}",
                (center[0] - 90, center[1] + 70), FONT, 0.35, theme["text"], 1)
    return frame


def draw_pedal_bars(frame, origin, accel_amount, brake_amount, throttle_state):
    theme = _theme()
    x, y = origin
    cv2.putText(frame, "ACCEL", (x, y), FONT, 0.4, theme["muted"], 1)
    for i in range(10):
        color = theme["accel"] if i < int(accel_amount * 10) else (50, 50, 50)
        cv2.rectangle(frame, (x + 55 + i * 12, y - 8), (x + 65 + i * 12, y + 2), color, -1)

    cv2.putText(frame, "BRAKE", (x, y + 25), FONT, 0.4, theme["muted"], 1)
    for i in range(10):
        color = theme["brake"] if i < int(brake_amount * 10) else (50, 50, 50)
        cv2.rectangle(frame, (x + 55 + i * 12, y + 17), (x + 65 + i * 12, y + 27), color, -1)

    mode_color = theme["accel"] if throttle_state == "ACCEL" else (
        theme["brake"] if throttle_state == "BRAKE" else theme["primary"]
    )
    cv2.putText(frame, throttle_state, (x, y + 50), FONT, 0.5, mode_color, 1)
    return frame


def draw_hand_open_state(frame, origin, left_open, right_open):
    theme = _theme()
    x, y = origin
    left_color = theme["text"] if left_open else theme["primary"]
    right_color = theme["text"] if right_open else theme["primary"]
    cv2.putText(frame, f"L: {'Open' if left_open else 'Fist'}", (x, y), FONT, 0.4, left_color, 1)
    cv2.putText(frame, f"R: {'Open' if right_open else 'Fist'}", (x, y + 18), FONT, 0.4, right_color, 1)
    return frame


def draw_toast(frame, text, y_offset=100):
    """Transient center-screen message, e.g. 'Calibrated!'"""
    theme = _theme()
    h, w = frame.shape[:2]
    cv2.putText(frame, text, (w // 2 - len(text) * 6, y_offset), FONT, 0.6, theme["primary"], 2)
    return frame
