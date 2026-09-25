"""pynput-based discrete key press/release, with a held-keys set so we never
double-press or leak a stuck key on exit."""

from pynput.keyboard import Controller, Key

_SPECIAL_KEYS = {
    "left": Key.left, "right": Key.right, "up": Key.up, "down": Key.down,
    "space": Key.space, "enter": Key.enter, "shift": Key.shift,
}


def _resolve(key_name: str):
    return _SPECIAL_KEYS.get(key_name, key_name)


class KeyboardController:
    def __init__(self):
        self._kb = Controller()
        self._held = set()

    def press(self, key_name: str):
        if key_name not in self._held:
            self._kb.press(_resolve(key_name))
            self._held.add(key_name)

    def release(self, key_name: str):
        if key_name in self._held:
            self._kb.release(_resolve(key_name))
            self._held.discard(key_name)

    def release_all(self):
        for key_name in list(self._held):
            self.release(key_name)

    def tap(self, key_name: str):
        self._kb.press(_resolve(key_name))
        self._kb.release(_resolve(key_name))
