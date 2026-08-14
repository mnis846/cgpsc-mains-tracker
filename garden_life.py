"""Study grove — scales from 1 tree to 55+ prelims blocks and mains sprint."""

from datetime import date, timedelta

import pandas as pd

from database import (
    get_daily_study_goal,
    get_scheduled_tests,
    get_setting,
    get_study_hours_for_date,
    get_study_hours_map,
    score_percentage,
    set_setting,
)

HARVEST_KEY = "last_harvest_tier"
MAX_TREES_KEY = "max_unlocked_trees"
SAKURA_SCORE_MIN = 60

# 220 days prelims → ~55 trees; +90 days mains sprint → ~22 more
PRELIMS_PREP_DAYS = 220
MAINS_SPRINT_DAYS = 90
STREAK_DAYS_PER_TREE = 4
PRELIMS_TREE_TARGET = PRELIMS_PREP_DAYS // STREAK_DAYS_PER_TREE  # 55
MAX_GROVE_TREES = PRELIMS_TREE_TARGET + (MAINS_SPRINT_DAYS // STREAK_DAYS_PER_TREE)  # 77
STREAK_LOOKBACK_DAYS = PRELIMS_PREP_DAYS + MAINS_SPRINT_DAYS + 30

HARVEST_TIERS = (
    {"id": "sprout", "min_days": 0, "emoji": "🌱", "label": "First Tree", "min_trees": 1},
    {"id": "grove", "min_days": 4, "emoji": "🌳", "label": "Second Tree", "min_trees": 2},
    {"id": "bloom", "min_days": 6, "emoji": "🌸", "label": "Cherry Bloom", "min_trees": 2},
    {"id": "golden", "min_days": 7, "emoji": "🏆", "label": "Golden Grove", "min_trees": 2},
)

# Product rules (also used by Godot / garden_api):
# 4 complete days → permanent tree · 6-day live streak → bloom · test >60% → fruit
BLOOM_STREAK_DAYS = 6
FRUIT_SCORE_MIN = SAKURA_SCORE_MIN


def get_goal_streak(today=None):
    """Consecutive complete goal-days (ending today or yesterday)."""
    if today is None:
        today = date.today()
    goal = float(get_daily_study_goal())
    hours_map = get_study_hours_map(today - timedelta(days=STREAK_LOOKBACK_DAYS), today)
    cursor = today
    if hours_map.get(today, 0) < goal:
        cursor = today - timedelta(days=1)
    streak = 0
    while cursor >= today - timedelta(days=STREAK_LOOKBACK_DAYS):
        if hours_map.get(cursor, 0) >= goal:
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break
    return streak


def count_complete_goal_days(today=None):
    """Lifetime lifetime days where study hours met the daily goal.

    Trees unlock from this total — they do NOT shrink when a streak breaks.
    """
    if today is None:
        today = date.today()
    goal = float(get_daily_study_goal())
    hours_map = get_study_hours_map(today - timedelta(days=STREAK_LOOKBACK_DAYS), today)
    return sum(1 for hours in hours_map.values() if hours >= goal)


def get_week_goal_days(today=None):
    if today is None:
        today = date.today()
    goal = float(get_daily_study_goal())
    hours_map = get_study_hours_map(today - timedelta(days=6), today)
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        hours = hours_map.get(d, 0)
        if hours >= goal:
            status = "complete"
        elif hours > 0:
            status = "partial"
        else:
            status = "empty"
        days.append({"date": d.isoformat(), "hours": hours, "status": status})
    return days


def _computed_tree_count(complete_days):
    """1 tree at start; +1 every 4 complete goal-days."""
    return min(MAX_GROVE_TREES, max(1, 1 + int(complete_days) // STREAK_DAYS_PER_TREE))


def unlocked_tree_count(complete_days=None, today=None):
    """Trees planted from cumulative complete goal-days (high-water mark).

    Accepts either a complete-day total or (legacy) a streak integer for callers
    that still pass streak by position — prefer passing complete_days explicitly.
    """
    if complete_days is None:
        complete_days = count_complete_goal_days(today)
    computed = _computed_tree_count(complete_days)
    try:
        stored = int(get_setting(MAX_TREES_KEY, "1") or 1)
    except (TypeError, ValueError):
        stored = 1
    unlocked = max(1, min(MAX_GROVE_TREES, max(computed, stored)))
    if unlocked > stored:
        set_setting(MAX_TREES_KEY, str(unlocked))
    return unlocked


def _tree_phase(tree_no):
    return "prelims" if tree_no <= PRELIMS_TREE_TARGET else "mains"


def _tests_by_no():
    df = get_scheduled_tests().sort_values("test_no")
    return {int(r["test_no"]): r for _, r in df.iterrows()}


def _tree_growth(complete_days, tree_no, has_flowers, has_fruit):
    """Growth stage from permanent progress (not today's streak)."""
    if has_fruit:
        return "fruiting"
    if has_flowers:
        return "sakura"  # bloomed canopy (legacy key used by map)
    # Tree N unlocks at (N-1)*4 complete days; maturity builds from there.
    unlock_at = max(0, (tree_no - 1) * STREAK_DAYS_PER_TREE)
    days_since_unlock = max(0, int(complete_days) - unlock_at)
    if days_since_unlock >= STREAK_DAYS_PER_TREE:
        return "mature"
    if days_since_unlock >= 2:
        return "young"
    return "sapling"


def _tree_meta(tree_no, test_row, complete_days, water, goal_streak, unlocked):
    """
    Permanent milestone tree.

    - has_fruit: matching test score > 60%
    - has_flowers / has_sakura: bloomed canopy (mature arc, or live 6-day streak
      on the newest tree)
    """
    phase = _tree_phase(tree_no)

    score_val = None
    test_no = None
    subject = ""
    topic = ""
    kind = "block"

    if test_row is not None:
        test_no = int(test_row["test_no"])
        kind = "test"
        subject = str(test_row.get("subject") or "")
        topic = str(test_row.get("topic_focus") or "")
        if test_row.get("status") == "Attempted":
            raw = test_row.get("score")
            if raw is not None and not pd.isna(raw):
                max_raw = test_row.get("max_score")
                pct = score_percentage(raw, max_raw)
                # Prefer % of total marks; fall back to raw value if Out of is missing
                score_val = pct if pct is not None else round(float(raw), 1)
    else:
        if phase == "prelims":
            subject = f"Prelims Block {tree_no}"
            topic = (
                f"Study arc · days {(tree_no - 1) * STREAK_DAYS_PER_TREE + 1}"
                f"–{tree_no * STREAK_DAYS_PER_TREE}"
            )
        else:
            block = tree_no - PRELIMS_TREE_TARGET
            subject = f"Mains Sprint {block}"
            topic = f"Post-prelims · block {block}"

    # Shiny fruit = weekly/block test > 60%
    has_fruit = score_val is not None and score_val > FRUIT_SCORE_MIN

    unlock_at = max(0, (tree_no - 1) * STREAK_DAYS_PER_TREE)
    days_since = max(0, int(complete_days) - unlock_at)
    matured = days_since >= STREAK_DAYS_PER_TREE
    is_newest = tree_no == unlocked
    bloom_from_streak = is_newest and int(goal_streak) >= BLOOM_STREAK_DAYS
    # Permanent trees that matured keep a soft bloom; live 6-day streak blooms newest
    has_flowers = matured or bloom_from_streak or has_fruit

    return {
        "tree_no": tree_no,
        "test_no": test_no,
        "kind": kind,
        "phase": phase,
        "subject": subject,
        "topic": topic,
        "score": score_val,
        "has_sakura": has_flowers,  # map/legacy: pink bloom canopy
        "has_flowers": has_flowers,
        "has_fruit": has_fruit,
        "water": round(water, 3),
        "growth": _tree_growth(complete_days, tree_no, has_flowers, has_fruit),
        "slot": tree_no - 1,
        "permanent": True,
        "wilted": False,
    }


def build_study_trees(today=None):
    """Build unlocked trees along the 220-day prelims → 90-day mains journey."""
    if today is None:
        today = date.today()

    goal_streak = get_goal_streak(today)
    complete_days = count_complete_goal_days(today)
    goal = float(get_daily_study_goal())
    today_hours = float(get_study_hours_for_date(today) or 0)
    water = min(1.0, today_hours / goal) if goal > 0 else 0.0
    unlocked = unlocked_tree_count(complete_days)
    tests = _tests_by_no()
    test_count = len(tests)

    trees = []
    for tree_no in range(1, unlocked + 1):
        test_row = tests.get(tree_no) if tree_no <= test_count else None
        trees.append(
            _tree_meta(tree_no, test_row, complete_days, water, goal_streak, unlocked)
        )

    if unlocked < MAX_GROVE_TREES:
        days_to_next_tree = max(0, unlocked * STREAK_DAYS_PER_TREE - complete_days)
    else:
        days_to_next_tree = 0

    next_tree = None
    if unlocked < MAX_GROVE_TREES:
        nxt_no = unlocked + 1
        test_row = tests.get(nxt_no) if nxt_no <= test_count else None
        meta = _tree_meta(nxt_no, test_row, complete_days, water, goal_streak, unlocked)
        next_tree = {
            "tree_no": nxt_no,
            "test_no": meta["test_no"],
            "subject": meta["subject"],
            "phase": meta["phase"],
            "days_away": days_to_next_tree,
        }

    return trees, unlocked, days_to_next_tree, next_tree, complete_days, goal_streak


def _harvest_tier(goal_streak, complete_days):
    """Permanent grove from total complete days; bloom/golden need live streak."""
    tier = HARVEST_TIERS[0]
    for candidate in HARVEST_TIERS:
        if candidate["id"] in ("bloom", "fruit", "golden"):
            if goal_streak >= candidate["min_days"]:
                tier = candidate
        elif max(goal_streak, complete_days) >= candidate["min_days"]:
            tier = candidate
    return tier


def sync_garden_life(today=None):
    if today is None:
        today = date.today()

    goal = float(get_daily_study_goal())
    today_hours = float(get_study_hours_for_date(today) or 0)
    goal_streak = get_goal_streak(today)
    complete_days = count_complete_goal_days(today)
    week = get_week_goal_days(today)
    complete_this_week = sum(1 for d in week if d["status"] == "complete")

    trees, unlocked, days_to_next_tree, next_tree, complete_days, goal_streak = (
        build_study_trees(today)
    )
    sakura_count = sum(1 for t in trees if t.get("has_flowers") or t.get("has_sakura"))
    fruit_count = sum(1 for t in trees if t.get("has_fruit"))
    prelims_trees = min(unlocked, PRELIMS_TREE_TARGET)

    life = 28
    for d in week:
        if d["status"] == "complete":
            life += 10
        elif d["status"] == "partial":
            life += 3
    life = min(100, life)

    tier = _harvest_tier(goal_streak, complete_days)
    goal_met_today = today_hours >= goal
    has_bloom = goal_streak >= BLOOM_STREAK_DAYS
    has_fruit_any = fruit_count > 0
    water_pct = int(min(100, (today_hours / goal) * 100)) if goal > 0 else 0

    # Active / in-progress sprout (not a permanent milestone yet)
    rem = goal_streak % STREAK_DAYS_PER_TREE if goal_streak > 0 else 0
    if goal_streak > 0 and rem == 0:
        active_tree = {"progress_days": 0, "wilted": False, "visible": False}
    elif goal_streak > 0:
        active_tree = {"progress_days": rem, "wilted": False, "visible": True}
    else:
        # Streak broken — only the in-progress sprout wilts; permanent trees stay lush
        active_tree = {"progress_days": 1, "wilted": True, "visible": True}

    journey_phase = "prelims" if unlocked <= PRELIMS_TREE_TARGET else "mains"
    trees_to_prelims_full = max(0, PRELIMS_TREE_TARGET - unlocked)

    if goal_met_today:
        mood = "flourishing"
        hint = (
            f"{goal_streak}-day goal streak · {complete_days} complete day(s) total · "
            f"{unlocked}/{MAX_GROVE_TREES} trees planted. "
            f"Prelims path: {prelims_trees}/{PRELIMS_TREE_TARGET}."
        )
    elif today_hours > 0:
        remaining = max(0, goal - today_hours)
        hint = (
            f"Watering {water_pct}% — {remaining:g}h more to hit today's {goal:g}h goal. "
            f"Grove: {unlocked} tree{'s' if unlocked != 1 else ''} from "
            f"{complete_days} complete day(s)."
        )
        mood = "growing"
    elif goal_streak > 0:
        mood = "thirsty"
        hint = (
            "Trees are thirsty — log study hours before midnight to protect your "
            f"{goal_streak}-day goal streak (needs full {goal:g}h)."
        )
    else:
        mood = "resting"
        hint = (
            f"Trees grow from complete days (full {goal:g}h goal), not partial logs. "
            f"You have {complete_days} complete day(s) · {unlocked} tree(s). "
            f"Every {STREAK_DAYS_PER_TREE} complete days plants the next tree."
        )

    if days_to_next_tree > 0 and next_tree:
        hint += f" · {days_to_next_tree} more complete day(s) until tree #{next_tree['tree_no']}."

    # Next permanent harvest tier from complete days; bloom/golden use streak
    next_tier = None
    days_to_next_tier = 0
    for candidate in HARVEST_TIERS:
        if candidate["id"] in ("bloom", "fruit", "golden"):
            if goal_streak < candidate["min_days"]:
                next_tier = candidate
                days_to_next_tier = candidate["min_days"] - goal_streak
                break
        elif max(goal_streak, complete_days) < candidate["min_days"]:
            next_tier = candidate
            days_to_next_tier = candidate["min_days"] - max(goal_streak, complete_days)
            break

    return {
        "life": life,
        "mood": mood,
        "goal_streak": goal_streak,
        "complete_days": complete_days,
        "harvest_tier": tier["id"],
        "harvest_label": tier["label"],
        "harvest_emoji": tier["emoji"],
        "trees": trees,
        "tree_count": len(trees),
        "unlocked_count": unlocked,
        "max_trees": MAX_GROVE_TREES,
        "prelims_target": PRELIMS_TREE_TARGET,
        "mains_slots": MAX_GROVE_TREES - PRELIMS_TREE_TARGET,
        "prelims_trees": prelims_trees,
        "trees_to_prelims_full": trees_to_prelims_full,
        "journey_phase": journey_phase,
        "has_fruit": has_fruit_any,
        "has_bloom": has_bloom,
        "has_flowers": sakura_count > 0,
        "sakura_count": sakura_count,
        "fruit_count": fruit_count,
        "active_tree": active_tree,
        "water_level": min(1.0, today_hours / goal) if goal > 0 else 0.0,
        "water_pct": water_pct,
        "today_hours": today_hours,
        "daily_goal": goal,
        "goal_met": goal_met_today,
        "week_days": week,
        "complete_this_week": complete_this_week,
        "days_to_next_tier": days_to_next_tier,
        "days_to_next_tree": days_to_next_tree,
        "next_tree": next_tree,
        "next_tier_label": next_tier["label"] if next_tier else "Max harvest",
        "hint": hint,
        "rules": (
            "4 complete days plant a permanent tree · "
            "6-day streak blooms cherry blossoms · "
            ">60% test adds shiny fruit · "
            "streak break only wilts the active sprout"
        ),
    }


_TIER_ALIASES = {"bloom": "bloom", "fruit": "bloom"}  # legacy fruit tier → bloom


def pop_harvest_unlocks(today=None):
    life = sync_garden_life(today)
    prev_raw = get_setting(HARVEST_KEY, None)
    prev = _TIER_ALIASES.get(prev_raw, prev_raw)
    current = life["harvest_tier"]
    if prev is None:
        set_setting(HARVEST_KEY, current)
        return None
    order = {t["id"]: i for i, t in enumerate(HARVEST_TIERS)}
    # Treat legacy "fruit" as bloom
    prev_order = order.get(prev, order.get("bloom", 0) if prev == "fruit" else 0)
    if order.get(current, 0) <= prev_order:
        return None
    set_setting(HARVEST_KEY, current)
    messages = {
        "grove": "4 complete goal-days — another tree joins your prelims path! 🌳",
        "bloom": "6-day goal streak — cherry blossoms on your newest tree! 🌸",
        "fruit": "6-day goal streak — cherry blossoms on your newest tree! 🌸",
        "golden": "7 perfect goal-days — golden hour over the whole grove! 🏆",
    }
    return {
        "tier": current,
        "emoji": life["harvest_emoji"],
        "label": life["harvest_label"],
        "message": messages.get(current, f"Grove milestone: {life['harvest_label']}"),
    }
