# Gaming Steering Simulation

## What is this?

Gaming Steering Simulation turns an ordinary webcam into a hands-free
steering wheel for racing games. You hold your hands up in front of your
camera as if gripping a wheel, and the app watches your hands to control
steering, acceleration, braking, gear shifts, and boost — no physical
wheel or extra hardware needed.

It works by tracking the position and shape of both your hands in every
camera frame, turning the tilt between your wrists into a steering angle,
and recognizing simple hand gestures (fists, thumbs up/down, open palms)
as game commands. That output is then sent to your PC either as a real
analog gamepad signal or as regular keyboard key presses, depending on
what your system supports.

## Why this was built

Hardware racing wheels are expensive and most people don't own one.
Keyboard-only controls (tap left, tap right) feel binary and unnatural —
real steering is continuous, not on/off. This project explores whether a
plain webcam and some computer vision can get closer to that continuous,
physical feel of steering, using hardware almost everyone already has.

It's also built to be genuinely usable, not just a proof of concept:
settings are configurable instead of hardcoded, it degrades gracefully
when optional features aren't available, and it works across Windows,
macOS, and Linux rather than just one platform.

## Features

- **Analog steering.** Steering strength is a continuous value, not just
  "left" or "right" — the more you tilt your wrists, the sharper the
  turn. When a virtual gamepad is available, this becomes a real analog
  stick axis; otherwise it falls back to keyboard key presses.
- **Full gesture set** for accelerating, braking, boosting, shifting
  gears, and pausing — see the [Gestures](#gestures) section below.
- **Live calibration.** Press a key (or say "calibrate") to reset what
  counts as "straight ahead" to however you're currently holding your
  hands, instead of relying on a fixed hardcoded angle.
- **Config-driven behavior.** Dead zone, maximum steering angle,
  smoothing, response curve (linear or exponential), gesture
  sensitivity, key bindings, and HUD colors are all stored in one
  settings file — nothing is buried in code.
- **Cross-platform camera detection.** Automatically finds a working
  camera backend for your OS (MSMF/DSHOW on Windows, AVFoundation on
  macOS, V4L2 on Linux) and remembers what worked so future launches are
  instant. If a resolution setting turns out to be unstable on your
  particular camera driver, it automatically falls back to one that
  works instead of crashing.
- **On-screen HUD** showing live steering angle and direction, current
  gear, pause state, FPS, and camera/tracking/controller status — all
  reflecting real internal state, not a fake simulated number.
- **Optional voice commands** — say "pause," "resume," "calibrate," or
  "reset gear" instead of using the keyboard, if you have a microphone.
- **Optional session analytics** — export a CSV and a summary chart of
  your steering angle and frame rate over a session, useful for spotting
  frame-rate drops or inconsistent steering.
- **Optional settings GUI** — a small window with sliders and checkboxes
  to adjust sensitivity and toggle features, if you'd rather not edit a
  JSON file by hand.

## Tech stack

| Technology | What it's used for |
|---|---|
| **Python** | The language the whole project is written in |
| **OpenCV** | Captures webcam frames, draws the on-screen HUD, displays the window, reads keyboard input |
| **MediaPipe (Tasks API)** | Detects both hands per frame and returns 21 landmark points (wrist, knuckles, fingertips) for each |
| **NumPy** | Numerical support used internally by OpenCV and MediaPipe |
| **pynput** | Simulates keyboard key presses/releases — the fallback control method |
| **vgamepad** | Creates a virtual Xbox 360 controller so games see real analog input (Windows only) |
| **customtkinter** | Powers the optional settings window |
| **SpeechRecognition + PyAudio** | Powers the optional voice command listener |
| **matplotlib** | Generates the optional session summary chart |

## How it works

1. **Capture** — a frame is grabbed from your webcam.
2. **Track** — MediaPipe locates both hands and returns 21 (x, y) points
   per hand.
3. **Compute** — the angle between your two wrists becomes a steering
   value; hand shapes (fist vs. open, thumb direction) are checked
   against gesture rules to determine acceleration, braking, gear
   shifts, boost, and pause state.
4. **Output** — the computed values are sent out as either analog
   gamepad input or keyboard key presses.
5. **Render** — the camera feed is displayed with an overlay HUD showing
   everything the app currently "thinks" — steering angle, gear, pause
   state, FPS, and system status.

## Setup

**Requirements:** Python 3.9+, a webcam, and (optionally, for analog
gamepad output) Windows with the ViGEmBus driver.

```bash
git clone <https://github.com/nvthenarcss/steering-wheel-simulation>
cd gaming-steering-simulation
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# or: .venv\Scripts\activate       # Windows (Command Prompt)
# or: source .venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

Only `opencv-python`, `mediapipe`, `numpy`, and `pynput` are strictly
required. Everything else in `requirements.txt` is optional — voice
commands, the settings GUI, analytics, and gamepad output all work
without crashing if their dependency isn't installed; they just quietly
disable themselves.

## Usage

```bash
python main.py
```

The first launch takes a few extra seconds while it automatically tests
which camera backend works on your system. After that, it remembers the
result and starts instantly.

If you'd rather adjust settings with sliders instead of editing a config
file by hand, run this first:

```bash
python settings_gui.py
```

### Keyboard controls (while running)

| Key | Action |
|---|---|
| `q` | Quit |
| `c` | Calibrate steering center (hold your hands "straight," then press) |
| `r` | Reset gear back to 1 |

## Gestures

| Gesture | What it does |
|---|---|
| Tilt both wrists left | Steer left — the further you tilt, the stronger the input |
| Tilt both wrists right | Steer right |
| Hold wrists level | Steer straight |
| Right hand closed into a fist | Accelerate |
| Left hand closed into a fist | Brake |
| Both hands closed into fists at once | Boost |
| Thumbs up (thumb pointing up, other fingers curled) | Shift gear up |
| Thumbs down (thumb pointing down, other fingers curled) | Shift gear down |
| Both hands held fully open for about 1.5 seconds | Toggle pause / resume |

All of the thresholds behind these gestures — how curled counts as a
fist, how long you need to hold your hands open to pause, the cooldown
between gear shifts — are adjustable in the config file if any of them
feel too sensitive or too slow for your hands.

## Configuration

Settings are stored in `~/.gaming_steering/config.json`, created
automatically with sensible defaults the first time you run the app. A
few examples of what you can change:

```jsonc
{
  "steering": {
    "dead_zone_degrees": 6,        // how many degrees of tilt are ignored near center
    "max_angle_degrees": 45,       // tilt angle for full steering lock
    "smoothing_factor": 0.35,      // higher = snappier, lower = smoother
    "response_curve": "linear"     // or "exponential" for sharper full-lock response
  },
  "controller": {
    "mode": "auto"                 // "auto" | "gamepad" | "keyboard"
  },
  "voice": { "enabled": false },
  "analytics": { "enabled": false }
}
```

## Project structure

```
main.py                        entry point / main loop
config.py                      persistent settings (single source of truth)
logger_setup.py                rotating file + console logging
camera.py                      cross-platform camera detection & opening
hand_tracker.py                MediaPipe hand tracking wrapper
steering.py                    steering angle math, calibration, smoothing
gestures.py                    fist/open/thumbs detection, gear + pause state
dashboard.py                   on-screen HUD rendering
voice_commands.py              optional background voice recognition
analytics.py                   optional session CSV + chart export
settings_gui.py                optional pre-launch settings window
controller/
  keyboard_controller.py       keyboard fallback (discrete key press/release)
  gamepad_controller.py        analog virtual gamepad output
  output_manager.py            picks a backend, exposes one interface to main.py
```

## Known limitations

- Analog gamepad output only works on Windows (a constraint of the
  `vgamepad` library itself).
- Voice commands need an internet connection, since they use an online
  speech recognition service.
- The HUD reflects the app's own gesture/system state — it does not read
  real telemetry from any specific game.
- Gesture sensitivity is tuned generically and will likely need small
  adjustments in the config file for your hand size, camera, and
  lighting conditions.


