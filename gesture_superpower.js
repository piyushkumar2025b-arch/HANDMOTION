// ============================================================
// GESTURA — Superpower FX Module (Iron Man / Fire / Eyes / Objects)
// Add AFTER gestura_supabase.js in your HTML:
//   <canvas id="fx-canvas" style="position:fixed;inset:0;pointer-events:none;z-index:60;transform:scaleX(-1);"></canvas>
//   <canvas id="eye-canvas" style="position:fixed;inset:0;pointer-events:none;z-index:61;"></canvas>
//   <script src="gestura_superpowers.js"></script>
// ============================================================

const FX = (() => {
  // ─── CANVAS SETUP ────────────────────────────────────────
  let fxCanvas, fxCtx, eyeCanvas, eyeCtx;
  let W = window.innerWidth, H = window.innerHeight;

  function init() {
    fxCanvas = document.getElementById('fx-canvas');
    eyeCanvas = document.getElementById('eye-canvas');
    if (!fxCanvas || !eyeCanvas) {
      // Auto-create if missing
      fxCanvas = Object.assign(document.createElement('canvas'), { id: 'fx-canvas' });
      Object.assign(fxCanvas.style, { position:'fixed', inset:'0', pointerEvents:'none', zIndex:'60', transform:'scaleX(-1)' });
      document.body.appendChild(fxCanvas);

      eyeCanvas = Object.assign(document.createElement('canvas'), { id: 'eye-canvas' });
      Object.assign(eyeCanvas.style, { position:'fixed', inset:'0', pointerEvents:'none', zIndex:'61' });
      document.body.appendChild(eyeCanvas);
    }
    fxCtx = fxCanvas.getContext('2d');
    eyeCtx = eyeCanvas.getContext('2d');
    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(fxLoop);
  }

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    fxCanvas.width = eyeCanvas.width = W;
    fxCanvas.height = eyeCanvas.height = H;
  }

  // ─── PARTICLE POOL ────────────────────────────────────────
  const particles = [];

  function spawnParticle(opts) {
    particles.push({
      x: opts.x, y: opts.y,
      vx: opts.vx || 0, vy: opts.vy || 0,
      life: 1.0, decay: opts.decay || 0.02,
      r: opts.r || 8, rDecay: opts.rDecay || 0.1,
      color: opts.color || '#ff6a00',
      glow: opts.glow || '#ff6a00',
      type: opts.type || 'fire', // fire | spark | energy | heart | star
      gravity: opts.gravity !== undefined ? opts.gravity : 0.08,
      alpha: opts.alpha || 1,
    });
  }

  // ─── POWER STATE ──────────────────────────────────────────
  const powerState = {
    activeMode: null,        // 'ironman'|'fire'|'iloveyou'|'thunder'|'portal'|'freeze'
    palmPositions: [],       // [{x,y}] mirrored screen coords
    eyePositions: [],        // [{x,y}] for face landmarks (if available)
    intensity: 0,
    duration: 0,
    objects: [],             // spawned objects
    beams: [],               // active beam lines
  };

  // ─── IRON MAN REPULSOR ────────────────────────────────────
  function triggerRepulsor(palmX, palmY) {
    // Orange-gold energy ring + beam
    const bx = palmX * W, by = palmY * H;
    // Ring burst
    for (let i = 0; i < 30; i++) {
      const angle = (i / 30) * Math.PI * 2;
      const speed = 3 + Math.random() * 5;
      spawnParticle({
        x: bx, y: by,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        decay: 0.025, r: 5 + Math.random() * 8, rDecay: 0.15,
        color: '#ffd700', glow: '#ff8c00',
        type: 'spark', gravity: 0,
      });
    }
    // Center energy ball
    powerState.objects.push({ type: 'repulsorBall', x: bx, y: by, life: 1.0, r: 30 });

    // Beam forward
    powerState.beams.push({ x1: bx, y1: by, x2: bx, y2: -100, life: 1.0, color: '#00f5ff', width: 8 });

    if (window.GesturaDB) window.GesturaDB.logSuperpower('REPULSOR', 'OPEN_PALM', 800);
  }

  // ─── FIRE HANDS ───────────────────────────────────────────
  function emitFireHands(landmarks) {
    if (!landmarks) return;
    const tips = [4, 8, 12, 16, 20]; // finger tip indices
    tips.forEach(idx => {
      if (!landmarks[idx]) return;
      const x = landmarks[idx].x * W;
      const y = landmarks[idx].y * H;
      for (let i = 0; i < 4; i++) {
        const spread = (Math.random() - 0.5) * 2;
        spawnParticle({
          x: x + spread * 8, y,
          vx: spread * 1.5, vy: -(2 + Math.random() * 4),
          decay: 0.03, r: 6 + Math.random() * 10, rDecay: 0.12,
          color: Math.random() > 0.5 ? '#ff6a00' : '#ff2222',
          glow: '#ff6a00', type: 'fire', gravity: -0.05,
        });
      }
    });
    // Palm ember base
    if (landmarks[0]) {
      const px = landmarks[0].x * W, py = landmarks[0].y * H;
      for (let i = 0; i < 8; i++) {
        spawnParticle({
          x: px + (Math.random() - 0.5) * 60, y: py,
          vx: (Math.random() - 0.5) * 3, vy: -(1 + Math.random() * 3),
          decay: 0.02, r: 12 + Math.random() * 16, rDecay: 0.08,
          color: '#ff4400', glow: '#ff8800', type: 'fire', gravity: -0.03,
        });
      }
    }
  }

  // ─── THUNDER / LIGHTNING ──────────────────────────────────
  function emitThunder(palmX, palmY) {
    const bx = palmX * W, by = palmY * H;
    // Lightning bolt particles
    for (let i = 0; i < 20; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 5 + Math.random() * 10;
      spawnParticle({
        x: bx, y: by,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        decay: 0.04, r: 3 + Math.random() * 6, rDecay: 0.2,
        color: '#b44fff', glow: '#00f5ff', type: 'spark', gravity: 0,
      });
    }
    // Random lightning forks
    for (let f = 0; f < 4; f++) {
      const endX = bx + (Math.random() - 0.5) * 400;
      const endY = by + (Math.random() - 0.5) * 400;
      powerState.beams.push({
        x1: bx, y1: by, x2: endX, y2: endY,
        life: 1.0, color: '#b44fff', width: 2 + Math.random() * 3,
        jitter: true,
      });
    }
    if (window.GesturaDB) window.GesturaDB.logSuperpower('THUNDER', 'PEACE', 500);
  }

  // ─── I LOVE YOU EYES — Flame Hearts ───────────────────────
  function emitHeartEyes(eyePos) {
    // eyePos: [{x,y},{x,y}] in screen px
    eyePos.forEach(pos => {
      for (let i = 0; i < 3; i++) {
        spawnParticle({
          x: pos.x + (Math.random() - 0.5) * 20,
          y: pos.y,
          vx: (Math.random() - 0.5) * 2,
          vy: -(1 + Math.random() * 3),
          decay: 0.02, r: 14 + Math.random() * 10, rDecay: 0.1,
          color: '#ff006e', glow: '#ff006e', type: 'heart', gravity: -0.02,
        });
      }
    });

    // Draw flaming eye overlay directly
    eyePos.forEach(pos => {
      const r = 22;
      eyeCtx.save();
      eyeCtx.shadowColor = '#ff006e';
      eyeCtx.shadowBlur = 30;
      // Eye white
      eyeCtx.beginPath();
      eyeCtx.ellipse(pos.x, pos.y, r, r * 0.65, 0, 0, Math.PI * 2);
      eyeCtx.fillStyle = 'rgba(255,0,110,0.8)';
      eyeCtx.fill();
      // Heart pupil
      drawHeart(eyeCtx, pos.x, pos.y, 12, '#fff');
      eyeCtx.restore();
    });
  }

  // ─── PORTAL / WORMHOLE ────────────────────────────────────
  function emitPortal(palmX, palmY, t) {
    const cx = palmX * W, cy = palmY * H;
    const rings = 5;
    for (let ring = 0; ring < rings; ring++) {
      const radius = 20 + ring * 18;
      const steps = 20;
      for (let i = 0; i < steps; i++) {
        const angle = (i / steps) * Math.PI * 2 + t * (ring % 2 === 0 ? 1 : -1) * 0.05;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius * 0.4;
        spawnParticle({
          x, y,
          vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5,
          decay: 0.1, r: 3, rDecay: 0.05,
          color: ring % 2 === 0 ? '#b44fff' : '#00f5ff',
          glow: '#b44fff', type: 'spark', gravity: 0,
        });
      }
    }
    if (window.GesturaDB) window.GesturaDB.logSuperpower('PORTAL', 'PINCH', 200);
  }

  // ─── FREEZE / ICE ─────────────────────────────────────────
  function emitFreeze(landmarks) {
    if (!landmarks) return;
    const tips = [4, 8, 12, 16, 20];
    tips.forEach(idx => {
      if (!landmarks[idx]) return;
      const x = landmarks[idx].x * W, y = landmarks[idx].y * H;
      for (let i = 0; i < 3; i++) {
        const angle = Math.random() * Math.PI * 2;
        spawnParticle({
          x: x + Math.cos(angle) * 10, y: y + Math.sin(angle) * 10,
          vx: Math.cos(angle) * (1 + Math.random() * 2),
          vy: Math.sin(angle) * (1 + Math.random() * 2) - 1,
          decay: 0.015, r: 4 + Math.random() * 8, rDecay: 0.05,
          color: '#aaeeff', glow: '#00f5ff', type: 'star', gravity: -0.01,
        });
      }
    });
  }

  // ─── SPAWNED OBJECTS (Holographic) ───────────────────────
  function spawnHoloObject(type, x, y) {
    powerState.objects.push({
      type, x: x * W, y: y * H,
      life: 1.0, decay: 0.005,
      rotation: 0, scale: 0,
      targetScale: 1,
    });
    if (window.GesturaDB) window.GesturaDB.logSuperpower('HOLO_OBJECT_' + type.toUpperCase(), 'THREE', 2000);
  }

  // ─── DRAW HELPERS ─────────────────────────────────────────
  function drawHeart(ctx, x, y, size, color) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.beginPath();
    const s = size;
    ctx.moveTo(x, y + s * 0.3);
    ctx.bezierCurveTo(x, y - s * 0.3, x - s, y - s * 0.3, x - s, y + s * 0.1);
    ctx.bezierCurveTo(x - s, y + s * 0.7, x, y + s * 1.1, x, y + s * 1.3);
    ctx.bezierCurveTo(x, y + s * 1.1, x + s, y + s * 0.7, x + s, y + s * 0.1);
    ctx.bezierCurveTo(x + s, y - s * 0.3, x, y - s * 0.3, x, y + s * 0.3);
    ctx.fill();
    ctx.restore();
  }

  function drawStar(ctx, cx, cy, r, color, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 15;
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2;
      const or = i % 2 === 0 ? r : r * 0.4;
      const px = cx + Math.cos(angle - Math.PI / 2) * or;
      const py = cy + Math.sin(angle - Math.PI / 2) * or;
      i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawLightningBolt(ctx, x1, y1, x2, y2, color, width, jitter) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.shadowColor = color;
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    if (jitter) {
      const segs = 6;
      for (let i = 1; i <= segs; i++) {
        const t = i / segs;
        const mx = x1 + (x2 - x1) * t + (Math.random() - 0.5) * 60;
        const my = y1 + (y2 - y1) * t + (Math.random() - 0.5) * 60;
        ctx.lineTo(mx, my);
      }
    } else {
      ctx.lineTo(x2, y2);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawRepulsorBall(ctx, obj) {
    const pulse = 0.5 + 0.5 * Math.sin(Date.now() * 0.01);
    ctx.save();
    const grad = ctx.createRadialGradient(obj.x, obj.y, 0, obj.x, obj.y, obj.r * (1 + pulse * 0.3));
    grad.addColorStop(0, 'rgba(255,255,255,0.9)');
    grad.addColorStop(0.3, 'rgba(255,215,0,0.7)');
    grad.addColorStop(0.7, 'rgba(255,106,0,0.4)');
    grad.addColorStop(1, 'rgba(255,106,0,0)');
    ctx.beginPath();
    ctx.arc(obj.x, obj.y, obj.r * (1.2 + pulse * 0.4), 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.shadowColor = '#ffd700';
    ctx.shadowBlur = 40;
    ctx.fill();
    ctx.restore();
    obj.life -= 0.015;
  }

  function drawHoloObject(ctx, obj) {
    obj.scale += (obj.targetScale - obj.scale) * 0.1;
    obj.rotation += 0.02;
    obj.life -= obj.decay;
    if (obj.life <= 0) return;

    ctx.save();
    ctx.translate(obj.x, obj.y);
    ctx.rotate(obj.rotation);
    ctx.scale(obj.scale, obj.scale);
    ctx.globalAlpha = Math.min(obj.life * 2, 1);

    const color = '#00f5ff';
    ctx.strokeStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 20;
    ctx.lineWidth = 1.5;

    if (obj.type === 'cube') {
      const s = 40;
      // Front face
      ctx.strokeRect(-s/2, -s/2, s, s);
      // Back face (offset)
      ctx.strokeRect(-s/2 + 15, -s/2 - 15, s, s);
      // Connectors
      ctx.beginPath();
      ctx.moveTo(-s/2, -s/2); ctx.lineTo(-s/2+15, -s/2-15);
      ctx.moveTo(s/2, -s/2);  ctx.lineTo(s/2+15, -s/2-15);
      ctx.moveTo(s/2, s/2);   ctx.lineTo(s/2+15, s/2-15);
      ctx.moveTo(-s/2, s/2);  ctx.lineTo(-s/2+15, s/2-15);
      ctx.stroke();
    } else if (obj.type === 'sphere') {
      const r = 35;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.4, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(0, 0, r * 0.4, r, 0, 0, Math.PI * 2); ctx.stroke();
    } else if (obj.type === 'shield') {
      ctx.beginPath();
      ctx.moveTo(0, -45); ctx.lineTo(35, -20);
      ctx.lineTo(35, 15);  ctx.lineTo(0, 45);
      ctx.lineTo(-35, 15); ctx.lineTo(-35, -20);
      ctx.closePath(); ctx.stroke();
      // Inner rings
      ctx.beginPath(); ctx.arc(0, 0, 18, 0, Math.PI * 2); ctx.stroke();
    } else if (obj.type === 'star') {
      drawStar(ctx, 0, 0, 40, color, 1);
    }
    ctx.restore();
  }

  // ─── MAIN FX LOOP ─────────────────────────────────────────
  let frame = 0;

  function fxLoop() {
    frame++;
    fxCtx.clearRect(0, 0, W, H);
    eyeCtx.clearRect(0, 0, W, H);

    // Draw beams
    powerState.beams = powerState.beams.filter(b => b.life > 0);
    powerState.beams.forEach(b => {
      drawLightningBolt(fxCtx, b.x1, b.y1, b.x2, b.y2, b.color, b.width * b.life, b.jitter);
      b.life -= 0.05;
    });

    // Draw objects
    powerState.objects = powerState.objects.filter(o => o.life > 0);
    powerState.objects.forEach(obj => {
      if (obj.type === 'repulsorBall') drawRepulsorBall(fxCtx, obj);
      else drawHoloObject(fxCtx, obj);
    });

    // Draw particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.life -= p.decay;
      p.r -= p.rDecay;

      if (p.life <= 0 || p.r <= 0) { particles.splice(i, 1); continue; }

      fxCtx.save();
      fxCtx.globalAlpha = p.life * p.alpha;
      fxCtx.shadowColor = p.glow;
      fxCtx.shadowBlur = p.r * 2;

      if (p.type === 'fire') {
        const grad = fxCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        grad.addColorStop(0, 'rgba(255,255,200,0.9)');
        grad.addColorStop(0.4, p.color);
        grad.addColorStop(1, 'rgba(255,0,0,0)');
        fxCtx.beginPath();
        fxCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        fxCtx.fillStyle = grad;
        fxCtx.fill();
      } else if (p.type === 'heart') {
        drawHeart(fxCtx, p.x - p.r * 0.8, p.y - p.r * 0.5, p.r * 0.8, p.color);
      } else if (p.type === 'star') {
        drawStar(fxCtx, p.x, p.y, p.r, p.color, p.life);
      } else {
        // spark / energy
        fxCtx.beginPath();
        fxCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        fxCtx.fillStyle = p.color;
        fxCtx.fill();
      }
      fxCtx.restore();
    }

    requestAnimationFrame(fxLoop);
  }

  // ─── PUBLIC API ───────────────────────────────────────────
  window.addEventListener('DOMContentLoaded', init);

  return {
    // Call each frame with current hand landmarks
    updateFrame(landmarks, palmX, palmY, eyePositions) {
      const mode = powerState.activeMode;
      if (!mode) return;
      if (mode === 'fire')      emitFireHands(landmarks);
      if (mode === 'thunder')   emitThunder(palmX, palmY);
      if (mode === 'portal')    emitPortal(palmX, palmY, frame);
      if (mode === 'freeze')    emitFreeze(landmarks);
      if (mode === 'iloveyou' && eyePositions?.length) emitHeartEyes(eyePositions);
    },

    // One-shot triggers
    triggerRepulsor(palmX, palmY) { triggerRepulsor(palmX, palmY); },
    spawnObject(type, palmX, palmY) { spawnHoloObject(type, palmX, palmY); },

    // Mode setter — call from gesture dispatcher in main HTML
    setMode(mode) {
      powerState.activeMode = powerState.activeMode === mode ? null : mode;
      return powerState.activeMode;
    },
    getMode() { return powerState.activeMode; },

    // Expose eye positions setter (for face mesh integration)
    setEyePositions(positions) { powerState.eyePositions = positions; },
  };
})();

window.GesturaFX = FX;