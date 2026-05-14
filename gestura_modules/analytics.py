"""Analytics helpers for gesture and superpower event streams."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import sqrt
from typing import Iterable, Mapping


def _get(row: Mapping, key: str, default=None):
    return row.get(key, default)


def parse_time(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def summarize_gestures(events: Iterable[Mapping]) -> dict:
    events = list(events)
    names = Counter(str(_get(row, "gesture_name", "UNKNOWN")) for row in events)
    confidences = [float(_get(row, "confidence", 0.0) or 0.0) for row in events]
    return {
        "total": len(events),
        "unique": len(names),
        "top_gestures": names.most_common(10),
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "low_confidence_count": sum(value < 0.55 for value in confidences),
    }


def summarize_superpowers(events: Iterable[Mapping]) -> dict:
    events = list(events)
    powers = Counter(str(_get(row, "power_name", "UNKNOWN")) for row in events)
    duration = [float(_get(row, "duration_ms", 0.0) or 0.0) for row in events]
    return {
        "total": len(events),
        "top_powers": powers.most_common(12),
        "avg_duration_ms": sum(duration) / len(duration) if duration else 0.0,
        "power_score": power_score(events),
    }


def power_score(events: Iterable[Mapping]) -> int:
    score = 0.0
    seen = set()
    for row in events:
        name = str(_get(row, "power_name", "UNKNOWN"))
        seen.add(name)
        duration = float(_get(row, "duration_ms", 500.0) or 500.0)
        score += 12.0 + min(18.0, duration / 120.0)
    score += len(seen) * 25.0
    return int(round(score))


def build_heatmap(events: Iterable[Mapping], width_bins: int = 60, height_bins: int = 40) -> list[list[int]]:
    grid = [[0 for _ in range(height_bins)] for _ in range(width_bins)]
    for row in events:
        x = _get(row, "palm_x")
        y = _get(row, "palm_y")
        if x is None or y is None:
            continue
        ix = min(width_bins - 1, max(0, int(float(x) * width_bins)))
        iy = min(height_bins - 1, max(0, int(float(y) * height_bins)))
        grid[ix][iy] += 1
    return grid


def events_per_minute(events: Iterable[Mapping], time_key: str = "created_at") -> dict[str, int]:
    buckets = Counter()
    for row in events:
        ts = parse_time(_get(row, time_key))
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        bucket = ts.replace(second=0, microsecond=0).isoformat()
        buckets[bucket] += 1
    return dict(sorted(buckets.items()))


def session_health(gesture_events: Iterable[Mapping], superpower_events: Iterable[Mapping]) -> dict:
    gesture_events = list(gesture_events)
    superpower_events = list(superpower_events)
    gesture_summary = summarize_gestures(gesture_events)
    super_summary = summarize_superpowers(superpower_events)
    confidence = gesture_summary["avg_confidence"]
    power_ratio = super_summary["total"] / max(1, gesture_summary["total"])
    health = 100.0
    health -= max(0.0, 0.72 - confidence) * 80.0
    health -= 12.0 if gesture_summary["low_confidence_count"] > max(5, gesture_summary["total"] * 0.2) else 0.0
    health += min(12.0, power_ratio * 100.0)
    return {
        "health_score": round(max(0.0, min(100.0, health)), 1),
        "gesture_summary": gesture_summary,
        "superpower_summary": super_summary,
        "power_ratio": round(power_ratio, 3),
    }


def detect_motion_outliers(events: Iterable[Mapping], z_threshold: float = 2.5) -> list[dict]:
    events = list(events)
    speeds = []
    previous = None
    for row in events:
        x = _get(row, "palm_x")
        y = _get(row, "palm_y")
        if x is None or y is None:
            speeds.append(0.0)
            previous = None
            continue
        current = (float(x), float(y))
        if previous is None:
            speeds.append(0.0)
        else:
            speeds.append(sqrt((current[0] - previous[0]) ** 2 + (current[1] - previous[1]) ** 2))
        previous = current

    if not speeds:
        return []
    avg = sum(speeds) / len(speeds)
    variance = sum((value - avg) ** 2 for value in speeds) / len(speeds)
    std = sqrt(variance)
    if std <= 1e-9:
        return []
    outliers = []
    for row, speed in zip(events, speeds):
        z = (speed - avg) / std
        if z >= z_threshold:
            outliers.append({"event": dict(row), "speed": speed, "z_score": z})
    return outliers


def leaderboard_rows(gesture_events: Iterable[Mapping], superpower_events: Iterable[Mapping], username: str = "local") -> list[dict]:
    gesture_events = list(gesture_events)
    superpower_events = list(superpower_events)
    favorite = Counter(str(_get(row, "gesture_name", "UNKNOWN")) for row in gesture_events).most_common(1)
    return [{
        "username": username,
        "total_gestures": len(gesture_events),
        "favorite_gesture": favorite[0][0] if favorite else "NONE",
        "superpower_score": power_score(superpower_events),
    }]

