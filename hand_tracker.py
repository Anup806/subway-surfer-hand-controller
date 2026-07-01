from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from urllib.request import urlretrieve

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_FILENAME = "hand_landmarker.task"
HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
]


@dataclass(frozen=True)
class HandLandmark:
    id: int
    x: int
    y: int
    x_norm: float
    y_norm: float


class HandTracker:
    def __init__(self, max_hands: int = 1, detection_confidence: float = 0.7, tracking_confidence: float = 0.7) -> None:
        self._model_path = self._ensure_model_file()
        self._landmarker = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(self._model_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=max_hands,
                min_hand_detection_confidence=detection_confidence,
                min_tracking_confidence=tracking_confidence,
            )
        )
        self._timestamp_ms = 0

    def _ensure_model_file(self) -> Path:
        model_path = Path(__file__).with_name(MODEL_FILENAME)
        if not model_path.exists():
            try:
                urlretrieve(MODEL_URL, model_path)
            except Exception as exc:
                raise RuntimeError(
                    "Unable to download the MediaPipe hand_landmarker.task model. "
                    "Check your internet connection or download the file manually from the official MediaPipe model URL."
                ) from exc
        return model_path

    def process(self, frame) -> Tuple[List[HandLandmark], Optional[str], object]:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self._timestamp_ms += 33
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)

        landmarks: List[HandLandmark] = []
        hand_label: Optional[str] = None

        if result.hand_landmarks:
            hand_landmarks = result.hand_landmarks[0]
            handedness = result.handedness[0][0].category_name if result.handedness else None
            hand_label = handedness
            height, width = frame.shape[:2]

            for landmark_id, landmark in enumerate(hand_landmarks):
                pixel_x = int(landmark.x * width)
                pixel_y = int(landmark.y * height)
                landmarks.append(
                    HandLandmark(
                        id=landmark_id,
                        x=pixel_x,
                        y=pixel_y,
                        x_norm=landmark.x,
                        y_norm=landmark.y,
                    )
                )

            self._draw_landmarks(frame, landmarks)

        return landmarks, hand_label, frame

    def _draw_landmarks(self, frame, landmarks: List[HandLandmark]) -> None:
        points = {landmark.id: (landmark.x, landmark.y) for landmark in landmarks}

        for start_id, end_id in HAND_CONNECTIONS:
            if start_id in points and end_id in points:
                cv2.line(frame, points[start_id], points[end_id], (0, 255, 0), 2, cv2.LINE_AA)

        for landmark in landmarks:
            color = (0, 0, 255) if landmark.id == 8 else (255, 165, 0)
            cv2.circle(frame, (landmark.x, landmark.y), 5, color, cv2.FILLED)

    def release(self) -> None:
        self._landmarker.close()