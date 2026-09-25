# 🎮 Gaming Steering v2

Control racing games with your hands — no hardware wheel required. A
webcam tracks your hands, tilts of your wrists become steering input, and
fist/thumb gestures handle throttle, braking, gear shifts, and boost.

This is a ground-up rebuild of an earlier prototype. The old version had a
lot of scaffolding (a config system, a logger, a steering-math module,
extra dependencies) that was never actually wired into the app — this
version fixes that, and adds real analog controller output and a handful
of new gestures on top.

---

## Features

- **Analog steering, not on/off key-taps.** When `vgamepad` and its driver
  are available (Windows), steering, throttle, and brake are emitted as
  real analog gamepad axes — far smoother than arrow-key input. Falls
  back to keyboard automatically everywhere else.
- **Gesture set:**
  - Tilt both wrists left/right → steer
  - Right fist → accelerate · Left fist → brake · Both fists → boost
  - Thumbs up / down → shift gear up / down
  - Hold both hands open for ~1.5s → pause / resume
- **Live calibration** — press `c` (or say "calibrate") to reset the
  steering center to however you're currently holding your hands, instead
  of a fixed hardcoded angle.
- **Config-driven** — dead zone, max angle, smoothing, response curve
  (linear/exponential), keymaps, gesture thresholds, and theme colors all
  live in one settings file, editable by hand or through a small GUI.
- **Cross-platform camera auto-detection** — probes available backends
  (MSMF/DSHOW on Windows, AVFoundation on macOS, V4L2 on Linux) at first
  launch and remembers what worked.
- **Optional extras, off by default:**
  - Voice commands (pause / resume / calibrate / reset gear)
  - Session analytics — CSV export + a steering/FPS summary chart
  - A `customtkinter` settings window so you don't have to hand-edit JSON

## Demo

*(add a GIF or screenshot of the HUD here once you've recorded one)*

## Requirements

- Python 3.9+
- A webcam
- Windows, for analog gamepad output (optional — keyboard fallback works
  everywhere)

## Installation

```bash
git clone <your-repo-url>
cd gaming_steering_v2
pip install -r requirements.txt
```

Core dependencies (`opencv-python`, `mediapipe`, `numpy`, `pynput`) are
required. Everything else in `requirements.txt` is optional and the app
degrades gracefully if it's missing — see [Optional features](#optional-features).

## Usage

```bash
python main.py
```

On first launch it probes your cameras automatically; this takes a few
seconds and only happens once.

Optional: run the settings window first if you'd rather use sliders than
edit JSON directly:

```bash
python settings_gui.py
```

### Controls

| Key | Action |
|---|---|
| `q` | Quit |
| `c` | Calibrate steering center |
| `r` | Reset gear to 1 |

### Gestures

| Gesture | Action |
|---|---|
| Tilt wrists left/right | Steer |
| Right hand fist | Accelerate |
| Left hand fist | Brake |
| Both fists | Boost |
| Thumbs up | Gear up |
| Thumbs down | Gear down |
| Both hands open, held ~1.5s | Pause / resume |

## Configuration

All settings persist to `~/.gaming_steering/config.json`, created with
sane defaults on first run. Key sections:

```jsonc
{
  "steering": {
    "dead_zone_degrees": 6,
    "max_angle_degrees": 45,
    "smoothing_factor": 0.35,
    "response_curve": "linear"   // or "exponential"
  },
  "controller": {
    "mode": "auto"               // "auto" | "gamepad" | "keyboard"
  },
  "voice": { "enabled": false },
  "analytics": { "enabled": false }
}
```

## Optional features

| Feature | Needs | Enable via |
|---|---|---|
| Analog gamepad | `vgamepad` + ViGEmBus driver (Windows) | automatic if available |
| Voice commands | `SpeechRecognition`, `PyAudio`, a microphone | `voice.enabled: true` |
| Session analytics | `matplotlib` | `analytics.enabled: true` |
| Settings GUI | `customtkinter` | run `settings_gui.py` |

Each of these is checked at runtime and quietly disables itself if the
dependency or hardware isn't available — the core app never crashes
because an optional extra is missing.

## Project layout

```
main.py                        entry point / main loop
config.py                      persistent settings (single source of truth)
logger_setup.py                rotating file + console logging
camera.py                      cross-platform camera probing & opening
hand_tracker.py                 MediaPipe Hands wrapper
steering.py                     angle → analog strength, calibration, smoothing
gestures.py                     fist/open/thumbs detection, gear + pause state
dashboard.py                    HUD rendering (theme-driven)
voice_commands.py               optional background voice recognition
analytics.py                    optional session CSV + chart export
settings_gui.py                 optional pre-launch settings window
controller/
  keyboard_controller.py        pynput fallback (discrete key press/release)
  gamepad_controller.py         vgamepad analog output
  output_manager.py             picks a backend, exposes one interface
```

## Known limitations

- Analog gamepad output is Windows-only today (`vgamepad`'s constraint,
  not this app's).
- Voice recognition uses Google's free speech API and needs an internet
  connection.
- The HUD reflects gesture/system state, not real in-game telemetry —
  there's no per-game integration.
- Gesture thresholds (fist curl %, hold durations) are tuned generically;
  expect to adjust `gestures.*` in config for your hand size and lighting.

## Contributing

Issues and PRs welcome — in particular, real-world testing reports (which
games it works well with, gesture thresholds that needed tweaking, OS/
camera combos that misbehave) are the most useful thing right now, since
this hasn't been run outside of code review yet.

## License

Add a license of your choice (MIT is a reasonable default for a project
like this) before publishing.
