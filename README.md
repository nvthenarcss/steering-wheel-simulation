cat > README.md << 'EOF'
# 🎮 Gaming Steering v2

Control racing games with your hands — no hardware wheel required. A
webcam tracks your hands, tilts of your wrists become steering input, and
fist/thumb gestures handle throttle, braking, gear shifts, and boost.

## Features

- Analog steering via virtual gamepad (vgamepad), automatic keyboard fallback
- Gestures: tilt to steer, right fist accelerate, left fist brake, both fists boost, thumbs up/down to shift gears, hold both hands open ~1.5s to pause/resume
- Live calibration (press 'c') instead of a fixed hardcoded center angle
- Config-driven: dead zone, max angle, smoothing, response curve, keymaps, theme colors
- Cross-platform camera auto-detection
- Optional voice commands, session analytics (CSV + chart), and a settings GUI

## Installation

\`\`\`bash
pip install -r requirements.txt
python main.py
\`\`\`

Optional settings window:
\`\`\`bash
python settings_gui.py
\`\`\`

## Controls

| Key | Action |
|---|---|
| q | Quit |
| c | Calibrate steering center |
| r | Reset gear to 1 |

## Gestures

| Gesture | Action |
|---|---|
| Tilt wrists left/right | Steer |
| Right hand fist | Accelerate |
| Left hand fist | Brake |
| Both fists | Boost |
| Thumbs up | Gear up |
| Thumbs down | Gear down |
| Both hands open, held ~1.5s | Pause / resume |

## Project layout

\`\`\`
main.py                        entry point / main loop
config.py                      persistent settings
logger_setup.py                rotating file + console logging
camera.py                      cross-platform camera probing
hand_tracker.py                MediaPipe Hand Landmarker (Tasks API) wrapper
steering.py                    angle -> analog strength, calibration, smoothing
gestures.py                    fist/open/thumbs detection, gear + pause state
dashboard.py                   HUD rendering (theme-driven)
voice_commands.py              optional background voice recognition
analytics.py                   optional session CSV + chart export
settings_gui.py                optional pre-launch settings window
controller/
  keyboard_controller.py       pynput fallback
  gamepad_controller.py        vgamepad analog output
  output_manager.py            picks a backend, exposes one interface
\`\`\`

## Known limitations

- Analog gamepad output is Windows-only (vgamepad's constraint)
- Voice recognition needs an internet connection (Google speech API)
- HUD reflects gesture/system state, not real in-game telemetry
EOF