// ============================================================
// GESTURA Power Pack
// Additive 50+ superpower layer for the existing MediaPipe flow.
// It wraps window.onResults, keeps the current recognizer intact,
// and uses Canvas, Web Audio, Vibration, CustomEvent, and vector math.
// ============================================================

(function () {
  'use strict';

  const VERSION = '4.0.0-powerpack';
  const TAU = Math.PI * 2;
  const MAX_SPARKS = 420;

  const LM = {
    WRIST: 0,
    THUMB_CMC: 1,
    THUMB_MCP: 2,
    THUMB_IP: 3,
    THUMB_TIP: 4,
    INDEX_MCP: 5,
    INDEX_PIP: 6,
    INDEX_DIP: 7,
    INDEX_TIP: 8,
    MIDDLE_MCP: 9,
    MIDDLE_PIP: 10,
    MIDDLE_DIP: 11,
    MIDDLE_TIP: 12,
    RING_MCP: 13,
    RING_PIP: 14,
    RING_DIP: 15,
    RING_TIP: 16,
    PINKY_MCP: 17,
    PINKY_PIP: 18,
    PINKY_DIP: 19,
    PINKY_TIP: 20,
  };

  const POWER_DEFS = [
    { id: 'arc_repulsor', name: 'Arc Repulsor', pose: 'openPalm', motion: 'jab', effect: 'beam', color: '#00f5ff', cooldown: 800, duration: 780, priority: 92 },
    { id: 'photon_shield', name: 'Photon Shield', pose: 'openPalm', motion: 'hold', effect: 'shield', color: '#39ff14', cooldown: 1300, duration: 1200, priority: 78 },
    { id: 'solar_flare', name: 'Solar Flare', pose: 'openPalm', motion: 'swipeUp', effect: 'flare', color: '#ffb700', cooldown: 950, duration: 900, priority: 82 },
    { id: 'wind_slash', name: 'Wind Slash', pose: 'openPalm', motion: 'swipeLeft', effect: 'slash', color: '#9ef7ff', cooldown: 850, duration: 720, priority: 80 },
    { id: 'force_push', name: 'Force Push', pose: 'openPalm', motion: 'swipeRight', effect: 'wave', color: '#00f5ff', cooldown: 850, duration: 760, priority: 80 },
    { id: 'earth_drop', name: 'Earth Drop', pose: 'openPalm', motion: 'swipeDown', effect: 'shockwave', color: '#ff6a00', cooldown: 950, duration: 900, priority: 79 },
    { id: 'storm_wave', name: 'Storm Wave', pose: 'openPalm', motion: 'wave', effect: 'storm', color: '#b44fff', cooldown: 1200, duration: 1050, priority: 84 },
    { id: 'vortex_ring', name: 'Vortex Ring', pose: 'openPalm', motion: 'circleCW', effect: 'portal', color: '#00f5ff', cooldown: 1000, duration: 1100, priority: 86 },
    { id: 'nebula_spiral', name: 'Nebula Spiral', pose: 'openPalm', motion: 'circleCCW', effect: 'gravity', color: '#ff006e', cooldown: 1000, duration: 1100, priority: 86 },
    { id: 'plasma_flick', name: 'Plasma Flick', pose: 'openPalm', motion: 'flick', effect: 'burst', color: '#ffe66d', cooldown: 700, duration: 620, priority: 88 },

    { id: 'seismic_smash', name: 'Seismic Smash', pose: 'fist', motion: 'swipeDown', effect: 'shockwave', color: '#ff6a00', cooldown: 950, duration: 930, priority: 84 },
    { id: 'meteor_punch', name: 'Meteor Punch', pose: 'fist', motion: 'jab', effect: 'comet', color: '#ff3300', cooldown: 780, duration: 760, priority: 91 },
    { id: 'rocket_uppercut', name: 'Rocket Uppercut', pose: 'fist', motion: 'swipeUp', effect: 'flame', color: '#ffb700', cooldown: 900, duration: 920, priority: 80 },
    { id: 'shadow_dash_left', name: 'Shadow Dash Left', pose: 'fist', motion: 'swipeLeft', effect: 'phase', color: '#8a5cff', cooldown: 850, duration: 700, priority: 76 },
    { id: 'shadow_dash_right', name: 'Shadow Dash Right', pose: 'fist', motion: 'swipeRight', effect: 'phase', color: '#8a5cff', cooldown: 850, duration: 700, priority: 76 },
    { id: 'power_charge', name: 'Power Charge', pose: 'fist', motion: 'hold', effect: 'charge', color: '#39ff14', cooldown: 1250, duration: 1200, priority: 72 },
    { id: 'thunder_shake', name: 'Thunder Shake', pose: 'fist', motion: 'shake', effect: 'storm', color: '#b44fff', cooldown: 900, duration: 980, priority: 86 },

    { id: 'laser_pointer', name: 'Laser Pointer', pose: 'point', motion: 'hold', effect: 'beam', color: '#ff006e', cooldown: 950, duration: 900, priority: 77 },
    { id: 'lightning_lance', name: 'Lightning Lance', pose: 'point', motion: 'jab', effect: 'storm', color: '#b44fff', cooldown: 780, duration: 760, priority: 90 },
    { id: 'railgun_snap', name: 'Railgun Snap', pose: 'point', motion: 'flick', effect: 'beam', color: '#d9fbff', cooldown: 740, duration: 620, priority: 89 },
    { id: 'time_skip', name: 'Time Skip', pose: 'point', motion: 'swipeRight', effect: 'time', color: '#00f5ff', cooldown: 950, duration: 920, priority: 80 },
    { id: 'rewind_field', name: 'Rewind Field', pose: 'point', motion: 'swipeLeft', effect: 'time', color: '#ff006e', cooldown: 950, duration: 920, priority: 80 },
    { id: 'sky_hook', name: 'Sky Hook', pose: 'point', motion: 'swipeUp', effect: 'tether', color: '#39ff14', cooldown: 860, duration: 780, priority: 78 },
    { id: 'earth_bind', name: 'Earth Bind', pose: 'point', motion: 'swipeDown', effect: 'web', color: '#ffb700', cooldown: 860, duration: 820, priority: 78 },
    { id: 'orbit_draw', name: 'Orbit Draw', pose: 'point', motion: 'circleCW', effect: 'orbit', color: '#00f5ff', cooldown: 980, duration: 1080, priority: 83 },
    { id: 'reverse_orbit', name: 'Reverse Orbit', pose: 'point', motion: 'circleCCW', effect: 'orbit', color: '#ff006e', cooldown: 980, duration: 1080, priority: 83 },

    { id: 'twin_beam', name: 'Twin Beam', pose: 'peace', motion: 'jab', effect: 'beam', color: '#00f5ff', cooldown: 780, duration: 760, priority: 89 },
    { id: 'blink_left', name: 'Blink Left', pose: 'peace', motion: 'swipeLeft', effect: 'phase', color: '#9ef7ff', cooldown: 780, duration: 600, priority: 75 },
    { id: 'blink_right', name: 'Blink Right', pose: 'peace', motion: 'swipeRight', effect: 'phase', color: '#9ef7ff', cooldown: 780, duration: 600, priority: 75 },
    { id: 'levitation_field', name: 'Levitation Field', pose: 'peace', motion: 'swipeUp', effect: 'field', color: '#39ff14', cooldown: 900, duration: 980, priority: 76 },
    { id: 'descent_field', name: 'Descent Field', pose: 'peace', motion: 'swipeDown', effect: 'field', color: '#ffb700', cooldown: 900, duration: 980, priority: 76 },
    { id: 'charm_field', name: 'Charm Field', pose: 'peace', motion: 'hold', effect: 'aura', color: '#ff4fd8', cooldown: 1300, duration: 1180, priority: 70 },
    { id: 'duplicate_trail', name: 'Duplicate Trail', pose: 'peace', motion: 'wave', effect: 'trail', color: '#00f5ff', cooldown: 1050, duration: 1060, priority: 77 },

    { id: 'portal_open', name: 'Portal Open', pose: 'pinch', motion: 'hold', effect: 'portal', color: '#b44fff', cooldown: 1200, duration: 1200, priority: 87 },
    { id: 'portal_throw', name: 'Portal Throw', pose: 'pinch', motion: 'flick', effect: 'portal', color: '#00f5ff', cooldown: 780, duration: 900, priority: 90 },
    { id: 'reality_thread', name: 'Reality Thread', pose: 'pinch', motion: 'swipeRight', effect: 'tether', color: '#39ff14', cooldown: 860, duration: 850, priority: 78 },
    { id: 'thread_pull', name: 'Thread Pull', pose: 'pinch', motion: 'swipeLeft', effect: 'tether', color: '#ff006e', cooldown: 860, duration: 850, priority: 78 },
    { id: 'spark_forge', name: 'Spark Forge', pose: 'pinch', motion: 'jab', effect: 'forge', color: '#ffb700', cooldown: 760, duration: 760, priority: 86 },
    { id: 'micro_well', name: 'Micro Well', pose: 'pinch', motion: 'circleCW', effect: 'gravity', color: '#00f5ff', cooldown: 950, duration: 1100, priority: 82 },
    { id: 'time_knot', name: 'Time Knot', pose: 'pinch', motion: 'circleCCW', effect: 'time', color: '#ff006e', cooldown: 950, duration: 1100, priority: 82 },

    { id: 'sonic_boom', name: 'Sonic Boom', pose: 'rock', motion: 'jab', effect: 'wave', color: '#39ff14', cooldown: 760, duration: 760, priority: 88 },
    { id: 'amp_wave', name: 'Amp Wave', pose: 'rock', motion: 'shake', effect: 'wave', color: '#ff006e', cooldown: 880, duration: 920, priority: 83 },
    { id: 'shock_chord', name: 'Shock Chord', pose: 'rock', motion: 'swipeUp', effect: 'storm', color: '#b44fff', cooldown: 900, duration: 860, priority: 78 },
    { id: 'riff_slash', name: 'Riff Slash', pose: 'rock', motion: 'swipeRight', effect: 'slash', color: '#ffb700', cooldown: 820, duration: 720, priority: 78 },

    { id: 'drone_swarm', name: 'Drone Swarm', pose: 'three', motion: 'circleCW', effect: 'swarm', color: '#00f5ff', cooldown: 1050, duration: 1180, priority: 80 },
    { id: 'holo_cube', name: 'Holo Cube', pose: 'three', motion: 'hold', effect: 'cube', color: '#00f5ff', cooldown: 1300, duration: 1350, priority: 71 },
    { id: 'tri_beam', name: 'Tri Beam', pose: 'three', motion: 'jab', effect: 'beam', color: '#39ff14', cooldown: 780, duration: 760, priority: 86 },
    { id: 'ai_scan', name: 'AI Scan', pose: 'four', motion: 'hold', effect: 'scan', color: '#00f5ff', cooldown: 1300, duration: 1200, priority: 72 },
    { id: 'data_rain', name: 'Data Rain', pose: 'four', motion: 'swipeDown', effect: 'data', color: '#39ff14', cooldown: 900, duration: 1000, priority: 77 },
    { id: 'quantum_grid', name: 'Quantum Grid', pose: 'four', motion: 'swipeUp', effect: 'grid', color: '#00f5ff', cooldown: 900, duration: 1000, priority: 77 },
    { id: 'energy_net', name: 'Energy Net', pose: 'four', motion: 'wave', effect: 'web', color: '#9ef7ff', cooldown: 1000, duration: 1030, priority: 77 },

    { id: 'heart_burst', name: 'Heart Burst', pose: 'love', motion: 'hold', effect: 'heart', color: '#ff006e', cooldown: 1300, duration: 1100, priority: 72 },
    { id: 'signal_call', name: 'Signal Call', pose: 'phone', motion: 'jab', effect: 'rings', color: '#39ff14', cooldown: 850, duration: 900, priority: 78 },
    { id: 'web_caster', name: 'Web Caster', pose: 'web', motion: 'jab', effect: 'web', color: '#d9fbff', cooldown: 820, duration: 860, priority: 82 },
    { id: 'ice_claw', name: 'Ice Claw', pose: 'claw', motion: 'swipeDown', effect: 'ice', color: '#9ef7ff', cooldown: 920, duration: 950, priority: 78 },
    { id: 'nova_claw', name: 'Nova Claw', pose: 'claw', motion: 'swipeUp', effect: 'flare', color: '#ffb700', cooldown: 920, duration: 950, priority: 78 },

    { id: 'clap_nova', name: 'Clap Nova', two: 'clap', effect: 'shockwave', color: '#ffb700', cooldown: 1200, duration: 1050, priority: 98 },
    { id: 'star_gate', name: 'Star Gate', two: 'expand', effect: 'portal', color: '#b44fff', cooldown: 1150, duration: 1250, priority: 94 },
    { id: 'crush_field', name: 'Crush Field', two: 'compress', effect: 'gravity', color: '#ff006e', cooldown: 1150, duration: 1250, priority: 94 },
    { id: 'balance_aura', name: 'Balance Aura', two: 'mirror', effect: 'aura', color: '#39ff14', cooldown: 1450, duration: 1280, priority: 74 },
    { id: 'fusion_core', name: 'Fusion Core', two: 'palmsTogetherHold', effect: 'charge', color: '#00f5ff', cooldown: 1500, duration: 1300, priority: 88 },
  ];

  const powerById = new Map(POWER_DEFS.map((power) => [power.id, power]));
  const histories = new Map();
  const twoHandHistory = [];
  const lastFired = new Map();
  const activeEffects = [];
  const sparks = [];

  let canvas = null;
  let ctx = null;
  let panel = null;
  let currentEl = null;
  let meterEl = null;
  let recentEl = null;
  let enabled = true;
  let renderStarted = false;
  let audioCtx = null;
  let globalLastFire = 0;
  let width = window.innerWidth;
  let height = window.innerHeight;
  let dpr = Math.min(2, window.devicePixelRatio || 1);

  const stats = {
    fired: 0,
    current: 'STANDBY',
    recent: [],
    lastPowerAt: 0,
  };

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function smoothstep(edge0, edge1, value) {
    const x = clamp((value - edge0) / (edge1 - edge0), 0, 1);
    return x * x * (3 - 2 * x);
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - clamp(t, 0, 1), 3);
  }

  function dist2(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  function dist3(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y, (a.z || 0) - (b.z || 0));
  }

  function meanPoint(points) {
    const total = points.reduce((acc, point) => {
      acc.x += point.x;
      acc.y += point.y;
      acc.z += point.z || 0;
      return acc;
    }, { x: 0, y: 0, z: 0 });
    return {
      x: total.x / points.length,
      y: total.y / points.length,
      z: total.z / points.length,
    };
  }

  function screenPoint(point) {
    return {
      x: (1 - point.x) * width,
      y: point.y * height,
      z: point.z || 0,
    };
  }

  function handScale(lm) {
    const palmWidth = dist2(lm[LM.INDEX_MCP], lm[LM.PINKY_MCP]);
    const palmHeight = dist2(lm[LM.WRIST], lm[LM.MIDDLE_MCP]);
    return Math.max(0.06, palmWidth * 0.75 + palmHeight * 0.8);
  }

  function palmCenter(lm) {
    return meanPoint([lm[LM.WRIST], lm[LM.INDEX_MCP], lm[LM.MIDDLE_MCP], lm[LM.PINKY_MCP]]);
  }

  function fingerUp(lm, tip, pip) {
    return lm[tip].y < lm[pip].y - 0.012;
  }

  function thumbExtended(lm) {
    const tipSpread = dist2(lm[LM.THUMB_TIP], lm[LM.INDEX_MCP]);
    const knuckleSpread = dist2(lm[LM.THUMB_IP], lm[LM.INDEX_MCP]);
    return tipSpread > knuckleSpread * 1.12 || Math.abs(lm[LM.THUMB_TIP].x - lm[LM.THUMB_IP].x) > 0.038;
  }

  function classifyPose(lm) {
    const scale = handScale(lm);
    const thumb = thumbExtended(lm);
    const index = fingerUp(lm, LM.INDEX_TIP, LM.INDEX_PIP);
    const middle = fingerUp(lm, LM.MIDDLE_TIP, LM.MIDDLE_PIP);
    const ring = fingerUp(lm, LM.RING_TIP, LM.RING_PIP);
    const pinky = fingerUp(lm, LM.PINKY_TIP, LM.PINKY_PIP);
    const fingers = { thumb, index, middle, ring, pinky };
    const raised = [index, middle, ring, pinky].filter(Boolean).length;
    const thumbIndex = dist2(lm[LM.THUMB_TIP], lm[LM.INDEX_TIP]);
    const thumbMiddle = dist2(lm[LM.THUMB_TIP], lm[LM.MIDDLE_TIP]);
    const thumbRing = dist2(lm[LM.THUMB_TIP], lm[LM.RING_TIP]);
    const thumbPinky = dist2(lm[LM.THUMB_TIP], lm[LM.PINKY_TIP]);
    const spread = Math.abs(Math.atan2(lm[LM.INDEX_TIP].y - lm[LM.WRIST].y, lm[LM.INDEX_TIP].x - lm[LM.WRIST].x) -
      Math.atan2(lm[LM.PINKY_TIP].y - lm[LM.WRIST].y, lm[LM.PINKY_TIP].x - lm[LM.WRIST].x));
    const bentCount = [
      [LM.INDEX_TIP, LM.INDEX_PIP, LM.INDEX_MCP],
      [LM.MIDDLE_TIP, LM.MIDDLE_PIP, LM.MIDDLE_MCP],
      [LM.RING_TIP, LM.RING_PIP, LM.RING_MCP],
      [LM.PINKY_TIP, LM.PINKY_PIP, LM.PINKY_MCP],
    ].filter(([tip, pip, mcp]) => lm[tip].y > lm[pip].y - 0.004 && lm[tip].y < lm[mcp].y + scale * 0.28).length;

    let pose = 'unknown';
    if (thumbIndex < 0.044 && middle && ring && pinky) pose = 'ok';
    else if (thumbIndex < 0.047) pose = 'pinch';
    else if (thumbMiddle < 0.047) pose = 'middlePinch';
    else if (thumbRing < 0.05) pose = 'ringPinch';
    else if (thumbPinky < 0.055) pose = 'pinkyPinch';
    else if (thumb && index && pinky && !middle && !ring) pose = 'love';
    else if (thumb && pinky && !index && !middle && !ring) pose = 'phone';
    else if (index && middle && pinky && !ring) pose = 'web';
    else if (index && pinky && !middle && !ring) pose = 'rock';
    else if (thumb && index && !middle && !ring && !pinky) pose = 'fingerGun';
    else if (index && middle && ring && pinky && thumb) pose = 'openPalm';
    else if (index && middle && ring && pinky) pose = 'four';
    else if (!index && !middle && !ring && !pinky) pose = 'fist';
    else if (index && !middle && !ring && !pinky) pose = 'point';
    else if (index && middle && !ring && !pinky) pose = 'peace';
    else if (index && middle && ring && !pinky) pose = 'three';
    else if (index && middle && ring && pinky) pose = 'four';
    else if (bentCount >= 3) pose = 'claw';
    else if (raised >= 3 && spread > 0.55) pose = 'openPalm';

    return {
      pose,
      fingers,
      raised,
      scale,
      spread,
      pinches: { thumbIndex, thumbMiddle, thumbRing, thumbPinky },
      fingerKey: [thumb, index, middle, ring, pinky].map((value) => (value ? '1' : '0')).join(''),
    };
  }

  function ensureCanvas() {
    if (canvas) return;
    canvas = document.createElement('canvas');
    canvas.id = 'gestura-powerpack-canvas';
    Object.assign(canvas.style, {
      position: 'fixed',
      inset: '0',
      width: '100vw',
      height: '100vh',
      pointerEvents: 'none',
      zIndex: '62',
    });
    document.body.appendChild(canvas);
    ctx = canvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas, { passive: true });
  }

  function resizeCanvas() {
    if (!canvas || !ctx) return;
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function ensurePanel() {
    if (panel) return;
    const style = document.createElement('style');
    style.textContent = `
      #gestura-powerpack-panel {
        position: fixed;
        right: 20px;
        bottom: 74px;
        width: 260px;
        z-index: 120;
        color: #00f5ff;
        background: rgba(0, 245, 255, 0.045);
        border: 1px solid rgba(0, 245, 255, 0.18);
        border-left: 3px solid #ffb700;
        backdrop-filter: blur(10px);
        font-family: 'Share Tech Mono', monospace;
        padding: 12px 14px;
      }
      #gestura-powerpack-panel .gpp-title {
        color: rgba(0, 245, 255, 0.58);
        font-size: 9px;
        letter-spacing: 3px;
        margin-bottom: 8px;
      }
      #gestura-powerpack-current {
        min-height: 22px;
        color: #ffb700;
        font-family: 'Orbitron', sans-serif;
        font-size: 13px;
        font-weight: 700;
        text-shadow: 0 0 18px rgba(255, 183, 0, 0.5);
      }
      #gestura-powerpack-meter {
        height: 4px;
        width: 0%;
        margin: 8px 0 10px;
        background: #ffb700;
        box-shadow: 0 0 16px rgba(255, 183, 0, 0.6);
        transition: width 0.18s ease;
      }
      #gestura-powerpack-recent {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
      #gestura-powerpack-recent span {
        max-width: 112px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        border: 1px solid rgba(0, 245, 255, 0.2);
        padding: 2px 5px;
        font-size: 8px;
        color: rgba(0, 245, 255, 0.68);
      }
      @media (max-width: 760px) {
        #gestura-powerpack-panel {
          right: 12px;
          left: 12px;
          bottom: 66px;
          width: auto;
        }
      }
    `;
    document.head.appendChild(style);

    panel = document.createElement('div');
    panel.id = 'gestura-powerpack-panel';
    panel.innerHTML = `
      <div class="gpp-title">POWER PACK ${POWER_DEFS.length}+ ONLINE</div>
      <div id="gestura-powerpack-current">STANDBY</div>
      <div id="gestura-powerpack-meter"></div>
      <div id="gestura-powerpack-recent"></div>
    `;
    document.body.appendChild(panel);
    currentEl = panel.querySelector('#gestura-powerpack-current');
    meterEl = panel.querySelector('#gestura-powerpack-meter');
    recentEl = panel.querySelector('#gestura-powerpack-recent');
  }

  function updatePanel() {
    if (!currentEl) return;
    const elapsed = performance.now() - stats.lastPowerAt;
    const freshness = clamp(1 - elapsed / 1500, 0, 1);
    currentEl.textContent = enabled ? stats.current : 'POWER PACK OFF';
    meterEl.style.width = Math.round(freshness * 100) + '%';
    recentEl.innerHTML = stats.recent.slice(0, 5).map((name) => `<span title="${name}">${name}</span>`).join('');
  }

  function addHistory(id, sample) {
    if (!histories.has(id)) histories.set(id, []);
    const history = histories.get(id);
    history.push(sample);
    while (history.length > 34) history.shift();
    return history;
  }

  function sampleWindow(history, maxAgeMs) {
    const now = performance.now();
    return history.filter((sample) => now - sample.t <= maxAgeMs);
  }

  function directionChanges(values, threshold) {
    let prevSign = 0;
    let flips = 0;
    for (let i = 1; i < values.length; i += 1) {
      const delta = values[i] - values[i - 1];
      if (Math.abs(delta) < threshold) continue;
      const sign = Math.sign(delta);
      if (prevSign && sign !== prevSign) flips += 1;
      prevSign = sign;
    }
    return flips;
  }

  function circularMotion(samples) {
    if (samples.length < 14) return null;
    const center = meanPoint(samples);
    const radius = samples.reduce((sum, sample) => sum + Math.hypot(sample.x - center.x, sample.y - center.y), 0) / samples.length;
    if (radius < 0.045) return null;
    let travel = 0;
    for (let i = 1; i < samples.length; i += 1) {
      const a0 = Math.atan2(samples[i - 1].y - center.y, samples[i - 1].x - center.x);
      const a1 = Math.atan2(samples[i].y - center.y, samples[i].x - center.x);
      let delta = a1 - a0;
      while (delta > Math.PI) delta -= TAU;
      while (delta < -Math.PI) delta += TAU;
      travel += delta;
    }
    if (Math.abs(travel) > Math.PI * 1.35) return travel > 0 ? 'circleCW' : 'circleCCW';
    return null;
  }

  function stableHold(samples) {
    if (samples.length < 18) return false;
    const center = meanPoint(samples);
    const spread = Math.max(...samples.map((sample) => Math.hypot(sample.x - center.x, sample.y - center.y)));
    const age = samples[samples.length - 1].t - samples[0].t;
    return age > 520 && spread < 0.035;
  }

  function analyzeHand(lm, handedness, index) {
    const poseInfo = classifyPose(lm);
    const center = palmCenter(lm);
    const indexTip = lm[LM.INDEX_TIP];
    const sample = {
      t: performance.now(),
      x: center.x,
      y: center.y,
      z: center.z || 0,
      ix: indexTip.x,
      iy: indexTip.y,
      iz: indexTip.z || 0,
    };
    const id = `${handedness || 'Hand'}-${index}`;
    const history = addHistory(id, sample);
    const short = sampleWindow(history, 650);
    const long = sampleWindow(history, 1050);
    const first = short[0] || sample;
    const last = short[short.length - 1] || sample;
    const dt = Math.max(16, last.t - first.t);
    const dx = last.x - first.x;
    const dy = last.y - first.y;
    const dz = last.z - first.z;
    const speed = dist3(last, first) / dt * 1000;
    const motions = new Set();
    const xValues = long.map((sampleItem) => sampleItem.x);
    const yValues = long.map((sampleItem) => sampleItem.y);
    const xSpan = xValues.length ? Math.max(...xValues) - Math.min(...xValues) : 0;
    const ySpan = yValues.length ? Math.max(...yValues) - Math.min(...yValues) : 0;

    if (short.length >= 5 && dt < 760) {
      if (Math.abs(dx) > 0.13 && Math.abs(dx) > Math.abs(dy) * 1.18) motions.add(dx > 0 ? 'swipeRight' : 'swipeLeft');
      if (Math.abs(dy) > 0.13 && Math.abs(dy) > Math.abs(dx) * 1.08) motions.add(dy > 0 ? 'swipeDown' : 'swipeUp');
    }

    if (speed > 0.85 && short.length >= 4) motions.add('flick');
    if (Math.abs(dz) > 0.027 && speed > 0.22) motions.add(dz < 0 ? 'jab' : 'pullBack');
    if (directionChanges(xValues, 0.018) >= 4 && xSpan > 0.08) motions.add('shake');
    if (directionChanges(xValues, 0.016) >= 3 && xSpan > 0.13 && poseInfo.pose === 'openPalm') motions.add('wave');
    if (directionChanges(yValues, 0.016) >= 3 && ySpan > 0.12) motions.add('zigzag');
    if (stableHold(long)) motions.add('hold');
    const circle = circularMotion(long);
    if (circle) motions.add(circle);

    const screen = screenPoint(center);
    const zone = screen.y < height * 0.33 ? 'top' : screen.y > height * 0.68 ? 'bottom' : 'middle';

    return {
      id,
      lm,
      handedness,
      index,
      center,
      screen,
      indexScreen: screenPoint(indexTip),
      pose: poseInfo.pose,
      fingers: poseInfo.fingers,
      raised: poseInfo.raised,
      scale: poseInfo.scale,
      spread: poseInfo.spread,
      fingerKey: poseInfo.fingerKey,
      history,
      motions,
      velocity: { x: dx / dt * 1000, y: dy / dt * 1000, z: dz / dt * 1000 },
      speed,
      zone,
    };
  }

  function analyzeTwoHands(hands) {
    const motions = new Set();
    if (hands.length < 2) return { motions, source: null };

    const a = hands[0];
    const b = hands[1];
    const center = {
      x: (a.center.x + b.center.x) * 0.5,
      y: (a.center.y + b.center.y) * 0.5,
      z: ((a.center.z || 0) + (b.center.z || 0)) * 0.5,
    };
    const distance = dist2(a.center, b.center);
    const now = performance.now();
    twoHandHistory.push({ t: now, d: distance, x: center.x, y: center.y, z: center.z });
    while (twoHandHistory.length > 28) twoHandHistory.shift();
    const short = twoHandHistory.filter((sample) => now - sample.t <= 720);
    const first = short[0] || twoHandHistory[0];
    const last = short[short.length - 1] || twoHandHistory[twoHandHistory.length - 1];
    const dt = Math.max(16, last.t - first.t);
    const dd = last.d - first.d;
    const closeSpeed = dd / dt * 1000;
    const samePose = a.pose === b.pose && a.pose !== 'unknown';
    const yClose = Math.abs(a.center.y - b.center.y) < 0.09;
    const xDistance = Math.abs(a.center.x - b.center.x);

    if (last.d < 0.13 && closeSpeed < -0.16) motions.add('clap');
    if (dd > 0.105 && xDistance > 0.18) motions.add('expand');
    if (dd < -0.095 && first.d > 0.18) motions.add('compress');
    if (last.d < 0.12 && stableHold(short)) motions.add('palmsTogetherHold');
    if (samePose && yClose && xDistance > 0.18 && stableHold(short)) motions.add('mirror');

    return {
      motions,
      distance,
      source: screenPoint(center),
      hands: [a, b],
    };
  }

  function buildFrameFeatures(results) {
    const landmarks = results.multiHandLandmarks || [];
    const handedness = results.multiHandedness || [];
    const hands = landmarks.map((lm, index) => {
      const label = handedness[index] && handedness[index].label ? handedness[index].label : 'Unknown';
      return analyzeHand(lm, label, index);
    });
    hands.sort((a, b) => b.speed - a.speed);
    const primary = hands[0] || null;
    return {
      hands,
      primary,
      twoHand: analyzeTwoHands(hands),
      time: performance.now(),
    };
  }

  function matchesPower(power, frame) {
    if (power.two) return frame.twoHand && frame.twoHand.motions.has(power.two);
    const hand = frame.primary;
    if (!hand) return false;
    if (power.pose && hand.pose !== power.pose) return false;
    if (power.motion && !hand.motions.has(power.motion)) return false;
    if (power.minSpeed && hand.speed < power.minSpeed) return false;
    if (power.zone && hand.zone !== power.zone) return false;
    return true;
  }

  function triggerPowers(frame) {
    if (!enabled || !frame.primary) return;
    const now = performance.now();
    if (now - globalLastFire < 150) return;

    const matches = POWER_DEFS.filter((power) => {
      const cooldown = power.cooldown || 1000;
      return matchesPower(power, frame) && now - (lastFired.get(power.id) || 0) > cooldown;
    }).sort((a, b) => (b.priority || 0) - (a.priority || 0));

    if (!matches.length) return;
    const power = matches[0];
    lastFired.set(power.id, now);
    globalLastFire = now;
    firePower(power, frame);
  }

  function sourceForPower(power, frame) {
    if (power.two && frame.twoHand.source) return frame.twoHand.source;
    if (!frame.primary) return { x: width * 0.5, y: height * 0.5 };
    const pose = frame.primary.pose;
    if (pose === 'point' || pose === 'pinch' || pose === 'fingerGun') return frame.primary.indexScreen;
    return frame.primary.screen;
  }

  function triggerLabel(power, frame) {
    if (power.two) return power.two.toUpperCase();
    const pose = frame.primary ? frame.primary.pose.toUpperCase() : 'HAND';
    const motion = power.motion ? power.motion.toUpperCase() : 'MOTION';
    return `${pose} + ${motion}`;
  }

  function firePower(power, frame) {
    const now = performance.now();
    const source = sourceForPower(power, frame);
    const velocity = frame.primary ? frame.primary.velocity : { x: 0, y: -0.5, z: 0 };
    const duration = power.duration || 900;
    activeEffects.push({
      id: power.id,
      name: power.name,
      effect: power.effect,
      color: power.color,
      x: source.x,
      y: source.y,
      vx: velocity.x,
      vy: velocity.y,
      born: now,
      duration,
      seed: Math.random() * 1000,
      label: triggerLabel(power, frame),
    });

    spawnBurst(source.x, source.y, power.color, power.effect === 'storm' ? 34 : 22, power.effect);
    stats.fired += 1;
    stats.current = power.name.toUpperCase();
    stats.lastPowerAt = now;
    stats.recent = [power.name, ...stats.recent.filter((name) => name !== power.name)].slice(0, 5);
    updatePanel();
    pulseTone(power);
    vibrate(12);
    logPower(power, frame, duration);

    if (typeof window.showToast === 'function') {
      window.showToast(power.name.toUpperCase(), triggerLabel(power, frame), power.color);
    }
    if (typeof window.addToLog === 'function') {
      window.addToLog('POWER: ' + power.name);
    }
    window.dispatchEvent(new CustomEvent('gestura:superpower', {
      detail: {
        id: power.id,
        name: power.name,
        trigger: triggerLabel(power, frame),
        version: VERSION,
      },
    }));
  }

  function logPower(power, frame, duration) {
    try {
      const uses = JSON.parse(localStorage.getItem('gesturaPowerUses') || '{}');
      uses[power.id] = (uses[power.id] || 0) + 1;
      localStorage.setItem('gesturaPowerUses', JSON.stringify(uses));
    } catch (error) {
      // LocalStorage can be blocked in private contexts.
    }

    if (window.GesturaDB && typeof window.GesturaDB.logSuperpower === 'function') {
      window.GesturaDB.logSuperpower(power.name, triggerLabel(power, frame), Math.round(duration));
    }
  }

  function vibrate(ms) {
    if (navigator.vibrate) navigator.vibrate(ms);
  }

  function pulseTone(power) {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) return;
    try {
      if (!audioCtx) audioCtx = new AudioContextCtor();
      if (audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      const index = POWER_DEFS.findIndex((item) => item.id === power.id);
      osc.type = power.effect === 'storm' ? 'sawtooth' : 'triangle';
      osc.frequency.value = 170 + (index % 18) * 24;
      gain.gain.setValueAtTime(0.0001, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.045, audioCtx.currentTime + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.11);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    } catch (error) {
      // Audio is optional; browsers can block it until a user gesture.
    }
  }

  function spawnBurst(x, y, color, count, mode) {
    for (let i = 0; i < count; i += 1) {
      const angle = Math.random() * TAU;
      const speed = lerp(1.2, mode === 'beam' ? 8 : 5.5, Math.random());
      sparks.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1,
        decay: lerp(0.014, 0.038, Math.random()),
        radius: lerp(2, 8, Math.random()),
        color,
        gravity: mode === 'flame' ? -0.045 : 0.018,
      });
    }
    while (sparks.length > MAX_SPARKS) sparks.shift();
  }

  function drawRing(cx, cy, radius, color, alpha, lineWidth) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.shadowColor = color;
    ctx.shadowBlur = 22;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, TAU);
    ctx.stroke();
    ctx.restore();
  }

  function drawPolygon(cx, cy, radius, sides, color, alpha, rotation) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowColor = color;
    ctx.shadowBlur = 18;
    ctx.beginPath();
    for (let i = 0; i <= sides; i += 1) {
      const angle = rotation + i / sides * TAU;
      const x = cx + Math.cos(angle) * radius;
      const y = cy + Math.sin(angle) * radius;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawLightning(x1, y1, x2, y2, color, alpha, widthValue) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.lineWidth = widthValue;
    ctx.shadowColor = color;
    ctx.shadowBlur = 24;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    const segments = 9;
    for (let i = 1; i <= segments; i += 1) {
      const t = i / segments;
      const jitter = (1 - Math.abs(0.5 - t) * 1.6) * 34;
      ctx.lineTo(
        lerp(x1, x2, t) + (Math.random() - 0.5) * jitter,
        lerp(y1, y2, t) + (Math.random() - 0.5) * jitter
      );
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawHeart(cx, cy, radius, color, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 22;
    ctx.beginPath();
    ctx.moveTo(cx, cy + radius * 0.35);
    ctx.bezierCurveTo(cx - radius, cy - radius * 0.35, cx - radius * 1.25, cy + radius * 0.52, cx, cy + radius * 1.15);
    ctx.bezierCurveTo(cx + radius * 1.25, cy + radius * 0.52, cx + radius, cy - radius * 0.35, cx, cy + radius * 0.35);
    ctx.fill();
    ctx.restore();
  }

  function drawEffect(effect, now) {
    const age = now - effect.born;
    const progress = clamp(age / effect.duration, 0, 1);
    const eased = easeOutCubic(progress);
    const alpha = 1 - progress;
    const color = effect.color;
    const cx = effect.x;
    const cy = effect.y;
    const direction = Math.atan2(effect.vy || -0.4, effect.vx || 0.001);
    const reach = Math.max(width, height) * 0.75;

    if (effect.effect === 'beam') {
      const x2 = cx + Math.cos(direction) * reach;
      const y2 = cy + Math.sin(direction) * reach;
      drawLightning(cx, cy, x2, y2, color, alpha, 5 + alpha * 8);
      drawRing(cx, cy, 18 + eased * 42, color, alpha, 3);
    } else if (effect.effect === 'shield') {
      drawPolygon(cx, cy, 54 + eased * 44, 6, color, alpha, effect.seed + eased * TAU);
      drawRing(cx, cy, 36 + eased * 80, color, alpha * 0.6, 2);
    } else if (effect.effect === 'portal') {
      for (let i = 0; i < 5; i += 1) {
        ctx.save();
        ctx.globalAlpha = alpha * (1 - i * 0.11);
        ctx.translate(cx, cy);
        ctx.rotate(effect.seed + eased * TAU * (i % 2 ? -1 : 1));
        ctx.scale(1, 0.42 + i * 0.035);
        ctx.strokeStyle = i % 2 ? color : '#ffffff';
        ctx.lineWidth = 2;
        ctx.shadowColor = color;
        ctx.shadowBlur = 24;
        ctx.beginPath();
        ctx.arc(0, 0, 26 + i * 16 + eased * 24, 0, TAU);
        ctx.stroke();
        ctx.restore();
      }
    } else if (effect.effect === 'storm') {
      for (let i = 0; i < 5; i += 1) {
        const angle = effect.seed + i / 5 * TAU + progress;
        drawLightning(cx, cy, cx + Math.cos(angle) * (120 + eased * 120), cy + Math.sin(angle) * (80 + eased * 80), color, alpha * 0.82, 2.4);
      }
    } else if (effect.effect === 'shockwave' || effect.effect === 'wave') {
      for (let i = 0; i < 4; i += 1) {
        drawRing(cx, cy, 18 + eased * (90 + i * 55), color, alpha * (1 - i * 0.18), 2.2);
      }
    } else if (effect.effect === 'slash' || effect.effect === 'phase') {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(cx, cy);
      ctx.rotate(direction);
      ctx.strokeStyle = color;
      ctx.lineWidth = 4;
      ctx.shadowColor = color;
      ctx.shadowBlur = 26;
      ctx.beginPath();
      ctx.moveTo(-110 * eased, -26);
      ctx.quadraticCurveTo(0, 50 * Math.sin(progress * Math.PI), 180 * eased, 20);
      ctx.stroke();
      ctx.restore();
    } else if (effect.effect === 'gravity') {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowColor = color;
      ctx.shadowBlur = 24;
      ctx.beginPath();
      for (let i = 0; i < 110; i += 1) {
        const t = i / 109;
        const radius = (1 - t) * (130 - eased * 40);
        const angle = effect.seed + t * TAU * 3.4 + eased * TAU;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.restore();
    } else if (effect.effect === 'grid' || effect.effect === 'scan') {
      ctx.save();
      ctx.globalAlpha = alpha * 0.75;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      const size = 160 + eased * 80;
      for (let offset = -size; offset <= size; offset += 24) {
        ctx.beginPath();
        ctx.moveTo(cx - size, cy + offset);
        ctx.lineTo(cx + size, cy + offset);
        ctx.moveTo(cx + offset, cy - size);
        ctx.lineTo(cx + offset, cy + size);
        ctx.stroke();
      }
      ctx.restore();
      drawRing(cx, cy, 44 + eased * 90, color, alpha, 2);
    } else if (effect.effect === 'web' || effect.effect === 'tether') {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6;
      ctx.shadowColor = color;
      ctx.shadowBlur = 16;
      for (let i = 0; i < 12; i += 1) {
        const angle = effect.seed + i / 12 * TAU;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(angle) * (80 + eased * 140), cy + Math.sin(angle) * (80 + eased * 140));
        ctx.stroke();
      }
      for (let ring = 0; ring < 3; ring += 1) {
        drawRing(cx, cy, 34 + ring * 42 + eased * 30, color, alpha * 0.5, 1.2);
      }
      ctx.restore();
    } else if (effect.effect === 'cube') {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(cx, cy);
      ctx.rotate(effect.seed + eased * TAU * 0.35);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowColor = color;
      ctx.shadowBlur = 20;
      const s = 44 + eased * 18;
      ctx.strokeRect(-s / 2, -s / 2, s, s);
      ctx.strokeRect(-s / 2 + 18, -s / 2 - 18, s, s);
      ctx.beginPath();
      ctx.moveTo(-s / 2, -s / 2); ctx.lineTo(-s / 2 + 18, -s / 2 - 18);
      ctx.moveTo(s / 2, -s / 2); ctx.lineTo(s / 2 + 18, -s / 2 - 18);
      ctx.moveTo(s / 2, s / 2); ctx.lineTo(s / 2 + 18, s / 2 - 18);
      ctx.moveTo(-s / 2, s / 2); ctx.lineTo(-s / 2 + 18, s / 2 - 18);
      ctx.stroke();
      ctx.restore();
    } else if (effect.effect === 'heart') {
      drawHeart(cx, cy - eased * 35, 28 + eased * 28, color, alpha);
      drawRing(cx, cy, 28 + eased * 98, color, alpha * 0.65, 2);
    } else if (effect.effect === 'ice') {
      for (let i = 0; i < 9; i += 1) {
        drawPolygon(cx + Math.cos(i) * eased * 70, cy + Math.sin(i * 1.7) * eased * 70, 12 + i, 6, color, alpha * 0.85, effect.seed + i);
      }
    } else if (effect.effect === 'data') {
      ctx.save();
      ctx.globalAlpha = alpha * 0.8;
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      for (let i = 0; i < 34; i += 1) {
        const x = cx + Math.sin(effect.seed + i * 3.1) * 150;
        const y = cy - 180 + ((effect.seed * 17 + i * 31 + eased * 420) % 360);
        ctx.fillRect(x, y, 2, 18);
      }
      ctx.restore();
    } else if (effect.effect === 'flame' || effect.effect === 'flare' || effect.effect === 'forge' || effect.effect === 'comet' || effect.effect === 'charge' || effect.effect === 'swarm' || effect.effect === 'trail' || effect.effect === 'aura' || effect.effect === 'rings' || effect.effect === 'field' || effect.effect === 'orbit' || effect.effect === 'time') {
      drawSpecialRings(effect, progress, alpha, color, cx, cy);
    } else {
      drawRing(cx, cy, 30 + eased * 100, color, alpha, 2.5);
    }
  }

  function drawSpecialRings(effect, progress, alpha, color, cx, cy) {
    const eased = easeOutCubic(progress);
    if (effect.effect === 'time') {
      for (let i = 0; i < 3; i += 1) {
        ctx.save();
        ctx.globalAlpha = alpha * (1 - i * 0.2);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.shadowColor = color;
        ctx.shadowBlur = 18;
        ctx.beginPath();
        ctx.arc(cx, cy, 36 + i * 28 + eased * 35, effect.seed + progress * TAU, effect.seed + progress * TAU + Math.PI * 1.35);
        ctx.stroke();
        ctx.restore();
      }
    } else if (effect.effect === 'orbit' || effect.effect === 'swarm') {
      for (let i = 0; i < 16; i += 1) {
        const angle = effect.seed + i / 16 * TAU + progress * TAU;
        const radius = 44 + Math.sin(progress * Math.PI) * 100;
        drawRing(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius * 0.55, 4 + alpha * 4, color, alpha, 1.5);
      }
    } else if (effect.effect === 'aura' || effect.effect === 'field' || effect.effect === 'charge') {
      const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 150 + eased * 70);
      gradient.addColorStop(0, color + 'cc');
      gradient.addColorStop(0.45, color + '33');
      gradient.addColorStop(1, color + '00');
      ctx.save();
      ctx.globalAlpha = alpha * 0.7;
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(cx, cy, 150 + eased * 70, 0, TAU);
      ctx.fill();
      ctx.restore();
      drawRing(cx, cy, 42 + eased * 110, color, alpha, 2);
    } else {
      for (let i = 0; i < 3; i += 1) {
        drawRing(cx, cy, 18 + eased * (70 + i * 40), color, alpha * (1 - i * 0.18), 2);
      }
    }
  }

  function drawSparks() {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = sparks.length - 1; i >= 0; i -= 1) {
      const spark = sparks[i];
      spark.x += spark.vx;
      spark.y += spark.vy;
      spark.vy += spark.gravity;
      spark.vx *= 0.988;
      spark.vy *= 0.988;
      spark.life -= spark.decay;
      if (spark.life <= 0) {
        sparks.splice(i, 1);
        continue;
      }
      ctx.globalAlpha = spark.life;
      ctx.fillStyle = spark.color;
      ctx.shadowColor = spark.color;
      ctx.shadowBlur = spark.radius * 2.4;
      ctx.beginPath();
      ctx.arc(spark.x, spark.y, Math.max(0.5, spark.radius * spark.life), 0, TAU);
      ctx.fill();
    }
    ctx.restore();
  }

  function render(now) {
    if (!ctx) {
      requestAnimationFrame(render);
      return;
    }
    ctx.clearRect(0, 0, width, height);
    for (let i = activeEffects.length - 1; i >= 0; i -= 1) {
      const effect = activeEffects[i];
      if (now - effect.born > effect.duration) {
        activeEffects.splice(i, 1);
        continue;
      }
      drawEffect(effect, now);
    }
    drawSparks();
    updatePanel();
    requestAnimationFrame(render);
  }

  function startRenderLoop() {
    if (renderStarted) return;
    renderStarted = true;
    requestAnimationFrame(render);
  }

  function update(results) {
    if (!enabled || !results || !results.multiHandLandmarks) return;
    ensureCanvas();
    ensurePanel();
    startRenderLoop();
    const frame = buildFrameFeatures(results);
    triggerPowers(frame);
  }

  function manualFire(powerId) {
    ensureCanvas();
    ensurePanel();
    startRenderLoop();
    const power = powerById.get(powerId) || POWER_DEFS[0];
    const fakeFrame = {
      primary: {
        pose: 'manual',
        velocity: { x: 0, y: -0.5, z: 0 },
        screen: { x: width * 0.5, y: height * 0.5 },
        indexScreen: { x: width * 0.5, y: height * 0.5 },
      },
      twoHand: { source: { x: width * 0.5, y: height * 0.5 }, motions: new Set() },
    };
    firePower(power, fakeFrame);
  }

  function installResultHook() {
    if (window.__gesturaPowerpackHooked) return;
    const tryHook = () => {
      if (typeof window.onResults !== 'function') {
        window.setTimeout(tryHook, 80);
        return;
      }
      const original = window.onResults;
      window.onResults = function gesturaPowerpackOnResults(results) {
        const output = original.apply(this, arguments);
        try {
          window.GesturaPowerpack.update(results);
        } catch (error) {
          console.warn('[GesturaPowerpack] update failed:', error);
        }
        return output;
      };
      window.__gesturaPowerpackHooked = true;
    };
    tryHook();
  }

  window.GesturaPowerpack = {
    version: VERSION,
    powers: POWER_DEFS.slice(),
    enable() {
      enabled = true;
      ensurePanel();
      updatePanel();
    },
    disable() {
      enabled = false;
      updatePanel();
    },
    isEnabled() {
      return enabled;
    },
    update,
    fire: manualFire,
    getStats() {
      return {
        fired: stats.fired,
        current: stats.current,
        recent: stats.recent.slice(),
        totalPowers: POWER_DEFS.length,
      };
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      ensureCanvas();
      ensurePanel();
      startRenderLoop();
      installResultHook();
    }, { once: true });
  } else {
    ensureCanvas();
    ensurePanel();
    startRenderLoop();
    installResultHook();
  }
})();
