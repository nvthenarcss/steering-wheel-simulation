"""
Single interface the main loop talks to, regardless of whether output is
going to a virtual analog gamepad or falling back to discrete key presses.
Auto-detects which is available unless the user forced a mode in config.
"""

from config import config
from logger_setup import get_logger
from controller.keyboard_controller import KeyboardController
from controller.gamepad_controller import GamepadController, GamepadUnavailable

log = get_logger(__name__)


class OutputManager:
    def __init__(self):
        self.mode = None
        self._gamepad = None
        self._keyboard = None
        self._init_backend()

    def _init_backend(self):
        requested = config.get("controller", "mode", default="auto")

        if requested in ("auto", "gamepad"):
            try:
                self._gamepad = GamepadController()
                self.mode = "gamepad"
                log.info("Controller output: virtual gamepad (analog)")
                return
            except GamepadUnavailable as exc:
                if requested == "gamepad":
                    log.error(f"Gamepad mode forced but unavailable: {exc}")
                    raise
                log.info(f"Gamepad unavailable ({exc}), falling back to keyboard")

        self._keyboard = KeyboardController()
        self.mode = "keyboard"
        log.info("Controller output: keyboard (digital)")

    def apply(self, steering, throttle_state, gear_shifted, gear_direction, boost):
        """
        steering: dict from SteeringProcessor.process()
        throttle_state: "ACCEL" | "BRAKE" | "NEUTRAL"
        gear_shifted: bool, fired this frame
        gear_direction: "up" | "down" | None
        boost: bool
        """
        if self.mode == "gamepad":
            self._apply_gamepad(steering, throttle_state, gear_shifted, gear_direction, boost)
        else:
            self._apply_keyboard(steering, throttle_state, gear_shifted, gear_direction, boost)

    def _apply_gamepad(self, steering, throttle_state, gear_shifted, gear_direction, boost):
        pad = self._gamepad
        pad.set_steering(steering["strength"])
        pad.set_throttle(1.0 if throttle_state == "ACCEL" else 0.0)
        pad.set_brake(1.0 if throttle_state == "BRAKE" else 0.0)
        pad.update()
        if gear_shifted and gear_direction:
            pad.press_button("gear_up" if gear_direction == "up" else "gear_down")
        if boost:
            pad.press_button("boost")

    def _apply_keyboard(self, steering, throttle_state, gear_shifted, gear_direction, boost):
        kb = self._keyboard
        keymap = config.get("controller", "keymap")

        if steering["direction"] == "LEFT":
            kb.press(keymap["steer_left"])
            kb.release(keymap["steer_right"])
        elif steering["direction"] == "RIGHT":
            kb.press(keymap["steer_right"])
            kb.release(keymap["steer_left"])
        else:
            kb.release(keymap["steer_left"])
            kb.release(keymap["steer_right"])

        if throttle_state == "ACCEL":
            kb.press(keymap["accelerate"])
            kb.release(keymap["brake"])
        elif throttle_state == "BRAKE":
            kb.press(keymap["brake"])
            kb.release(keymap["accelerate"])
        else:
            kb.release(keymap["accelerate"])
            kb.release(keymap["brake"])

        if gear_shifted and gear_direction:
            kb.tap(keymap["gear_up"] if gear_direction == "up" else keymap["gear_down"])
        if boost:
            kb.tap(keymap["boost"])

    def release_all(self):
        if self.mode == "gamepad" and self._gamepad:
            self._gamepad.reset()
        elif self.mode == "keyboard" and self._keyboard:
            self._keyboard.release_all()
