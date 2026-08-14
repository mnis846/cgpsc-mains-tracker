"""Syllabus Atlas — hierarchical topics, mastery states, spaced revision."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from database import DatabaseError, add_garden_xp, db_connection, get_setting, set_setting
from atlas_syllabus import ATLAS_SEED_VERSION, iter_nodes

STATES = ("unseen", "scouted", "mapped", "held", "fortified")
STATE_RANK = {name: idx for idx, name in enumerate(STATES)}

STATE_META = {
    "unseen": {"label": "Fog", "short": "Fog", "verb": "Scout"},
    "scouted": {"label": "Scouted", "short": "Scout", "verb": "Map"},
    "mapped": {"label": "Mapped", "short": "Notes", "verb": "Hold"},
    "held": {"label": "Held", "short": "Held", "verb": "Fortify"},
    "fortified": {"label": "Fortified", "short": "Master", "verb": "Drill"},
}

ACTIONS = {
    "scout": "scouted",
    "map": "mapped",
    "revise": "held",
    "fortify": "fortified",
}

# SM-2-lite intervals in days
INTERVALS = (1, 3, 7, 15, 30, 45)

# Visual mastery: yellow first-pass → forest when 10-mark ready
MASTERY_WEIGHT = {
    "unseen": 0.0,
    "scouted": 0.28,
    "mapped": 0.52,
    "held": 0.78,
    "fortified": 1.0,
}
# Days overdue for colour to lose half its saturation
DECAY_HALF_LIFE_DAYS = 18
DECAY_FLOOR = 0.12

XP_FOR_FIRST_REACH = {
    "scouted": 12,
    "mapped": 8,
    "held": 10,
    "fortified": 20,
}
XP_REVISE_REPEAT = 4
SEED_FLAG = "atlas_seed_version"

def _date_str(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def ensure_atlas():
    """Create tables and upsert the seed tree. Safe to call on every boot."""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS atlas_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                parent_slug TEXT,
                title TEXT NOT NULL,
                paper TEXT DEFAULT '',
                kind TEXT NOT NULL,
                accent TEXT DEFAULT 'accent',
                sort_order INTEGER DEFAULT 0,
                is_custom INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS atlas_progress (
                node_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL DEFAULT 'unseen',
                confidence INTEGER DEFAULT 0,
                last_studied DATE,
                next_due DATE,
                revision_count INTEGER DEFAULT 0,
                study_count INTEGER DEFAULT 0,
                last_note TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node_id) REFERENCES atlas_nodes(id) ON DELETE CASCADE
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS atlas_study_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                log_date DATE NOT NULL,
                action TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT,
                confidence INTEGER,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node_id) REFERENCES atlas_nodes(id) ON DELETE CASCADE
            )"""
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_atlas_nodes_parent ON atlas_nodes(parent_slug)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_atlas_nodes_kind ON atlas_nodes(kind)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_atlas_progress_due ON atlas_progress(next_due)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_atlas_log_date ON atlas_study_log(log_date)"
        )
    _seed_tree()


def _seed_tree():
    current = get_setting(SEED_FLAG, "")
    # Always upsert seed nodes so new slugs land without wiping progress.
    rows = [
        (
            node["slug"],
            node["parent_slug"],
            node["title"],
            node["paper"],
            node["kind"],
            node["accent"],
            node["sort_order"],
        )
        for node in iter_nodes()
    ]
    with db_connection() as conn:
        c = conn.cursor()
        c.executemany(
            """INSERT INTO atlas_nodes
               (slug, parent_slug, title, paper, kind, accent, sort_order, is_custom)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)
               ON CONFLICT(slug) DO UPDATE SET
                   parent_slug = excluded.parent_slug,
                   title = CASE
                       WHEN atlas_nodes.is_custom = 1 THEN atlas_nodes.title
                       ELSE excluded.title
                   END,
                   paper = excluded.paper,
                   kind = excluded.kind,
                   accent = excluded.accent,
                   sort_order = excluded.sort_order
            """,
            rows,
        )
    if str(current) != str(ATLAS_SEED_VERSION):
        set_setting(SEED_FLAG, str(ATLAS_SEED_VERSION))


def _row_to_node(row, progress=None):
    node = dict(row)
    prog = progress or {}
    state = prog.get("state") or "unseen"
    node["state"] = state
    node["state_label"] = STATE_META[state]["label"]
    node["confidence"] = int(prog.get("confidence") or 0)
    node["last_studied"] = _parse_date(prog.get("last_studied"))
    node["next_due"] = _parse_date(prog.get("next_due"))
    node["revision_count"] = int(prog.get("revision_count") or 0)
    node["study_count"] = int(prog.get("study_count") or 0)
    node["last_note"] = prog.get("last_note") or ""
    node["is_custom"] = bool(node.get("is_custom"))
    return node


def _progress_map(conn, node_ids: Iterable[int]) -> dict[int, dict]:
    ids = [int(i) for i in node_ids]
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM atlas_progress WHERE node_id IN ({placeholders})",
        ids,
    ).fetchall()
    return {int(row["node_id"]): dict(row) for row in rows}


def get_regions():
    ensure_atlas()
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT * FROM atlas_nodes
               WHERE kind = 'region' AND archived = 0
               ORDER BY sort_order, id"""
        ).fetchall()
    return [dict(row) for row in rows]


def get_units(region_slug):
    ensure_atlas()
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT * FROM atlas_nodes
               WHERE parent_slug = ? AND kind = 'unit' AND archived = 0
               ORDER BY sort_order, id""",
            (region_slug,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_node(slug):
    ensure_atlas()
    with db_connection(commit=False) as conn:
        row = conn.execute(
            "SELECT * FROM atlas_nodes WHERE slug = ?", (slug,)
        ).fetchone()
        if not row:
            return None
        prog = _progress_map(conn, [row["id"]]).get(row["id"])
    return _row_to_node(row, prog)


def get_topics(unit_slug):
    ensure_atlas()
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT * FROM atlas_nodes
               WHERE parent_slug = ? AND kind = 'topic' AND archived = 0
               ORDER BY sort_order, id""",
            (unit_slug,),
        ).fetchall()
        progress = _progress_map(conn, [r["id"] for r in rows])
    return [_row_to_node(row, progress.get(row["id"])) for row in rows]


def search_topics(query, limit=40):
    ensure_atlas()
    q = (query or "").strip()
    if not q:
        return []
    like = f"%{q}%"
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT n.*, p.title AS parent_title, g.title AS region_title
               FROM atlas_nodes n
               LEFT JOIN atlas_nodes p ON p.slug = n.parent_slug
               LEFT JOIN atlas_nodes g ON g.slug = p.parent_slug
               WHERE n.kind = 'topic' AND n.archived = 0
                 AND (n.title LIKE ? OR p.title LIKE ? OR g.title LIKE ?)
               ORDER BY n.title
               LIMIT ?""",
            (like, like, like, int(limit)),
        ).fetchall()
        progress = _progress_map(conn, [r["id"] for r in rows])
    results = []
    for row in rows:
        node = _row_to_node(row, progress.get(row["id"]))
        node["parent_title"] = row["parent_title"] or ""
        node["region_title"] = row["region_title"] or ""
        results.append(node)
    return results


def _topic_rows_with_lineage(conn):
    return conn.execute(
        """SELECT n.*, u.slug AS unit_slug, u.title AS unit_title,
                  r.slug AS region_slug, r.title AS region_title, r.accent AS region_accent
           FROM atlas_nodes n
           JOIN atlas_nodes u ON u.slug = n.parent_slug AND u.kind = 'unit'
           JOIN atlas_nodes r ON r.slug = u.parent_slug AND r.kind = 'region'
           WHERE n.kind = 'topic' AND n.archived = 0
           ORDER BY r.sort_order, u.sort_order, n.sort_order, n.id"""
    ).fetchall()


def get_all_topics():
    ensure_atlas()
    with db_connection(commit=False) as conn:
        rows = _topic_rows_with_lineage(conn)
        progress = _progress_map(conn, [r["id"] for r in rows])
    topics = []
    for row in rows:
        node = _row_to_node(row, progress.get(row["id"]))
        node["unit_slug"] = row["unit_slug"]
        node["unit_title"] = row["unit_title"]
        node["region_slug"] = row["region_slug"]
        node["region_title"] = row["region_title"]
        node["accent"] = row["region_accent"] or node.get("accent") or "accent"
        topics.append(node)
    return topics


def _coverage_from_states(states: list[str]) -> dict:
    total = len(states)
    counts = {name: 0 for name in STATES}
    for state in states:
        counts[state if state in counts else "unseen"] += 1
    touched = total - counts["unseen"]
    weighted = (
        counts["scouted"] * 0.25
        + counts["mapped"] * 0.5
        + counts["held"] * 0.8
        + counts["fortified"] * 1.0
    )
    return {
        "total": total,
        "counts": counts,
        "touched": touched,
        "unseen": counts["unseen"],
        "fortified": counts["fortified"],
        "coverage": round((touched / total) * 100, 1) if total else 0.0,
        "mastery": round((weighted / total) * 100, 1) if total else 0.0,
    }


def get_unit_summaries(region_slug=None):
    topics = get_all_topics()
    if region_slug:
        topics = [t for t in topics if t["region_slug"] == region_slug]
    grouped: dict[str, list] = {}
    meta = {}
    for topic in topics:
        key = topic["unit_slug"]
        grouped.setdefault(key, []).append(topic)
        meta[key] = {
            "slug": key,
            "title": topic["unit_title"],
            "region_slug": topic["region_slug"],
            "region_title": topic["region_title"],
            "accent": topic["accent"],
        }
    summaries = []
    for slug, unit_topics in grouped.items():
        info = meta[slug]
        cov = _coverage_from_states([t["state"] for t in unit_topics])
        due = sum(1 for t in unit_topics if _is_due(t))
        summaries.append({**info, **cov, "due": due, "topics": unit_topics})
    summaries.sort(key=lambda s: (s["region_title"], s["title"]))
    return summaries


def get_region_summaries():
    topics = get_all_topics()
    grouped: dict[str, list] = {}
    meta = {}
    for topic in topics:
        key = topic["region_slug"]
        grouped.setdefault(key, []).append(topic)
        meta[key] = {
            "slug": key,
            "title": topic["region_title"],
            "accent": topic["accent"],
            "paper": topic.get("paper") or "",
        }
    summaries = []
    for slug, region_topics in grouped.items():
        info = meta[slug]
        cov = _coverage_from_states([t["state"] for t in region_topics])
        due = sum(1 for t in region_topics if _is_due(t))
        summaries.append({**info, **cov, "due": due})
    summaries.sort(key=lambda s: s["title"])
    return summaries


def get_atlas_overview(today=None):
    today = today or date.today()
    topics = get_all_topics()
    cov = _coverage_from_states([t["state"] for t in topics])
    due = [t for t in topics if _is_due(t, today)]
    overdue = [t for t in due if t["next_due"] and t["next_due"] < today]
    units = get_unit_summaries()
    blind = [u for u in units if u["touched"] == 0]
    return {
        **cov,
        "due_today": len(due),
        "overdue": len(overdue),
        "blind_units": len(blind),
        "units": len(units),
        "regions": len(get_regions()),
    }


def _is_due(topic, today=None):
    today = today or date.today()
    if topic["state"] == "unseen":
        return False
    due = topic.get("next_due")
    return due is not None and due <= today


def topic_vitality(topic, today=None):
    """Mastery × freshness. Untouched nodes bleach; drilled ones stay dark green."""
    today = today or date.today()
    state = topic.get("state") or "unseen"
    mastery = MASTERY_WEIGHT.get(state, 0.0)
    conf = int(topic.get("confidence") or 0)
    if mastery > 0 and conf:
        mastery = min(1.0, mastery + (conf - 3) * 0.03)

    last = topic.get("last_studied")
    due = topic.get("next_due")
    overdue_days = 0
    if state == "unseen" or not last:
        decay = 0.0 if state == "unseen" else DECAY_FLOOR
    elif due and today <= due:
        decay = 1.0
    else:
        if due:
            overdue_days = max(0, (today - due).days)
        else:
            overdue_days = max(0, (today - last).days)
        decay = max(DECAY_FLOOR, 0.5 ** (overdue_days / DECAY_HALF_LIFE_DAYS))

    return {
        "mastery": round(mastery, 3),
        "decay": round(decay, 3),
        "vitality": round(mastery * (decay if state != "unseen" else 0.0), 3),
        "overdue_days": overdue_days,
        "fresh": decay >= 0.92 and mastery > 0,
        "fading": decay < 0.7 and mastery > 0,
    }


def next_interval_days(revision_count, confidence):
    index = max(0, min(int(revision_count), len(INTERVALS) - 1))
    if confidence and confidence <= 2:
        index = max(0, index - 1)
    elif confidence and confidence >= 4:
        index = min(len(INTERVALS) - 1, index + 1)
    return INTERVALS[index]


def _already_awarded_today(node_id, action, today):
    with db_connection(commit=False) as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS n FROM atlas_study_log
               WHERE node_id = ? AND action = ? AND log_date = ?""",
            (int(node_id), action, _date_str(today)),
        ).fetchone()
    return int(row["n"] or 0) > 0


def record_study(slug, action, *, confidence=3, note="", today=None, log_activity=True):
    """Advance (or refresh) a topic. Returns {node, reward, changed}."""
    if action not in ACTIONS:
        raise DatabaseError(f"Unknown atlas action: {action}")
    today = today or date.today()
    node = get_node(slug)
    if not node or node["kind"] != "topic":
        raise DatabaseError("Topic not found.")

    target = ACTIONS[action]
    from_state = node["state"]
    to_state = target if STATE_RANK[target] >= STATE_RANK[from_state] else from_state
    conf = max(0, min(int(confidence or 0), 5))
    note = (note or "").strip()

    new_revision = int(node["revision_count"] or 0)
    if action in ("revise", "fortify"):
        new_revision += 1
    interval = next_interval_days(new_revision, conf or 3)
    next_due = today + timedelta(days=interval)
    already_today = _already_awarded_today(node["id"], action, today)

    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO atlas_progress
               (node_id, state, confidence, last_studied, next_due,
                revision_count, study_count, last_note, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(node_id) DO UPDATE SET
                   state = excluded.state,
                   confidence = excluded.confidence,
                   last_studied = excluded.last_studied,
                   next_due = excluded.next_due,
                   revision_count = excluded.revision_count,
                   study_count = atlas_progress.study_count + 1,
                   last_note = CASE
                       WHEN excluded.last_note = '' THEN atlas_progress.last_note
                       ELSE excluded.last_note
                   END,
                   updated_at = CURRENT_TIMESTAMP
            """,
            (
                node["id"],
                to_state,
                conf,
                _date_str(today),
                _date_str(next_due),
                new_revision,
                note,
            ),
        )
        c.execute(
            """INSERT INTO atlas_study_log
               (node_id, log_date, action, from_state, to_state, confidence, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                node["id"],
                _date_str(today),
                action,
                from_state,
                to_state,
                conf or None,
                note,
            ),
        )

    reward = _award_atlas_xp(
        node, action, from_state, to_state, already_today=already_today
    )

    if log_activity:
        try:
            from logbook import add_activity_log

            verb = {
                "scout": "first pass",
                "map": "notes",
                "revise": "revised",
                "fortify": "mastered",
            }[action]
            lineage = _lineage_label(slug)
            add_activity_log(
                today,
                f"Atlas · {lineage} — {verb}",
                node.get("paper") or "",
                None,
            )
        except Exception:
            pass

    updated = get_node(slug)
    return {
        "node": updated,
        "reward": reward,
        "changed": from_state != to_state,
        "from_state": from_state,
        "to_state": to_state,
        "next_due": next_due,
    }


def _lineage_label(slug):
    node = get_node(slug)
    if not node:
        return slug
    parts = [node["title"]]
    parent = node.get("parent_slug")
    if parent:
        unit = get_node(parent)
        if unit:
            parts.insert(0, unit["title"])
            if unit.get("parent_slug"):
                region = get_node(unit["parent_slug"])
                if region:
                    parts.insert(0, region["title"])
    return " · ".join(parts)


def _award_atlas_xp(node, action, from_state, to_state, *, already_today=False):
    xp = 0
    message = ""
    if STATE_RANK[to_state] > STATE_RANK[from_state]:
        xp = XP_FOR_FIRST_REACH.get(to_state, 0)
        label = STATE_META[to_state]["label"]
        message = f"Atlas · {node['title']} is now {label}"
    elif not already_today:
        xp = XP_REVISE_REPEAT
        message = f"Atlas drill · {node['title']}"
    if xp <= 0:
        return None
    add_garden_xp(xp, f"atlas_{action}", message)
    return {"xp": xp, "message": message}


def save_topic_details(slug, *, note=None, confidence=None):
    """Write notes / confidence without changing mastery or due date."""
    node = get_node(slug)
    if not node or node["kind"] != "topic":
        raise DatabaseError("Topic not found.")
    note_val = None if note is None else (note or "").strip()
    conf_val = None if confidence is None else max(0, min(int(confidence), 5))
    with db_connection() as conn:
        conn.execute(
            """INSERT INTO atlas_progress
               (node_id, last_note, confidence, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(node_id) DO UPDATE SET
                   last_note = COALESCE(?, atlas_progress.last_note),
                   confidence = COALESCE(?, atlas_progress.confidence),
                   updated_at = CURRENT_TIMESTAMP""",
            (
                node["id"],
                note_val or "",
                conf_val or 0,
                note_val,
                conf_val,
            ),
        )
    return get_node(slug)


def snooze_topic(slug, days=1, today=None):
    today = today or date.today()
    node = get_node(slug)
    if not node:
        raise DatabaseError("Topic not found.")
    due = today + timedelta(days=max(1, int(days)))
    with db_connection() as conn:
        conn.execute(
            """INSERT INTO atlas_progress (node_id, next_due, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(node_id) DO UPDATE SET
                   next_due = excluded.next_due,
                   updated_at = CURRENT_TIMESTAMP""",
            (node["id"], _date_str(due)),
        )
    return due


def reset_topic(slug):
    node = get_node(slug)
    if not node:
        raise DatabaseError("Topic not found.")
    with db_connection() as conn:
        conn.execute("DELETE FROM atlas_progress WHERE node_id = ?", (node["id"],))
    return get_node(slug)


def add_custom_topic(title, unit_slug, paper=""):
    title = (title or "").strip()
    if not title:
        raise DatabaseError("Topic title cannot be empty.")
    unit = get_node(unit_slug)
    if not unit or unit["kind"] != "unit":
        raise DatabaseError("Pick a unit to place this topic under.")
    from uuid import uuid4

    slug = f"custom.{uuid4().hex[:10]}"
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COALESCE(MAX(sort_order), -1) FROM atlas_nodes WHERE parent_slug = ?",
            (unit_slug,),
        )
        next_order = int(c.fetchone()[0]) + 1
        c.execute(
            """INSERT INTO atlas_nodes
               (slug, parent_slug, title, paper, kind, accent, sort_order, is_custom)
               VALUES (?, ?, ?, ?, 'topic', ?, ?, 1)""",
            (
                slug,
                unit_slug,
                title,
                paper or unit.get("paper") or "",
                unit.get("accent") or "accent",
                next_order,
            ),
        )
    return get_node(slug)


def add_custom_unit(title, region_slug):
    title = (title or "").strip()
    if not title:
        raise DatabaseError("Unit title cannot be empty.")
    region = get_node(region_slug)
    if not region or region["kind"] != "region":
        raise DatabaseError("Pick a region for this unit.")
    from uuid import uuid4

    slug = f"custom.unit.{uuid4().hex[:8]}"
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COALESCE(MAX(sort_order), -1) FROM atlas_nodes WHERE parent_slug = ?",
            (region_slug,),
        )
        next_order = int(c.fetchone()[0]) + 1
        c.execute(
            """INSERT INTO atlas_nodes
               (slug, parent_slug, title, paper, kind, accent, sort_order, is_custom)
               VALUES (?, ?, ?, ?, 'unit', ?, ?, 1)""",
            (
                slug,
                region_slug,
                title,
                region.get("paper") or "",
                region.get("accent") or "accent",
                next_order,
            ),
        )
    return get_node(slug)


def archive_custom_node(slug):
    node = get_node(slug)
    if not node:
        raise DatabaseError("Not found.")
    if not node["is_custom"]:
        raise DatabaseError("Seeded syllabus topics stay on the map.")
    with db_connection() as conn:
        conn.execute(
            "UPDATE atlas_nodes SET archived = 1 WHERE slug = ?", (slug,)
        )


def get_expedition(today=None, explore=3, hold=3):
    """Today's mix: dark corners to open + territory due for holding."""
    today = today or date.today()
    topics = get_all_topics()
    units = {u["slug"]: u for u in get_unit_summaries()}

    unseen = [t for t in topics if t["state"] == "unseen"]
    unseen.sort(
        key=lambda t: (
            units.get(t["unit_slug"], {}).get("coverage", 0),
            -int(units.get(t["unit_slug"], {}).get("total") or 0),
            t["region_title"],
            t["unit_title"],
            t["sort_order"],
        )
    )

    due = [t for t in topics if _is_due(t, today)]
    due.sort(key=lambda t: (t["next_due"] or today, -STATE_RANK[t["state"]]))

    # If nothing is due yet, surface weakest recently-touched topics.
    if not due:
        weak = [
            t
            for t in topics
            if t["state"] in ("scouted", "mapped") and t.get("last_studied")
        ]
        weak.sort(key=lambda t: t["last_studied"] or today)
        due = weak

    return {
        "explore": unseen[:explore],
        "hold": due[:hold],
        "explore_left": max(0, len(unseen) - explore),
        "hold_left": max(0, len(due) - hold),
    }


def get_due_topics(today=None, limit=20):
    today = today or date.today()
    due = [t for t in get_all_topics() if _is_due(t, today)]
    due.sort(key=lambda t: (t["next_due"] or today, t["title"]))
    return due[:limit]


def get_blind_units(limit=8):
    blinds = [u for u in get_unit_summaries() if u["touched"] == 0]
    blinds.sort(key=lambda u: (u["region_title"], u["title"]))
    return blinds[:limit]


def get_recent_atlas_log(limit=12):
    ensure_atlas()
    with db_connection(commit=False) as conn:
        rows = conn.execute(
            """SELECT l.log_date, l.action, l.to_state, l.note, n.title, n.slug,
                      u.title AS unit_title
               FROM atlas_study_log l
               JOIN atlas_nodes n ON n.id = l.node_id
               LEFT JOIN atlas_nodes u ON u.slug = n.parent_slug
               ORDER BY l.id DESC
               LIMIT ?""",
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]
