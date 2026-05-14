"""
╔══════════════════════════════════════════════════════════════════╗
║         GESTURA ULTRA — app.py  (Main Entry Point)              ║
║                                                                  ║
║  Run:  streamlit run app.py                                      ║
║                                                                  ║
║  Architecture:                                                   ║
║    • app.py          ← YOU ARE HERE (orchestrator)               ║
║    • exams.html      ← Full-screen webcam + gesture UI (main UI) ║
║    • gestura_powerpack.js  ← Superpower FX engine (inlined)     ║
║    • gestura_modules/      ← Python backend workers              ║
║        ├── gesture_classifier.py  ← Pose + motion recognition   ║
║        ├── superpower_catalog.py  ← Power definitions           ║
║        ├── feature_engine.py      ← Hand landmark math          ║
║        ├── math_core.py           ← Vector + geometry utils     ║
║        ├── analytics.py           ← Session stats               ║
║        ├── storage.py             ← JSONL event store           ║
║        ├── simulator.py           ← Offline gesture simulator   ║
║        ├── export_tools.py        ← CSV / Markdown reports      ║
║        └── api_server.py          ← FastAPI classify endpoint   ║
║                                                                  ║
║  Optional env vars (create a .env file):                        ║
║    SUPABASE_URL = https://YOUR_PROJECT.supabase.co               ║
║    SUPABASE_KEY = YOUR_SERVICE_ROLE_KEY                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import sys
import json
import pathlib
import threading
from datetime import datetime, timezone

# ── Ensure project root is importable regardless of CWD ──────────────────────
ROOT = pathlib.Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Load .env for local dev ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ── Streamlit ─────────────────────────────────────────────────────────────────
import streamlit as st

# ── Page config — MUST be first Streamlit call ───────────────────────────────
st.set_page_config(
    page_title="GESTURA ULTRA",
    page_icon="🖐",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/gestura/gestura",
        "About": "GESTURA ULTRA — Hand Motion AI",
    },
)

# ── Hide Streamlit chrome so the HTML fills the viewport cleanly ──────────────
st.markdown("""
<style>
  #MainMenu, footer, header,
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { display: none !important; }
  .main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
  }
  section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Load all Python backend workers
#
# Each module in gestura_modules/ is imported here once and cached.
# st.cache_resource means this runs ONCE per server process — not on every
# page rerun — so classifier state (motion history, buffers) is preserved.
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def _load_backend() -> dict:
    """Import every gestura_modules worker once and return as a shared dict."""
    workers: dict = {}

    # ── Superpower catalog ────────────────────────────────────────────────
    try:
        from gestura_modules.superpower_catalog import (
            POWER_CATALOG, search_powers, to_json_ready,
        )
        workers["POWER_CATALOG"]  = POWER_CATALOG
        workers["search_powers"]  = search_powers
        workers["to_json_ready"]  = to_json_ready
    except Exception as exc:
        workers["superpower_catalog_error"] = str(exc)

    # ── Gesture classifier ────────────────────────────────────────────────
    try:
        from gestura_modules.gesture_classifier import GestureClassifier
        workers["classifier"] = GestureClassifier()
    except Exception as exc:
        workers["gesture_classifier_error"] = str(exc)

    # ── Analytics ─────────────────────────────────────────────────────────
    try:
        from gestura_modules.analytics import (
            session_health, summarize_gestures, summarize_superpowers,
        )
        workers["session_health"]        = session_health
        workers["summarize_gestures"]    = summarize_gestures
        workers["summarize_superpowers"] = summarize_superpowers
    except Exception as exc:
        workers["analytics_error"] = str(exc)

    # ── Storage (JSONL event store) ───────────────────────────────────────
    try:
        from gestura_modules.storage import JsonlEventStore, export_csv, export_json
        workers["event_store"] = JsonlEventStore(ROOT / "gestura_events.jsonl")
        workers["export_csv"]  = export_csv
        workers["export_json"] = export_json
    except Exception as exc:
        workers["storage_error"] = str(exc)

    # ── Offline simulator ─────────────────────────────────────────────────
    try:
        from gestura_modules.simulator import classify_simulation
        workers["classify_simulation"] = classify_simulation
    except Exception as exc:
        workers["simulator_error"] = str(exc)

    # ── Export tools ──────────────────────────────────────────────────────
    try:
        from gestura_modules.export_tools import build_markdown_report
        workers["build_markdown_report"] = build_markdown_report
    except Exception as exc:
        workers["export_tools_error"] = str(exc)

    # ── API server classify function ──────────────────────────────────────
    try:
        from gestura_modules.api_server import classify_payload
        workers["classify_payload"] = classify_payload
    except Exception as exc:
        workers["api_server_error"] = str(exc)

    return workers


_backend = _load_backend()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Start FastAPI backend in a daemon thread (port 8765)
#
# The HTML frontend POSTs landmark data to http://localhost:8765/classify
# and receives Python-classified gesture + power results back in real time.
# If FastAPI/uvicorn are not installed the HTML falls back to its own
# JavaScript classifier — no crash.
# ═══════════════════════════════════════════════════════════════════════════════

def _start_api_server() -> None:
    """Launch the FastAPI classify/powers server silently in the background."""
    try:
        import uvicorn
        from gestura_modules.api_server import create_app
        api_app = create_app()
        config   = uvicorn.Config(
            api_app,
            host="0.0.0.0",
            port=8765,
            log_level="warning",
        )
        uvicorn.Server(config).run()
    except ImportError:
        pass   # FastAPI/uvicorn not installed — HTML uses JS classifier
    except OSError:
        pass   # Port already in use — server already running


# Start the API thread exactly once per Streamlit server process
if "api_thread_started" not in st.session_state:
    threading.Thread(target=_start_api_server, daemon=True).start()
    st.session_state["api_thread_started"] = True


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Build the HTML payload
#
# Steps:
#   1. Read exams.html  (webcam + MediaPipe + gesture HUD)
#   2. Inline gestura_powerpack.js so no separate file server is needed
#   3. Inject window.PYTHON_POWERS  — live Python catalog as a JS global
#      (keeps the HTML superpower engine in sync with Python definitions)
#   4. Inject window.GESTURA_API    — URL of the FastAPI backend
#
# @st.cache_data caches the built HTML string so the file I/O only happens
# once per server process even across reruns.
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _build_html() -> str:
    html_path = ROOT / "exams.html"
    js_path   = ROOT / "gestura_powerpack.js"

    if not html_path.exists():
        return "<h1 style='color:red'>exams.html not found — place it next to app.py</h1>"

    html = html_path.read_text(encoding="utf-8")

    # ── Inline gestura_powerpack.js ───────────────────────────────────────
    # Replaces the <script src="gestura_powerpack.js"> tag so the HTML is
    # self-contained and doesn't need a separate static file server.
    if js_path.exists():
        js_code = js_path.read_text(encoding="utf-8")
        html = html.replace(
            '<script src="gestura_powerpack.js"></script>',
            f"<script>\n/* gestura_powerpack.js — inlined by app.py */\n{js_code}\n</script>",
        )

    # ── Build JSON of live Python power catalog ───────────────────────────
    powers_json = "[]"
    if "to_json_ready" in _backend and "POWER_CATALOG" in _backend:
        try:
            powers_json = json.dumps(
                _backend["to_json_ready"](_backend["POWER_CATALOG"].values()),
                ensure_ascii=False,
            )
        except Exception:
            pass

    # ── Bootstrap script — injected before </head> ────────────────────────
    # These globals are available to all JS in exams.html the moment it loads.
    bootstrap = f"""
<script>
/* ── Injected by app.py ─────────────────────────────────────────────── */
window.PYTHON_POWERS = {powers_json};        // Live catalog from gestura_modules
window.GESTURA_API   = 'http://localhost:8765'; // FastAPI backend (/classify, /powers)
console.log('[GESTURA] Python backend powers loaded:', window.PYTHON_POWERS.length);
</script>
"""
    html = html.replace("</head>", bootstrap + "\n</head>", 1)
    return html


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Render exams.html as the primary (fullscreen) UI component
#
# exams.html is the MAIN user interface: webcam feed, MediaPipe hand tracking,
# gesture classification HUD, and superpower visual effects all live there.
# Everything below this call is a supporting control panel.
# ═══════════════════════════════════════════════════════════════════════════════

st.components.v1.html(
    _build_html(),
    height=820,      # Adjust if your display is taller or shorter
    scrolling=False,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Control panel (rendered below the gesture viewport)
#
# Three columns:
#   • Backend worker status — shows which modules loaded successfully
#   • Live power catalog    — table of all superpowers from Python backend
#   • Analytics & export   — event counts, gesture summaries, classifier test
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
col_status, col_catalog, col_analytics = st.columns([1, 2, 2])

# ── Column 1: Worker status ───────────────────────────────────────────────────
with col_status:
    st.markdown("#### ⚙️ Backend Workers")
    _worker_checks = [
        ("superpower_catalog", "POWER_CATALOG"),
        ("gesture_classifier", "classifier"),
        ("analytics",          "summarize_gestures"),
        ("storage",            "event_store"),
        ("simulator",          "classify_simulation"),
        ("export_tools",       "build_markdown_report"),
        ("api_server",         "classify_payload"),
    ]
    for module_name, key in _worker_checks:
        loaded = key in _backend
        err    = _backend.get(f"{module_name}_error", "")
        st.markdown(
            f"{'🟢' if loaded else '🔴'} `{module_name}`"
            + (f"  \n<small style='color:#f88'>{err}</small>" if err else ""),
            unsafe_allow_html=True,
        )

# ── Column 2: Live Python power catalog ──────────────────────────────────────
with col_catalog:
    st.markdown("#### ⚡ Power Catalog (Python backend)")
    if "POWER_CATALOG" in _backend:
        import pandas as pd
        catalog_rows = [
            {
                "Power":   p.name,
                "Trigger": (
                    p.trigger.pose
                    or p.trigger.two_hand
                    or p.trigger.motion
                    or "—"
                ),
                "Effect":  p.effect,
            }
            for p in list(_backend["POWER_CATALOG"].values())[:20]
        ]
        st.dataframe(pd.DataFrame(catalog_rows), use_container_width=True, height=260)
    else:
        st.warning("Power catalog not loaded — check worker status.")

# ── Column 3: Analytics, simulator, export ───────────────────────────────────
with col_analytics:
    st.markdown("#### 📊 Analytics & Export")

    # Load recorded events from the JSONL store
    events: list = []
    if "event_store" in _backend:
        try:
            store  = _backend["event_store"]
            events = list(store.load_all()) if hasattr(store, "load_all") else []
        except Exception:
            pass

    st.caption(f"Recorded events: **{len(events)}**")

    if events and "summarize_gestures" in _backend:
        try:
            st.json(_backend["summarize_gestures"](events), expanded=False)
        except Exception as exc:
            st.caption(f"Summary error: {exc}")

    # ── Python classifier test UI ─────────────────────────────────────────
    if "classify_simulation" in _backend:
        st.markdown("**🧪 Test Python Classifier**")
        sim_col1, sim_col2 = st.columns(2)
        pose_choice   = sim_col1.selectbox(
            "Pose",
            ["openPalm", "fist", "point", "peace", "pinch", "rock", "love"],
            key="sim_pose",
        )
        motion_choice = sim_col2.selectbox(
            "Motion",
            ["jab", "swipe_left", "swipe_right", "circle", "push", "pull", "wave"],
            key="sim_motion",
        )
        if st.button("Run Classifier", use_container_width=True):
            try:
                st.json(_backend["classify_simulation"](pose_choice, motion_choice))
            except Exception as exc:
                st.error(f"Classifier error: {exc}")

    # ── Export button ─────────────────────────────────────────────────────
    if events and "export_csv" in _backend:
        try:
            csv_bytes = _backend["export_csv"](events).encode("utf-8")
            st.download_button(
                "⬇ Export Events (CSV)",
                data=csv_bytes,
                file_name=f"gestura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception:
            pass
