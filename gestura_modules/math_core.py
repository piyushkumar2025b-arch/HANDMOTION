"""Numerical helpers for hand-motion analysis.

Dependency-free. Works with MediaPipe-style landmarks represented as
dicts, tuples, lists, or dataclasses exposing x/y/z attributes.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import acos, atan2, cos, hypot, isfinite, pi, sin, sqrt
from statistics import mean
from typing import Iterable, List, Sequence

EPS = 1e-9
TAU = pi * 2.0


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float = 0.0

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vec3":
        """Support scalar * Vec3 in addition to Vec3 * scalar."""
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> "Vec3":
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> "Vec3":
        """Unary negation: -vec."""
        return Vec3(-self.x, -self.y, -self.z)

    def __abs__(self) -> float:
        """abs(vec) returns the magnitude."""
        return self.mag()

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def mag(self) -> float:
        return sqrt(self.dot(self))

    def normalized(self) -> "Vec3":
        m = self.mag()
        return self if m < EPS else self * (1.0 / m)

    def as_tuple(self) -> tuple:
        return (self.x, self.y, self.z)


def clamp(value: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, value))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return default if abs(denominator) < EPS else numerator / denominator


def point(value) -> Vec3:
    """Convert a MediaPipe landmark-like value into Vec3."""
    if isinstance(value, Vec3):
        return value
    if isinstance(value, dict):
        return Vec3(float(value.get("x", 0.0)), float(value.get("y", 0.0)), float(value.get("z", 0.0)))
    if hasattr(value, "x") and hasattr(value, "y"):
        return Vec3(float(value.x), float(value.y), float(getattr(value, "z", 0.0)))
    if isinstance(value, (list, tuple)):
        z = value[2] if len(value) > 2 else 0.0
        return Vec3(float(value[0]), float(value[1]), float(z))
    raise TypeError(f"Cannot convert {type(value)!r} to Vec3")


def points(values: Iterable) -> List[Vec3]:
    return [point(item) for item in values]


def distance(a, b, use_z: bool = False) -> float:
    pa, pb = point(a), point(b)
    if use_z:
        return (pa - pb).mag()
    return hypot(pa.x - pb.x, pa.y - pb.y)


def centroid(values: Iterable) -> Vec3:
    """Return the mean position of a set of landmarks."""
    pts = [point(v) for v in values]
    if not pts:
        return Vec3(0.0, 0.0, 0.0)
    n = len(pts)
    return Vec3(
        sum(p.x for p in pts) / n,
        sum(p.y for p in pts) / n,
        sum(p.z for p in pts) / n,
    )


def angle_between(a, b, c=None) -> float:
    """Angle at vertex b, or angle between two vectors from origin.

    Two-arg form: angle between vectors a and b (treated as Vec3 from origin).
    Three-arg form: angle at point b formed by a->b->c.
    """
    if c is None:
        va, vb = point(a).normalized(), point(b).normalized()
        dot = clamp(va.dot(vb), -1.0, 1.0)
        return acos(dot)
    pa, pb, pc = point(a), point(b), point(c)
    v1 = (pa - pb).normalized()
    v2 = (pc - pb).normalized()
    dot = clamp(v1.dot(v2), -1.0, 1.0)
    return acos(dot)


def direction_changes(values: Sequence[float], threshold: float = 0.01) -> int:
    """Count direction reversals in a 1-D signal, ignoring noise < threshold."""
    changes = 0
    direction = 0
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        if abs(delta) < threshold:
            continue
        new_dir = 1 if delta > 0 else -1
        if direction != 0 and new_dir != direction:
            changes += 1
        direction = new_dir
    return changes


def resample_path(path: Iterable, n: int) -> List[Vec3]:
    """Resample a path to exactly n evenly-spaced points by arc length."""
    pts = [point(p) for p in path]
    if len(pts) < 2:
        return pts * n if pts else []
    dists = [0.0]
    for a, b in zip(pts, pts[1:]):
        dists.append(dists[-1] + (a - b).mag())
    total = dists[-1]
    if total < EPS:
        return [pts[0]] * n
    targets = [total * i / max(1, n - 1) for i in range(n)]
    result: List[Vec3] = []
    j = 0
    for target in targets:
        while j < len(pts) - 2 and dists[j + 1] < target:
            j += 1
        seg = dists[j + 1] - dists[j]
        t = 0.0 if seg < EPS else (target - dists[j]) / seg
        result.append(Vec3(
            pts[j].x + t * (pts[j + 1].x - pts[j].x),
            pts[j].y + t * (pts[j + 1].y - pts[j].y),
            pts[j].z + t * (pts[j + 1].z - pts[j].z),
        ))
    return result


def circularity_score(path: Iterable, samples: int = 32) -> float:
    """Score 0–1 of how circular a path is (1 = perfect circle)."""
    pts = resample_path(path, samples)
    if len(pts) < 6:
        return 0.0
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    radii = [hypot(p.x - cx, p.y - cy) for p in pts]
    avg_r = mean(radii) or EPS
    variance = mean((r - avg_r) ** 2 for r in radii)
    radius_stability = 1.0 / (1.0 + sqrt(variance) / avg_r)
    angles = [atan2(p.y - cy, p.x - cx) for p in pts]
    travel = 0.0
    for prev_angle, curr_angle in zip(angles, angles[1:]):
        delta = curr_angle - prev_angle
        while delta > pi:
            delta -= TAU
        while delta < -pi:
            delta += TAU
        travel += delta
    turn_score = clamp(abs(travel) / TAU, 0.0, 1.0)
    return radius_stability * turn_score


def curvature(path: Iterable) -> float:
    pts = points(path)
    if len(pts) < 3:
        return 0.0
    total = 0.0
    for i in range(1, len(pts) - 1):
        total += abs(angle_between(pts[i - 1], pts[i], pts[i + 1]))
    return total / max(1, len(pts) - 2)


def exponential_smooth(values: Sequence[float], alpha: float = 0.35) -> List[float]:
    if not values:
        return []
    alpha = clamp(alpha, 0.0, 1.0)
    smoothed = [float(values[0])]
    for value in values[1:]:
        smoothed.append(smoothed[-1] + alpha * (float(value) - smoothed[-1]))
    return smoothed


def dynamic_time_warping(path_a: Iterable, path_b: Iterable, samples: int = 32) -> float:
    a = resample_path(path_a, samples)
    b = resample_path(path_b, samples)
    if not a or not b:
        return 0.0
    prev = [float("inf")] * (len(b) + 1)
    prev[0] = 0.0
    for pa in a:
        row = [float("inf")]
        for j, pb in enumerate(b, start=1):
            cost = distance(pa, pb)
            row.append(cost + min(row[j - 1], prev[j], prev[j - 1]))
        prev = row
    value = prev[-1] / max(1, samples)
    return value if isfinite(value) else float("inf")


class Kalman1D:
    """Small 1D Kalman filter for landmark smoothing."""

    def __init__(self, process_noise: float = 0.008, measurement_noise: float = 0.05):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimate = 0.0
        self.error = 1.0
        self.ready = False

    def update(self, measurement: float) -> float:
        if not self.ready:
            self.estimate = float(measurement)
            self.ready = True
            return self.estimate
        self.error += self.process_noise
        gain = self.error / (self.error + self.measurement_noise)
        self.estimate += gain * (float(measurement) - self.estimate)
        self.error *= 1.0 - gain
        return self.estimate

    def reset(self) -> None:
        self.estimate = 0.0
        self.error = 1.0
        self.ready = False


class OneEuroFilter:
    """Adaptive smoothing filter for live hand cursor movement."""

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.03, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.last_value: float | None = None
        self.last_derivative = 0.0
        self.last_time: float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (TAU * cutoff)
        return 1.0 / (1.0 + tau / max(EPS, dt))

    def update(self, value: float, timestamp: float) -> float:
        value = float(value)
        if self.last_time is None:
            self.last_value = value
            self.last_time = timestamp
            return value
        dt = max(EPS, timestamp - self.last_time)
        derivative = (value - self.last_value) / dt
        d_alpha = self._alpha(self.d_cutoff, dt)
        derivative_hat = d_alpha * derivative + (1.0 - d_alpha) * self.last_derivative
        cutoff = self.min_cutoff + self.beta * abs(derivative_hat)
        alpha = self._alpha(cutoff, dt)
        filtered = alpha * value + (1.0 - alpha) * self.last_value
        self.last_value = filtered
        self.last_derivative = derivative_hat
        self.last_time = timestamp
        return filtered

    def reset(self) -> None:
        self.last_value = None
        self.last_derivative = 0.0
        self.last_time = None
