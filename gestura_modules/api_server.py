"""Optional FastAPI API for GESTURA classification and power lookup."""

from __future__ import annotations

from typing import Any

from .gesture_classifier import GestureClassifier
from .simulator import classify_simulation
from .superpower_catalog import POWER_CATALOG, search_powers, to_json_ready


classifier = GestureClassifier()


def classify_payload(payload: dict[str, Any]) -> dict:
    hands = payload.get("hands") or payload.get("multiHandLandmarks") or []
    labels = payload.get("labels")
    result = classifier.update(hands, labels)
    return {
        "hands": [
            {
                "hand_id": hand.hand_id,
                "pose": hand.pose.name,
                "confidence": hand.pose.confidence,
                "motions": sorted(hand.motions),
                "features": hand.features,
            }
            for hand in result.hands
        ],
        "two_hand_motions": sorted(result.two_hand_motions),
        "powers": [power.name for power in result.powers],
    }


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError as exc:
        raise RuntimeError("Install FastAPI with: pip install fastapi uvicorn") from exc

    app = FastAPI(title="GESTURA Power API", version="1.0.0")

    @app.get("/health")
    def health():
        return {"ok": True, "powers": len(POWER_CATALOG)}

    @app.get("/powers")
    def powers(q: str = "", tag: str | None = None):
        return to_json_ready(search_powers(q, tag))

    @app.post("/classify")
    def classify(payload: dict[str, Any]):
        return classify_payload(payload)

    @app.get("/simulate")
    def simulate(pose: str = "openPalm", motion: str = "jab"):
        return classify_simulation(pose, motion)

    return app


app = None
try:
    app = create_app()
except RuntimeError:
    # FastAPI is optional. Importing this module should still work without it.
    app = None

