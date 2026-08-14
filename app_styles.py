"""Desktop dashboard CSS — theme system (Nova, Paper light, Classic fallback)."""

DEFAULT_THEME = "nova"
THEME_OPTIONS = {
    "nova": {
        "label": "Nova (upgraded)",
        "description": "Dark study cockpit with clear hierarchy",
    },
    "paper": {
        "label": "Paper (daytime)",
        "description": "Warm light notebook mode for daytime reading",
    },
    "classic": {
        "label": "Classic (fallback)",
        "description": "Original black-slick study shell",
    },
}

# Shared base used by both themes (fonts + resets that stay stable)
_SHARED_BASE = """
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;600&display=swap');

    html, body, [class*="css"] {
        font-family: var(--font) !important;
        color: var(--text);
        -webkit-font-smoothing: antialiased;
    }

    .stApp, [data-testid="stAppViewContainer"] {
        background: var(--app-bg) !important;
        background-attachment: fixed !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        background: transparent !important;
    }

    .block-container {
        padding-top: var(--page-pad-top);
        padding-bottom: 2.25rem;
        padding-left: var(--page-pad-x) !important;
        padding-right: var(--page-pad-x) !important;
        max-width: min(var(--page-max), 98vw) !important;
    }

    header[data-testid="stHeader"] {
        background: var(--header-bg) !important;
        backdrop-filter: blur(14px);
        border-bottom: 1px solid var(--border);
        min-height: 2.25rem !important;
    }
    #MainMenu, footer, .stDeployButton { visibility: hidden; height: 0; }

    hr { border: none; border-top: 1px solid var(--border); margin: 0.85rem 0; }

    [data-testid="stHorizontalBlock"] { gap: var(--col-gap) !important; }

    /* Wider sidebar for module navigation */
    section[data-testid="stSidebar"] {
        min-width: 16.5rem !important;
        width: 16.5rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        width: 100% !important;
        padding-top: 0.85rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    .sidebar-nav-label {
        font-family: var(--display);
        font-size: 0.66rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--muted) !important;
        margin: 0.15rem 0 0.45rem 0 !important;
    }
    .sidebar-nav-marker { height: 0; margin: 0; padding: 0; overflow: hidden; }
    .sidebar-nav-active-hint {
        font-size: 0.7rem !important;
        color: var(--faint) !important;
        margin: 0.45rem 0 0.15rem 0 !important;
        letter-spacing: 0.02em;
    }
    .sidebar-brand {
        padding: 0.1rem 0 0.7rem 0;
        margin-bottom: 0.45rem;
        border-bottom: 1px solid var(--border);
    }
    .sidebar-brand-name {
        font-family: var(--display);
        font-size: 1.08rem;
        font-weight: 800;
        color: var(--text) !important;
        margin: 0 0 0.18rem 0;
        letter-spacing: -0.02em;
    }
    .sidebar-brand-sub {
        font-size: 0.72rem;
        color: var(--muted) !important;
        margin: 0;
        line-height: 1.4;
    }

    /* Stacked sidebar nav buttons after the marker */
    section[data-testid="stSidebar"] .stButton > button {
        justify-content: flex-start !important;
        text-align: left !important;
        padding-left: 0.85rem !important;
        padding-right: 0.75rem !important;
        min-height: 2.4rem;
        border-radius: 11px !important;
        font-size: 0.86rem !important;
        letter-spacing: 0.01em;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: var(--sidebar-nav-idle, rgba(255,255,255,0.03)) !important;
        border: 1px solid transparent !important;
        color: var(--text-2) !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: var(--sidebar-nav-hover, rgba(124,140,255,0.1)) !important;
        border-color: var(--border) !important;
        color: var(--text) !important;
        transform: none;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        box-shadow: 0 4px 14px rgba(124, 140, 255, 0.22) !important;
        font-weight: 700 !important;
    }

    /* Page context under hero / metrics */
    .page-context {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.55rem;
        margin: 0 0 0.85rem 0;
    }
    .page-context-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-family: var(--display);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--text) !important;
        background: var(--accent-soft);
        border: 1px solid var(--border-strong);
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
    }
    .page-context-hint {
        font-size: 0.72rem;
        color: var(--faint) !important;
    }
"""

# ── Classic (fallback): original black-slick shell ──────────────────────────
CLASSIC_VARS = """
    :root {
        --bg-0: #07090f;
        --bg-1: #0c101a;
        --bg-2: #121826;
        --surface: rgba(22, 28, 42, 0.72);
        --surface-solid: #141a28;
        --surface-2: #1a2234;
        --surface-3: #232d42;
        --text: #eef2ff;
        --text-2: #c7d0e8;
        --muted: #8b95b2;
        --faint: #5d6785;
        --border: rgba(148, 163, 204, 0.14);
        --border-strong: rgba(148, 163, 204, 0.28);
        --accent: #7c6cff;
        --accent-2: #22d3ee;
        --accent-soft: rgba(124, 108, 255, 0.14);
        --teal: #34d399;
        --teal-soft: rgba(52, 211, 153, 0.12);
        --violet: #a78bfa;
        --violet-soft: rgba(167, 139, 250, 0.14);
        --coral: #fb7185;
        --coral-soft: rgba(251, 113, 133, 0.12);
        --sky: #38bdf8;
        --sky-soft: rgba(56, 189, 248, 0.12);
        --amber: #fbbf24;
        --amber-soft: rgba(251, 191, 36, 0.12);
        --success: #34d399;
        --danger: #f87171;
        --shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
        --shadow-sm: 0 4px 16px rgba(0, 0, 0, 0.22);
        --radius: 14px;
        --radius-sm: 10px;
        --radius-xs: 8px;
        --font: 'IBM Plex Sans', system-ui, sans-serif;
        --display: 'Outfit', system-ui, sans-serif;
        --app-bg:
            radial-gradient(1000px 520px at 10% -8%, rgba(124, 108, 255, 0.14), transparent 55%),
            radial-gradient(800px 420px at 92% 0%, rgba(34, 211, 238, 0.08), transparent 50%),
            linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 50%, #0a0e16 100%);
        --header-bg: rgba(7, 9, 15, 0.7);
        --page-pad-top: 0.65rem;
        --page-pad-x: 1.25rem;
        --page-max: 1680px;
        --col-gap: 0.65rem;
        --hero-grad: linear-gradient(135deg, rgba(22, 28, 42, 0.95) 0%, rgba(16, 22, 36, 0.92) 100%);
        --card-grad: linear-gradient(165deg, rgba(22, 28, 42, 0.9), rgba(14, 18, 30, 0.92));
        --metric-grad: linear-gradient(160deg, rgba(26, 34, 52, 0.95), rgba(16, 22, 36, 0.9));
        --btn-grad: linear-gradient(180deg, rgba(35, 45, 66, 0.95), rgba(24, 32, 50, 0.95));
        --btn-hover: linear-gradient(180deg, rgba(44, 56, 82, 0.98), rgba(30, 40, 62, 0.98));
        --primary-grad: linear-gradient(120deg, #7c6cff 0%, #22d3ee 100%);
        --primary-hover: linear-gradient(120deg, #8f82ff 0%, #3bdef5 100%);
        --tab-active: linear-gradient(120deg, #a5b4fc 0%, #67e8f9 55%, #6ee7b7 100%);
        --progress-grad: linear-gradient(90deg, #7c6cff, #22d3ee 55%, #34d399);
        --title-grad: linear-gradient(105deg, #ffffff 15%, #c4b5fd 55%, #67e8f9 100%);
        --sidebar-bg: linear-gradient(180deg, rgba(8, 10, 18, 0.98) 0%, rgba(10, 14, 24, 0.98) 100%);
        --sidebar-nav-idle: rgba(255, 255, 255, 0.03);
        --sidebar-nav-hover: rgba(124, 108, 255, 0.12);
        --input-bg: rgba(10, 14, 24, 0.9);
        --nav-active-fg: #071018;
        --primary-fg: #071018;
    }
"""

# ── Nova (upgraded): indigo + slate, mint used sparingly ─────────────────────
NOVA_VARS = """
    :root {
        --bg-0: #0b0f17;
        --bg-1: #101522;
        --bg-2: #171d2c;
        --surface: rgba(22, 30, 46, 0.82);
        --surface-solid: #151b2a;
        --surface-2: #1b2336;
        --surface-3: #253049;
        --text: #f1f4fb;
        --text-2: #c8d0e4;
        --muted: #8e9ab3;
        --faint: #65728c;
        --border: rgba(148, 168, 210, 0.14);
        --border-strong: rgba(148, 168, 210, 0.28);
        /* Primary family: cool indigo → soft blue (no rainbow clash) */
        --accent: #7c8cff;
        --accent-2: #5ec8ff;
        --accent-soft: rgba(124, 140, 255, 0.16);
        --teal: #3ecfad;
        --teal-soft: rgba(62, 207, 173, 0.12);
        --violet: #a5b4fc;
        --violet-soft: rgba(165, 180, 252, 0.14);
        --coral: #fb7185;
        --coral-soft: rgba(251, 113, 133, 0.12);
        --sky: #5ec8ff;
        --sky-soft: rgba(94, 200, 255, 0.12);
        --amber: #f0c14d;
        --amber-soft: rgba(240, 193, 77, 0.12);
        --success: #3ecfad;
        --danger: #fb7185;
        --shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
        --shadow-sm: 0 6px 18px rgba(0, 0, 0, 0.26);
        --radius: 16px;
        --radius-sm: 12px;
        --radius-xs: 9px;
        --font: 'IBM Plex Sans', system-ui, sans-serif;
        --display: 'Outfit', system-ui, sans-serif;
        --serif: 'Source Serif 4', Georgia, serif;
        --app-bg:
            radial-gradient(900px 460px at 6% -8%, rgba(124, 140, 255, 0.13), transparent 58%),
            radial-gradient(700px 380px at 98% 2%, rgba(94, 200, 255, 0.07), transparent 52%),
            linear-gradient(180deg, #0a0e16 0%, #0e1320 48%, #0b1018 100%);
        --header-bg: rgba(11, 15, 23, 0.78);
        --page-pad-top: 0.85rem;
        --page-pad-x: 1.5rem;
        --page-max: 1520px;
        --col-gap: 0.85rem;
        --hero-grad:
            linear-gradient(145deg, rgba(24, 32, 50, 0.98) 0%, rgba(16, 22, 36, 0.96) 55%, rgba(18, 26, 42, 0.98) 100%);
        --card-grad: linear-gradient(168deg, rgba(24, 32, 48, 0.96), rgba(14, 20, 32, 0.98));
        --metric-grad: linear-gradient(165deg, rgba(26, 34, 52, 0.98), rgba(16, 22, 36, 0.96));
        --btn-grad: linear-gradient(180deg, rgba(36, 46, 68, 0.96), rgba(24, 32, 50, 0.96));
        --btn-hover: linear-gradient(180deg, rgba(46, 58, 84, 0.98), rgba(30, 40, 60, 0.98));
        --primary-grad: linear-gradient(125deg, #7c8cff 0%, #5ec8ff 100%);
        --primary-hover: linear-gradient(125deg, #8f9cff 0%, #74d4ff 100%);
        --tab-active: linear-gradient(120deg, #7c8cff 0%, #5ec8ff 100%);
        --progress-grad: linear-gradient(90deg, #7c8cff, #5ec8ff 70%, #3ecfad);
        --title-grad: linear-gradient(110deg, #ffffff 12%, #c7d2fe 55%, #7dd3fc 100%);
        --sidebar-bg: linear-gradient(180deg, #0c101a 0%, #0f1420 55%, #101826 100%);
        --sidebar-nav-idle: rgba(255, 255, 255, 0.03);
        --sidebar-nav-hover: rgba(124, 140, 255, 0.1);
        --input-bg: rgba(12, 16, 26, 0.92);
        --nav-active-fg: #071018;
        --primary-fg: #071018;
    }
"""

# ── Paper (daytime): warm cream + indigo ink, teal only for success ──────────
PAPER_VARS = """
    :root {
        --bg-0: #f3efe7;
        --bg-1: #faf8f4;
        --bg-2: #ffffff;
        --surface: rgba(255, 255, 255, 0.92);
        --surface-solid: #ffffff;
        --surface-2: #f2ece2;
        --surface-3: #e7dfd2;
        --text: #1a1c22;
        --text-2: #3b3f4a;
        --muted: #6a7080;
        --faint: #9096a5;
        --border: rgba(40, 48, 72, 0.11);
        --border-strong: rgba(40, 48, 72, 0.2);
        --accent: #4f5fd6;
        --accent-2: #2a6f7a;
        --accent-soft: rgba(79, 95, 214, 0.11);
        --teal: #0f766e;
        --teal-soft: rgba(15, 118, 110, 0.1);
        --violet: #6366f1;
        --violet-soft: rgba(99, 102, 241, 0.1);
        --coral: #dc4b64;
        --coral-soft: rgba(220, 75, 100, 0.1);
        --sky: #0284c7;
        --sky-soft: rgba(2, 132, 199, 0.1);
        --amber: #c98512;
        --amber-soft: rgba(201, 133, 18, 0.12);
        --success: #0f766e;
        --danger: #dc4b64;
        --shadow: 0 14px 36px rgba(40, 48, 72, 0.08);
        --shadow-sm: 0 4px 14px rgba(40, 48, 72, 0.06);
        --radius: 16px;
        --radius-sm: 12px;
        --radius-xs: 9px;
        --font: 'IBM Plex Sans', system-ui, sans-serif;
        --display: 'Outfit', system-ui, sans-serif;
        --serif: 'Source Serif 4', Georgia, serif;
        --app-bg:
            radial-gradient(880px 440px at 4% -6%, rgba(79, 95, 214, 0.07), transparent 55%),
            radial-gradient(640px 340px at 100% 0%, rgba(42, 111, 122, 0.06), transparent 50%),
            linear-gradient(180deg, #f8f5ef 0%, #f3efe7 50%, #efe9df 100%);
        --header-bg: rgba(250, 248, 244, 0.88);
        --page-pad-top: 0.85rem;
        --page-pad-x: 1.5rem;
        --page-max: 1520px;
        --col-gap: 0.85rem;
        --hero-grad: linear-gradient(145deg, #ffffff 0%, #f8f5ef 55%, #f3eee6 100%);
        --card-grad: linear-gradient(168deg, #ffffff 0%, #faf8f4 100%);
        --metric-grad: linear-gradient(165deg, #ffffff 0%, #f7f4ee 100%);
        --btn-grad: linear-gradient(180deg, #ffffff 0%, #f2ece2 100%);
        --btn-hover: linear-gradient(180deg, #ffffff 0%, #e9e2d6 100%);
        --primary-grad: linear-gradient(125deg, #4f5fd6 0%, #3b82c4 100%);
        --primary-hover: linear-gradient(125deg, #5f6fe0 0%, #4a92d0 100%);
        --tab-active: linear-gradient(120deg, #4f5fd6 0%, #3b82c4 100%);
        --progress-grad: linear-gradient(90deg, #4f5fd6, #3b82c4 65%, #0f766e);
        --title-grad: linear-gradient(110deg, #1a1c22 10%, #4f5fd6 58%, #2a6f7a 100%);
        --sidebar-bg: linear-gradient(180deg, #fbf9f5 0%, #f3efe7 100%);
        --sidebar-nav-idle: rgba(40, 48, 72, 0.03);
        --sidebar-nav-hover: rgba(79, 95, 214, 0.08);
        --input-bg: #ffffff;
        --nav-active-fg: #ffffff;
        --primary-fg: #ffffff;
        --chip-fg: #3b4bc4;
        --heat-0: #e8e4db;
        --heat-1: #c4b5fd;
        --heat-2: #a5b4fc;
        --heat-3: #818cf8;
        --heat-4: #4f5fd6;
    }
"""

_COMPONENT_CSS = """
    /* ── Hero ─────────────────────────────────────────── */
    .app-hero {
        position: relative;
        overflow: hidden;
        background: var(--hero-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.9rem 1.25rem 0.85rem;
        margin-bottom: 0.75rem;
        color: var(--text);
        box-shadow: var(--shadow-sm);
    }
    .app-hero::before {
        content: "";
        position: absolute;
        inset: -50% auto auto -5%;
        width: 42%;
        height: 190%;
        background: radial-gradient(circle, var(--accent-soft), transparent 68%);
        pointer-events: none;
    }
    .app-hero::after {
        content: "";
        position: absolute;
        right: -8%;
        top: -40%;
        width: 36%;
        height: 180%;
        background: radial-gradient(circle, rgba(94, 234, 212, 0.06), transparent 70%);
        pointer-events: none;
    }
    .app-hero-top {
        position: relative;
        z-index: 1;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.35rem;
    }
    .app-hero-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.18rem 0.58rem;
        border-radius: 999px;
        font-family: var(--display);
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #e2ddff;
        background: var(--accent-soft);
        border: 1px solid rgba(139, 124, 255, 0.32);
    }
    .app-hero-title {
        position: relative;
        z-index: 1;
        font-family: var(--display);
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0 0 0.12rem 0;
        letter-spacing: -0.025em;
        line-height: 1.2;
        background: var(--title-grad);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .app-hero-greeting {
        position: relative;
        z-index: 1;
        font-family: var(--display);
        font-size: 0.92rem;
        font-weight: 600;
        margin: 0 0 0.08rem 0;
        color: var(--text);
    }
    .app-hero-motto {
        position: relative;
        z-index: 1;
        font-size: 0.8rem;
        margin: 0 0 0.3rem 0;
        color: var(--muted);
        max-width: 46rem;
        line-height: 1.4;
    }
    .app-hero-meta {
        position: relative;
        z-index: 1;
        font-size: 0.74rem;
        color: var(--faint);
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
    }

    /* Metric strip under hero */
    .metric-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.65rem;
        margin-bottom: 0.75rem;
    }
    .metric-tile {
        position: relative;
        overflow: hidden;
        background: var(--metric-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.7rem 0.85rem 0.65rem;
        box-shadow: var(--shadow-sm);
    }
    .metric-tile::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        border-radius: 3px 0 0 3px;
    }
    .metric-tile.m-streak::before { background: var(--coral); }
    .metric-tile.m-goal::before { background: var(--sky); }
    .metric-tile.m-xp::before { background: var(--teal); }
    .metric-tile.m-best::before { background: var(--violet); }
    .metric-tile-label {
        font-family: var(--display);
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
        margin: 0 0 0.2rem 0;
    }
    .metric-tile-value {
        font-family: var(--display);
        font-size: 1.2rem;
        font-weight: 800;
        color: var(--text);
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }
    .metric-tile-hint {
        font-size: 0.68rem;
        color: var(--faint);
        margin: 0.2rem 0 0 0;
    }

    /* Module nav marker (Streamlit cannot wrap widgets in custom HTML) */
    .wd-nav-marker {
        height: 0;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    .wd-nav-hint { display: none; }
    .wd-module-banner { display: none; }

    .workspace-panel {
        background: var(--card-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.1rem 0.95rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--shadow-sm);
    }
    .workspace-panel-head {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-end;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.65rem;
        padding-bottom: 0.55rem;
        border-bottom: 1px solid var(--border);
    }

    /* Theme badge in sidebar */
    .theme-switch-note {
        font-size: 0.72rem;
        color: var(--muted);
        line-height: 1.35;
        margin: 0.15rem 0 0.45rem 0;
    }

    @media (min-width: 1100px) {
        .app-hero {
            display: grid;
            grid-template-columns: 1.55fr auto;
            grid-template-areas:
                "top meta"
                "title meta"
                "greet meta";
            column-gap: 1.4rem;
            align-items: center;
        }
        .app-hero-top { grid-area: top; margin-bottom: 0.15rem; }
        .app-hero-title { grid-area: title; }
        .app-hero-greeting { grid-area: greet; }
        .app-hero-motto { display: none; }
        .app-hero-meta {
            grid-area: meta;
            justify-self: end;
            text-align: right;
            color: var(--text-2);
        }
    }
    @media (max-width: 800px) {
        .metric-strip { grid-template-columns: repeat(2, 1fr); }
        .wd-nav-shell { border-radius: 16px; }
    }

    /* Streamlit metric cards (fallback rows) */
    div[data-testid="stMetric"] {
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.6rem 0.8rem;
        box-shadow: var(--shadow-sm);
        background: var(--metric-grad);
    }
    div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] {
        border-top: 2px solid var(--coral);
    }
    div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] {
        border-top: 2px solid var(--sky);
    }
    div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] {
        border-top: 2px solid var(--teal);
    }
    div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] {
        border-top: 2px solid var(--violet);
    }
    div[data-testid="stMetric"] label {
        font-family: var(--display) !important;
        font-size: 0.62rem !important;
        color: var(--muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: var(--display) !important;
        font-size: 1.15rem !important;
        color: var(--text) !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: var(--muted) !important;
        font-size: 0.75rem !important;
    }

    .section-label {
        font-family: var(--display);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent-2);
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .section-title {
        font-family: var(--display);
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .workspace-hint {
        font-size: 0.74rem;
        color: var(--faint);
        margin: 0.15rem 0 0.5rem 0;
        line-height: 1.4;
    }
    .rail-title { font-size: 1rem !important; margin-bottom: 0.35rem !important; }
    .rail-muted { color: var(--muted); font-weight: 500; font-size: 0.9em; }
    .dash-rail-note {
        font-size: 0.74rem;
        color: var(--muted);
        margin: 0 0 0.55rem 0;
        line-height: 1.4;
    }

    .target-card-text {
        font-size: 0.92rem;
        line-height: 1.5;
        color: var(--text);
        margin: 0;
    }
    .target-done { text-decoration: line-through; color: var(--muted); }
    .target-skipped { color: var(--faint); font-style: italic; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--radius) !important;
        border-color: var(--border) !important;
        background: var(--card-grad) !important;
        box-shadow: var(--shadow-sm);
    }

    .period-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-family: var(--display);
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .morning-badge {
        background: var(--amber-soft);
        color: #fcd34d;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    .afternoon-badge {
        background: var(--sky-soft);
        color: #7dd3fc;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .evening-badge {
        background: var(--violet-soft);
        color: #c4b5fd;
        border: 1px solid rgba(167, 139, 250, 0.3);
    }

    .next-test-card {
        position: relative;
        overflow: hidden;
        background: var(--hero-grad);
        border: 1px solid var(--border-strong);
        padding: 1.05rem 1.25rem;
        border-radius: var(--radius);
        margin-bottom: 0.85rem;
        box-shadow: var(--shadow-sm);
    }
    .next-test-card::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 3px;
        background: linear-gradient(180deg, var(--violet), var(--accent-2));
    }
    .next-test-card h3 {
        margin: 0 0 0.28rem 0;
        font-family: var(--display);
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        font-weight: 700;
    }
    .next-test-card .test-title {
        font-family: var(--display);
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
        color: var(--text);
    }
    .next-test-card .test-date {
        font-size: 0.86rem;
        margin-top: 0.28rem;
        color: var(--text-2);
    }

    .stProgress > div > div > div > div {
        background: var(--progress-grad);
        border-radius: 999px;
    }
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.06) !important;
        border-radius: 999px;
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] > div { background: transparent !important; }
    section[data-testid="stSidebar"] h3 {
        font-family: var(--display) !important;
        color: var(--text) !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span { color: var(--text-2) !important; }
    /* Button labels must keep primary/secondary colors */
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stButton > button p,
    section[data-testid="stSidebar"] .stButton > button span {
        color: inherit !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {
        color: var(--primary-fg) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] p,
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] span {
        color: var(--text-2) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover p,
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover span {
        color: var(--text) !important;
    }
    .sidebar-brand-name { color: var(--text) !important; }
    .sidebar-brand-sub,
    .sidebar-nav-label,
    .sidebar-nav-active-hint { color: var(--muted) !important; }
    .sidebar-nav-active-hint { color: var(--faint) !important; }

    .stButton > button {
        border-radius: var(--radius-xs);
        font-family: var(--display);
        font-weight: 600;
        font-size: 0.8rem !important;
        min-height: 2.25rem;
        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;
        border: 1px solid var(--border);
        background: var(--btn-grad);
        color: var(--text);
        transition: transform 0.1s ease, box-shadow 0.12s ease, border-color 0.12s ease;
    }
    .stButton > button:hover {
        border-color: var(--border-strong);
        background: var(--btn-hover);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: var(--primary-grad);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: var(--primary-fg);
        font-weight: 700;
        box-shadow: 0 4px 18px rgba(139, 124, 255, 0.28);
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--primary-hover);
        color: var(--primary-fg);
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.03);
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stSelectbox [data-baseweb="select"] > div,
    div[data-baseweb="select"] > div {
        border-radius: var(--radius-xs) !important;
        border-color: var(--border) !important;
        background: var(--input-bg) !important;
        color: var(--text) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(139, 124, 255, 0.55) !important;
        box-shadow: 0 0 0 2px rgba(139, 124, 255, 0.14) !important;
    }

    .stForm {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem;
        background: var(--card-grad);
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    label { color: var(--text-2) !important; }

    /* Custom chrome must win over global markdown color rules */
    .app-hero-title { color: transparent !important; }
    .app-hero-greeting { color: var(--text) !important; }
    .app-hero-motto { color: var(--muted) !important; }
    .app-hero-meta { color: var(--faint) !important; }
    .app-hero-chip { color: #e2ddff !important; }
    .metric-tile-label { color: var(--muted) !important; }
    .metric-tile-value { color: var(--text) !important; }
    .metric-tile-hint { color: var(--faint) !important; }
    .section-label { color: var(--accent-2) !important; }
    .section-title { color: var(--text) !important; }
    .target-card-text { color: var(--text) !important; }
    .log-entry-body { color: var(--text) !important; }
    .log-entry-meta { color: var(--muted) !important; }
    .next-test-card .test-title { color: var(--text) !important; }
    .next-test-card .test-date { color: var(--text-2) !important; }
    .next-test-card h3 { color: var(--muted) !important; }
    .showup-title { color: var(--text) !important; }
    .sidebar-brand-name { color: var(--text) !important; }
    .sidebar-brand-sub { color: var(--muted) !important; }
    .theme-switch-note { color: var(--muted) !important; }
    .coach-name, .coach-line { color: var(--text) !important; }
    .period-badge.morning-badge { color: #fcd34d !important; }
    .period-badge.afternoon-badge { color: #7dd3fc !important; }
    .period-badge.evening-badge { color: #c4b5fd !important; }

    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
    div[data-testid="stExpander"] {
        background: rgba(18, 24, 38, 0.88);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        overflow: hidden;
    }

    .log-entry {
        background: var(--card-grad);
        border: 1px solid var(--border);
        border-left: 3px solid var(--violet);
        border-radius: var(--radius-xs);
        padding: 0.7rem 0.85rem;
        margin-bottom: 0.4rem;
    }
    .log-entry-meta {
        font-family: var(--display);
        font-size: 0.7rem;
        color: var(--muted);
        font-weight: 600;
        margin-bottom: 0.15rem;
    }
    .log-entry-body {
        font-size: 0.9rem;
        color: var(--text);
        line-height: 1.45;
        white-space: pre-wrap;
    }

    .log-undo-banner {
        background: var(--amber-soft);
        border: 1px solid rgba(251, 191, 36, 0.3);
        border-left: 3px solid var(--amber);
        border-radius: var(--radius-xs);
        padding: 0.55rem 0.75rem;
        font-size: 0.82rem;
        color: #fcd34d;
        margin-bottom: 0.45rem;
    }

    .coach-card {
        display: flex;
        gap: 0.9rem;
        align-items: flex-start;
        border-radius: var(--radius);
        padding: 0.9rem 1.05rem;
        margin-bottom: 0.8rem;
        color: var(--text);
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border);
    }
    .coach-yoda { background: linear-gradient(135deg, rgba(6, 78, 59, 0.7), rgba(10, 14, 24, 0.95)); border-color: rgba(52, 211, 153, 0.3); }
    .coach-vader { background: linear-gradient(135deg, rgba(55, 20, 28, 0.75), rgba(10, 14, 24, 0.95)); border-color: rgba(248, 113, 113, 0.3); }
    .coach-mando { background: linear-gradient(135deg, rgba(51, 65, 85, 0.75), rgba(10, 14, 24, 0.95)); border-color: rgba(148, 163, 184, 0.28); }
    .coach-dooku { background: linear-gradient(135deg, rgba(59, 7, 100, 0.7), rgba(10, 14, 24, 0.95)); border-color: rgba(167, 139, 250, 0.35); }
    .coach-anakin { background: linear-gradient(135deg, rgba(30, 58, 138, 0.7), rgba(10, 14, 24, 0.95)); border-color: rgba(56, 189, 248, 0.3); }
    .coach-deathstar { background: linear-gradient(135deg, rgba(51, 65, 85, 0.8), rgba(10, 14, 24, 0.95)); }
    .coach-jupiter { background: linear-gradient(135deg, rgba(120, 53, 15, 0.75), rgba(10, 14, 24, 0.95)); border-color: rgba(251, 191, 36, 0.3); }
    .coach-saturn { background: linear-gradient(135deg, rgba(87, 83, 78, 0.75), rgba(10, 14, 24, 0.95)); }
    .coach-avatar { font-size: 1.75rem; line-height: 1; }
    .coach-name { font-family: var(--display); font-size: 0.9rem; font-weight: 700; margin: 0 0 0.25rem 0; }
    .coach-title { font-weight: 500; opacity: 0.7; font-size: 0.75rem; }
    .coach-line { font-size: 0.88rem; line-height: 1.45; margin: 0; font-style: italic; opacity: 0.95; }

    .showup-card {
        background: var(--card-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.9rem 1.05rem 0.8rem;
        margin-bottom: 0.4rem;
        box-shadow: var(--shadow-sm);
    }
    .showup-head {
        display: flex; flex-wrap: wrap; justify-content: space-between;
        align-items: flex-start; gap: 0.6rem; margin-bottom: 0.55rem;
    }
    .showup-title {
        font-family: var(--display);
        font-size: 0.92rem;
        font-weight: 700;
        margin: 0 0 0.15rem 0;
        color: var(--text);
    }
    .showup-sub, .showup-foot, .showup-legend-label, .showup-dow, .showup-week-hdr {
        font-size: 0.7rem;
        color: var(--muted);
    }
    .showup-legend { display: flex; align-items: center; gap: 3px; }
    .showup-month-grid { display: flex; gap: 8px; align-items: flex-start; }
    .showup-dow-col {
        display: grid; grid-template-rows: repeat(7, 12px); gap: 2px; padding-top: 16px;
    }
    .showup-dow { line-height: 12px; text-align: right; padding-right: 2px; font-size: 0.58rem; }
    .showup-weeks-col { flex: 1; overflow-x: auto; }
    .showup-week-hdrs {
        display: grid; grid-auto-flow: column; gap: 2px; margin-bottom: 3px; min-height: 12px;
    }
    .showup-week-hdr { text-align: center; white-space: nowrap; font-size: 0.58rem; }
    .showup-grid {
        display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 12px);
        gap: 2px; padding-bottom: 2px;
    }
    .showup-cell { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
    .showup-legend .showup-cell { width: 9px; height: 9px; }
    .heat-out { background: transparent; opacity: 0.28; }
    .heat-0 { background: rgba(255, 255, 255, 0.04); box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03); }
    .heat-1 { background: #134e4a; }
    .heat-2 { background: #0f766e; }
    .heat-3 { background: #14b8a6; }
    .heat-4 { background: #2dd4bf; }
    .heat-today {
        outline: 1.5px solid #a5b4fc;
        box-shadow: 0 0 0 2px rgba(165, 180, 252, 0.2);
    }
    .showup-foot { margin: 0.45rem 0 0 0; }

    .stDownloadButton > button,
    .stLinkButton > a {
        border-radius: var(--radius-xs) !important;
        font-family: var(--display) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }

    div[data-testid="stTabs"] div[role="tablist"] {
        gap: 0.25rem;
        background: rgba(16, 22, 36, 0.88);
        border-radius: 999px;
        padding: 0.28rem;
        border: 1px solid var(--border);
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-family: var(--display);
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.42rem 0.9rem;
        border-radius: 999px;
        color: var(--muted);
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--nav-active-fg);
        background: var(--tab-active);
    }

    /* ── Syllabus Atlas ─────────────────────────────────── */
    .atlas-strip {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.35rem 0 0.85rem 0;
    }
    .atlas-tile {
        position: relative;
        background: var(--metric-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.7rem 0.8rem 0.65rem;
        box-shadow: var(--shadow-sm);
        overflow: hidden;
    }
    .atlas-tile-due { border-color: var(--amber); }
    .atlas-tile-label {
        font-family: var(--display);
        font-size: 0.62rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted) !important;
        margin: 0 0 0.2rem 0;
        font-weight: 700;
    }
    .atlas-tile-value {
        font-family: var(--display);
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text) !important;
        margin: 0;
        letter-spacing: -0.03em;
    }
    .atlas-tile-hint {
        font-size: 0.7rem;
        color: var(--faint) !important;
        margin: 0.15rem 0 0 0;
    }
    .atlas-ramp {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem 0.7rem;
        margin: 0.15rem 0 0.75rem 0;
        align-items: center;
    }
    .atlas-ramp-cell {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-2) !important;
        letter-spacing: 0.01em;
    }
    .atlas-ramp-cell i {
        width: 0.85rem;
        height: 0.85rem;
        border-radius: 999px;
        background: var(--c);
        box-shadow: 0 0 0 1px rgba(255,255,255,0.08), 0 0 10px color-mix(in srgb, var(--c) 45%, transparent);
        display: inline-block;
    }
    .atlas-ramp-cell.fade { color: var(--muted) !important; font-weight: 500; }
    .atlas-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0 0 1rem 0;
    }
    .atlas-legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        padding: 0.18rem 0.5rem;
        border-radius: 999px;
        border: 1px solid var(--border);
        color: var(--text-2) !important;
    }
    .atlas-legend-chip::before,
    .atlas-cell-mark {
        content: "";
        width: 0.55rem;
        height: 0.55rem;
        border-radius: 3px;
        background: currentColor;
        display: inline-block;
    }
    .atlas-legend-chip.st-unseen { color: var(--faint) !important; }
    .atlas-legend-chip.st-scouted { color: var(--sky) !important; }
    .atlas-legend-chip.st-mapped { color: var(--violet) !important; }
    .atlas-legend-chip.st-held { color: var(--amber) !important; }
    .atlas-legend-chip.st-fortified { color: var(--teal) !important; }

    .atlas-col-label {
        font-family: var(--display);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--muted) !important;
        margin: 0.15rem 0 0.45rem 0;
    }
    .atlas-quest {
        background: var(--card-grad);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.65rem 0.75rem 0.55rem;
        margin: 0 0 0.35rem 0;
        border-left: 3px solid var(--faint);
    }
    .atlas-quest.is-hold { border-left-color: var(--amber); }
    .atlas-quest-title {
        font-family: var(--display);
        font-weight: 700;
        font-size: 0.92rem;
        color: var(--text) !important;
        margin: 0 0 0.12rem 0;
    }
    .atlas-quest-meta {
        font-size: 0.72rem;
        color: var(--muted) !important;
        margin: 0;
    }
    .atlas-unit-map {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 0.55rem;
        margin: 0.35rem 0 0.85rem 0;
    }
    .atlas-unit-tile {
        position: relative;
        min-height: 4.4rem;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border);
        background: var(--surface-2);
        overflow: hidden;
        padding: 0.65rem 0.7rem;
    }
    .atlas-unit-fill {
        position: absolute;
        left: 0; bottom: 0; top: 0;
        background: linear-gradient(90deg, var(--accent-soft), var(--teal-soft));
        opacity: 0.85;
        pointer-events: none;
    }
    .atlas-unit-fog {
        position: absolute;
        inset: 0;
        background:
            repeating-linear-gradient(
                -18deg,
                transparent,
                transparent 6px,
                rgba(8, 10, 16, 0.18) 6px,
                rgba(8, 10, 16, 0.18) 7px
            );
        pointer-events: none;
    }
    .atlas-unit-name, .atlas-unit-meta { position: relative; z-index: 1; }
    .atlas-unit-name {
        font-family: var(--display);
        font-weight: 700;
        font-size: 0.86rem;
        color: var(--text) !important;
        margin: 0 0 0.15rem 0;
    }
    .atlas-unit-meta {
        font-size: 0.68rem;
        color: var(--muted) !important;
        margin: 0;
    }
    .atlas-unit-due {
        color: var(--amber) !important;
        font-weight: 700;
    }
    .atlas-constellation {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
        gap: 0.4rem;
        margin: 0.35rem 0 0.85rem 0;
    }
    .atlas-cell {
        display: flex;
        align-items: flex-start;
        gap: 0.4rem;
        min-height: 3.1rem;
        padding: 0.45rem 0.5rem;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: rgba(10, 14, 22, 0.35);
        color: var(--text-2);
    }
    .atlas-cell-mark {
        flex: 0 0 0.62rem;
        width: 0.62rem;
        height: 0.62rem;
        margin-top: 0.18rem;
        border-radius: 3px;
    }
    .atlas-cell-name {
        font-size: 0.74rem;
        line-height: 1.3;
        font-weight: 600;
    }
    .atlas-cell.st-unseen {
        opacity: 0.55;
        filter: saturate(0.3);
    }
    .atlas-cell.st-unseen .atlas-cell-mark { background: #4b5568; }
    .atlas-cell.st-scouted .atlas-cell-mark { background: var(--sky); }
    .atlas-cell.st-mapped .atlas-cell-mark { background: var(--violet); }
    .atlas-cell.st-held .atlas-cell-mark { background: var(--amber); }
    .atlas-cell.st-fortified {
        border-color: rgba(62, 207, 173, 0.4);
        box-shadow: 0 0 0 1px rgba(62, 207, 173, 0.12), 0 0 16px rgba(62, 207, 173, 0.08);
    }
    .atlas-cell.st-fortified .atlas-cell-mark { background: var(--teal); }
    .atlas-cell.st-scouted { background: var(--sky-soft); }
    .atlas-cell.st-mapped { background: var(--violet-soft); }
    .atlas-cell.st-held { background: var(--amber-soft); }
    .atlas-cell.st-fortified { background: var(--teal-soft); }
    .atlas-cell.is-selected {
        outline: 1.5px solid var(--accent);
        outline-offset: 1px;
    }
    .atlas-cell.is-due {
        box-shadow: 0 0 0 1px var(--amber);
    }
    .atlas-focus {
        background: var(--card-grad);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius);
        padding: 0.85rem 1rem 0.75rem;
        margin: 0.25rem 0 0.65rem 0;
    }
    .atlas-focus-kicker {
        font-size: 0.68rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted) !important;
        margin: 0 0 0.2rem 0;
        font-weight: 700;
    }
    .atlas-focus-title {
        font-family: var(--display);
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--text) !important;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
    }
    .atlas-focus-meta {
        font-size: 0.78rem;
        color: var(--text-2) !important;
        margin: 0;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
    }
    .atlas-due-rail {
        background: var(--amber-soft);
        border: 1px solid rgba(240, 193, 77, 0.28);
        border-radius: var(--radius-sm);
        padding: 0.65rem 0.75rem;
        margin: 0 0 0.75rem 0;
    }
    .atlas-due-rail p { margin: 0; }
    .atlas-due-rail .atlas-due-kicker {
        font-size: 0.66rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--amber) !important;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .atlas-due-rail .atlas-due-body {
        font-size: 0.8rem;
        color: var(--text-2) !important;
        line-height: 1.4;
    }
    .atlas-empty { color: var(--muted); font-size: 0.85rem; }

    @media (max-width: 900px) {
        .atlas-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
"""

# Nova-only polish on top of shared components
_NOVA_EXTRAS = """
    /* Tighter, more deliberate page rhythm */
    .app-hero {
        padding: 1.05rem 1.4rem 1rem;
        margin-bottom: 0.9rem;
        border-radius: 18px;
    }
    .app-hero-title {
        font-size: 1.48rem;
    }
    .app-hero-greeting {
        font-size: 0.95rem;
        opacity: 0.95;
    }

    /* Soft divider under metrics before nav */
    .metric-strip {
        margin-bottom: 0.95rem;
        gap: 0.75rem;
    }
    .metric-tile {
        border-radius: 14px;
        padding: 0.8rem 0.95rem 0.75rem;
        transition: border-color 0.15s ease, transform 0.12s ease;
    }
    .metric-tile:hover {
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }
    .metric-tile-value {
        font-size: 1.28rem;
    }

    /* Nav buttons: Streamlit nests widgets, so target via :has(.wd-nav-marker) */
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    div[data-testid="stHorizontalBlock"],
    div.element-container:has(.wd-nav-marker) + div.element-container
    div[data-testid="stHorizontalBlock"] {
        margin: 0 0 1rem 0 !important;
        padding: 0.4rem !important;
        background: linear-gradient(180deg, rgba(20, 26, 40, 0.92), rgba(14, 18, 28, 0.9)) !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        box-shadow: var(--shadow-sm);
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button,
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button {
        border-radius: 999px !important;
        min-height: 2.35rem;
        font-size: 0.78rem !important;
        letter-spacing: 0.01em;
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button[kind="secondary"],
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button[kind="secondary"] {
        background: transparent;
        border-color: transparent;
        color: var(--muted);
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button[kind="secondary"]:hover,
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text);
        border-color: transparent;
        transform: none;
    }

    /* Stronger section hierarchy */
    .section-label {
        letter-spacing: 0.12em;
        font-size: 0.66rem;
        color: var(--accent-2);
        opacity: 0.95;
    }
    .section-title {
        font-size: 1.18rem;
        margin-bottom: 0.55rem;
    }

    /* Targets / cards feel slightly more roomy */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
    }

    /* Primary actions glow more intentionally */
    .stButton > button[kind="primary"] {
        box-shadow: 0 6px 22px rgba(139, 124, 255, 0.22), 0 0 0 1px rgba(255,255,255,0.04) inset;
    }

    /* Expanders as soft panels */
    div[data-testid="stExpander"] {
        background: linear-gradient(165deg, rgba(22, 28, 42, 0.9), rgba(14, 18, 28, 0.94));
        border-radius: 14px;
        margin-bottom: 0.35rem;
    }

    /* Progress track taller for clarity */
    .stProgress > div > div {
        height: 0.55rem !important;
    }

    /* Better form breathing room */
    .stForm {
        padding: 1.1rem 1.15rem;
        border-radius: 16px;
    }

    /* Log entries slightly elevated */
    .log-entry {
        border-radius: 12px;
        transition: border-color 0.12s ease;
    }
    .log-entry:hover {
        border-color: var(--border-strong);
    }

    /* Coach cards more dimensional */
    .coach-card {
        border-radius: 16px;
        padding: 1rem 1.15rem;
    }

    /* Next test card: amber accent option feel */
    .next-test-card {
        border-radius: 16px;
        padding: 1.15rem 1.35rem;
    }

    @media (max-width: 640px) {
        .app-hero-title { font-size: 1.2rem; }
        .metric-tile-value { font-size: 1.1rem; }
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }
    }
"""

# Classic keeps compact hero / hides metric strip chrome if unused
_CLASSIC_EXTRAS = """
    .app-hero {
        padding: 0.75rem 1.1rem 0.7rem;
        margin-bottom: 0.55rem;
        border-radius: 14px;
    }
    .app-hero-title { font-size: 1.2rem; }
    .app-hero-greeting { font-size: 0.88rem; }
    .app-hero-motto { font-size: 0.78rem; }
    .app-hero::after { display: none; }

    .metric-strip {
        gap: 0.55rem;
        margin-bottom: 0.55rem;
    }
    .metric-tile {
        border-radius: 12px;
        padding: 0.55rem 0.75rem;
    }
    .metric-tile-value { font-size: 1.12rem; }

    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    div[data-testid="stHorizontalBlock"],
    div.element-container:has(.wd-nav-marker) + div.element-container
    div[data-testid="stHorizontalBlock"] {
        margin: 0 0 0.45rem 0 !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }

    /* Classic keeps brand via markdown headings */
    .sidebar-brand { display: none; }
    .page-context-hint { display: none; }
    .workspace-panel {
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
        margin-bottom: 0.5rem;
    }
    .workspace-panel-head {
        border-bottom: none;
        padding-bottom: 0;
        margin-bottom: 0.4rem;
    }
"""

# Paper reuses Nova layout chrome, then flips surfaces to warm light notebook
_PAPER_EXTRAS = """
    /* Layout rhythm matches Nova */
    .app-hero {
        padding: 1.05rem 1.4rem 1rem;
        margin-bottom: 0.9rem;
        border-radius: 18px;
        box-shadow: var(--shadow-sm), 0 0 0 1px rgba(255,255,255,0.7) inset;
    }
    .app-hero-title { font-size: 1.48rem; }
    .app-hero-greeting { font-size: 0.95rem; }
    .app-hero::after {
        background: radial-gradient(circle, rgba(13, 148, 136, 0.08), transparent 70%);
    }
    .app-hero-chip {
        color: var(--chip-fg, #4338ca) !important;
        border-color: rgba(91, 79, 214, 0.28);
        background: rgba(91, 79, 214, 0.1);
    }
    .app-hero-chip { color: #4338ca !important; }

    .metric-strip { margin-bottom: 0.95rem; gap: 0.75rem; }
    .metric-tile {
        border-radius: 14px;
        padding: 0.8rem 0.95rem 0.75rem;
        transition: border-color 0.15s ease, transform 0.12s ease, box-shadow 0.15s ease;
    }
    .metric-tile:hover {
        border-color: var(--border-strong);
        transform: translateY(-1px);
        box-shadow: 0 8px 22px rgba(60, 48, 32, 0.1);
    }
    .metric-tile-value { font-size: 1.28rem; }

    /* Light pill nav */
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    div[data-testid="stHorizontalBlock"],
    div.element-container:has(.wd-nav-marker) + div.element-container
    div[data-testid="stHorizontalBlock"] {
        margin: 0 0 1rem 0 !important;
        padding: 0.4rem !important;
        background: linear-gradient(180deg, #ffffff 0%, #f7f2e9 100%) !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        box-shadow: var(--shadow-sm);
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button,
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button {
        border-radius: 999px !important;
        min-height: 2.35rem;
        font-size: 0.78rem !important;
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button[kind="secondary"],
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button[kind="secondary"] {
        background: transparent;
        border-color: transparent;
        color: var(--muted);
    }
    div[data-testid="stElementContainer"]:has(.wd-nav-marker) + div[data-testid="stElementContainer"]
    .stButton > button[kind="secondary"]:hover,
    div.element-container:has(.wd-nav-marker) + div.element-container
    .stButton > button[kind="secondary"]:hover {
        background: rgba(60, 48, 32, 0.05);
        color: var(--text);
        border-color: transparent;
        transform: none;
    }

    .section-label {
        letter-spacing: 0.12em;
        font-size: 0.66rem;
        color: var(--accent-2) !important;
    }
    .section-title {
        font-size: 1.18rem;
        margin-bottom: 0.55rem;
        color: var(--text) !important;
    }

    /* Heatmap: light notebook contribution cells */
    .heat-0 {
        background: var(--heat-0, #e8e2d6) !important;
        box-shadow: inset 0 0 0 1px rgba(60, 48, 32, 0.06) !important;
    }
    .heat-1 { background: var(--heat-1, #99f6e4) !important; }
    .heat-2 { background: var(--heat-2, #5eead4) !important; }
    .heat-3 { background: var(--heat-3, #14b8a6) !important; }
    .heat-4 { background: var(--heat-4, #0f766e) !important; }
    .heat-today {
        outline: 1.5px solid #5b4fd6 !important;
        box-shadow: 0 0 0 2px rgba(91, 79, 214, 0.18) !important;
    }

    /* Tabs / expanders / forms on paper */
    div[data-testid="stTabs"] div[role="tablist"] {
        background: rgba(255, 255, 255, 0.9) !important;
    }
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px;
    }
    .stForm {
        padding: 1.1rem 1.15rem;
        border-radius: 16px;
        background: #ffffff !important;
    }
    .atlas-cell {
        background: rgba(255, 255, 255, 0.72);
    }
    .atlas-unit-tile { background: #fffdf8; }
    .atlas-unit-fog {
        background:
            repeating-linear-gradient(
                -18deg,
                transparent,
                transparent 6px,
                rgba(60, 48, 32, 0.06) 6px,
                rgba(60, 48, 32, 0.06) 7px
            );
    }
    .atlas-quest { background: #fffdf8; }

    .stButton > button[kind="primary"] {
        box-shadow: 0 6px 18px rgba(91, 79, 214, 0.22);
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover {
        color: #ffffff !important;
    }
    .stProgress > div > div {
        height: 0.55rem !important;
        background: rgba(60, 48, 32, 0.08) !important;
    }

    /* Soft coach cards for light reading */
    .coach-yoda { background: linear-gradient(135deg, rgba(209, 250, 229, 0.95), #ffffff); border-color: rgba(13, 148, 136, 0.28); }
    .coach-vader { background: linear-gradient(135deg, rgba(254, 226, 226, 0.95), #ffffff); border-color: rgba(225, 29, 72, 0.25); }
    .coach-mando { background: linear-gradient(135deg, rgba(226, 232, 240, 0.95), #ffffff); border-color: rgba(100, 116, 139, 0.25); }
    .coach-dooku { background: linear-gradient(135deg, rgba(237, 233, 254, 0.95), #ffffff); border-color: rgba(109, 94, 240, 0.28); }
    .coach-anakin { background: linear-gradient(135deg, rgba(224, 242, 254, 0.95), #ffffff); border-color: rgba(2, 132, 199, 0.28); }
    .coach-deathstar { background: linear-gradient(135deg, rgba(226, 232, 240, 0.95), #ffffff); }
    .coach-jupiter { background: linear-gradient(135deg, rgba(254, 243, 199, 0.95), #ffffff); border-color: rgba(217, 119, 6, 0.28); }
    .coach-saturn { background: linear-gradient(135deg, rgba(245, 245, 244, 0.95), #ffffff); }
    .coach-name, .coach-line { color: var(--text) !important; }

    /* Garden surfaces on paper */
    .garden-compact, .garden-hero, .hay-farm-panel, .garden-stat {
        background: linear-gradient(165deg, #ffffff, #f7f2e9) !important;
        border-color: var(--border) !important;
    }
    .garden-stage-title { color: #0f766e !important; }
    .garden-xp, .garden-xp-total, .garden-stat .v { color: #0d9488 !important; }
    .garden-next { color: var(--text-2) !important; }
    .garden-hint, .garden-mode-note, .garden-stat .k { color: var(--muted) !important; }

    .log-entry {
        background: #ffffff !important;
        border-radius: 12px;
    }
    .log-entry:hover { border-color: var(--border-strong); }
    .showup-card { background: #ffffff !important; }
    .next-test-card {
        border-radius: 16px;
        padding: 1.15rem 1.35rem;
        background: linear-gradient(145deg, #ffffff, #f7f2e9) !important;
    }

    /* Streamlit widgets that still inherit dark base theme */
    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: var(--text-2) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] p,
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] span {
        color: var(--text-2) !important;
    }
    .sidebar-brand-name { color: var(--text) !important; }
    .sidebar-nav-label { color: var(--muted) !important; }
    div[data-testid="stMetric"] {
        background: var(--metric-grad) !important;
        border: 1px solid var(--border) !important;
    }
    div[data-testid="stMetric"] label { color: var(--muted) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--text) !important; }
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stSelectbox [data-baseweb="select"] > div,
    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    label { color: var(--text-2) !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
    .stCode, code, pre {
        background: #f3ede3 !important;
        color: var(--text) !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="tooltip"] {
        background: #ffffff !important;
        color: var(--text) !important;
    }

    /* Period badges readable on cream */
    .morning-badge {
        background: rgba(217, 119, 6, 0.12) !important;
        color: #b45309 !important;
        border-color: rgba(217, 119, 6, 0.28) !important;
    }
    .afternoon-badge {
        background: rgba(2, 132, 199, 0.1) !important;
        color: #0369a1 !important;
        border-color: rgba(2, 132, 199, 0.25) !important;
    }
    .evening-badge {
        background: rgba(91, 79, 214, 0.1) !important;
        color: #4c1d95 !important;
        border-color: rgba(91, 79, 214, 0.25) !important;
    }
    .period-badge.morning-badge { color: #b45309 !important; }
    .period-badge.afternoon-badge { color: #0369a1 !important; }
    .period-badge.evening-badge { color: #4c1d95 !important; }

    .log-undo-banner {
        background: rgba(217, 119, 6, 0.1) !important;
        color: #b45309 !important;
        border-color: rgba(217, 119, 6, 0.25) !important;
    }

    @media (max-width: 640px) {
        .app-hero-title { font-size: 1.2rem; }
        .metric-tile-value { font-size: 1.1rem; }
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }
    }
"""


def resolve_theme(name: str | None) -> str:
    """Normalize theme name; unknown values fall back to default."""
    key = (name or DEFAULT_THEME).strip().lower()
    if key not in THEME_OPTIONS:
        return DEFAULT_THEME
    return key


def get_app_css(theme: str | None = None) -> str:
    """Return full <style> block for the selected theme."""
    theme = resolve_theme(theme)
    if theme == "paper":
        vars_block, extras = PAPER_VARS, _PAPER_EXTRAS
    elif theme == "classic":
        vars_block, extras = CLASSIC_VARS, _CLASSIC_EXTRAS
    else:
        vars_block, extras = NOVA_VARS, _NOVA_EXTRAS
    return f"""
<style>
{vars_block}
{_SHARED_BASE}
{_COMPONENT_CSS}
{extras}
</style>
"""


# Backward-compatible default export (Nova)
APP_CSS = get_app_css(DEFAULT_THEME)

__all__ = [
    "APP_CSS",
    "DEFAULT_THEME",
    "THEME_OPTIONS",
    "get_app_css",
    "resolve_theme",
]
