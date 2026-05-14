// ============================================================
// GESTURA — Supabase Database Module
// Drop this <script> tag AFTER the Supabase CDN in gestura HTML
// Add to HTML head: <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
// Then: <script src="gestura_supabase.js"></script>
// ============================================================

// ─── CONFIG (replace with your project values) ────────────────
const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co';
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ─── SESSION ID (per browser visit) ──────────────────────────
const SESSION_ID = crypto.randomUUID();
let sessionStart = Date.now();

// ─── SCHEMA (run once in Supabase SQL Editor) ─────────────────
/*
CREATE TABLE IF NOT EXISTS gesture_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  total_gestures INT DEFAULT 0,
  superpower_uses JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS gesture_events (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  gesture_name TEXT NOT NULL,
  finger_count INT,
  confidence FLOAT,
  palm_x FLOAT,
  palm_y FLOAT,
  power_mode TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS superpower_log (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  power_name TEXT NOT NULL,
  trigger_gesture TEXT,
  duration_ms INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leaderboard (
  id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL,
  total_gestures INT DEFAULT 0,
  favorite_gesture TEXT,
  superpower_score INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);
*/

// ─── START SESSION ────────────────────────────────────────────
async function dbStartSession() {
  const { error } = await supabase.from('gesture_sessions').insert({
    session_id: SESSION_ID,
    started_at: new Date().toISOString(),
  });
  if (error) console.warn('[Supabase] Session start error:', error.message);
  else console.log('[Supabase] Session started:', SESSION_ID);
}

// ─── LOG GESTURE EVENT ────────────────────────────────────────
let gestureBuffer = [];
let flushTimer = null;

function dbLogGesture(gestureName, fingerCount, confidence, palmX, palmY, powerMode = null) {
  gestureBuffer.push({
    session_id: SESSION_ID,
    gesture_name: gestureName,
    finger_count: fingerCount,
    confidence: parseFloat(confidence.toFixed(3)),
    palm_x: parseFloat(palmX.toFixed(3)),
    palm_y: parseFloat(palmY.toFixed(3)),
    power_mode: powerMode,
    created_at: new Date().toISOString(),
  });

  // Batch flush every 3 seconds
  clearTimeout(flushTimer);
  flushTimer = setTimeout(flushGestureBuffer, 3000);
}

async function flushGestureBuffer() {
  if (gestureBuffer.length === 0) return;
  const batch = [...gestureBuffer];
  gestureBuffer = [];
  const { error } = await supabase.from('gesture_events').insert(batch);
  if (error) console.warn('[Supabase] Gesture flush error:', error.message);
}

// ─── LOG SUPERPOWER USE ───────────────────────────────────────
async function dbLogSuperpower(powerName, triggerGesture, durationMs) {
  const { error } = await supabase.from('superpower_log').insert({
    session_id: SESSION_ID,
    power_name: powerName,
    trigger_gesture: triggerGesture,
    duration_ms: durationMs,
    created_at: new Date().toISOString(),
  });
  if (error) console.warn('[Supabase] Superpower log error:', error.message);
}

// ─── END SESSION ──────────────────────────────────────────────
async function dbEndSession(totalGestures, superpowerUses) {
  await flushGestureBuffer();
  const { error } = await supabase.from('gesture_sessions').update({
    ended_at: new Date().toISOString(),
    total_gestures: totalGestures,
    superpower_uses: superpowerUses,
  }).eq('session_id', SESSION_ID);
  if (error) console.warn('[Supabase] Session end error:', error.message);
}

// ─── FETCH LEADERBOARD ────────────────────────────────────────
async function dbGetLeaderboard(limit = 10) {
  const { data, error } = await supabase
    .from('leaderboard')
    .select('*')
    .order('superpower_score', { ascending: false })
    .limit(limit);
  if (error) { console.warn('[Supabase] Leaderboard error:', error.message); return []; }
  return data;
}

// ─── UPSERT LEADERBOARD ENTRY ─────────────────────────────────
async function dbUpdateLeaderboard(username, totalGestures, favoriteGesture, superpowerScore) {
  const { error } = await supabase.from('leaderboard').upsert({
    username,
    total_gestures: totalGestures,
    favorite_gesture: favoriteGesture,
    superpower_score: superpowerScore,
  }, { onConflict: 'username' });
  if (error) console.warn('[Supabase] Leaderboard update error:', error.message);
}

// ─── REALTIME: SUBSCRIBE TO GESTURE EVENTS ───────────────────
function dbSubscribeGestures(callback) {
  return supabase
    .channel('gesture-live')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'gesture_events',
    }, payload => callback(payload.new))
    .subscribe();
}

// ─── AUTO INIT ────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  dbStartSession();
  window.addEventListener('beforeunload', () => {
    dbEndSession(window._gestureCount || 0, window._superpowerUses || {});
  });
});

// ─── EXPORTS ─────────────────────────────────────────────────
window.GesturaDB = {
  logGesture: dbLogGesture,
  logSuperpower: dbLogSuperpower,
  getLeaderboard: dbGetLeaderboard,
  updateLeaderboard: dbUpdateLeaderboard,
  subscribeGestures: dbSubscribeGestures,
  endSession: dbEndSession,
  SESSION_ID,
};