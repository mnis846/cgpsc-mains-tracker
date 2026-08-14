"""
FastAPI bridge for the Godot Study Garden.

Serves milestone JSON at GET /api/garden/milestones so the Godot client
can render permanent trees, blooms, fruits, and the active sprout.

Run (from repo root, with venv active):
    pip install fastapi uvicorn
    uvicorn garden_api:app --reload --port 8000

Godot default: http://127.0.0.1:8000/api/garden/milestones
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from garden_life import (
    STREAK_DAYS_PER_TREE,
    count_complete_goal_days,
    get_goal_streak,
    unlocked_tree_count,
)
from database import (
    get_daily_study_goal,
    get_scheduled_tests,
    get_study_hours_map,
    score_percentage,
)

app = FastAPI(
    title="CGPSC Study Garden API",
    version="1.0.0",
    description="Milestone feed for the Godot garden visualizer",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Godot / product rules (see garden_life + user spec)
PLANT_STREAK_DAYS = 4          # permanent tree
BLOOM_STREAK_DAYS = 6          # cherry blossoms on the active long streak
FRUIT_SCORE_MIN = 60.0         # shiny fruits when matching test > 60%
DEFAULT_GOAL_HOURS = 6.0


def _test_scores_by_block() -> dict[int, float]:
    """Map tree/block index (1-based) → best score % for that test_no if present."""
    df = get_scheduled_tests()
    out: dict[int, float] = {}
    if df is None or df.empty:
        return out
    for _, row in df.sort_values("test_no").iterrows():
        if str(row.get("status") or "") != "Attempted":
            continue
        raw = row.get("score")
        if raw is None:
            continue
        try:
            import pandas as pd

            if pd.isna(raw):
                continue
        except Exception:
            pass
        pct = score_percentage(raw, row.get("max_score"))
        if pct is None:
            try:
                pct = float(raw)
            except (TypeError, ValueError):
                continue
        tno = int(row["test_no"])
        prev = out.get(tno)
        if prev is None or pct > prev:
            out[tno] = float(pct)
    return out


def _milestone_achieved_date(tree_no: int, today: date) -> str:
    """Approximate plant date: day when complete_days first reached (tree_no)*4.

    We walk recent hours map and find the Nth complete day.
    """
    goal = float(get_daily_study_goal() or DEFAULT_GOAL_HOURS)
    start = today - timedelta(days=400)
    hours_map = get_study_hours_map(start, today)
    need = tree_no * STREAK_DAYS_PER_TREE
    complete = 0
    # Chronological
    for i in range(400, -1, -1):
        d = today - timedelta(days=i)
        if hours_map.get(d, 0) >= goal:
            complete += 1
            if complete >= need:
                return d.isoformat()
    return today.isoformat()


def build_garden_payload(today: Optional[date] = None) -> dict[str, Any]:
    """
    Build the Godot-facing schema:

    - 4 consecutive complete goal-days → permanent milestone tree (also mirrored
      by cumulative complete-day unlocks already used in garden_life).
    - Extending a live streak to 6 days → has_flowers on the newest tree.
    - Matching weekly/block test > 60% → has_fruits on that tree.
    - Streak break → active_tree.wilted true (permanent milestones untouched).
    """
    if today is None:
        today = date.today()

    goal = float(get_daily_study_goal() or DEFAULT_GOAL_HOURS)
    streak = int(get_goal_streak(today))
    complete_days = int(count_complete_goal_days(today))
    unlocked = int(unlocked_tree_count(complete_days, today))
    scores = _test_scores_by_block()

    milestones: list[dict[str, Any]] = []
    for tree_no in range(1, unlocked + 1):
        score = scores.get(tree_no)
        has_fruits = score is not None and score > FRUIT_SCORE_MIN
        # Flowers: permanent beauty once the tree is "mature" (4+ complete days
        # after unlock) OR the live streak is long enough for the newest tree.
        unlock_at = max(0, (tree_no - 1) * STREAK_DAYS_PER_TREE)
        days_since = max(0, complete_days - unlock_at)
        matured = days_since >= STREAK_DAYS_PER_TREE
        is_newest = tree_no == unlocked
        bloom_from_streak = is_newest and streak >= BLOOM_STREAK_DAYS
        has_flowers = matured or bloom_from_streak or has_fruits

        milestones.append(
            {
                "id": tree_no,
                "achieved_date": _milestone_achieved_date(tree_no, today),
                "has_flowers": bool(has_flowers),
                "has_fruits": bool(has_fruits),
                "test_score": round(score, 1) if score is not None else None,
            }
        )

    # Active / in-progress slot (not yet permanent)
    rem = streak % PLANT_STREAK_DAYS if streak > 0 else 0
    if streak > 0 and rem == 0:
        # Exactly completed a plant cycle — active slot empty until next day
        active = {"progress_days": 0, "wilted": False}
    elif streak > 0:
        active = {"progress_days": rem, "wilted": False}
    else:
        # Streak broken: wilt only the in-progress sprout (visual), not permanent trees
        active = {"progress_days": 1, "wilted": True}

    return {
        "current_streak_days": streak,
        "daily_goal_hours": goal,
        "complete_days": complete_days,
        "milestones": milestones,
        "active_tree": active,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "CGPSC Study Garden API",
        "milestones": "/api/garden/milestones",
        "health": "/api/health",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/garden/milestones")
def garden_milestones() -> dict[str, Any]:
    """Primary feed for Godot GardenManager."""
    return build_garden_payload()


@app.get("/api/garden/state")
def garden_state_alias() -> dict[str, Any]:
    """Alias used by some clients."""
    return build_garden_payload()
