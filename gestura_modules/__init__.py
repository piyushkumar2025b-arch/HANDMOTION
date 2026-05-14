"""Additive Python module pack for the GESTURA hand-motion project.

These modules provide reusable math, recognition, superpower, analytics,
storage, simulation, and API helpers.

NOTE: Heavy imports (GestureClassifier, feature extraction) are intentionally
lazy so that the Streamlit dashboard can import only what it needs without
pulling in optional deps (FastAPI, MediaPipe, etc.).
"""

# Light, always-safe exports
from .superpower_catalog import POWER_CATALOG, Superpower, PowerTrigger
from .analytics import session_health, summarize_gestures, summarize_superpowers
from .storage import JsonlEventStore, export_csv, export_json

__all__ = [
    # Superpower catalog
    "POWER_CATALOG",
    "Superpower",
    "PowerTrigger",
    # Analytics
    "session_health",
    "summarize_gestures",
    "summarize_superpowers",
    # Storage
    "JsonlEventStore",
    "export_csv",
    "export_json",
]

# Heavy runtime modules — only imported on demand by the dashboard's try/except
# GestureClassifier, classify_pose, classify_motion → gestura_modules.gesture_classifier
# extract_hand_features, FeatureVector         → gestura_modules.feature_engine
