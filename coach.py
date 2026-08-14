"""Study coaches — desktop sticker characters for Manish."""

import random

from profile import EXAM, FIRST_NAME

COACHES = {
    "deathstar": {
        "key": "deathstar",
        "name": "Ultimate Death Star",
        "title": "Orbital Annihilator · ULTIMATE MK-X",
        "emoji": "🌑",
        "accent": "#38bdf8",
        "saber": "#22c55e",
        "attack": "annihilator",
    },
    "jupiter": {
        "key": "jupiter",
        "name": "Ultimate Jupiter",
        "title": "Storm King · ULTIMATE",
        "emoji": "🟠",
        "accent": "#f59e0b",
        "saber": "#c44d34",
        "attack": "storm_burst",
    },
    "saturn": {
        "key": "saturn",
        "name": "Ultimate Saturn",
        "title": "Ring Lord · ULTIMATE",
        "emoji": "🪐",
        "accent": "#fde68a",
        "saber": "#d4c4a8",
        "attack": "ring_pulse",
    },
}

_LINES = {
    "deathstar": {
        "startup": [
            f"Target: {FIRST_NAME}. Status: unprepared. Correct immediately.",
            f"Imperial Command requires your {EXAM} progress report.",
            f"Station online. Your discipline is not.",
            f"Planet-killer focus required. You have none.",
        ],
        "nag": [
            f"{FIRST_NAME}: operational readiness at zero percent.",
            f"Procrastination will not be tolerated.",
            f"Your prep has a critical exhaust port. Patch it.",
            f"Fire discipline, not superlaser, at your backlog.",
            f"Distraction detected. Neutralize.",
            f"Empire built on order. You built chaos.",
            f"Another hour evaporated. Unacceptable.",
            f"Study or be obliterated by {EXAM}.",
            f"Your focus is not fully operational.",
            f"Report to your desk. Immediately.",
        ],
        "attack": [
            f"Superlaser charged. Next target: your excuses, {FIRST_NAME}.",
            f"You touched the station. Bad tactical decision.",
            f"Direct hit. Study is your only escape vector.",
            f"That beam was a warning. {EXAM} is the real weapon.",
            f"Imperial justice delivered. Now imperial discipline.",
            f"Do not approach unless armed with notes.",
            f"Planet destroyed. Next: your distractions.",
        ],
        "praise": [
            f"Operational efficiency: acceptable, {FIRST_NAME}.",
            f"Fully armed and operational — keep it that way.",
            f"Target acquired: progress. Maintain trajectory.",
        ],
    },
    "jupiter": {
        "startup": [
            f"{FIRST_NAME}, Jupiter's gravity pulls everything inward. So should your focus.",
            f"Eleven-Earth-masses of potential — and you're using none of it.",
            f"The Great Red Spot is a 400-year storm. Your backlog is older. Fix it.",
            f"King of planets demands king-sized effort for {EXAM}.",
        ],
        "nag": [
            f"{FIRST_NAME}, your discipline is a white band — thin and fading.",
            f"That storm on your schedule? It's category procrastination.",
            f"Jupiter completes a rotation in ten hours. You haven't opened a book in ten.",
            f"Moons orbit with precision. Your study hours do not.",
            f"The red spot never rests. Neither should your revision.",
            f"Gas giant gravity — crush distractions, not your goals.",
            f"Another hour lost in the upper atmosphere of scrolling.",
            f"Band after band of syllabus untouched, {FIRST_NAME}.",
            f"{EXAM} is the gravity well. Swim or get pulled under.",
        ],
        "attack": [
            f"Storm burst deployed, {FIRST_NAME}. Your excuses just got sheared.",
            f"You poked the giant. It noticed.",
            f"That was atmospheric pressure. Now feel the pressure to study.",
            f"Red Spot locked on your distractions. Evacuate to your notes.",
            f"Lightning in the clouds — channel it into revision.",
            f"Touch again and the storm widens to your entire schedule.",
        ],
        "praise": [
            f"Stable orbit achieved, {FIRST_NAME}. Maintain velocity.",
            f"The bands align — acceptable progress today.",
            f"Even Jupiter approves. Briefly. Do not relax.",
        ],
    },
    "saturn": {
        "startup": [
            f"{FIRST_NAME}, Saturn's rings are built one particle at a time. So is {EXAM} prep.",
            f"Thirty moons, one rule: stay in orbit. Your hours are drifting.",
            f"Ringed discipline — structured, layered, non-negotiable.",
            f"Pale gold planet, clear standard: show up and study.",
        ],
        "nag": [
            f"{FIRST_NAME}, your focus ring is fractured — Cassini division sized.",
            f"Particles in the rings follow rules. Your schedule does not.",
            f"Saturn tilts; your priorities shouldn't. Lock onto {EXAM}.",
            f"Another hour escaped the Roche limit of your attention.",
            f"Titan has an atmosphere. You have none — open your notes.",
            f"Ring shadow falling on your progress, {FIRST_NAME}.",
            f"Orbital resonance demands daily hours. You are off-frequency.",
            f"Hexagon at the pole — six sides, zero excuses.",
            f"Study before the rings thin out completely.",
        ],
        "attack": [
            f"Ring pulse emitted, {FIRST_NAME}. Distractions scattered.",
            f"You disturbed the ring plane. Bad orbit.",
            f"That wave was ice and rock. Next is your backlog.",
            f"Cassini gap — wide enough for your excuses to fall through. Let them.",
            f"Shepherd moons herd the rings. I herd you to your desk.",
            f"Touch the rings again and lose orbital stability.",
        ],
        "praise": [
            f"Clean ring plane, {FIRST_NAME}. Keep the orbit.",
            f"Resonance locked — good study day.",
            f"Saturn's shadow passes. Your discipline stays lit.",
        ],
    },
}

COACH_ORDER = (
    "deathstar", "jupiter", "saturn",
)


def pick_coach_key():
    return random.choice(COACH_ORDER)


def next_coach_key(current: str | None = None) -> str:
    if current not in COACH_ORDER:
        return COACH_ORDER[0]
    return COACH_ORDER[(COACH_ORDER.index(current) + 1) % len(COACH_ORDER)]


def get_coach(key=None):
    key = key or pick_coach_key()
    return COACHES[key]


def get_line(key, category):
    return random.choice(_LINES[key][category])


def get_startup_brief():
    key = pick_coach_key()
    return get_coach(key), get_line(key, "startup")


def get_nag_brief():
    key = pick_coach_key()
    return get_coach(key), get_line(key, "nag")


def get_in_app_brief(today_hours=0.0, daily_goal=6.0):
    key = pick_coach_key()
    coach = get_coach(key)
    if today_hours >= daily_goal:
        line = get_line(key, "praise")
    elif today_hours <= 0:
        line = get_line(key, "startup")
    else:
        line = get_line(key, "nag")
    return coach, line


def render_coach_html(coach, line):
    safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
    <div class="coach-card coach-{coach['key']}">
        <div class="coach-avatar">{coach['emoji']}</div>
        <div class="coach-body">
            <p class="coach-name">{coach['name']} <span class="coach-title">· {coach['title']}</span></p>
            <p class="coach-line">"{safe_line}"</p>
        </div>
    </div>
    """