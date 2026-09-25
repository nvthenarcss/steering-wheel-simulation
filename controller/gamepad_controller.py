"""
Virtual Xbox360 controller output via vgamepad.

This is the headline upgrade over the original repo: steering becomes a real
analog stick axis instead of a binary key-press, and throttle/brake become
analog triggers. Games that support controller input (almost all racing
games) get vastly smoother, more precise control than arrow keys can offer.

vgamepad requires the ViGEmBus driver on Windows (vgamepad's own installer
handles this) and is Windows-only today. GamepadUnavailable is raised (not
a bare exception) so callers can cleanly fall back to keyboard mode.
"""


class GamepadUnavailable(Exception):
    pass


class GamepadController:
    def __init__(self):
        try:
            import vgamepad as vg
        except ImportError as exc:
            raise GamepadUnavailable(f"vgamepad not installed: {exc}") from exc

        try:
            self._pad = vg.VX360Gamepad()
        except Exception as exc:  # driver missing, permissions, etc.
            raise GamepadUnavailable(f"Could not initialize virtual gamepad: {exc}") from exc

        self._vg = vg

    def set_steering(self, strength: float):
        """strength: -1.0 (full left) .. 1.0 (full right)"""
        strength = max(-1.0, min(1.0, strength))
        self._pad.left_joystick_float(x_value_float=strength, y_value_float=0.0)

    def set_throttle(self, value: float):
        """value: 0.0 .. 1.0"""
        value = max(0.0, min(1.0, value))
        self._pad.right_trigger_float(value_float=value)

    def set_brake(self, value: float):
        value = max(0.0, min(1.0, value))
        self._pad.left_trigger_float(value_float=value)

    def press_button(self, name: str):
        button = {
            "gear_up": self._vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "gear_down": self._vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "boost": self._vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        }.get(name)
        if button is None:
            return
        self._pad.press_button(button=button)
        self._pad.update()
        self._pad.release_button(button=button)

    def update(self):
        self._pad.update()

    def reset(self):
        self._pad.reset()
        self._pad.update()
