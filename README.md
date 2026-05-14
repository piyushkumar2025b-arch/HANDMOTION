# GESTURA ULTRA — Streamlit Analytics Dashboard

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables (optional — runs in demo mode without them)
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Run the dashboard
streamlit run gestura_dashboard.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Service role or anon key |

Without these, the dashboard runs in **Demo Mode** with synthetic data.

## Supabase Schema

The dashboard expects these tables:

```sql
-- Gesture events
CREATE TABLE gesture_events (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  timestamptz DEFAULT now(),
  gesture_name text NOT NULL,
  confidence  float,
  palm_x      float,
  palm_y      float,
  power_mode  text
);

-- Superpower log
CREATE TABLE superpower_log (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  timestamptz DEFAULT now(),
  power_name  text NOT NULL,
  duration_ms integer
);

-- Sessions
CREATE TABLE gesture_sessions (
  session_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at  timestamptz DEFAULT now(),
  ended_at    timestamptz,
  total_gestures integer DEFAULT 0
);

-- Leaderboard
CREATE TABLE leaderboard (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username         text NOT NULL,
  total_gestures   integer DEFAULT 0,
  favorite_gesture text,
  superpower_score integer DEFAULT 0
);
```

## Deployment (Streamlit Community Cloud)

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file to `gestura_dashboard.py`
4. Add `SUPABASE_URL` and `SUPABASE_KEY` in the Secrets panel

## Module Overview

| Module | Purpose |
|--------|---------|
| `math_core.py` | Vec3, distance, angle, circularity, Kalman/OneEuro filters |
| `feature_engine.py` | Extract 20-feature FeatureVector from 21 MediaPipe landmarks |
| `gesture_classifier.py` | Rule-based pose + motion classifier + stateful GestureClassifier |
| `superpower_catalog.py` | 61 superpowers with triggers, effects, colors, priorities |
| `analytics.py` | Summarize, heatmap, health score, outlier detection |
| `storage.py` | JSONL/CSV local store + optional Supabase wrapper |
| `export_tools.py` | Markdown reports + CSV/JSON export bundles |
| `simulator.py` | Synthetic landmark sequences for testing |
| `api_server.py` | Optional FastAPI server (classify, simulate, power lookup) |
