"""
Optional voice commands ("pause", "resume", "calibrate", "reset gear").

Runs in a background thread so it never blocks the camera loop. If
SpeechRecognition/PyAudio aren't installed or no microphone is found, it
disables itself cleanly instead of crashing the whole app — the same
"degrade gracefully" pattern as the gamepad controller.
"""

import threading
import queue

from config import config
from logger_setup import get_logger

log = get_logger(__name__)


class VoiceListener:
    def __init__(self):
        self.available = False
        self.command_queue: "queue.Queue[str]" = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None

        if not config.get("voice", "enabled", default=False):
            return

        try:
            import speech_recognition as sr  # noqa: F401
        except ImportError as exc:
            log.warning(f"Voice commands disabled: {exc}")
            return

        self._sr = sr
        self.available = True

    def start(self):
        if not self.available:
            return
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def poll_command(self):
        """Returns the next recognized action string (e.g. 'pause') or None."""
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None

    def _listen_loop(self):
        recognizer = self._sr.Recognizer()
        try:
            mic = self._sr.Microphone()
        except OSError as exc:
            log.warning(f"No microphone available for voice commands: {exc}")
            self.available = False
            return

        phrase_map = config.get("voice", "commands", default={})

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        while not self._stop_event.is_set():
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                text = recognizer.recognize_google(audio).lower()
                for phrase, action in phrase_map.items():
                    if phrase in text:
                        self.command_queue.put(action)
                        log.info(f"Voice command recognized: '{text}' -> {action}")
            except self._sr.WaitTimeoutError:
                continue
            except self._sr.UnknownValueError:
                continue
            except Exception as exc:  # noqa: BLE001 - keep the thread alive no matter what
                log.debug(f"Voice loop error: {exc}")
                continue
