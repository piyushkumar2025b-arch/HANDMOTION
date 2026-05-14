"""
GESTURA ULTRA — Streamlit Analytics Dashboard
==============================================
Run: streamlit run gestura_dashboard.py

Set env vars (create a .env file or set in environment):
  SUPABASE_URL=https://YOUR_PROJECT.supabase.co
  SUPABASE_KEY=YOUR_SERVICE_ROLE_KEY

Without Supabase, the dashboard runs in DEMO MODE with synthetic data.
"""

import os
import random
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Load .env for local dev; on Streamlit Cloud secrets come via st.secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_env(key: str, default: str = "") -> str:
    """Read from st.secrets first (Streamlit Cloud), then os.environ (.env / system)."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="GESTURA ULTRA",
    page_icon="🖐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/gestura/gestura",
        "Report a bug": None,
        "About": "GESTURA ULTRA v3.0 — Hand Motion Analytics",
    },
)

# ─── CUSTOM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');
  html, body, [data-testid="stApp"] { background: #020408 !important; }
  .main .block-container { background: #020408; padding-top: 1rem; }
  h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f5ff !important; letter-spacing: 0.04em; }
  .metric-card {
    background: rgba(0,245,255,0.04);
    border: 1px solid rgba(0,245,255,0.18);
    border-left: 3px solid #00f5ff;
    padding: 14px 18px;
    border-radius: 4px;
    margin-bottom: 8px;
  }
  .power-badge {
    display: inline-block;
    background: rgba(255,106,0,0.1);
    border: 1px solid rgba(255,106,0,0.35);
    padding: 3px 10px;
    border-radius: 3px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: #ff9955;
    margin-bottom: 4px;
  }
  .demo-banner {
    background: rgba(255,180,0,0.08);
    border: 1px solid rgba(255,180,0,0.3);
    border-radius: 4px;
    padding: 8px 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px;
    color: #ffb700;
    margin-bottom: 12px;
  }
  [data-testid="stMetricValue"] {
    color: #39ff14 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1.9rem !important;
  }
  [data-testid="stMetricLabel"] { color: rgba(0,245,255,0.7) !important; font-size: 0.75rem !important; }
  [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
  [data-testid="stSidebar"] { background: #030810 !important; border-right: 1px solid rgba(0,245,255,0.12); }
  .stDataFrame { background: rgba(0,5,15,0.8) !important; }
  div[data-testid="stStatusWidget"] { display: none; }
  footer { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ─── DEMO DATA GENERATOR ─────────────────────────────────────
GESTURE_NAMES = [
    "openPalm", "fist", "point", "peace", "pinch",
    "rock", "love", "phone", "three", "four", "claw",
]
POWER_NAMES = [
    "Arc Repulsor", "Photon Shield", "Solar Flare", "Wind Slash", "Force Push",
    "Storm Wave", "Vortex Ring", "Meteor Punch", "Lightning Lance", "Portal Open",
    "Twin Beam", "Sonic Boom", "Clap Nova", "Star Gate",
]


def _demo_gesture_events(hours: int, n: int = 300) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    rows = []
    for _ in range(n):
        offset = random.uniform(0, hours * 3600)
        ts = now - timedelta(seconds=offset)
        rows.append({
            "created_at": ts.isoformat(),
            "gesture_name": random.choices(
                GESTURE_NAMES,
                weights=[30, 20, 15, 15, 10, 5, 5, 5, 5, 3, 2],
            )[0],
            "confidence": round(random.gauss(0.84, 0.08), 3),
            "palm_x": round(random.gauss(0.5, 0.18), 4),
            "palm_y": round(random.gauss(0.5, 0.18), 4),
            "power_mode": random.choice([""] * 6 + ["FIRE", "THUNDER", "PORTAL"]),
        })
    return pd.DataFrame(rows)


def _demo_superpower_log(hours: int, n: int = 80) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    rows = []
    for _ in range(n):
        offset = random.uniform(0, hours * 3600)
        ts = now - timedelta(seconds=offset)
        rows.append({
            "created_at": ts.isoformat(),
            "power_name": random.choices(POWER_NAMES)[0],
            "duration_ms": random.randint(600, 1400),
        })
    return pd.DataFrame(rows)


def _demo_sessions(n: int = 12) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(n):
        start = now - timedelta(hours=i * 2 + random.uniform(0, 1))
        duration = random.randint(180, 900)
        rows.append({
            "session_id": f"sess-{random.randint(100000, 999999)}",
            "started_at": start.isoformat(),
            "ended_at": (start + timedelta(seconds=duration)).isoformat() if i > 0 else None,
            "total_gestures": random.randint(20, 200),
        })
    return pd.DataFrame(rows)


def _demo_leaderboard(n: int = 10) -> pd.DataFrame:
    names = ["IronHand", "GestureGod", "WaveRider", "PalmStar", "SignMaster",
             "FingerFury", "HandHero", "MotionMage", "GripGuru", "SwipeKing"]
    rows = []
    for i, name in enumerate(names[:n]):
        rows.append({
            "username": name,
            "total_gestures": random.randint(50, 800),
            "favorite_gesture": random.choice(GESTURE_NAMES),
            "superpower_score": random.randint(100, 1000),
        })
    return pd.DataFrame(rows).sort_values("superpower_score", ascending=False).reset_index(drop=True)


# ─── SUPABASE CLIENT ──────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_supabase():
    url = _get_env("SUPABASE_URL").strip()
    key = _get_env("SUPABASE_KEY").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as exc:
        st.warning(f"Supabase connection failed: {exc}. Running in demo mode.")
        return None


# ─── DATA LOADERS ─────────────────────────────────────────────
@st.cache_data(ttl=15, show_spinner=False)
def load_gesture_events(hours: int, demo: bool = False) -> pd.DataFrame:
    if demo:
        return _demo_gesture_events(hours)
    sb = _get_supabase()
    if sb is None:
        return _demo_gesture_events(hours)
    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        res = sb.table("gesture_events").select("*").gte("created_at", since).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as exc:
        st.error(f"Error loading gesture events: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=15, show_spinner=False)
def load_superpower_log(hours: int, demo: bool = False) -> pd.DataFrame:
    if demo:
        return _demo_superpower_log(hours)
    sb = _get_supabase()
    if sb is None:
        return _demo_superpower_log(hours)
    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        res = sb.table("superpower_log").select("*").gte("created_at", since).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as exc:
        st.error(f"Error loading superpower log: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def load_sessions(demo: bool = False) -> pd.DataFrame:
    if demo:
        return _demo_sessions()
    sb = _get_supabase()
    if sb is None:
        return _demo_sessions()
    try:
        res = sb.table("gesture_sessions").select("*").order("started_at", desc=True).limit(50).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as exc:
        st.error(f"Error loading sessions: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def load_leaderboard(demo: bool = False) -> pd.DataFrame:
    if demo:
        return _demo_leaderboard()
    sb = _get_supabase()
    if sb is None:
        return _demo_leaderboard()
    try:
        res = sb.table("leaderboard").select("*").order("superpower_score", desc=True).limit(20).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as exc:
        st.error(f"Error loading leaderboard: {exc}")
        return pd.DataFrame()


# ─── SIDEBAR ──────────────────────────────────────────────────
sb_client = _get_supabase()
is_demo = sb_client is None

with st.sidebar:
    st.markdown("# 🖐 GESTURA")
    st.markdown("### ULTRA Dashboard")
    st.divider()

    time_range = st.selectbox(
        "Time Range",
        ["Last 1h", "Last 6h", "Last 24h", "Last 7d"],
        index=2,
    )
    hours_map = {"Last 1h": 1, "Last 6h": 6, "Last 24h": 24, "Last 7d": 168}
    hours = hours_map[time_range]

    st.divider()
    auto_refresh = st.toggle("Auto Refresh (15s)", value=False)

    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("**Active Superpowers**")
    powers_display = [
        ("FIRE HANDS", "🔥"), ("IRON MAN", "🦾"), ("THUNDER", "⚡"),
        ("I LOVE YOU", "💕"), ("PORTAL", "🌀"), ("FREEZE", "❄️"),
        ("SONIC BOOM", "💥"), ("STAR GATE", "🌌"),
    ]
    for power, emoji in powers_display:
        st.markdown(f'<span class="power-badge">{emoji} {power}</span>', unsafe_allow_html=True)

    if is_demo:
        st.divider()
        st.markdown(
            '<div class="demo-banner">⚡ DEMO MODE<br>Set SUPABASE_URL + SUPABASE_KEY<br>in .env to connect live data</div>',
            unsafe_allow_html=True,
        )

# ─── AUTO-REFRESH (non-blocking JS meta-refresh) ─────────────────────────────
# time.sleep() blocks the Streamlit thread on Cloud — use a JS redirect instead.
if auto_refresh:
    st.markdown(
        '<meta http-equiv="refresh" content="15">',
        unsafe_allow_html=True,
    )

# ─── LOAD DATA ────────────────────────────────────────────────
with st.spinner("Loading data..."):
    df_gestures = load_gesture_events(hours, demo=is_demo)
    df_powers = load_superpower_log(hours, demo=is_demo)
    df_sessions = load_sessions(demo=is_demo)
    df_leader = load_leaderboard(demo=is_demo)

# ─── HEADER ───────────────────────────────────────────────────
st.markdown("# ⚡ GESTURA ULTRA — Live Analytics")
mode_label = "DEMO MODE" if is_demo else "LIVE"
st.caption(f"Data range: last {hours}h · Mode: {mode_label} · Auto-refresh: {'ON' if auto_refresh else 'OFF'}")

if is_demo:
    st.markdown(
        '<div class="demo-banner">🔵 Running in Demo Mode — synthetic data shown. '
        'Add SUPABASE_URL and SUPABASE_KEY to .env for live data.</div>',
        unsafe_allow_html=True,
    )

# ─── TOP METRICS ──────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_gestures = len(df_gestures) if not df_gestures.empty else 0

# BUG FIX: original code used .get() on DataFrame which doesn't work for column check
if not df_sessions.empty and "ended_at" in df_sessions.columns:
    active_sessions = df_sessions["ended_at"].isna().sum()
else:
    active_sessions = 0

total_powers = len(df_powers) if not df_powers.empty else 0

unique_gestures = (
    df_gestures["gesture_name"].nunique()
    if not df_gestures.empty and "gesture_name" in df_gestures.columns
    else 0
)

avg_conf = (
    f"{df_gestures['confidence'].clip(0, 1).mean() * 100:.1f}%"
    if not df_gestures.empty and "confidence" in df_gestures.columns
    else "—"
)

col1.metric("Total Gestures", f"{total_gestures:,}")
col2.metric("Active Sessions", active_sessions)
col3.metric("Superpower Uses", f"{total_powers:,}")
col4.metric("Unique Gestures", unique_gestures)
col5.metric("Avg Confidence", avg_conf)

st.divider()

# ─── CHARTS ROW 1 ─────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("🖐 Gesture Frequency")
    if not df_gestures.empty and "gesture_name" in df_gestures.columns:
        freq = df_gestures["gesture_name"].value_counts().reset_index()
        freq.columns = ["gesture", "count"]
        fig = px.bar(
            freq.head(12), x="count", y="gesture", orientation="h",
            color="count", color_continuous_scale="Teal",
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,5,10,0.5)",
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(categoryorder="total ascending"),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No gesture data yet — start GESTURA and wave your hands!")

with right:
    st.subheader("⚡ Superpower Usage")
    if not df_powers.empty and "power_name" in df_powers.columns:
        pfreq = df_powers["power_name"].value_counts().reset_index()
        pfreq.columns = ["power", "count"]
        color_map = {
            "Arc Repulsor": "#00f5ff", "Photon Shield": "#39ff14",
            "Solar Flare": "#ffb700", "Wind Slash": "#9ef7ff",
            "Force Push": "#00f5ff", "Storm Wave": "#b44fff",
            "Vortex Ring": "#00f5ff", "Meteor Punch": "#ff3300",
            "Lightning Lance": "#b44fff", "Portal Open": "#b44fff",
            "Twin Beam": "#00f5ff", "Sonic Boom": "#39ff14",
            "Clap Nova": "#ffb700", "Star Gate": "#b44fff",
        }
        fig2 = px.pie(
            pfreq, names="power", values="count",
            color="power", color_discrete_map=color_map,
            template="plotly_dark", hole=0.4,
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No superpower events yet — activate FIRE mode!")

# ─── CHARTS ROW 2 ─────────────────────────────────────────────
left2, right2 = st.columns(2)

with left2:
    st.subheader("📍 Palm Position Heatmap")
    if (
        not df_gestures.empty
        and "palm_x" in df_gestures.columns
        and "palm_y" in df_gestures.columns
    ):
        sample = df_gestures[["palm_x", "palm_y"]].dropna().head(2000)
        # BUG FIX: clamp coordinates to [0, 1] to avoid chart distortion
        sample = sample[(sample["palm_x"].between(0, 1)) & (sample["palm_y"].between(0, 1))]
        if len(sample) >= 5:
            fig3 = go.Figure(go.Histogram2dContour(
                x=sample["palm_x"],
                y=sample["palm_y"],
                colorscale="Electric",
                reversescale=False,
                ncontours=20,
                showscale=False,
            ))
            fig3.update_layout(
                xaxis=dict(range=[0, 1], title="Palm X"),
                yaxis=dict(range=[0, 1], title="Palm Y", autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,5,10,0.5)",
                template="plotly_dark",
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Not enough palm position data yet")
    else:
        st.info("Need palm position data (palm_x, palm_y columns)")

with right2:
    st.subheader("⏱ Gestures Over Time")
    if not df_gestures.empty and "created_at" in df_gestures.columns:
        df_t = df_gestures.copy()
        # BUG FIX: handle timezone-naive timestamps and parse errors gracefully
        df_t["created_at"] = pd.to_datetime(df_t["created_at"], utc=True, errors="coerce")
        df_t = df_t.dropna(subset=["created_at"])
        if not df_t.empty:
            # Choose bin size based on time range
            freq_label = "5min" if hours <= 24 else "1h"
            df_t = (
                df_t.set_index("created_at")
                .resample(freq_label)
                .size()
                .reset_index(name="count")
            )
            fig4 = px.area(
                df_t, x="created_at", y="count",
                template="plotly_dark",
                color_discrete_sequence=["#00f5ff"],
            )
            fig4.update_traces(fillcolor="rgba(0,245,255,0.1)", line_width=2)
            fig4.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,5,10,0.5)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
                xaxis_title="",
                yaxis_title=f"Gestures / {freq_label}",
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No valid timestamp data")
    else:
        st.info("No timeline data yet")

st.divider()

# ─── LEADERBOARD + SESSIONS ───────────────────────────────────
lb_col, sess_col = st.columns([1.2, 1])

with lb_col:
    st.subheader("🏆 Leaderboard")
    if not df_leader.empty:
        # BUG FIX: check columns exist before slicing
        required_cols = {"username", "total_gestures", "favorite_gesture", "superpower_score"}
        available = required_cols & set(df_leader.columns)
        display_lb = df_leader[sorted(available, key=list(required_cols).index)].copy()
        medals = ["🥇", "🥈", "🥉"] + [f"#{i + 4}" for i in range(max(0, len(display_lb) - 3))]
        display_lb.index = medals[: len(display_lb)]
        col_config = {}
        if "total_gestures" in display_lb.columns:
            col_config["total_gestures"] = st.column_config.NumberColumn("Gestures", format="%d ✋")
        if "superpower_score" in display_lb.columns:
            col_config["superpower_score"] = st.column_config.ProgressColumn(
                "Power Score", max_value=int(display_lb["superpower_score"].max() or 1000)
            )
        if "username" in display_lb.columns:
            col_config["username"] = "Player"
        if "favorite_gesture" in display_lb.columns:
            col_config["favorite_gesture"] = "Fav Gesture"
        st.dataframe(display_lb, use_container_width=True, column_config=col_config)
    else:
        st.info("No leaderboard entries yet")

with sess_col:
    st.subheader("📋 Recent Sessions")
    if not df_sessions.empty:
        sess_cols = [c for c in ["session_id", "started_at", "total_gestures"] if c in df_sessions.columns]
        sess_disp = df_sessions[sess_cols].copy()
        if "session_id" in sess_disp.columns:
            sess_disp["session_id"] = sess_disp["session_id"].astype(str).str[:10] + "…"
        if "started_at" in sess_disp.columns:
            sess_disp["started_at"] = (
                pd.to_datetime(sess_disp["started_at"], utc=True, errors="coerce")
                .dt.strftime("%H:%M:%S")
            )
        st.dataframe(sess_disp, use_container_width=True, height=280)
    else:
        st.info("No sessions recorded")

# ─── CONFIDENCE DISTRIBUTION ──────────────────────────────────
if not df_gestures.empty and "confidence" in df_gestures.columns:
    st.divider()
    st.subheader("🎯 Confidence Distribution")
    conf_data = df_gestures["confidence"].clip(0, 1).dropna()
    fig5 = px.histogram(
        conf_data, nbins=40,
        template="plotly_dark",
        color_discrete_sequence=["#00f5ff"],
        labels={"value": "Confidence", "count": "Events"},
    )
    fig5.update_traces(marker_line_width=0, opacity=0.8)
    fig5.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,5,10,0.5)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        showlegend=False,
        bargap=0.05,
    )
    # Threshold line at 0.55
    fig5.add_vline(x=0.55, line_dash="dash", line_color="#ff6a00",
                   annotation_text="Low confidence threshold (0.55)",
                   annotation_position="top right",
                   annotation_font_color="#ff6a00")
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ─── LIVE EVENT FEED ──────────────────────────────────────────
st.subheader("🔴 Live Event Feed")
if not df_gestures.empty and "created_at" in df_gestures.columns:
    recent = (
        df_gestures
        .copy()
        .assign(created_at=pd.to_datetime(df_gestures["created_at"], utc=True, errors="coerce"))
        .dropna(subset=["created_at"])
        .sort_values("created_at", ascending=False)
        .head(25)
    )
    for _, row in recent.iterrows():
        g = row.get("gesture_name", "?")
        t = str(row.get("created_at", ""))[:19].replace("T", " ")
        conf = float(row.get("confidence", 0) or 0)
        pm = str(row.get("power_mode", "") or "").strip()
        # Color-code by confidence
        conf_color = "#39ff14" if conf >= 0.8 else ("#ffb700" if conf >= 0.55 else "#ff4444")
        badge = f"&nbsp; 🔥 <span style='color:#ff6a00'>{pm}</span>" if pm else ""
        st.markdown(
            f"`{t}` &nbsp; **{g}** &nbsp;"
            f"<span style='color:{conf_color}'>conf: {conf:.2f}</span>{badge}",
            unsafe_allow_html=True,
        )
else:
    st.info("Waiting for gesture events…")

# ─── EXPORT SECTION ───────────────────────────────────────────
st.divider()
st.subheader("📦 Export Data")
exp_col1, exp_col2, exp_col3 = st.columns(3)

with exp_col1:
    if not df_gestures.empty:
        csv_data = df_gestures.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download Gesture Events (CSV)",
            data=csv_data,
            file_name=f"gesture_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

with exp_col2:
    if not df_powers.empty:
        csv_data2 = df_powers.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download Superpower Log (CSV)",
            data=csv_data2,
            file_name=f"superpower_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

with exp_col3:
    try:
        from gestura_modules.export_tools import build_markdown_report
        if not df_gestures.empty and not df_powers.empty:
            report = build_markdown_report(
                df_gestures.to_dict("records"),
                df_powers.to_dict("records"),
                title=f"GESTURA Report — {datetime.now().strftime('%Y-%m-%d')}",
            )
            st.download_button(
                "⬇ Download Full Report (MD)",
                data=report.encode("utf-8"),
                file_name=f"gestura_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
    except Exception:
        pass

# ─── FOOTER ───────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center style='font-family:Share Tech Mono,monospace;font-size:11px;color:rgba(0,245,255,0.25);'>"
    "GESTURA ULTRA v3.0 &nbsp;·&nbsp; IRON HAND AI &nbsp;·&nbsp; STREAMLIT ANALYTICS"
    "</center>",
    unsafe_allow_html=True,
)
