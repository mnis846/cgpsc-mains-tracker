"""Study Garden — year-long jungle map that grows with your prep."""

from profile import EXAM, FIRST_NAME

GARDEN_STAGES = [
    {"name": "Barren Plot", "min_xp": 0, "emoji": "🏚️", "sky": "#5c5348", "ground": "#3a3228", "biome": "wasteland"},
    {"name": "Ash Soil", "min_xp": 30, "emoji": "🪨", "sky": "#635a4f", "ground": "#40362c", "biome": "wasteland"},
    {"name": "First Sprout", "min_xp": 80, "emoji": "🌱", "sky": "#6a6155", "ground": "#443a30", "biome": "wasteland"},
    {"name": "Scrubland", "min_xp": 150, "emoji": "🌿", "sky": "#6e6558", "ground": "#4a4236", "biome": "scrubland"},
    {"name": "Trail Cleared", "min_xp": 250, "emoji": "🥾", "sky": "#756b5c", "ground": "#504638", "biome": "scrubland"},
    {"name": "Campfire Ring", "min_xp": 400, "emoji": "🔥", "sky": "#7a6f5e", "ground": "#524a3c", "biome": "camp"},
    {"name": "Fence Line", "min_xp": 600, "emoji": "🪵", "sky": "#6d7560", "ground": "#4f5a42", "biome": "camp"},
    {"name": "Small Outpost", "min_xp": 850, "emoji": "🏕️", "sky": "#647060", "ground": "#4a5540", "biome": "outpost"},
    {"name": "Water Tank", "min_xp": 1150, "emoji": "💧", "sky": "#5a6b62", "ground": "#425248", "biome": "outpost"},
    {"name": "Green Patch", "min_xp": 1500, "emoji": "🌳", "sky": "#556854", "ground": "#3d523c", "biome": "green_zone"},
    {"name": "Pine Belt", "min_xp": 1900, "emoji": "🌲", "sky": "#4f6350", "ground": "#364a38", "biome": "green_zone"},
    {"name": "Supply Yard", "min_xp": 2400, "emoji": "📦", "sky": "#4a5e4c", "ground": "#314436", "biome": "green_zone"},
    {"name": "Reinforced Base", "min_xp": 3000, "emoji": "🛡️", "sky": "#455a46", "ground": "#2c3f30", "biome": "reclaimed"},
    {"name": "Berry Thicket", "min_xp": 3700, "emoji": "🫐", "sky": "#3f553f", "ground": "#283a2a", "biome": "reclaimed"},
    {"name": "Overgrown Wall", "min_xp": 4500, "emoji": "🌴", "sky": "#3a5038", "ground": "#243526", "biome": "overgrown"},
    {"name": "Wild Perimeter", "min_xp": 5400, "emoji": "🦌", "sky": "#344a32", "ground": "#1f3020", "biome": "overgrown"},
    {"name": "Reclaimed Sector", "min_xp": 6500, "emoji": "🦜", "sky": "#2e442c", "ground": "#1a2a1a", "biome": "overgrown"},
    {"name": "Apex Haven", "min_xp": 8000, "emoji": "🏆", "sky": "#284028", "ground": "#142214", "biome": "apex_haven"},
]

XP_REWARDS = {
    "daily_checkin": 25,
    "per_hour": 30,
    "target_done": 25,
    "all_targets": 100,
    "daily_goal": 75,
    "streak_per_day": 8,
    "streak_cap": 60,
    "atlas_scout": 12,
    "atlas_map": 8,
    "atlas_hold": 10,
    "atlas_fortify": 20,
    "atlas_drill": 4,
}


def get_stage_info(xp):
    stage_idx = 0
    for i, stage in enumerate(GARDEN_STAGES):
        if xp >= stage["min_xp"]:
            stage_idx = i
    current = GARDEN_STAGES[stage_idx]
    next_stage = GARDEN_STAGES[stage_idx + 1] if stage_idx + 1 < len(GARDEN_STAGES) else None
    if next_stage:
        span = next_stage["min_xp"] - current["min_xp"]
        progress = (xp - current["min_xp"]) / span if span else 1.0
        xp_to_next = next_stage["min_xp"] - xp
    else:
        progress = 1.0
        xp_to_next = 0
    return {
        "index": stage_idx,
        "current": current,
        "next": next_stage,
        "progress": min(max(progress, 0.0), 1.0),
        "xp_to_next": max(xp_to_next, 0),
        "is_max": next_stage is None,
    }


def _tree_svg(stage_idx, sway=True):
    """Compact SVG tree for dashboard cards."""
    anim = (
        '<animateTransform attributeName="transform" type="rotate" '
        'values="-1 100 170;1 100 170;-1 100 170" dur="4s" repeatCount="indefinite"/>'
        if sway
        else ""
    )
    visual_idx = min(stage_idx, 9)
    glow = "filter: drop-shadow(0 0 12px rgba(72,187,120,0.45));" if stage_idx >= 6 else ""

    parts = {
        0: '<ellipse cx="100" cy="210" rx="18" ry="10" fill="#8D6E63"/><ellipse cx="100" cy="205" rx="10" ry="6" fill="#6D4C41"/>',
        1: '<rect x="97" y="175" width="6" height="35" rx="3" fill="#558B2F"/><ellipse cx="100" cy="172" rx="14" ry="9" fill="#7CB342"/>',
        2: '<rect x="96" y="155" width="8" height="55" rx="4" fill="#558B2F"/><ellipse cx="100" cy="148" rx="22" ry="14" fill="#66BB6A"/>',
        3: '<rect x="94" y="130" width="12" height="80" rx="5" fill="#6D4C41"/><ellipse cx="100" cy="118" rx="32" ry="22" fill="#43A047"/>',
        4: '<rect x="92" y="108" width="16" height="102" rx="6" fill="#5D4037"/><ellipse cx="100" cy="88" rx="42" ry="30" fill="#2E7D32"/>',
        5: '<rect x="90" y="88" width="20" height="122" rx="7" fill="#4E342E"/><ellipse cx="100" cy="68" rx="52" ry="36" fill="#1B5E20"/>',
        6: '<rect x="88" y="72" width="24" height="138" rx="8" fill="#3E2723"/><ellipse cx="100" cy="52" rx="58" ry="40" fill="#1B5E20"/><circle cx="88" cy="42" r="6" fill="#F06292"/>',
        7: '<rect x="86" y="58" width="28" height="152" rx="9" fill="#3E2723"/><ellipse cx="100" cy="38" rx="62" ry="44" fill="#1B5E20"/><circle cx="92" cy="32" r="8" fill="#E53935"/>',
        8: '<rect x="84" y="42" width="32" height="168" rx="10" fill="#2E1B0E"/><ellipse cx="100" cy="28" rx="68" ry="48" fill="#0D3B1E"/><circle cx="95" cy="22" r="9" fill="#FFD700"/>',
        9: '<rect x="82" y="30" width="36" height="180" rx="11" fill="#1A0F05"/><ellipse cx="100" cy="22" rx="74" ry="52" fill="#052E14"/><text x="100" y="6" font-size="18" fill="#FFF59D">👑</text>',
    }
    trunk = parts.get(visual_idx, parts[9])
    return f"""
    <svg viewBox="0 0 200 230" width="100%" height="220" style="{glow}">
      <defs><linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{GARDEN_STAGES[stage_idx]['sky']}"/>
        <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
      </linearGradient></defs>
      <rect x="0" y="0" width="200" height="230" rx="16" fill="url(#skyGrad)"/>
      <ellipse cx="100" cy="220" rx="80" ry="14" fill="{GARDEN_STAGES[stage_idx]['ground']}" opacity="0.35"/>
      <g>{anim}{trunk}</g>
    </svg>
    """


def render_garden_card(garden_state, compact=False):
    info = garden_state["stage_info"]
    stage = info["current"]
    xp = garden_state["xp"]
    pct = int(info["progress"] * 100)
    if info["is_max"]:
        next_line = f"Apex Haven unlocked — {FIRST_NAME}, you reclaimed the zone! 🏆"
    else:
        next_line = f"{info['xp_to_next']} XP to <b>{info['next']['name']}</b> {info['next']['emoji']}"
    bar_color = "#48BB78" if pct > 50 else "#4299E1"
    svg = _tree_svg(info["index"])
    if compact:
        return f"""
        <div class="garden-compact">
          <div class="garden-compact-tree">{svg}</div>
          <div class="garden-compact-info">
            <div class="garden-stage-title">{stage['emoji']} {stage['name']}</div>
            <div class="garden-xp">{xp:,} XP · {pct}% to next</div>
            <div class="garden-bar"><div class="garden-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
          </div>
        </div>"""
    return f"""
    <div class="garden-hero">
      <div class="garden-visual">{svg}</div>
      <div class="garden-details">
        <div class="garden-stage-title">{stage['emoji']} {stage['name']}</div>
        <div class="garden-xp-total">{xp:,} Growth XP</div>
        <div class="garden-bar"><div class="garden-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>
        <div class="garden-next">{next_line}</div>
        <div class="garden-hint">🌾 {FIRST_NAME}, 55 prelims trees + mains sprint — full daily goal, +1 permanent tree every 4 complete days, 6-day streaks bloom 🌸, &gt;60% tests fruit 🍎.</div>
      </div>
    </div>"""


GARDEN_CSS = """
<style>
    .garden-compact {
        display: flex; align-items: center; gap: 1rem;
        background: var(--card-grad, linear-gradient(145deg, rgba(22, 28, 42, 0.95), rgba(14, 32, 30, 0.9)));
        border: 1px solid var(--border, rgba(148, 163, 204, 0.16)); border-radius: var(--radius, 14px);
        padding: 0.75rem 1.1rem; margin-bottom: 0.85rem;
        box-shadow: var(--shadow-sm, 0 6px 18px rgba(0, 0, 0, 0.22));
    }
    .garden-compact-tree { width: 80px; flex-shrink: 0; }
    .garden-compact-info { flex: 1; }
    .garden-hero {
        display: flex; align-items: center; gap: 2rem;
        background: linear-gradient(135deg, rgba(22, 28, 42, 0.95) 0%, rgba(12, 36, 32, 0.9) 55%, rgba(18, 28, 48, 0.95) 100%);
        border: 1px solid var(--border, rgba(148, 163, 204, 0.16)); border-radius: var(--radius, 16px);
        padding: 1.2rem 1.5rem; margin-bottom: 0.85rem;
        box-shadow: var(--shadow-sm, 0 10px 28px rgba(0, 0, 0, 0.25));
    }
    .garden-visual { width: 200px; flex-shrink: 0; }
    .garden-details { flex: 1; }
    .garden-stage-title {
        font-family: var(--display, 'Outfit', system-ui, sans-serif);
        font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em;
        color: var(--accent-2, #6ee7b7); margin-bottom: 0.2rem;
    }
    .garden-xp, .garden-xp-total {
        font-family: var(--display, 'Outfit', system-ui, sans-serif);
        font-size: 0.95rem; color: var(--accent-2, #5eead4); font-weight: 600; margin-bottom: 0.4rem;
    }
    .garden-bar {
        height: 8px; background: rgba(255, 255, 255, 0.06);
        border-radius: 999px; overflow: hidden; margin-bottom: 0.4rem;
    }
    .garden-bar-fill {
        height: 100%; border-radius: 999px; transition: width 0.6s ease;
        background: var(--progress-grad, linear-gradient(90deg, #7c6cff, #22d3ee, #34d399)) !important;
    }
    .garden-next { font-size: 0.9rem; color: var(--text-2, #c7d0e8); margin-bottom: 0.3rem; }
    .garden-hint { font-size: 0.8rem; color: var(--muted, #8b95b2); font-style: italic; }
    .badge-grid { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.4rem; }
    .badge {
        display: inline-block; padding: 0.28rem 0.65rem; border-radius: 999px;
        font-size: 0.75rem; font-weight: 600;
        font-family: var(--display, 'Outfit', system-ui, sans-serif);
    }
    .badge-earned {
        background: var(--teal-soft, rgba(52, 211, 153, 0.12)); color: #6ee7b7;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .badge-locked {
        background: rgba(255, 255, 255, 0.04); color: var(--faint, #5d6785);
        border: 1px solid var(--border, rgba(148, 163, 204, 0.12));
    }
    .garden-map-fullbleed {
        margin-left: calc(-1 * var(--page-pad-x, 1.25rem));
        margin-right: calc(-1 * var(--page-pad-x, 1.25rem));
        width: calc(100% + 2 * var(--page-pad-x, 1.25rem)); max-width: none;
    }
    @media (min-width: 900px) {
        .garden-map-fullbleed {
            margin-left: calc(-50vw + 50%);
            margin-right: calc(-50vw + 50%);
            width: 100vw;
        }
    }
    .hay-farm-panel {
        background: var(--card-grad, linear-gradient(180deg, rgba(22, 28, 42, 0.95) 0%, rgba(12, 28, 26, 0.95) 100%));
        border: 1px solid var(--border, rgba(148, 163, 204, 0.14));
        border-radius: var(--radius, 14px);
        padding: 0.9rem 1.1rem; margin-top: 0.65rem;
    }
    .week-dots { display: flex; gap: 0.45rem; align-items: center; margin: 0.4rem 0; }
    .week-dot {
        width: 12px; height: 12px; border-radius: 50%;
        border: 2px solid var(--bg-0, #07090f); box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .week-dot.complete { background: var(--teal, #34d399); }
    .week-dot.partial { background: var(--amber, #fbbf24); }
    .week-dot.empty { background: rgba(255, 255, 255, 0.08); }
    .garden-mode-note {
        font-size: 0.74rem; color: var(--muted, #8b95b2); margin: 0.1rem 0 0.4rem 0;
    }
    .garden-stat-row {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.55rem;
        margin: 0.55rem 0 0.75rem 0;
    }
    .garden-stat {
        background: var(--metric-grad, linear-gradient(160deg, rgba(22, 28, 42, 0.95), rgba(14, 28, 28, 0.9)));
        border: 1px solid var(--border, rgba(148, 163, 204, 0.12));
        border-radius: var(--radius-sm, 12px);
        padding: 0.55rem 0.6rem; text-align: center;
    }
    .garden-stat .k {
        display: block; font-size: 0.62rem; color: var(--muted, #8b95b2); font-weight: 700;
        letter-spacing: 0.06em; font-family: var(--display, 'Outfit', system-ui, sans-serif);
    }
    .garden-stat .v {
        display: block; font-size: 0.9rem; color: var(--accent-2, #5eead4); font-weight: 700;
        margin-top: 0.15rem; font-family: var(--display, 'Outfit', system-ui, sans-serif);
    }
    @media (max-width: 700px) {
        .garden-stat-row { grid-template-columns: repeat(2, 1fr); }
    }
</style>
"""


def render_garden_stats_strip(life):
    """Compact metric chips under the map (no Streamlit metric bloat)."""
    life = life or {}
    return f"""
    <div class="garden-stat-row">
      <div class="garden-stat"><span class="k">TREES</span><span class="v">🌳 {life.get('tree_count', 1)}/{life.get('max_trees', 77)}</span></div>
      <div class="garden-stat"><span class="k">PRELIMS PATH</span><span class="v">{life.get('prelims_trees', 1)}/{life.get('prelims_target', 55)}</span></div>
      <div class="garden-stat"><span class="k">STREAK</span><span class="v">🔥 {life.get('goal_streak', 0)}d</span></div>
      <div class="garden-stat"><span class="k">BLOOM / FRUIT</span><span class="v">🌸 {life.get('sakura_count', 0)} · 🍎 {life.get('fruit_count', 0)}</span></div>
    </div>
    """


def render_interactive_garden(garden_state, height=760, mode="classic"):
    """Study jungle map. mode: 'classic' (stable) or 'living' (experimental)."""
    if mode == "living":
        from garden_map_v2 import render_garden_world_v2

        render_garden_world_v2(garden_state, height=height)
    else:
        from garden_map import render_garden_world

        render_garden_world(garden_state, height=height)
