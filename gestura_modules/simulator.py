"""Synthetic hand-landmark generator for testing gesture powers."""

from __future__ import annotations

from math import cos, pi, sin
from typing import Iterable, List

from .gesture_classifier import GestureClassifier


def base_hand(cx: float = 0.5, cy: float = 0.55, scale: float = 0.18) -> list[dict]:
    """Return a simple 21-point hand in MediaPipe landmark order."""
    x_offsets = [0.0, -0.08, -0.12, -0.15, -0.18, -0.05, -0.06, -0.065, -0.07, 0.0, 0.0, 0.0, 0.0, 0.05, 0.06, 0.065, 0.07, 0.1, 0.12, 0.135, 0.15]
    y_offsets = [0.13, 0.07, 0.02, -0.03, -0.08, 0.0, -0.08, -0.16, -0.24, -0.02, -0.12, -0.22, -0.32, 0.0, -0.09, -0.18, -0.27, 0.04, -0.04, -0.12, -0.2]
    return [{"x": cx + x * scale, "y": cy + y * scale, "z": 0.0} for x, y in zip(x_offsets, y_offsets)]


def apply_pose(landmarks: list[dict], pose: str) -> list[dict]:
    lm = [dict(point) for point in landmarks]
    folded = {
        "fist": [8, 12, 16, 20],
        "point": [12, 16, 20],
        "peace": [16, 20],
        "three": [20],
        "rock": [12, 16],
        "pinch": [],
        "love": [12, 16],
        "phone": [8, 12, 16],
        "web": [16],
        "claw": [],
    }
    if pose in folded:
        for tip in folded[pose]:
            lm[tip]["y"] += 0.11
    if pose == "pinch":
        lm[4]["x"], lm[4]["y"] = lm[8]["x"] + 0.006, lm[8]["y"] + 0.006
    if pose == "claw":
        for tip in [8, 12, 16, 20]:
            lm[tip]["y"] += 0.06
    if pose == "phone":
        lm[4]["x"] -= 0.03
        lm[20]["y"] -= 0.03
    return lm


def motion_path(motion: str, frames: int = 24, amplitude: float = 0.18) -> list[tuple[float, float, float]]:
    path = []
    for i in range(frames):
        t = i / max(1, frames - 1)
        if motion == "swipeRight":
            path.append((-amplitude / 2 + amplitude * t, 0.0, 0.0))
        elif motion == "swipeLeft":
            path.append((amplitude / 2 - amplitude * t, 0.0, 0.0))
        elif motion == "swipeUp":
            path.append((0.0, amplitude / 2 - amplitude * t, 0.0))
        elif motion == "swipeDown":
            path.append((0.0, -amplitude / 2 + amplitude * t, 0.0))
        elif motion == "circleCW":
            path.append((cos(t * 2 * pi) * amplitude * 0.5, sin(t * 2 * pi) * amplitude * 0.5, 0.0))
        elif motion == "circleCCW":
            path.append((cos(-t * 2 * pi) * amplitude * 0.5, sin(-t * 2 * pi) * amplitude * 0.5, 0.0))
        elif motion in {"wave", "shake"}:
            path.append((sin(t * 6 * pi) * amplitude * 0.45, 0.0, 0.0))
        elif motion == "jab":
            path.append((0.0, 0.0, -amplitude * t))
        elif motion == "hold":
            path.append((sin(t * 2 * pi) * 0.006, cos(t * 2 * pi) * 0.006, 0.0))
        else:
            path.append((0.0, 0.0, 0.0))
    return path


def simulate_sequence(pose: str, motion: str, frames: int = 24) -> list[list[dict]]:
    template = apply_pose(base_hand(), pose)
    sequence = []
    for dx, dy, dz in motion_path(motion, frames=frames):
        frame = []
        for point in template:
            item = dict(point)
            item["x"] += dx
            item["y"] += dy
            item["z"] += dz
            frame.append(item)
        sequence.append(frame)
    return sequence


def classify_simulation(pose: str, motion: str, frames: int = 24) -> dict:
    classifier = GestureClassifier()
    result = None
    for idx, frame in enumerate(simulate_sequence(pose, motion, frames=frames)):
        result = classifier.update([frame], ["sim"], now=idx / 30.0)
    return {
        "pose": pose,
        "motion": motion,
        "detected_pose": result.hands[0].pose.name if result and result.hands else "none",
        "detected_motions": sorted(result.hands[0].motions) if result and result.hands else [],
        "powers": [power.name for power in result.powers] if result else [],
    }


def batch_simulate(pairs: Iterable[tuple[str, str]]) -> list[dict]:
    return [classify_simulation(pose, motion) for pose, motion in pairs]

