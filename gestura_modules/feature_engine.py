"""Feature extraction for MediaPipe hand landmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

from .math_core import Vec3, angle_between, centroid, circularity_score, direction_changes, distance, point, safe_div


WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

TIP_IDS = (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
PIP_IDS = (THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP)
MCP_IDS = (THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)


@dataclass(frozen=True)
class FeatureVector:
    palm_x: float
    palm_y: float
    palm_z: float
    scale: float
    openness: float
    finger_spread: float
    pinch_index: float
    pinch_middle: float
    pinch_ring: float
    pinch_pinky: float
    thumb_angle: float
    palm_angle: float
    wrist_to_index: float
    wrist_to_pinky: float
    path_speed: float = 0.0
    path_acceleration: float = 0.0
    path_curvature: float = 0.0
    circularity: float = 0.0
    x_direction_changes: int = 0
    y_direction_changes: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def _finger_up(lm: Sequence, tip: int, pip: int) -> bool:
    return point(lm[tip]).y < point(lm[pip]).y - 0.012


def hand_scale(landmarks: Sequence) -> float:
    palm_width = distance(landmarks[INDEX_MCP], landmarks[PINKY_MCP])
    palm_height = distance(landmarks[WRIST], landmarks[MIDDLE_MCP])
    return max(0.04, palm_width * 0.75 + palm_height * 0.85)


def palm_center(landmarks: Sequence) -> Vec3:
    return centroid([landmarks[WRIST], landmarks[INDEX_MCP], landmarks[MIDDLE_MCP], landmarks[PINKY_MCP]])


def extract_hand_features(landmarks: Sequence, history: Iterable | None = None) -> FeatureVector:
    """Create a compact numerical vector from 21 MediaPipe landmarks."""
    if len(landmarks) < 21:
        raise ValueError("Expected at least 21 hand landmarks")

    scale = hand_scale(landmarks)
    palm = palm_center(landmarks)
    tips = [point(landmarks[i]) for i in TIP_IDS]
    wrist = point(landmarks[WRIST])
    thumb_tip = point(landmarks[THUMB_TIP])
    index_tip = point(landmarks[INDEX_TIP])
    middle_tip = point(landmarks[MIDDLE_TIP])
    ring_tip = point(landmarks[RING_TIP])
    pinky_tip = point(landmarks[PINKY_TIP])
    up_count = sum(
        [
            _finger_up(landmarks, INDEX_TIP, INDEX_PIP),
            _finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP),
            _finger_up(landmarks, RING_TIP, RING_PIP),
            _finger_up(landmarks, PINKY_TIP, PINKY_PIP),
        ]
    )
    openness = safe_div(sum(distance(tip, palm) for tip in tips), scale * len(tips))
    spread = safe_div(distance(index_tip, pinky_tip), scale)
    palm_angle = angle_between(point(landmarks[INDEX_MCP]) - wrist, point(landmarks[PINKY_MCP]) - wrist)
    thumb_angle = angle_between(landmarks[THUMB_TIP], landmarks[THUMB_MCP], landmarks[INDEX_MCP])

    centers = []
    if history:
        centers = [palm_center(frame) for frame in history if len(frame) >= 21]
    path_speed = 0.0
    path_acceleration = 0.0
    x_flips = y_flips = 0
    circularity = 0.0
    path_curv = 0.0
    if len(centers) >= 3:
        speeds = [distance(a, b) for a, b in zip(centers, centers[1:])]
        path_speed = sum(speeds[-5:]) / max(1, min(5, len(speeds)))
        accel_values = [b - a for a, b in zip(speeds, speeds[1:])]
        path_acceleration = sum(accel_values[-5:]) / max(1, min(5, len(accel_values)))
        x_flips = direction_changes([p.x for p in centers])
        y_flips = direction_changes([p.y for p in centers])
        circularity = circularity_score(centers)
        path_curv = sum(abs(angle_between(centers[i - 1], centers[i], centers[i + 1])) for i in range(1, len(centers) - 1))
        path_curv = safe_div(path_curv, len(centers) - 2)

    return FeatureVector(
        palm_x=palm.x,
        palm_y=palm.y,
        palm_z=palm.z,
        scale=scale,
        openness=openness,
        finger_spread=spread,
        pinch_index=safe_div(distance(thumb_tip, index_tip), scale),
        pinch_middle=safe_div(distance(thumb_tip, middle_tip), scale),
        pinch_ring=safe_div(distance(thumb_tip, ring_tip), scale),
        pinch_pinky=safe_div(distance(thumb_tip, pinky_tip), scale),
        thumb_angle=thumb_angle,
        palm_angle=palm_angle,
        wrist_to_index=safe_div(distance(wrist, index_tip), scale),
        wrist_to_pinky=safe_div(distance(wrist, pinky_tip), scale),
        path_speed=path_speed,
        path_acceleration=path_acceleration,
        path_curvature=path_curv,
        circularity=circularity,
        x_direction_changes=x_flips,
        y_direction_changes=y_flips,
    )

