"""Rule-based pose and motion classifier for GESTURA Python tools."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import monotonic
from typing import Deque, Iterable, List, Sequence, Set

from .feature_engine import (
    INDEX_MCP,
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_MCP,
    PINKY_PIP,
    PINKY_TIP,
    RING_MCP,
    RING_PIP,
    RING_TIP,
    THUMB_IP,
    THUMB_TIP,
    WRIST,
    extract_hand_features,
    palm_center,
)
from .math_core import Vec3, circularity_score, direction_changes, distance, point
from .superpower_catalog import Superpower, match_powers


@dataclass(frozen=True)
class FingerState:
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool

    @property
    def count(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    @property
    def key(self) -> str:
        return "".join("1" if item else "0" for item in [self.thumb, self.index, self.middle, self.ring, self.pinky])


@dataclass(frozen=True)
class PoseResult:
    name: str
    fingers: FingerState
    confidence: float


@dataclass(frozen=True)
class HandResult:
    hand_id: str
    pose: PoseResult
    motions: frozenset[str]
    center: Vec3
    features: dict


@dataclass(frozen=True)
class FrameResult:
    hands: tuple[HandResult, ...]
    two_hand_motions: frozenset[str] = field(default_factory=frozenset)
    powers: tuple[Superpower, ...] = field(default_factory=tuple)


def _finger_up(landmarks: Sequence, tip: int, pip: int) -> bool:
    return point(landmarks[tip]).y < point(landmarks[pip]).y - 0.012


def _thumb_extended(landmarks: Sequence) -> bool:
    thumb_tip = point(landmarks[THUMB_TIP])
    thumb_ip = point(landmarks[THUMB_IP])
    index_mcp = point(landmarks[INDEX_MCP])
    return distance(thumb_tip, index_mcp) > distance(thumb_ip, index_mcp) * 1.12


def classify_pose(landmarks: Sequence) -> PoseResult:
    features = extract_hand_features(landmarks)
    thumb = _thumb_extended(landmarks)
    index = _finger_up(landmarks, INDEX_TIP, INDEX_PIP)
    middle = _finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring = _finger_up(landmarks, RING_TIP, RING_PIP)
    pinky = _finger_up(landmarks, PINKY_TIP, PINKY_PIP)
    fingers = FingerState(thumb, index, middle, ring, pinky)
    pose = "unknown"
    confidence = 0.68

    if features.pinch_index < 0.34:
        pose, confidence = "pinch", 0.92
    elif thumb and index and pinky and not middle and not ring:
        pose, confidence = "love", 0.88
    elif thumb and pinky and not index and not middle and not ring:
        pose, confidence = "phone", 0.86
    elif index and middle and pinky and not ring:
        pose, confidence = "web", 0.84
    elif index and pinky and not middle and not ring:
        pose, confidence = "rock", 0.88
    elif index and middle and ring and pinky and thumb:
        pose, confidence = "openPalm", 0.9
    elif index and middle and ring and pinky:
        pose, confidence = "four", 0.86
    elif not index and not middle and not ring and not pinky:
        pose, confidence = "fist", 0.91
    elif index and not middle and not ring and not pinky:
        pose, confidence = "point", 0.9
    elif index and middle and not ring and not pinky:
        pose, confidence = "peace", 0.9
    elif index and middle and ring and not pinky:
        pose, confidence = "three", 0.88
    elif features.openness > 2.6 and features.finger_spread > 1.2:
        pose, confidence = "claw", 0.78

    return PoseResult(pose, fingers, confidence)


def classify_motion(history: Iterable[Sequence], timestamps: Iterable[float] | None = None) -> Set[str]:
    frames = [frame for frame in history if len(frame) >= 21]
    if len(frames) < 4:
        return set()
    times = list(timestamps) if timestamps is not None else list(range(len(frames)))
    if len(times) != len(frames):
        times = list(range(len(frames)))

    centers = [palm_center(frame) for frame in frames]
    start, end = centers[0], centers[-1]
    dt = max(1e-6, times[-1] - times[0])
    dx, dy, dz = end.x - start.x, end.y - start.y, end.z - start.z
    speed = (dx * dx + dy * dy + dz * dz) ** 0.5 / dt
    xs = [p.x for p in centers]
    ys = [p.y for p in centers]
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    motions: Set[str] = set()

    if abs(dx) > 0.12 and abs(dx) > abs(dy) * 1.15:
        motions.add("swipeRight" if dx > 0 else "swipeLeft")
    if abs(dy) > 0.12 and abs(dy) > abs(dx) * 1.05:
        motions.add("swipeDown" if dy > 0 else "swipeUp")
    if speed > 0.045:
        motions.add("flick")
    if dz < -0.024 and speed > 0.012:
        motions.add("jab")
    if direction_changes(xs, 0.018) >= 4 and x_span > 0.08:
        motions.add("shake")
    if direction_changes(xs, 0.016) >= 3 and x_span > 0.13:
        motions.add("wave")
    if direction_changes(ys, 0.016) >= 3 and y_span > 0.11:
        motions.add("zigzag")
    if circularity_score(centers) > 0.62:
        signed = _signed_turn(centers)
        motions.add("circleCW" if signed > 0 else "circleCCW")
    if max(distance(center, sum_centroid(centers)) for center in centers) < 0.035 and len(frames) >= 12:
        motions.add("hold")
    return motions


def sum_centroid(values: Sequence[Vec3]) -> Vec3:
    return Vec3(
        sum(v.x for v in values) / len(values),
        sum(v.y for v in values) / len(values),
        sum(v.z for v in values) / len(values),
    )


def _signed_turn(values: Sequence[Vec3]) -> float:
    center = sum_centroid(values)
    total = 0.0
    for a, b in zip(values, values[1:]):
        va = Vec3(a.x - center.x, a.y - center.y)
        vb = Vec3(b.x - center.x, b.y - center.y)
        total += va.x * vb.y - va.y * vb.x
    return total


class GestureClassifier:
    """Stateful classifier that converts landmark frames into power matches."""

    def __init__(self, history_size: int = 28):
        self.history_size = history_size
        self.histories: dict[str, Deque[Sequence]] = defaultdict(lambda: deque(maxlen=history_size))
        self.times: dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=history_size))
        self.two_hand_history: Deque[tuple[float, float]] = deque(maxlen=history_size)

    def update(self, hands: Iterable[Sequence], labels: Iterable[str] | None = None, now: float | None = None) -> FrameResult:
        now = monotonic() if now is None else now
        hand_list = list(hands)
        labels_list = list(labels) if labels is not None else [f"hand-{idx}" for idx in range(len(hand_list))]
        results: List[HandResult] = []

        for idx, landmarks in enumerate(hand_list):
            hand_id = labels_list[idx] if idx < len(labels_list) else f"hand-{idx}"
            history = self.histories[hand_id]
            times = self.times[hand_id]
            history.append(landmarks)
            times.append(now)
            pose = classify_pose(landmarks)
            motions = classify_motion(history, times)
            features = extract_hand_features(landmarks, history).as_dict()
            results.append(HandResult(hand_id, pose, frozenset(motions), palm_center(landmarks), features))

        two_hand = self._two_hand_motions(results, now)
        primary = max(results, key=lambda item: len(item.motions), default=None)
        powers = ()
        if primary:
            powers = tuple(match_powers(primary.pose.name, primary.motions, two_hand))
        return FrameResult(tuple(results), frozenset(two_hand), powers)

    def update_mediapipe_results(self, results) -> FrameResult:
        landmarks = getattr(results, "multiHandLandmarks", None) or results.get("multiHandLandmarks", [])
        handed = getattr(results, "multiHandedness", None) or results.get("multiHandedness", [])
        labels = []
        for idx, hand in enumerate(handed):
            label = hand.get("label") if isinstance(hand, dict) else getattr(hand, "label", None)
            labels.append(label or f"hand-{idx}")
        return self.update(landmarks, labels)

    def _two_hand_motions(self, hands: Sequence[HandResult], now: float) -> Set[str]:
        motions: Set[str] = set()
        if len(hands) < 2:
            return motions
        a, b = hands[0], hands[1]
        gap = distance(a.center, b.center)
        self.two_hand_history.append((now, gap))
        if len(self.two_hand_history) < 5:
            return motions
        first_t, first_gap = self.two_hand_history[0]
        last_t, last_gap = self.two_hand_history[-1]
        dt = max(1e-6, last_t - first_t)
        velocity = (last_gap - first_gap) / dt
        if last_gap < 0.13 and velocity < -0.08:
            motions.add("clap")
        if last_gap - first_gap > 0.1:
            motions.add("expand")
        if last_gap - first_gap < -0.1 and first_gap > 0.18:
            motions.add("compress")
        if last_gap < 0.12 and len(self.two_hand_history) >= 12 and abs(velocity) < 0.015:
            motions.add("palmsTogetherHold")
        if a.pose.name == b.pose.name and abs(a.center.y - b.center.y) < 0.08 and last_gap > 0.18:
            motions.add("mirror")
        return motions

