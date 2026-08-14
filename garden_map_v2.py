"""Garden of Words aesthetic — open study grove for Streamlit.

Quiet cinematic Japanese garden (Makoto Shinkai–inspired): soft rain, overcast
light, deep greens, wet stone, mist, restrained blooms. Open-space layout kept;
no cute/pastel anime chibi look.
"""

import json

import streamlit as st

from garden_life import MAX_GROVE_TREES, PRELIMS_TREE_TARGET
from profile import FIRST_NAME

GARDEN_UI_VERSION = "2026.07-garden-of-words-v1"


def render_garden_world_v2(garden_state, height=820):
    life = garden_state.get("life") or garden_state.get("vitality") or {}
    data = {
        "version": GARDEN_UI_VERSION,
        "xp": garden_state.get("xp", 0),
        "life": life.get("life", 40),
        "mood": life.get("mood", "growing"),
        "goalStreak": life.get("goal_streak", 0),
        "harvestTier": life.get("harvest_tier", "sprout"),
        "harvestLabel": life.get("harvest_label", "First Tree"),
        "harvestEmoji": life.get("harvest_emoji", "🌱"),
        "trees": life.get("trees", []),
        "treeCount": life.get("tree_count", 1),
        "unlockedCount": life.get("unlocked_count", 1),
        "maxTrees": life.get("max_trees", MAX_GROVE_TREES),
        "prelimsTarget": life.get("prelims_target", PRELIMS_TREE_TARGET),
        "prelimsTrees": life.get("prelims_trees", 1),
        "treesToPrelims": life.get("trees_to_prelims_full", PRELIMS_TREE_TARGET - 1),
        "journeyPhase": life.get("journey_phase", "prelims"),
        "hasFruit": life.get("has_fruit", False),
        "hasBloom": life.get("has_bloom", False),
        "sakuraCount": life.get("sakura_count", 0),
        "fruitCount": life.get("fruit_count", 0),
        "activeTree": life.get("active_tree")
        or {"progress_days": 0, "wilted": False, "visible": False},
        "waterLevel": life.get("water_level", 0),
        "waterPct": life.get("water_pct", 0),
        "todayHours": life.get("today_hours", 0),
        "dailyGoal": life.get("daily_goal", 6),
        "goalMet": life.get("goal_met", False),
        "daysToNextTree": life.get("days_to_next_tree", 4),
        "nextTree": life.get("next_tree"),
        "weekDays": life.get("week_days", []),
        "hint": life.get("hint", ""),
        "rules": life.get(
            "rules",
            "4 days plant · 6 days bloom · >60% test fruits · streak break wilts active only",
        ),
        "firstName": FIRST_NAME,
        "completeDays": life.get("complete_days", 0),
    }
    payload = json.dumps(data)
    min_h = max(680, height - 20)

    html = f"""
    <div class="lg-wrap" data-garden-version="{GARDEN_UI_VERSION}">
      <canvas id="lgCanvas" class="lg-canvas"></canvas>
      <div class="lg-badge">言の葉 · quiet garden</div>
      <div class="lg-hint" id="lgHintBar">Drag · scroll zoom · click a tree</div>
    </div>
    <style>
      .lg-wrap {{
        position: relative;
        width: 100%;
        min-height: {min_h}px;
        background: #4a5a58;
        overflow: hidden;
        border-radius: 14px;
        box-shadow:
          0 0 0 1px rgba(120, 140, 130, 0.25),
          0 22px 50px rgba(20, 30, 28, 0.4);
      }}
      .lg-canvas {{
        width: 100%;
        min-height: {min_h}px;
        display: block;
        cursor: grab;
        touch-action: none;
      }}
      .lg-canvas.grab {{ cursor: grabbing; }}
      .lg-badge {{
        position: absolute; top: 12px; right: 12px; z-index: 3;
        background: rgba(28, 36, 34, 0.72);
        color: rgba(220, 230, 220, 0.9);
        border: 1px solid rgba(180, 200, 190, 0.18);
        padding: 7px 14px; border-radius: 6px;
        font: 500 10px/1.2 'Segoe UI',system-ui,sans-serif;
        letter-spacing: 0.08em;
        backdrop-filter: blur(10px);
        pointer-events: none;
      }}
      .lg-hint {{
        position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%);
        background: rgba(20, 28, 26, 0.65); backdrop-filter: blur(12px);
        color: rgba(210, 220, 210, 0.85);
        border: 1px solid rgba(160, 180, 170, 0.15);
        padding: 8px 16px; border-radius: 6px; white-space: nowrap;
        font: 500 10px/1.4 'Segoe UI',system-ui,sans-serif; pointer-events: none;
        z-index: 2; letter-spacing: 0.04em;
      }}
      .lg-tip {{
        position: absolute; z-index: 5; min-width: 160px; max-width: 250px;
        background: rgba(22, 30, 28, 0.94);
        border: 1px solid rgba(140, 170, 150, 0.28);
        border-radius: 8px; padding: 11px 13px; color: #d8e2d8;
        font: 400 11px/1.5 'Segoe UI',system-ui,sans-serif;
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.35); pointer-events: none;
        display: none;
      }}
      .lg-tip.on {{ display: block; }}
      .lg-tip strong {{ display: block; color: #a8c8b0; margin-bottom: 4px; font-weight: 600; }}
      .lg-tip .m {{ color: rgba(180, 195, 185, 0.55); font-size: 10px; }}
    </style>
    <div class="lg-tip" id="lgTip"></div>
    <script>
    (function() {{
      try {{
      const D = {payload};
      const cvs = document.getElementById('lgCanvas');
      const tipEl = document.getElementById('lgTip');
      if (!cvs) return;
      const ctx = cvs.getContext('2d');

      // Open world (kept)
      const WW = 1720, WH = 1200;
      const CX = WW * 0.5, CY = WH * 0.56;

      let W = 0, H = 0, t = 0, panX = 0, panY = 0, zoom = 1;
      let drag = false, dx = 0, dy = 0, moved = 0, selected = null;
      const posCache = {{}};
      const rain = [], mist = [], petals = [], leaves = [], ripples = [];
      const stones = [], ferns = [], puddles = [];

      function rng(seed) {{
        let s = (seed % 2147483646) || 1;
        return function() {{ s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }};
      }}
      function clamp(v, a, b) {{ return Math.max(a, Math.min(b, v)); }}

      function treeBloomed(tree) {{
        return !!(tree && (tree.has_sakura || tree.has_flowers || tree.growth === 'sakura'));
      }}
      function treeFruited(tree) {{
        return !!(tree && (tree.has_fruit || tree.growth === 'fruiting'));
      }}

      function treeWorldPos(slot) {{
        if (posCache[slot]) return posCache[slot];
        const golden = Math.PI * (3 - Math.sqrt(5));
        const r = rng(slot * 7919 + 42);
        const ring = 80 + Math.sqrt(slot + 0.85) * 80;
        const ang = slot * golden + 0.35;
        let x = CX + Math.cos(ang) * ring * 1.35 + (r() - 0.5) * 30;
        let y = CY + Math.sin(ang) * ring * 0.7 + (r() - 0.5) * 24;
        // Keep pavilion / pond clear
        const pdx = x - (CX - 200), pdy = y - (CY + 10);
        if (pdx * pdx + pdy * pdy * 1.6 < 100 * 100) {{ x += 115; y += 45; }}
        x = clamp(x, 140, WW - 140);
        y = clamp(y, 360, WH - 100);
        posCache[slot] = {{ x, y }};
        return posCache[slot];
      }}

      function screenPos(wx, wy, parallax) {{
        parallax = parallax == null ? 1 : parallax;
        return {{
          x: (wx + panX * parallax - W / 2) * zoom + W / 2,
          y: (wy + panY * parallax - H / 2) * zoom + H / 2
        }};
      }}

      function inView(sx, sy, m) {{
        m = m || 100;
        return sx > -m && sx < W + m && sy > -m && sy < H + m;
      }}

      function roundRect(x, y, w, h, r) {{
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
      }}

      function initWorld() {{
        rain.length = 0; mist.length = 0; petals.length = 0; leaves.length = 0;
        stones.length = 0; ferns.length = 0; puddles.length = 0; ripples.length = 0;
        const r = rng(42000 + (D.treeCount || 0) * 11);

        // Soft rain (Garden of Words staple)
        for (let i = 0; i < 140; i++) {{
          rain.push({{
            x: r() * WW, y: r() * WH,
            len: 10 + r() * 18, sp: 3.2 + r() * 2.8,
            a: 0.08 + r() * 0.14, thick: 0.6 + r() * 0.8
          }});
        }}
        // Ground mist bands
        for (let i = 0; i < 10; i++) {{
          mist.push({{
            x: r() * WW, y: 420 + r() * 400,
            w: 120 + r() * 200, h: 30 + r() * 50,
            sp: 0.08 + r() * 0.12, a: 0.04 + r() * 0.06
          }});
        }}
        // Sparse, elegant falling petals (only if blooms exist)
        const nPetals = Math.min(28, 6 + (D.sakuraCount || 0) * 3);
        for (let i = 0; i < nPetals; i++) {{
          petals.push({{
            x: r() * WW, y: r() * WH * 0.6,
            vx: 0.15 + r() * 0.25, vy: 0.2 + r() * 0.3,
            rot: r() * 6.28, spin: (r() - 0.5) * 0.03,
            s: 1.6 + r() * 2, a: 0.35 + r() * 0.35
          }});
        }}
        for (let i = 0; i < 16; i++) {{
          leaves.push({{
            x: r() * WW, y: 400 + r() * 500,
            vx: 0.1 + r() * 0.2, vy: 0.05 + r() * 0.12,
            rot: r() * 6.28, spin: (r() - 0.5) * 0.02,
            s: 3 + r() * 3, a: 0.25 + r() * 0.25
          }});
        }}
        // Wet stepping stones — quiet path through clearing
        for (let i = 0; i < 16; i++) {{
          const u = i / 15;
          stones.push({{
            x: CX - 300 + u * 620 + Math.sin(u * 3.5) * 36,
            y: CY + 55 + Math.sin(u * 2.8) * 42,
            rx: 14 + (i % 3) * 2, ry: 8 + (i % 2),
            wet: true
          }});
        }}
        for (let i = 0; i < 12; i++) {{
          stones.push({{
            x: 160 + r() * (WW - 320),
            y: 430 + r() * (WH - 500),
            rx: 10 + r() * 14, ry: 6 + r() * 6,
            wet: r() > 0.4
          }});
        }}
        // Rain puddles
        for (let i = 0; i < 10; i++) {{
          puddles.push({{
            x: 200 + r() * (WW - 400),
            y: 450 + r() * (WH - 520),
            rx: 16 + r() * 28, ry: 6 + r() * 10
          }});
        }}
        // Fern clusters
        for (let i = 0; i < 22; i++) {{
          ferns.push({{
            x: 100 + r() * (WW - 200),
            y: 420 + r() * (WH - 480),
            s: 0.7 + r() * 0.6, a: r() * 0.5
          }});
        }}
      }}

      function resize() {{
        const parent = cvs.parentElement;
        let rw = (parent && parent.clientWidth) || 0;
        if (rw < 80) rw = Math.min(1200, (window.innerWidth || 900) - 24);
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        W = Math.floor(rw);
        H = Math.max({min_h}, Math.floor(W * 0.6));
        cvs.width = Math.floor(W * dpr);
        cvs.height = Math.floor(H * dpr);
        cvs.style.width = W + 'px';
        cvs.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        initWorld();

        const trees = D.trees || [];
        let fx = CX, fy = CY;
        if (trees.length) {{
          let sx = 0, sy = 0;
          trees.forEach(tr => {{ const p = treeWorldPos(tr.slot); sx += p.x; sy += p.y; }});
          fx = sx / trees.length; fy = sy / trees.length;
        }}
        panX = W * 0.5 - fx;
        panY = H * 0.52 - fy;
        zoom = 1.0;
        clampPan();
      }}

      function clampPan() {{
        const pad = 50;
        panX = Math.min(pad, Math.max(W - WW - pad, panX));
        panY = Math.min(pad, Math.max(H - WH - pad, panY));
      }}

      // ─── Overcast Shinkai sky ─────────────────────────────────────
      function drawSky() {{
        const g = ctx.createLinearGradient(0, 0, 0, H);
        // Soft rainy day: cool greys → muted green horizon
        if (D.mood === 'flourishing') {{
          g.addColorStop(0, '#6a7a82');
          g.addColorStop(0.35, '#8a9aa0');
          g.addColorStop(0.65, '#a8b8b0');
          g.addColorStop(1, '#7a9a78');
        }} else {{
          g.addColorStop(0, '#5a6870');
          g.addColorStop(0.3, '#74848c');
          g.addColorStop(0.55, '#8e9c98');
          g.addColorStop(0.78, '#7a9080');
          g.addColorStop(1, '#5a7a5e');
        }}
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);

        // Soft cloud sheets (not cartoon puffs)
        for (let i = 0; i < 6; i++) {{
          const cy = H * (0.08 + i * 0.07);
          const drift = Math.sin(t * 0.004 + i) * 20 + panX * 0.04;
          const cg = ctx.createLinearGradient(0, cy - 30, 0, cy + 40);
          cg.addColorStop(0, 'rgba(255,255,255,0)');
          cg.addColorStop(0.5, 'rgba(220, 228, 230, ' + (0.06 + i * 0.015) + ')');
          cg.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = cg;
          ctx.fillRect(drift - 40, cy - 35, W + 80, 70);
        }}

        // Soft diffused light break in clouds
        const sx = W * 0.62 + Math.sin(t * 0.003) * 8;
        const sy = H * 0.22;
        const sun = ctx.createRadialGradient(sx, sy, 0, sx, sy, 180);
        sun.addColorStop(0, 'rgba(255, 250, 235, 0.14)');
        sun.addColorStop(0.4, 'rgba(200, 215, 210, 0.06)');
        sun.addColorStop(1, 'transparent');
        ctx.fillStyle = sun;
        ctx.beginPath(); ctx.arc(sx, sy, 180, 0, Math.PI * 2); ctx.fill();

        // Very soft light shafts (overcast god rays)
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 5; i++) {{
          const ang = 0.35 + i * 0.12 + Math.sin(t * 0.006 + i) * 0.02;
          const len = 420;
          ctx.beginPath();
          ctx.moveTo(sx, sy);
          ctx.lineTo(sx + Math.cos(ang) * len, sy + Math.sin(ang) * len);
          ctx.lineTo(sx + Math.cos(ang + 0.07) * len * 0.9, sy + Math.sin(ang + 0.07) * len * 0.9);
          ctx.closePath();
          ctx.fillStyle = 'rgba(230, 240, 235, ' + (0.012 + 0.008 * Math.sin(t * 0.015 + i)) + ')';
          ctx.fill();
        }}
        ctx.restore();
      }}

      function drawDistantTrees() {{
        // Soft forest wall — muted silhouettes
        const layers = [
          {{ y: 0.40, c: 'rgba(55, 70, 62, 0.35)', p: 0.15, dens: 18 }},
          {{ y: 0.46, c: 'rgba(45, 65, 52, 0.45)', p: 0.28, dens: 22 }},
          {{ y: 0.52, c: 'rgba(38, 58, 45, 0.55)', p: 0.4, dens: 16 }}
        ];
        for (let L = 0; L < layers.length; L++) {{
          const layer = layers[L];
          const baseY = H * layer.y;
          const shift = panX * layer.p * 0.12;
          ctx.fillStyle = layer.c;
          for (let i = 0; i < layer.dens; i++) {{
            const x = ((i / layer.dens) * (W + 100) - 50 + shift * 0.5) % (W + 100) - 20;
            const h = 40 + (i % 5) * 12 + L * 8;
            ctx.beginPath();
            ctx.moveTo(x, baseY + 30);
            ctx.lineTo(x - 18 - L * 4, baseY + 30);
            ctx.lineTo(x, baseY - h);
            ctx.lineTo(x + 18 + L * 4, baseY + 30);
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            ctx.arc(x, baseY - h + 8, 16 + L * 3, 0, Math.PI * 2);
            ctx.fill();
          }}
        }}
      }}

      // ─── Ground ──────────────────────────────────────────────────
      function drawGround() {{
        const c = screenPos(CX, CY + 30);
        // Deep wet green meadow
        const g = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, 800 * zoom);
        g.addColorStop(0, '#4a7a52');
        g.addColorStop(0.35, '#3a6a44');
        g.addColorStop(0.7, '#2d5536');
        g.addColorStop(1, '#1e3a26');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.ellipse(c.x, c.y, 800 * zoom, 430 * zoom, 0, 0, Math.PI * 2);
        ctx.fill();

        // Moss patches
        const r = rng(77);
        for (let i = 0; i < 24; i++) {{
          const wx = 180 + r() * (WW - 360);
          const wy = 420 + r() * (WH - 500);
          const p = screenPos(wx, wy);
          if (!inView(p.x, p.y, 20)) continue;
          ctx.fillStyle = 'rgba(60, 110, 70, ' + (0.15 + r() * 0.15) + ')';
          ctx.beginPath();
          ctx.ellipse(p.x, p.y, (20 + r() * 30) * zoom, (8 + r() * 12) * zoom, r() * 0.5, 0, Math.PI * 2);
          ctx.fill();
        }}

        // Wet grass strokes
        for (let i = 0; i < 180; i++) {{
          const wx = 100 + ((i * 97) % (WW - 200));
          const wy = 400 + ((i * 53) % (WH - 480));
          const p = screenPos(wx, wy);
          if (!inView(p.x, p.y, 0)) continue;
          const sway = Math.sin(t * 0.02 + i * 0.3) * 1.2 * zoom;
          ctx.strokeStyle = 'rgba(40, 80, 48, 0.35)';
          ctx.lineWidth = 1 * zoom;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x + sway, p.y - (6 + (i % 5)) * zoom);
          ctx.stroke();
        }}

        // Ferns
        for (let i = 0; i < ferns.length; i++) {{
          const f = ferns[i];
          const p = screenPos(f.x, f.y);
          if (!inView(p.x, p.y, 20)) continue;
          const s = f.s * zoom;
          const sway = Math.sin(t * 0.018 + f.a * 5) * 2 * zoom;
          ctx.strokeStyle = 'rgba(50, 90, 55, 0.45)';
          ctx.lineWidth = 1.2 * zoom;
          for (let k = 0; k < 5; k++) {{
            const ang = -1.2 + k * 0.5;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.quadraticCurveTo(
              p.x + Math.cos(ang) * 10 * s + sway,
              p.y - 8 * s,
              p.x + Math.cos(ang) * 16 * s + sway,
              p.y - 14 * s
            );
            ctx.stroke();
          }}
        }}

        // Puddles (rain reflections)
        for (let i = 0; i < puddles.length; i++) {{
          const u = puddles[i];
          const p = screenPos(u.x, u.y);
          if (!inView(p.x, p.y, 20)) continue;
          const pg = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, u.rx * zoom);
          pg.addColorStop(0, 'rgba(140, 170, 175, 0.35)');
          pg.addColorStop(0.6, 'rgba(80, 110, 100, 0.25)');
          pg.addColorStop(1, 'rgba(40, 60, 50, 0.1)');
          ctx.fillStyle = pg;
          ctx.beginPath();
          ctx.ellipse(p.x, p.y, u.rx * zoom, u.ry * zoom, 0, 0, Math.PI * 2);
          ctx.fill();
          // soft sky reflection streak
          ctx.strokeStyle = 'rgba(200, 215, 210, 0.2)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.ellipse(p.x - 4 * zoom, p.y - 2 * zoom, u.rx * 0.4 * zoom, u.ry * 0.25 * zoom, -0.2, 0, Math.PI);
          ctx.stroke();
        }}

        // Wet stones
        for (let i = 0; i < stones.length; i++) {{
          const s = stones[i];
          const p = screenPos(s.x, s.y);
          if (!inView(p.x, p.y, 10)) continue;
          const sg = ctx.createRadialGradient(p.x - 3, p.y - 2, 0, p.x, p.y, s.rx * zoom);
          if (s.wet) {{
            sg.addColorStop(0, 'rgba(130, 140, 135, 0.85)');
            sg.addColorStop(0.5, 'rgba(90, 100, 95, 0.8)');
            sg.addColorStop(1, 'rgba(55, 65, 60, 0.7)');
          }} else {{
            sg.addColorStop(0, 'rgba(110, 115, 108, 0.7)');
            sg.addColorStop(1, 'rgba(70, 75, 68, 0.6)');
          }}
          ctx.fillStyle = sg;
          ctx.beginPath();
          ctx.ellipse(p.x, p.y, s.rx * zoom, s.ry * zoom, 0, 0, Math.PI * 2);
          ctx.fill();
          if (s.wet) {{
            ctx.strokeStyle = 'rgba(200, 215, 210, 0.25)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.ellipse(p.x - 2, p.y - 1, s.rx * 0.5 * zoom, s.ry * 0.3 * zoom, -0.3, 0, Math.PI);
            ctx.stroke();
          }}
        }}
      }}

      function drawPond() {{
        const wx = CX - 200, wy = CY + 10;
        const sp = screenPos(wx, wy);
        if (!inView(sp.x, sp.y, 130)) return;
        const rx = 100 * zoom, ry = 44 * zoom;

        // Dark wet shore
        ctx.fillStyle = 'rgba(30, 45, 38, 0.35)';
        ctx.beginPath();
        ctx.ellipse(sp.x + 2, sp.y + 4, rx + 10 * zoom, ry + 7 * zoom, 0, 0, Math.PI * 2);
        ctx.fill();

        // Still rain-pond — cool muted reflection
        const wg = ctx.createRadialGradient(sp.x - 10, sp.y - 8, 0, sp.x, sp.y, rx);
        wg.addColorStop(0, 'rgba(150, 175, 175, 0.55)');
        wg.addColorStop(0.4, 'rgba(80, 115, 115, 0.6)');
        wg.addColorStop(0.8, 'rgba(40, 70, 70, 0.55)');
        wg.addColorStop(1, 'rgba(25, 50, 48, 0.45)');
        ctx.fillStyle = wg;
        ctx.beginPath();
        ctx.ellipse(sp.x, sp.y, rx, ry, 0, 0, Math.PI * 2);
        ctx.fill();

        // Soft sky reflection
        ctx.save();
        ctx.beginPath();
        ctx.ellipse(sp.x, sp.y, rx * 0.9, ry * 0.85, 0, 0, Math.PI * 2);
        ctx.clip();
        const refl = ctx.createLinearGradient(sp.x, sp.y - ry, sp.x, sp.y + ry);
        refl.addColorStop(0, 'rgba(180, 195, 200, 0.2)');
        refl.addColorStop(1, 'rgba(40, 60, 55, 0.1)');
        ctx.fillStyle = refl;
        ctx.fillRect(sp.x - rx, sp.y - ry, rx * 2, ry * 2);

        // Rain ripple rings
        for (let i = 0; i < 4; i++) {{
          const phase = (t * 0.03 + i * 1.4) % 3;
          const rr = phase * 14 * zoom;
          ctx.strokeStyle = 'rgba(200, 220, 215, ' + (0.15 * (1 - phase / 3)) + ')';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.ellipse(
            sp.x + Math.sin(i * 2) * 25 * zoom,
            sp.y + Math.cos(i * 1.5) * 10 * zoom,
            rr, rr * 0.4, 0, 0, Math.PI * 2
          );
          ctx.stroke();
        }}
        ctx.restore();

        ctx.strokeStyle = 'rgba(50, 70, 60, 0.4)';
        ctx.lineWidth = 3 * zoom;
        ctx.beginPath();
        ctx.ellipse(sp.x, sp.y, rx, ry, 0, 0, Math.PI * 2);
        ctx.stroke();
      }}

      function drawPavilion() {{
        // Quiet wooden shelter / bench feel — not a bright torii carnival
        const wx = CX + 320, wy = CY - 100;
        const sp = screenPos(wx, wy);
        if (!inView(sp.x, sp.y, 100)) return;
        const z = zoom;

        // Shadow
        ctx.fillStyle = 'rgba(20, 30, 25, 0.2)';
        ctx.beginPath();
        ctx.ellipse(sp.x, sp.y + 28 * z, 50 * z, 12 * z, 0, 0, Math.PI * 2);
        ctx.fill();

        // Posts
        ctx.fillStyle = '#4a3a30';
        ctx.fillRect(sp.x - 32 * z, sp.y - 20 * z, 5 * z, 48 * z);
        ctx.fillRect(sp.x + 27 * z, sp.y - 20 * z, 5 * z, 48 * z);
        // Roof
        const rg = ctx.createLinearGradient(sp.x, sp.y - 50 * z, sp.x, sp.y - 15 * z);
        rg.addColorStop(0, '#3d4a42');
        rg.addColorStop(1, '#2a3530');
        ctx.fillStyle = rg;
        ctx.beginPath();
        ctx.moveTo(sp.x - 48 * z, sp.y - 18 * z);
        ctx.lineTo(sp.x, sp.y - 48 * z);
        ctx.lineTo(sp.x + 48 * z, sp.y - 18 * z);
        ctx.lineTo(sp.x + 42 * z, sp.y - 12 * z);
        ctx.lineTo(sp.x - 42 * z, sp.y - 12 * z);
        ctx.closePath();
        ctx.fill();
        // Bench
        ctx.fillStyle = '#5a4a3c';
        ctx.fillRect(sp.x - 28 * z, sp.y + 8 * z, 56 * z, 4 * z);
        // Soft rain drips from eaves
        ctx.strokeStyle = 'rgba(180, 200, 195, 0.2)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 5; i++) {{
          const dx = -30 + i * 15;
          const drop = ((t * 0.4 + i * 20) % 40);
          ctx.beginPath();
          ctx.moveTo(sp.x + dx * z, sp.y - 12 * z);
          ctx.lineTo(sp.x + dx * z, sp.y - 12 * z + drop * 0.4 * z);
          ctx.stroke();
        }}
      }}

      // ─── Trees (realistic soft, not candy anime) ─────────────────
      function growthScale(tree) {{
        const m = {{ sapling: 0.55, young: 0.75, mature: 0.95, fruiting: 1.05, sakura: 1.08 }};
        return (m[tree.growth] || 0.8) * (1 + Math.sin(t * 0.018 + (tree.slot || 0)) * 0.008);
      }}

      function drawTree(tree) {{
        const wp = treeWorldPos(tree.slot);
        const sp = screenPos(wp.x, wp.y);
        if (!inView(sp.x, sp.y, 90)) return;

        const s = growthScale(tree) * zoom;
        const wind = Math.sin(t / 60 + tree.slot * 0.5) * 1.8 * zoom;
        const x = sp.x, y = sp.y;
        const bloomed = treeBloomed(tree);
        const fruited = treeFruited(tree);
        const sel = selected && selected.slot === tree.slot;

        // Soft wet shadow
        ctx.fillStyle = 'rgba(15, 30, 20, 0.28)';
        ctx.beginPath();
        ctx.ellipse(x + 1, y + 5, 26 * s, 8 * s, 0, 0, Math.PI * 2);
        ctx.fill();

        if (sel) {{
          ctx.strokeStyle = 'rgba(160, 190, 170, 0.55)';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.ellipse(x, y + 6, 30 * s, 10 * s, 0, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);
        }}

        // Trunk — muted brown, wet look
        const tg = ctx.createLinearGradient(x - 6 * s, y, x + 6 * s, y);
        tg.addColorStop(0, '#3e3228');
        tg.addColorStop(0.4, '#5c4a3a');
        tg.addColorStop(1, '#2e241c');
        ctx.fillStyle = tg;
        ctx.beginPath();
        ctx.moveTo(x - 5 * s + wind * 0.1, y);
        ctx.quadraticCurveTo(x - 3.5 * s + wind * 0.4, y - 24 * s, x - 3 * s + wind, y - 50 * s);
        ctx.lineTo(x + 3 * s + wind, y - 50 * s);
        ctx.quadraticCurveTo(x + 3.5 * s + wind * 0.4, y - 24 * s, x + 5 * s + wind * 0.1, y);
        ctx.closePath();
        ctx.fill();
        // Wet bark sheen
        ctx.strokeStyle = 'rgba(180, 190, 180, 0.1)';
        ctx.lineWidth = 1.2 * s;
        ctx.beginPath();
        ctx.moveTo(x - 1 * s + wind * 0.3, y - 8 * s);
        ctx.lineTo(x + wind * 0.7, y - 45 * s);
        ctx.stroke();

        // Foliage — deep natural greens; bloom = soft muted pink, not neon
        const canopy = bloomed ? [
          {{ dx: 0, dy: -58, r: 30, c0: '#c4a8a8', c1: '#7a5a5a' }},
          {{ dx: -20, dy: -46, r: 20, c0: '#d0b4b4', c1: '#8a6565' }},
          {{ dx: 20, dy: -48, r: 18, c0: '#b89898', c1: '#6a4a4a' }},
          {{ dx: -8, dy: -70, r: 16, c0: '#d8c0c0', c1: '#9a7070' }},
          {{ dx: 12, dy: -66, r: 15, c0: '#c8acac', c1: '#805858' }},
          {{ dx: 0, dy: -42, r: 14, c0: '#a88888', c1: '#5a4040' }}
        ] : [
          {{ dx: 0, dy: -56, r: 30, c0: '#5a8a58', c1: '#1e4024' }},
          {{ dx: -20, dy: -44, r: 20, c0: '#6a9a64', c1: '#2a5030' }},
          {{ dx: 20, dy: -46, r: 18, c0: '#4a7a48', c1: '#183820' }},
          {{ dx: -8, dy: -68, r: 16, c0: '#70a068', c1: '#2e5534' }},
          {{ dx: 12, dy: -64, r: 15, c0: '#5a8854', c1: '#244828' }},
          {{ dx: 0, dy: -40, r: 14, c0: '#4a7048', c1: '#1a3820' }}
        ];

        for (let i = 0; i < canopy.length; i++) {{
          const b = canopy[i];
          const cx = x + b.dx * s + wind;
          const cy = y + b.dy * s;
          const rg = ctx.createRadialGradient(
            cx - b.r * 0.25 * s, cy - b.r * 0.3 * s, 0,
            cx, cy, b.r * s
          );
          rg.addColorStop(0, b.c0);
          rg.addColorStop(1, b.c1);
          ctx.fillStyle = rg;
          ctx.beginPath();
          ctx.arc(cx, cy, b.r * s, 0, Math.PI * 2);
          ctx.fill();
        }}

        // Soft rain-dark edge on canopy
        ctx.strokeStyle = 'rgba(10, 25, 15, 0.12)';
        ctx.lineWidth = 2 * s;
        ctx.beginPath();
        ctx.arc(x + wind, y - 52 * s, 28 * s, 0.2, Math.PI - 0.2);
        ctx.stroke();

        // Sparse restrained blossoms
        if (bloomed) {{
          const r = rng(tree.slot * 91 + 5);
          for (let i = 0; i < 8; i++) {{
            const fx = x + (r() - 0.5) * 48 * s + wind;
            const fy = y - 40 * s - r() * 35 * s;
            ctx.fillStyle = 'rgba(230, 210, 210, ' + (0.45 + r() * 0.3) + ')';
            ctx.beginPath();
            ctx.arc(fx, fy, (1.6 + r() * 1.4) * s, 0, Math.PI * 2);
            ctx.fill();
          }}
        }}

        // Fruit — deep muted, not shiny cartoon
        if (fruited) {{
          const fruits = [[-10, -44], [8, -52], [14, -36], [-2, -58], [4, -32]];
          for (let i = 0; i < fruits.length; i++) {{
            const fx = x + fruits[i][0] * s + wind;
            const fy = y + fruits[i][1] * s;
            const rr = 4 * s;
            const fg = ctx.createRadialGradient(fx - 1, fy - 1, 0, fx, fy, rr);
            fg.addColorStop(0, '#a05048');
            fg.addColorStop(1, '#5a2820');
            ctx.fillStyle = fg;
            ctx.beginPath(); ctx.arc(fx, fy, rr, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = 'rgba(220, 200, 180, 0.2)';
            ctx.beginPath(); ctx.arc(fx - rr * 0.25, fy - rr * 0.25, rr * 0.25, 0, Math.PI * 2); ctx.fill();
          }}
        }}

        // Quiet label
        if (s / zoom >= 0.65) {{
          const tw = 52 * zoom, th = 16 * zoom;
          ctx.fillStyle = 'rgba(18, 26, 24, 0.7)';
          roundRect(x - tw / 2, y + 12 * zoom, tw, th, 4);
          ctx.fill();
          ctx.fillStyle = 'rgba(200, 215, 200, 0.85)';
          ctx.font = '500 ' + Math.max(8, 8 * zoom) + 'px Segoe UI,sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          const tag = tree.test_no ? ('T' + tree.test_no) : ('#' + tree.tree_no);
          ctx.fillText(tag, x, y + 12 * zoom + th / 2);
          if (fruited && tree.score != null) {{
            ctx.fillStyle = 'rgba(200, 160, 130, 0.8)';
            ctx.font = '500 ' + Math.max(7, 7.5 * zoom) + 'px sans-serif';
            ctx.fillText(tree.score + '%', x, y - 78 * s);
          }}
        }}
      }}

      function drawActiveSprout() {{
        const active = D.activeTree || {{}};
        if (!active.visible) return;
        const slot = (D.trees || []).length;
        const wp = treeWorldPos(slot);
        const sp = screenPos(wp.x, wp.y);
        if (!inView(sp.x, sp.y)) return;
        const wilted = !!active.wilted;
        const progress = Math.max(1, active.progress_days || 1);
        const s = (0.42 + progress * 0.08) * zoom;
        const wind = Math.sin(t / 50) * (wilted ? 0.4 : 1.5) * zoom;
        const lean = wilted ? 6 * zoom : 0;
        const x = sp.x + lean, y = sp.y;

        ctx.strokeStyle = wilted ? 'rgba(140, 130, 80, 0.5)' : 'rgba(140, 170, 150, 0.45)';
        ctx.setLineDash([4 * zoom, 5 * zoom]);
        ctx.lineWidth = 1.5 * zoom;
        ctx.beginPath();
        ctx.ellipse(sp.x, y + 8, 24 * zoom, 8 * zoom, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = wilted ? '#6a5a40' : '#4a3a30';
        ctx.fillRect(x - 2.2 * s + wind * 0.1, y - 16 * s, 4.4 * s, 18 * s);

        const rg = ctx.createRadialGradient(x + wind, y - 22 * s, 0, x + wind, y - 22 * s, 13 * s);
        if (wilted) {{
          rg.addColorStop(0, '#a09050'); rg.addColorStop(1, '#6a6030');
        }} else {{
          rg.addColorStop(0, '#6a9a60'); rg.addColorStop(1, '#2a5030');
        }}
        ctx.fillStyle = rg;
        ctx.beginPath();
        ctx.arc(x + wind, y - 22 * s, 13 * s, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(190, 205, 190, 0.75)';
        ctx.font = '500 ' + Math.max(9, 10 * zoom) + 'px Segoe UI,sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(wilted ? 'wilting · streak paused' : 'growing · day ' + progress + '/4', sp.x, y + 26 * zoom);
      }}

      function drawMarker() {{
        // Subtle presence marker — not a chibi
        const trees = D.trees || [];
        let wx = CX, wy = CY + 60;
        if (trees.length) {{
          const last = treeWorldPos(trees[trees.length - 1].slot);
          wx = last.x + 24; wy = last.y + 8;
        }}
        const sp = screenPos(wx, wy);
        if (!inView(sp.x, sp.y, 20)) return;
        const z = zoom;
        const pulse = 0.35 + 0.15 * Math.sin(t * 0.05);
        ctx.strokeStyle = 'rgba(180, 200, 190, ' + pulse + ')';
        ctx.lineWidth = 1.5 * z;
        ctx.beginPath();
        ctx.ellipse(sp.x, sp.y, 10 * z, 4 * z, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = 'rgba(200, 215, 200, 0.7)';
        ctx.beginPath();
        ctx.arc(sp.x, sp.y - 2 * z, 2.5 * z, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(180, 195, 185, 0.55)';
        ctx.font = '400 ' + Math.max(8, 8.5 * z) + 'px Segoe UI,sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(D.firstName || 'you', sp.x, sp.y + 16 * z);
      }}

      // ─── Atmosphere particles ────────────────────────────────────
      function drawRain() {{
        ctx.lineCap = 'round';
        for (let i = 0; i < rain.length; i++) {{
          const d = rain[i];
          d.y += d.sp;
          d.x += 0.4;
          if (d.y > WH) {{ d.y = -20; d.x = Math.random() * WW; }}
          if (d.x > WW) d.x = 0;
          const p = screenPos(d.x, d.y);
          if (!inView(p.x, p.y, 20)) continue;
          ctx.strokeStyle = 'rgba(200, 215, 215, ' + d.a + ')';
          ctx.lineWidth = d.thick * zoom;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x + 1.5 * zoom, p.y + d.len * zoom);
          ctx.stroke();
        }}
      }}

      function drawMist() {{
        for (let i = 0; i < mist.length; i++) {{
          const m = mist[i];
          m.x += m.sp;
          if (m.x > WW + 100) m.x = -150;
          const p = screenPos(m.x, m.y);
          if (!inView(p.x, p.y, 120)) continue;
          const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, m.w * zoom);
          g.addColorStop(0, 'rgba(200, 215, 210, ' + m.a + ')');
          g.addColorStop(1, 'transparent');
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.ellipse(p.x, p.y, m.w * zoom, m.h * zoom, 0, 0, Math.PI * 2);
          ctx.fill();
        }}
      }}

      function drawPetals() {{
        for (let i = 0; i < petals.length; i++) {{
          const p = petals[i];
          p.x += p.vx; p.y += p.vy; p.rot += p.spin;
          if (p.y > WH - 40) {{ p.y = 80; p.x = Math.random() * WW; }}
          const sp = screenPos(p.x, p.y);
          if (!inView(sp.x, sp.y, 0)) continue;
          ctx.save();
          ctx.translate(sp.x, sp.y);
          ctx.rotate(p.rot);
          ctx.globalAlpha = p.a;
          ctx.fillStyle = '#c8b0b0';
          ctx.beginPath();
          ctx.ellipse(0, 0, p.s * zoom, p.s * 0.5 * zoom, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }}
        ctx.globalAlpha = 1;
      }}

      function drawLeaves() {{
        for (let i = 0; i < leaves.length; i++) {{
          const L = leaves[i];
          L.x += L.vx; L.y += L.vy; L.rot += L.spin;
          if (L.x > WW) L.x = 0;
          if (L.y > WH) L.y = 400;
          const p = screenPos(L.x, L.y);
          if (!inView(p.x, p.y, 0)) continue;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(L.rot);
          ctx.globalAlpha = L.a;
          ctx.fillStyle = '#3a5a38';
          ctx.beginPath();
          ctx.ellipse(0, 0, L.s * zoom, L.s * 0.4 * zoom, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }}
        ctx.globalAlpha = 1;
      }}

      function drawPostFX() {{
        // Cool cinematic vignette
        const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.15, W / 2, H / 2, H * 0.92);
        g.addColorStop(0, 'transparent');
        g.addColorStop(0.65, 'transparent');
        g.addColorStop(1, 'rgba(15, 25, 28, 0.4)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);

        // Soft cool grade (rain day)
        ctx.save();
        ctx.globalCompositeOperation = 'soft-light';
        const grade = ctx.createLinearGradient(0, 0, 0, H);
        grade.addColorStop(0, 'rgba(140, 160, 175, 0.15)');
        grade.addColorStop(0.5, 'rgba(120, 150, 140, 0.08)');
        grade.addColorStop(1, 'rgba(40, 70, 55, 0.12)');
        ctx.fillStyle = grade;
        ctx.fillRect(0, 0, W, H);
        ctx.restore();

        // Subtle rain screen overlay near camera
        ctx.fillStyle = 'rgba(180, 200, 200, 0.02)';
        ctx.fillRect(0, 0, W, H);
      }}

      function drawHud() {{
        const boxH = 100;
        ctx.fillStyle = 'rgba(16, 24, 22, 0.78)';
        ctx.strokeStyle = 'rgba(140, 165, 150, 0.22)';
        ctx.lineWidth = 1;
        roundRect(12, 12, W - 24, boxH, 8);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = 'rgba(200, 215, 205, 0.92)';
        ctx.font = '500 14px Segoe UI,sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText((D.firstName || 'Your') + "  ·  quiet garden", 28, 38);

        ctx.fillStyle = 'rgba(170, 190, 180, 0.75)';
        ctx.font = '400 12px Segoe UI,sans-serif';
        ctx.fillText(
          (D.treeCount || 0) + ' trees   ·   ' +
          (D.sakuraCount || 0) + ' bloomed   ·   ' +
          (D.fruitCount || 0) + ' fruited   ·   ' +
          (D.goalStreak || 0) + 'd streak   ·   ' +
          (D.waterPct || 0) + '% today',
          28, 58
        );

        ctx.fillStyle = 'rgba(150, 170, 160, 0.5)';
        ctx.font = '400 11px Segoe UI,sans-serif';
        const rules = D.rules || '';
        ctx.fillText(rules.length > 110 ? rules.slice(0, 107) + '…' : rules, 28, 76);

        const bw = W - 56;
        ctx.fillStyle = 'rgba(60, 80, 70, 0.5)';
        roundRect(28, 88, bw, 6, 3); ctx.fill();
        ctx.fillStyle = 'rgba(120, 170, 160, 0.7)';
        roundRect(28, 88, bw * Math.min(1, D.waterLevel || 0), 6, 3); ctx.fill();

        if ((D.daysToNextTree || 0) > 0) {{
          ctx.fillStyle = 'rgba(180, 200, 190, 0.7)';
          ctx.font = '500 11px sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText((D.daysToNextTree) + 'd → next tree', W - 28, 76);
          ctx.textAlign = 'left';
        }}
      }}

      function drawMinimap() {{
        const mw = 110, mh = 72, mx = W - mw - 14, my = H - mh - 40;
        ctx.fillStyle = 'rgba(16, 24, 22, 0.82)';
        ctx.strokeStyle = 'rgba(140, 165, 150, 0.2)';
        roundRect(mx, my, mw, mh, 6); ctx.fill(); ctx.stroke();
        const sx = (mw - 10) / WW, sy = (mh - 10) / WH;
        ctx.fillStyle = '#2a4a32';
        ctx.beginPath();
        ctx.ellipse(mx + mw / 2, my + mh / 2 + 2, (mw - 16) / 2, (mh - 18) / 2, 0, 0, Math.PI * 2);
        ctx.fill();
        (D.trees || []).forEach(tree => {{
          const wp = treeWorldPos(tree.slot);
          ctx.fillStyle = treeFruited(tree) ? '#a07050' : (treeBloomed(tree) ? '#a08080' : '#5a8a58');
          ctx.beginPath();
          ctx.arc(mx + 5 + wp.x * sx, my + 5 + wp.y * sy, 2, 0, Math.PI * 2);
          ctx.fill();
        }});
        ctx.strokeStyle = 'rgba(200, 215, 205, 0.4)';
        ctx.strokeRect(mx + 5 - panX * sx, my + 5 - panY * sy, (W / zoom) * sx, (H / zoom) * sy);
      }}

      function hitTest(sx, sy) {{
        const trees = (D.trees || []).slice().sort((a, b) =>
          treeWorldPos(b.slot).y - treeWorldPos(a.slot).y
        );
        for (let i = 0; i < trees.length; i++) {{
          const tree = trees[i];
          const wp = treeWorldPos(tree.slot);
          const sp = screenPos(wp.x, wp.y);
          const s = growthScale(tree) * zoom;
          const ddx = sx - sp.x, ddy = sy - (sp.y - 28 * s);
          if (ddx * ddx + ddy * ddy < (30 * s) * (30 * s)) return tree;
        }}
        return null;
      }}

      function showTip(tree, sx, sy) {{
        if (!tipEl) return;
        if (!tree) {{ tipEl.className = 'lg-tip'; return; }}
        const status = treeFruited(tree)
          ? 'Fruited · test >60%'
          : (treeBloomed(tree) ? 'Bloomed' : (tree.growth || 'growing'));
        const score = tree.score != null ? tree.score + '%' : '—';
        const tag = tree.test_no ? ('T' + tree.test_no) : ('#' + tree.tree_no);
        tipEl.innerHTML = '<strong>' + tag + ' · ' + (tree.phase || 'prelims') + '</strong>' +
          (tree.subject || 'Study block') + '<br><span class="m">' + status +
          ' · score ' + score + '</span>';
        tipEl.className = 'lg-tip on';
        const wrap = cvs.parentElement;
        tipEl.style.position = 'absolute';
        tipEl.style.left = Math.min((wrap.clientWidth || W) - 220, Math.max(8, sx + 12)) + 'px';
        tipEl.style.top = Math.min(H - 80, Math.max(8, sy - 60)) + 'px';
        if (tipEl.parentElement !== wrap) wrap.appendChild(tipEl);
      }}

      function frame() {{
        t++;
        if (W < 40) {{ resize(); requestAnimationFrame(frame); return; }}

        drawSky();
        drawDistantTrees();
        drawGround();
        drawPond();
        drawPavilion();

        const trees = (D.trees || []).slice().sort((a, b) =>
          treeWorldPos(a.slot).y - treeWorldPos(b.slot).y
        );
        for (let i = 0; i < trees.length; i++) drawTree(trees[i]);

        drawActiveSprout();
        drawMarker();
        drawMist();
        drawLeaves();
        drawPetals();
        drawRain();
        drawPostFX();
        drawHud();
        drawMinimap();
        requestAnimationFrame(frame);
      }}

      function clientToCanvas(clientX, clientY) {{
        const rect = cvs.getBoundingClientRect();
        return {{
          sx: (clientX - rect.left) * (W / Math.max(1, rect.width)),
          sy: (clientY - rect.top) * (H / Math.max(1, rect.height))
        }};
      }}

      cvs.addEventListener('mousedown', function(e) {{
        drag = true; moved = 0; dx = e.clientX; dy = e.clientY;
        cvs.classList.add('grab');
      }});
      window.addEventListener('mouseup', function(e) {{
        if (!drag) return;
        drag = false; cvs.classList.remove('grab');
        if (moved < 8) {{
          const p = clientToCanvas(e.clientX, e.clientY);
          selected = hitTest(p.sx, p.sy);
          showTip(selected, p.sx, p.sy);
        }}
      }});
      window.addEventListener('mousemove', function(e) {{
        if (!drag) return;
        const mx = e.clientX - dx, my = e.clientY - dy;
        moved += Math.abs(mx) + Math.abs(my);
        panX += mx / zoom; panY += my / zoom;
        dx = e.clientX; dy = e.clientY;
        clampPan();
      }});
      cvs.addEventListener('wheel', function(e) {{
        e.preventDefault();
        zoom = Math.min(1.6, Math.max(0.62, zoom - e.deltaY * 0.001));
        clampPan();
      }}, {{ passive: false }});
      cvs.addEventListener('touchstart', function(e) {{
        if (e.touches.length === 1) {{
          e.preventDefault();
          drag = true; moved = 0;
          dx = e.touches[0].clientX; dy = e.touches[0].clientY;
        }}
      }}, {{ passive: false }});
      cvs.addEventListener('touchmove', function(e) {{
        if (!drag || e.touches.length !== 1) return;
        e.preventDefault();
        const mx = e.touches[0].clientX - dx, my = e.touches[0].clientY - dy;
        moved += Math.abs(mx) + Math.abs(my);
        panX += mx / zoom; panY += my / zoom;
        dx = e.touches[0].clientX; dy = e.touches[0].clientY;
        clampPan();
      }}, {{ passive: false }});
      cvs.addEventListener('touchend', function(e) {{
        if (!drag) return;
        drag = false;
        if (moved < 10 && e.changedTouches[0]) {{
          const p = clientToCanvas(e.changedTouches[0].clientX, e.changedTouches[0].clientY);
          selected = hitTest(p.sx, p.sy);
          showTip(selected, p.sx, p.sy);
        }}
      }});

      resize();
      if (typeof ResizeObserver !== 'undefined' && cvs.parentElement) {{
        new ResizeObserver(function() {{ resize(); }}).observe(cvs.parentElement);
      }}
      setTimeout(resize, 200);
      setTimeout(resize, 600);
      frame();
      }} catch (err) {{
        console.error('Quiet garden error', err);
        var el = document.getElementById('lgHintBar');
        if (el) el.textContent = 'Map error: ' + (err && err.message ? err.message : err);
      }}
    }})();
    </script>
    """
    st.iframe(html, height=height, width="stretch")
