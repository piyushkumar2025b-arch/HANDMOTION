# ⚡ GESTURA ULTRA — Hand Motion Analytics Dashboard

A real-time Streamlit analytics dashboard for the GESTURA hand-motion superpower system.  
Works in **Demo Mode** (synthetic data) out of the box — no camera or Supabase required.

---

## 🚀 Deploy to Streamlit Cloud (3 steps)

1. **Push this folder to a GitHub repo** (make sure `.gitignore` is respected — no `.env` or `secrets.toml` in the repo).

2. **Go to [share.streamlit.io](https://share.streamlit.io)** → *New app* → pick your repo.
   - Main file: `gestura_dashboard.py`
   - Python version: `3.10` or higher

3. **Add secrets** (optional — only for live Supabase data):
   - In the Cloud dashboard → *App Settings* → *Secrets*, paste:
     ```toml
     SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
     SUPABASE_KEY = "YOUR_SERVICE_ROLE_OR_ANON_KEY"
     ```
   - Without secrets, the app runs in **Demo Mode** (fully functional with synthetic data).

---

## 💻 Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) create a .env file for live Supabase data
cp .env.example .env
# edit .env and fill in SUPABASE_URL and SUPABASE_KEY

# 3. Launch
streamlit run gestura_dashboard.py
```

---

## 📁 Project Structure

```
gestura_dashboard.py        ← Main Streamlit app (entry point)
requirements.txt            ← Python dependencies
.streamlit/
  config.toml               ← Theme + server settings
  secrets.toml              ← Local secrets (NOT committed)
.env.example                ← Template for local .env
.gitignore                  ← Keeps secrets out of git
gestura_modules/            ← Pure-Python utility modules
  __init__.py
  analytics.py
  export_tools.py
  feature_engine.py
  gesture_classifier.py
  math_core.py
  storage.py
  superpower_catalog.py
  simulator.py
  api_server.py             ← Optional FastAPI server (not used by dashboard)
```

---

## 🗄️ Supabase Tables (for live mode)

| Table             | Key columns                                              |
|-------------------|----------------------------------------------------------|
| `gesture_events`  | `created_at`, `gesture_name`, `confidence`, `palm_x`, `palm_y`, `power_mode` |
| `superpower_log`  | `created_at`, `power_name`, `duration_ms`               |
| `gesture_sessions`| `session_id`, `started_at`, `ended_at`, `total_gestures` |
| `leaderboard`     | `username`, `total_gestures`, `favorite_gesture`, `superpower_score` |

---

## ✨ Features

- 📊 Real-time gesture frequency, superpower usage, and timeline charts
- 📍 Palm position heatmap
- 🏆 Leaderboard with progress bars
- 📋 Recent sessions table
- 🎯 Confidence distribution histogram with threshold marker
- 🔴 Live event feed (last 25 events, colour-coded by confidence)
- 📦 CSV + Markdown export buttons
- ⚡ Demo mode — zero config needed

---

*GESTURA ULTRA v3.0 · Iron Hand AI · Streamlit Analytics*
