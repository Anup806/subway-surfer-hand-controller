from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean
from typing import Any, Deque, Dict, List, Optional, Tuple


@dataclass
class GestureState:
    current_direction: Optional[str] = None
    smoothed_point: Optional[Tuple[int, int]] = None
    raw_point: Optional[Tuple[int, int]] = None
    is_punch: bool = False
    zone: Optional[str] = None


class GestureController:
    def __init__(self, smoothing_window: int = 5, horizontal_line_ratio: float = 0.30) -> None:
        self.smoothing_window = max(1, smoothing_window)
        self.horizontal_line_ratio = horizontal_line_ratio
        self.state = GestureState()
        self._recent_points: Deque[Tuple[int, int]] = deque(maxlen=self.smoothing_window)

    def update(self, landmarks: Optional[List[Any]], frame_width: int, frame_height: int) -> GestureState:
        if not landmarks:
            self._recent_points.clear()
            self.state.current_direction = None
            self.state.smoothed_point = None
            self.state.raw_point = None
            self.state.is_punch = False
            self.state.zone = None
            return self.state

        landmark_map: Dict[int, Any] = {landmark.id: landmark for landmark in landmarks}
        raw_point = self._compute_palm_center(landmark_map)

        self.state.raw_point = raw_point
        self._recent_points.append(raw_point)
        smoothed_x = round(mean(point[0] for point in self._recent_points))
        smoothed_y = round(mean(point[1] for point in self._recent_points))
        smoothed_point = (smoothed_x, smoothed_y)
        self.state.smoothed_point = smoothed_point

        self.state.is_punch = self._is_punch(landmark_map)
        if self.state.is_punch:
            self.state.current_direction = "DOWN"
            self.state.zone = "PUNCH"
            return self.state

        self.state.zone = self._resolve_zone(smoothed_point, frame_width, frame_height)
        self.state.current_direction = self._resolve_direction(self.state.zone)
        return self.state

    def _compute_palm_center(self, landmark_map: Dict[int, Any]) -> Tuple[int, int]:
        anchor_ids = [0, 5, 9, 13, 17]
        anchor_points = [landmark_map[landmark_id] for landmark_id in anchor_ids if landmark_id in landmark_map]
        if not anchor_points:
            first_landmark = next(iter(landmark_map.values()))
            return first_landmark.x, first_landmark.y

        center_x = round(mean(point.x for point in anchor_points))
        center_y = round(mean(point.y for point in anchor_points))
        return center_x, center_y

    def _resolve_zone(self, point: Tuple[int, int], frame_width: int, frame_height: int) -> Optional[str]:
        left_line_x = frame_width / 3
        right_line_x = frame_width * 2 / 3
        horizontal_line_y = frame_height * self.horizontal_line_ratio
        x_coord, y_coord = point

        if x_coord < left_line_x:
            return "LEFT"
        if x_coord > right_line_x:
            return "RIGHT"
        if y_coord < horizontal_line_y:
            return "UP"
        return None

    def _resolve_direction(self, zone: Optional[str]) -> Optional[str]:
        if zone in {"LEFT", "RIGHT", "UP"}:
            return zone
        return None

    def _is_punch(self, landmark_map: Dict[int, Any]) -> bool:
        fingertip_ids = [4, 8, 12, 16, 20]
        palm_anchor_ids = [0, 5, 9, 13, 17]

        if not all(landmark_id in landmark_map for landmark_id in fingertip_ids + palm_anchor_ids):
            return False

        palm_center_x = mean(landmark_map[landmark_id].x for landmark_id in palm_anchor_ids)
        palm_center_y = mean(landmark_map[landmark_id].y for landmark_id in palm_anchor_ids)
        palm_center = (palm_center_x, palm_center_y)

        palm_span = max(
            ((landmark_map[5].x - landmark_map[17].x) ** 2 + (landmark_map[5].y - landmark_map[17].y) ** 2) ** 0.5,
            ((landmark_map[0].x - landmark_map[9].x) ** 2 + (landmark_map[0].y - landmark_map[9].y) ** 2) ** 0.5,
            1.0,
        )

        fingertip_distances = []
        for fingertip_id in fingertip_ids:
            tip = landmark_map[fingertip_id]
            distance = ((tip.x - palm_center[0]) ** 2 + (tip.y - palm_center[1]) ** 2) ** 0.5
            fingertip_distances.append(distance)

        average_tip_distance = mean(fingertip_distances)
        max_tip_distance = max(fingertip_distances)

        return average_tip_distance <= palm_span * 0.75 and max_tip_distance <= palm_span * 0.95

    def reset_neutral(self) -> None:
        self.state.current_direction = None
        self.state.smoothed_point = None
        self.state.raw_point = None
        self.state.is_punch = False
        self.state.zone = None
        self._recent_points.clear()

    def set_smoothing_window(self, smoothing_window: int) -> None:
        self.smoothing_window = max(1, smoothing_window)
        self._recent_points = deque(self._recent_points, maxlen=self.smoothing_window)