"""Report builders for GESTURA data."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .analytics import session_health
from .storage import export_csv, export_json


def build_markdown_report(gesture_events: Iterable[Mapping], superpower_events: Iterable[Mapping], title: str = "GESTURA Report") -> str:
    health = session_health(list(gesture_events), list(superpower_events))
    gesture_summary = health["gesture_summary"]
    super_summary = health["superpower_summary"]
    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Health score: {health['health_score']}",
        f"Total gestures: {gesture_summary['total']}",
        f"Unique gestures: {gesture_summary['unique']}",
        f"Average confidence: {gesture_summary['avg_confidence']:.3f}",
        f"Superpower uses: {super_summary['total']}",
        f"Power score: {super_summary['power_score']}",
        "",
        "## Top Gestures",
    ]
    lines.extend(f"- {name}: {count}" for name, count in gesture_summary["top_gestures"])
    lines.append("")
    lines.append("## Top Superpowers")
    lines.extend(f"- {name}: {count}" for name, count in super_summary["top_powers"])
    lines.append("")
    return "\n".join(lines)


def export_bundle(gesture_events: Iterable[Mapping], superpower_events: Iterable[Mapping], directory: str | Path) -> dict[str, Path]:
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    gesture_events = list(gesture_events)
    superpower_events = list(superpower_events)
    report = build_markdown_report(gesture_events, superpower_events)
    report_path = output_dir / "gestura_report.md"
    report_path.write_text(report, encoding="utf-8")
    return {
        "gestures_csv": export_csv(gesture_events, output_dir / "gesture_events.csv"),
        "superpowers_csv": export_csv(superpower_events, output_dir / "superpower_events.csv"),
        "gestures_json": export_json(gesture_events, output_dir / "gesture_events.json"),
        "superpowers_json": export_json(superpower_events, output_dir / "superpower_events.json"),
        "report": report_path,
    }

