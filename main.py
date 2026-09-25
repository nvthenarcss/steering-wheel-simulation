"""
Gaming Steering v2 — entry point.

Controls while running:
  q       quit
  c       calibrate (hold hands "straight" first, then press)
  m       toggle controller mode (gamepad <-> keyboard), if gamepad available
  r       reset gear to 1

Gestures:
  Left fist  = brake        Right fist = accelerate   (either hand can be reassigned in config)
  Thumbs up  = shift up      Thumbs down = shift down
  Both hands held open ~1.5s = pause/resume toggle
  Both fists at once          = boost
"""

import time
import cv2

from config import config
from logger_setup import get_logger
from camera import open_camera
from hand_tracker import HandTracker
from steering import SteeringProcessor
from gestures import GestureState, is_fist, is_thumbs_up, is_thumbs_down
from controller.output_manager import OutputManager
from voice_commands import VoiceListener
from analytics import SessionAnalytics
import dashboard

log = get_logger(__name__)


def main():
    log.info("Starting Gaming Steering v2...")

    cap = open_camera()
    tracker = HandTracker()
    steering = SteeringProcessor()
    gestures = GestureState()
    output = OutputManager()
    voice = VoiceListener()
    voice.start()
    analytics = SessionAnalytics()

    show_skeleton = config.get("gui", "show_hand_skeleton", default=True)

    toast_text, toast_until = "", 0.0

    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                log.warning("Camera frame read failed")
                continue

            if config.get("camera", "flip_horizontal", default=True):
                frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands = tracker.process(rgb, frame_width, frame_height)

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev_time, 1e-6))
            prev_time = now

            left = hands.get("Left")
            right = hands.get("Right")
            tracking_ok = left is not None and right is not None

            steering_result = {"angle_degrees": 0.0, "strength": 0.0, "direction": "STRAIGHT"}
            throttle_state = "NEUTRAL"
            gear_shifted = False
            gear_direction = None
            boost = False
            left_open = right_open = True

            if tracking_ok:
                left_points = left["points"]
                right_points = right["points"]

                steering_result = steering.process(left_points[0], right_points[0])

                left_fist = is_fist(left_points)
                right_fist = is_fist(right_points)
                left_open, right_open = not left_fist, not right_fist

                if right_fist and not left_fist:
                    throttle_state = "ACCEL"
                elif left_fist and not right_fist:
                    throttle_state = "BRAKE"
                elif left_fist and right_fist:
                    boost = True
                    throttle_state = "ACCEL"

                thumbs_up = is_thumbs_up(right_points) or is_thumbs_up(left_points)
                thumbs_down = is_thumbs_down(right_points) or is_thumbs_down(left_points)
                gear_shifted = gestures.maybe_shift(thumbs_up, thumbs_down)
                if gear_shifted:
                    gear_direction = "up" if thumbs_up else "down"
                    toast_text, toast_until = f"Gear {gestures.gear}", now + 1.0

                both_open = left_open and right_open
                if gestures.update_pause_hold(both_open):
                    toast_text = "Paused" if gestures.paused else "Resumed"
                    toast_until = now + 1.2

                if show_skeleton:
                    tracker.draw(frame, left_points)
                    tracker.draw(frame, right_points)

            # Voice commands can also drive pause/calibrate/gear-reset
            voice_action = voice.poll_command()
            if voice_action == "pause":
                gestures.paused = True
            elif voice_action == "resume":
                gestures.paused = False
            elif voice_action == "calibrate":
                steering.calibrate()
                toast_text, toast_until = "Calibrated!", now + 1.0
            elif voice_action == "reset_gear":
                gestures.reset_gear()

            if not gestures.paused:
                output.apply(steering_result, throttle_state, gear_shifted, gear_direction, boost)
            else:
                output.release_all()

            analytics.maybe_sample(fps, steering_result["angle_degrees"], steering_result["strength"],
                                    gestures.gear, throttle_state)

            # ---- Draw HUD ----
            frame = dashboard.draw_status_bar(frame, fps, cap.isOpened(), tracking_ok,
                                               output.mode, gestures.gear, gestures.paused)
            frame = dashboard.draw_pause_progress(frame, gestures.pause_hold_progress(left_open and right_open))
            frame = dashboard.draw_steering_wheel(
                frame, (frame_width // 2, frame_height - 120),
                steering_result["angle_degrees"], steering_result["direction"], steering_result["strength"],
            )
            frame = dashboard.draw_pedal_bars(
                frame, (frame_width - 220, frame_height - 160),
                1.0 if throttle_state == "ACCEL" else 0.0,
                1.0 if throttle_state == "BRAKE" else 0.0,
                throttle_state,
            )
            frame = dashboard.draw_hand_open_state(frame, (frame_width - 220, frame_height - 90), left_open, right_open)

            if now < toast_until:
                frame = dashboard.draw_toast(frame, toast_text)

            cv2.imshow("Virtual Steering Wheel", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                steering.calibrate()
                toast_text, toast_until = "Calibrated!", time.time() + 1.0
            elif key == ord("r"):
                gestures.reset_gear()
            elif key == ord("m"):
                log.info("Manual mode toggle requested (edit config.json 'controller.mode' and restart to force a mode)")

    finally:
        log.info("Shutting down...")
        voice.stop()
        output.release_all()
        analytics.export()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
