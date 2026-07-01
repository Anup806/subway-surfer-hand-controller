from __future__ import annotations

import cv2

from gesture_controller import GestureController
from hand_tracker import HandTracker
from keyboard_control import KeyboardController


WINDOW_NAME = "Subway Surfer Hand Control"
CAMERA_INDEX = 0
DEFAULT_SMOOTHING_WINDOW = 5
DEFAULT_KEY_MODE = "tap"
LEFT_LINE_RATIO = 1 / 3
RIGHT_LINE_RATIO = 2 / 3
HORIZONTAL_LINE_RATIO = 0.30


def draw_overlay(frame, state, smoothing_window: int, key_mode: str) -> None:
    height, width = frame.shape[:2]
    left_line_x = int(width * LEFT_LINE_RATIO)
    right_line_x = int(width * RIGHT_LINE_RATIO)
    horizontal_line_y = int(height * HORIZONTAL_LINE_RATIO)

    cv2.line(frame, (left_line_x, 0), (left_line_x, height), (255, 255, 255), 2, cv2.LINE_AA)
    cv2.line(frame, (right_line_x, 0), (right_line_x, height), (255, 255, 255), 2, cv2.LINE_AA)
    cv2.line(frame, (0, horizontal_line_y), (width, horizontal_line_y), (0, 255, 255), 2, cv2.LINE_AA)

    if state.smoothed_point is None:
        current_x, current_y = 0, 0
    else:
        current_x, current_y = state.smoothed_point

    current_text = f"Palm center: ({current_x}, {current_y})"
    direction_text = f"Direction: {state.current_direction or 'NONE'}"
    smoothing_text = f"Smoothing: {smoothing_window} frames"
    punch_text = f"Punch: {'YES' if state.is_punch else 'NO'}"
    zone_text = f"Zone: {state.zone or 'CENTER'}"
    mode_text = f"Mode: {key_mode.upper()}"

    overlay_y = 30
    for text in [current_text, direction_text, zone_text, punch_text, smoothing_text, mode_text]:
        cv2.putText(frame, text, (20, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        overlay_y += 30

    cv2.putText(
        frame,
        "Zones: left | middle-up | right | punch anywhere = down. Keys: [/] smoothing | t=tap | h=hold | q=quit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


def main() -> None:
    tracker = HandTracker(max_hands=1, detection_confidence=0.7, tracking_confidence=0.7)
    gesture_controller = GestureController(smoothing_window=DEFAULT_SMOOTHING_WINDOW, horizontal_line_ratio=HORIZONTAL_LINE_RATIO)
    keyboard = KeyboardController(mode=DEFAULT_KEY_MODE)

    capture = cv2.VideoCapture(CAMERA_INDEX)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    capture.set(cv2.CAP_PROP_FPS, 30)

    if not capture.isOpened():
        raise RuntimeError("Could not open webcam. Check camera permissions and index.")

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            landmarks, hand_label, annotated_frame = tracker.process(frame)

            state = gesture_controller.update(landmarks, annotated_frame.shape[1], annotated_frame.shape[0])

            keyboard.set_direction(state.current_direction)
            draw_overlay(
                annotated_frame,
                state,
                gesture_controller.smoothing_window,
                keyboard.mode,
            )

            if state.smoothed_point is not None:
                cv2.circle(annotated_frame, state.smoothed_point, 10, (0, 0, 255), cv2.FILLED)
                cv2.putText(
                    annotated_frame,
                    f"Center: {state.smoothed_point}",
                    (state.smoothed_point[0] + 10, state.smoothed_point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )

            if hand_label:
                cv2.putText(
                    annotated_frame,
                    f"Hand: {hand_label}",
                    (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 200, 0),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imshow(WINDOW_NAME, annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("["):
                new_window = max(1, gesture_controller.smoothing_window - 1)
                gesture_controller.set_smoothing_window(new_window)
            if key == ord("]"):
                gesture_controller.set_smoothing_window(gesture_controller.smoothing_window + 1)
            if key == ord("t"):
                keyboard.set_mode("tap")
            if key == ord("h"):
                keyboard.set_mode("hold")

    finally:
        keyboard.reset()
        tracker.release()
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()