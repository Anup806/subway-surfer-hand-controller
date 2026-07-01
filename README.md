# Subway Surfer Hand Controller

Control Subway Surfers on Windows with your webcam and hand position.

## What it does

- Detects one hand using MediaPipe Hands Tasks.
- Draws two vertical guides and one horizontal guide on the webcam feed.
- Uses the palm center to decide movement zones.
- Detects a fist or punch gesture for down.
- Sends arrow key input with either tap mode or held-key mode.
- Shows live coordinates, zone, punch state, and debug info on the webcam feed.

## Files

- `main.py` runs the application.
- `hand_tracker.py` handles MediaPipe hand detection and drawing landmarks.
- `gesture_controller.py` smooths palm-center motion and converts movement into zone-based directions.
- `keyboard_control.py` sends arrow key input in tap or hold mode.
- `requirements.txt` lists dependencies.

## Setup on Windows 11

1. Open PowerShell in the project folder.
2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

The first run will download the MediaPipe hand landmark model automatically into the project folder.

5. Run the app:

```powershell
python main.py
```

6. Bring Subway Surfers to the foreground before using the controls.

## Controls

- Keep an open palm in the middle lower zone for no input.
- Move your hand center into the left section to trigger left.
- Move your hand center into the right section to trigger right.
- Move your hand center above the horizontal line in the middle section to trigger up.
- Make a fist or punch to trigger down, even if your hand is still in the middle normal zone.
- Tap mode sends a quick key press and release when a direction is detected.
- Hold mode keeps the arrow key pressed until the direction returns to neutral.
- `]` and `[` adjust smoothing window size.
- `t` switches to tap mode.
- `h` switches to hold mode.
- `q` quits.

## Troubleshooting

- If the webcam does not open, check Windows camera permissions and ensure no other app is using the camera.
- If movement feels jittery, increase the smoothing window.
- If Subway Surfers does not react, make sure the game window is focused and that keyboard control is allowed.
- If `pynput` fails to send input, run the app normally on the desktop, not from a restricted terminal or remote session.
- If you see a model download error, confirm the machine can reach `storage.googleapis.com` or download `hand_landmarker.task` manually into the project folder.

## Notes

- The hand center is smoothed across a short frame window to reduce jitter.
- For best results, keep your hand well lit and inside the camera frame.