"""Personal profile for Manish's CGPSC Mains Tracker."""

FULL_NAME = "Manish Tandan"
FIRST_NAME = "Manish"
EXAM = "CGPSC Mains"
EXAM_YEAR = 2026
MOTTO = "Show up daily. Clear Mains."

GREETINGS = {
    "morning": f"Good morning, {FIRST_NAME}!",
    "afternoon": f"Good afternoon, {FIRST_NAME}!",
    "evening": f"Good evening, {FIRST_NAME}!",
}

PERIOD_NUDGES = {
    "morning": "Start the day with clear targets — one paper, one win.",
    "afternoon": "Afternoon check-in: stay on track before the day slips away.",
    "evening": "Evening wrap-up — log hours and reflect on what moved the needle.",
}


def greeting(period_key):
    return GREETINGS.get(period_key, f"Hello, {FIRST_NAME}!")


def period_nudge(period_key):
    return PERIOD_NUDGES.get(period_key, MOTTO)


def possessive(label):
    return f"{FIRST_NAME}'s {label}"