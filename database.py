import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from profile import FIRST_NAME


def resolve_data_dir():
    """Return a writable directory for the SQLite database."""
    override = os.environ.get("TRACKER_DATA_DIR")
    if override:
        path = Path(override)
    else:
        try:
            from android.storage import app_storage_path

            path = Path(app_storage_path())
        except ImportError:
            path = Path(__file__).resolve().parent
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path():
    return str(resolve_data_dir() / "cgpsc_mains_tracker.db")


DB_PATH = get_db_path()
_UNSET = object()
DEFAULT_DAILY_GOAL_HOURS = 6.0


class DatabaseError(Exception):
    """Raised when a SQLite operation fails."""


def get_conn():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


@contextmanager
def db_connection(*, commit=True):
    conn = get_conn()
    try:
        yield conn
        if commit:
            conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise DatabaseError(str(exc)) from exc
    finally:
        conn.close()


def _date_str(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _parse_log_date(value):
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def default_max_score(test_type, *, series="mains"):
    """Sensible default total marks by series/type.

    Mains: FLT 200, sectional 100.
    Prelims: full mocks (GS/CSAT FLT) 200, sectionals 100.
    """
    kind = (test_type or "").strip().upper()
    if kind in ("FLT", "MOCK", "FULL"):
        return 200.0
    if series == "prelims" and kind in ("GS", "CSAT", "APTITUDE"):
        return 200.0
    return 100.0


DEFAULT_PRELIMS_SERIES_TITLE = "Upcoming Prelims Test Series"

# Placeholder plan for Oct–Nov prelims window — dates left blank until schedule is out.
PRELIMS_PLACEHOLDER_TESTS = [
    (1, "GS", "Sectional", "History & Culture", None, "Ancient · Medieval · Modern · Art", 100),
    (2, "GS", "Sectional", "Geography", None, "India + Chhattisgarh", 100),
    (3, "GS", "Sectional", "Polity & Governance", None, "Constitution · Schemes · Local bodies", 100),
    (4, "GS", "Sectional", "Economy", None, "India + CG economy · Budget basics", 100),
    (5, "GS", "Sectional", "Science & Environment", None, "GS science · ecology · tech", 100),
    (6, "GS", "Sectional", "CG Special + Current Affairs", None, "CG GK · CA last 12 months", 100),
    (7, "GS", "FLT", "GS Full Mock 1", None, "Paper-I complete (200)", 200),
    (8, "GS", "FLT", "GS Full Mock 2", None, "Paper-I complete (200)", 200),
    (9, "GS", "FLT", "GS Full Mock 3", None, "Paper-I complete (200)", 200),
    (10, "GS", "FLT", "GS Full Mock 4", None, "Paper-I complete (200)", 200),
    (11, "CSAT", "FLT", "CSAT / Aptitude Mock 1", None, "Paper-II qualifying", 200),
    (12, "CSAT", "FLT", "CSAT / Aptitude Mock 2", None, "Paper-II qualifying", 200),
    (13, "GS", "FLT", "GS Full Mock 5 — final", None, "Pre-exam full dress rehearsal", 200),
]


def score_percentage(score, max_score):
    """Return marks as a 0–100 percentage, or None if either value is missing/invalid."""
    if score is None or max_score is None:
        return None
    try:
        if pd.isna(score) or pd.isna(max_score):
            return None
        max_val = float(max_score)
        if max_val <= 0:
            return None
        return round(float(score) / max_val * 100, 1)
    except (TypeError, ValueError):
        return None


def _ensure_scheduled_tests_max_score(cursor):
    """Add max_score column on existing DBs and backfill defaults by test type."""
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(scheduled_tests)").fetchall()}
    if "max_score" not in cols:
        cursor.execute("ALTER TABLE scheduled_tests ADD COLUMN max_score REAL")
    cursor.execute(
        """UPDATE scheduled_tests
           SET max_score = CASE
               WHEN UPPER(COALESCE(test_type, '')) = 'FLT' THEN 200
               ELSE 100
           END
           WHERE max_score IS NULL OR max_score <= 0"""
    )


def init_db():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_date DATE UNIQUE NOT NULL,
                evening_reflection TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_target_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                planned_hours REAL DEFAULT 0,
                order_index INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Pending',
                actual_hours REAL DEFAULT 0,
                completion_notes TEXT DEFAULT '',
                FOREIGN KEY (plan_id) REFERENCES daily_plans(id) ON DELETE CASCADE
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_study_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE UNIQUE NOT NULL,
                hours REAL NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS scheduled_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_no INTEGER UNIQUE,
                level TEXT,
                test_type TEXT,
                subject TEXT,
                scheduled_date DATE,
                topic_focus TEXT,
                status TEXT DEFAULT 'Not Attempted',
                hours_studied REAL DEFAULT 0,
                score REAL,
                max_score REAL,
                remarks TEXT,
                attempt_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        _ensure_scheduled_tests_max_score(c)
        c.execute(
            """CREATE TABLE IF NOT EXISTS prelims_scheduled_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_no INTEGER UNIQUE,
                paper TEXT,
                test_type TEXT,
                subject TEXT,
                scheduled_date DATE,
                topic_focus TEXT,
                status TEXT DEFAULT 'Not Attempted',
                hours_studied REAL DEFAULT 0,
                score REAL,
                max_score REAL,
                remarks TEXT,
                attempt_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS garden_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                xp_amount INTEGER NOT NULL,
                message TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS study_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE NOT NULL,
                subject TEXT DEFAULT '',
                activity TEXT NOT NULL,
                duration_hours REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_logs_date "
            "ON study_activity_logs(log_date)"
        )
    from atlas import ensure_atlas

    ensure_atlas()


def seed_sample_tests():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM scheduled_tests")
        if c.fetchone()[0] > 0:
            return
        # CGPSC Mains Monsoon Test Series (29 June – 30 October 2026)
        tests = [
            (1, "Level-1", "Sectional", "Welfare Policy & Act", "2026-06-29", "Paper-7/Part-I", 100),
            (2, "Level-1", "Sectional", "Organizations & Sports", "2026-07-03", "Paper-7/Part-II", 100),
            (3, "Level-1", "Sectional", "Education & HRD", "2026-07-09", "Paper-7/Part-III", 100),
            (4, "Level-1", "FLT", "Level-1 FLT-1", "2026-07-13", "Paper-7 Complete", 200),
            (5, "Level-1", "Sectional", "Indian & C.G. Economy", "2026-07-18", "Paper-5/Part-I", 100),
            (6, "Level-1", "Sectional", "Indian Geography", "2026-07-21", "Paper-5/Part-II", 100),
            (7, "Level-1", "Sectional", "CG Geography", "2026-07-25", "Paper-5/Part-III", 100),
            (8, "Level-1", "FLT", "Level-1 FLT-2", "2026-07-31", "Paper-5 Complete", 200),
            (9, "Level-1", "Sectional", "Indian History", "2026-08-04", "Paper-3/Part-I", 100),
            (10, "Level-1", "Sectional", "Constitution & Public Administration", "2026-08-07", "Paper-3/Part-II", 100),
            (11, "Level-1", "Sectional", "CG History", "2026-08-11", "Paper-3/Part-III", 100),
            (12, "Level-1", "FLT", "Level-1 FLT-3", "2026-08-17", "Paper-3 Complete", 200),
            (13, "Level-1", "Sectional", "Hindi Language", "2026-08-21", "Paper-1/Part-I", 100),
            (14, "Level-1", "Sectional", "English Language", "2026-08-24", "Paper-1/Part-II", 100),
            (15, "Level-1", "Sectional", "Chhattisgarhi Language", "2026-09-01", "Paper-1/Part-III", 100),
            (16, "Level-1", "FLT", "Level-1 FLT-4", "2026-09-05", "Paper-1 Complete", 200),
            (17, "Level-1", "Sectional", "General Science", "2026-09-09", "Paper-4/Part-I", 100),
            (18, "Level-1", "Sectional", "Maths and Reasoning", "2026-09-12", "Paper-4/Part-II", 100),
            (19, "Level-1", "Sectional", "Applied Science", "2026-09-15", "Paper-4/Part-III", 100),
            (20, "Level-1", "FLT", "Level-1 FLT-5", "2026-09-21", "Paper-4 Complete", 200),
            (21, "Level-1", "Sectional", "Philosophy", "2026-09-25", "Paper-6/Part-I", 100),
            (22, "Level-1", "Sectional", "Sociology", "2026-09-28", "Paper-6/Part-II", 100),
            (23, "Level-1", "Sectional", "Social Aspects of Chhattisgarh", "2026-10-02", "Paper-6/Part-III", 100),
            (24, "Level-1", "FLT", "Level-1 FLT-6", "2026-10-08", "Paper-6 Complete", 200),
            (25, "Level-1", "FLT", "Level-1 FLT-7", "2026-10-15", "Paper-2 Complete", 200),
            (26, "Level-2", "FLT", "Paper-01", "2026-10-26", "FLT-08", 200),
            (27, "Level-2", "FLT", "Paper-02", "2026-10-26", "FLT-09", 200),
            (28, "Level-2", "FLT", "Paper-03", "2026-10-27", "FLT-10", 200),
            (29, "Level-2", "FLT", "Paper-04", "2026-10-27", "FLT-11", 200),
            (30, "Level-2", "FLT", "Paper-05", "2026-10-28", "FLT-12", 200),
            (31, "Level-2", "FLT", "Paper-06", "2026-10-28", "FLT-13", 200),
            (32, "Level-2", "FLT", "Paper-07", "2026-10-29", "FLT-14", 200),
        ]
        c.executemany(
            """INSERT INTO scheduled_tests
               (test_no, level, test_type, subject, scheduled_date, topic_focus, max_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            tests,
        )


def seed_prelims_placeholders(*, force=False):
    """Create Upcoming Prelims Test Series placeholders if the table is empty.

    Dates are left NULL so you can fill the schedule when the institute releases it.
    Set force=True only to re-seed after clearing the table.
    """
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM prelims_scheduled_tests")
        count = c.fetchone()[0]
        if count > 0 and not force:
            return False
        if count > 0 and force:
            c.execute("DELETE FROM prelims_scheduled_tests")
        c.executemany(
            """INSERT INTO prelims_scheduled_tests
               (test_no, paper, test_type, subject, scheduled_date, topic_focus, max_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            PRELIMS_PLACEHOLDER_TESTS,
        )
    if not get_setting("prelims_series_title"):
        set_setting("prelims_series_title", DEFAULT_PRELIMS_SERIES_TITLE)
    return True


def get_prelims_series_title():
    return get_setting("prelims_series_title", DEFAULT_PRELIMS_SERIES_TITLE) or DEFAULT_PRELIMS_SERIES_TITLE


def set_prelims_series_title(title):
    title = (title or "").strip() or DEFAULT_PRELIMS_SERIES_TITLE
    set_setting("prelims_series_title", title)
    return title


def get_setting(key, default=None):
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = c.fetchone()
    return row[0] if row else default


def set_setting(key, value):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO app_settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, str(value)),
        )


def get_daily_study_goal():
    raw = get_setting("daily_study_goal_hours", str(DEFAULT_DAILY_GOAL_HOURS))
    try:
        return max(0.5, float(raw))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_GOAL_HOURS


def set_daily_study_goal(hours):
    set_setting("daily_study_goal_hours", max(0.5, float(hours)))


def add_daily_study_hours(log_date, hours, notes="", *, award_xp=True):
    """Log study hours. Awards garden XP once per call (all entry points)."""
    date_str = _date_str(log_date)
    hours = float(hours)
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, hours, notes FROM daily_study_hours WHERE log_date = ?",
            (date_str,),
        )
        row = c.fetchone()
        if row:
            new_hours = float(row[1]) + hours
            old_notes = (row[2] or "").strip()
            new_note = (notes or "").strip()
            if new_note and old_notes:
                merged_notes = f"{old_notes}; {new_note}"
            elif new_note:
                merged_notes = new_note
            else:
                merged_notes = old_notes
            c.execute(
                """UPDATE daily_study_hours
                   SET hours = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_hours, merged_notes, row[0]),
            )
        else:
            c.execute(
                "INSERT INTO daily_study_hours (log_date, hours, notes) VALUES (?, ?, ?)",
                (date_str, hours, notes or ""),
            )
    reward = None
    if award_xp and hours > 0:
        reward = award_hours_garden_xp(hours)
    return {"logged": True, "hours": hours, "reward": reward}


def get_study_hours_for_date(log_date):
    date_str = _date_str(log_date)
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        c.execute("SELECT hours FROM daily_study_hours WHERE log_date = ?", (date_str,))
        row = c.fetchone()
    return float(row[0]) if row else 0.0


def get_week_study_hours(anchor_date=None):
    if anchor_date is None:
        anchor_date = date.today()
    monday = anchor_date - timedelta(days=anchor_date.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    with db_connection(commit=False) as conn:
        rows = []
        for d, name in zip(week_dates, day_names):
            date_str = d.isoformat()
            c = conn.cursor()
            c.execute(
                "SELECT hours, notes FROM daily_study_hours WHERE log_date = ?",
                (date_str,),
            )
            row = c.fetchone()
            rows.append(
                {
                    "day": name,
                    "log_date": d,
                    "hours": float(row[0]) if row else 0.0,
                    "notes": row[1] if row else "",
                    "is_today": d == date.today(),
                }
            )
    return pd.DataFrame(rows)


def get_recent_study_hours(limit=14):
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT log_date, hours, notes, updated_at
               FROM daily_study_hours
               ORDER BY log_date DESC
               LIMIT ?""",
            conn,
            params=(limit,),
        )


def get_study_streak(today=None):
    """Consecutive study days ending today, or yesterday if today is not logged yet."""
    if today is None:
        today = date.today()
    hours_by_date = get_study_hours_map(today - timedelta(days=400), today)
    cursor = today
    if hours_by_date.get(today, 0) <= 0:
        cursor = today - timedelta(days=1)
    streak = 0
    while cursor >= today - timedelta(days=400):
        if hours_by_date.get(cursor, 0) > 0:
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break
    return streak


def get_study_hours_map(start_date, end_date=None):
    """Return {date: hours} for each day in the inclusive range."""
    if end_date is None:
        end_date = date.today()
    start_str = _date_str(start_date)
    end_str = _date_str(end_date)
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            "SELECT log_date, hours FROM daily_study_hours WHERE log_date >= ? AND log_date <= ?",
            conn,
            params=(start_str, end_str),
        )
    result = {}
    for _, row in df.iterrows():
        result[_parse_log_date(row["log_date"])] = float(row["hours"])
    return result


def get_longest_streak():
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            "SELECT log_date, hours FROM daily_study_hours ORDER BY log_date ASC",
            conn,
        )
    if df.empty:
        return 0

    study_dates = sorted(
        _parse_log_date(row["log_date"])
        for _, row in df.iterrows()
        if float(row["hours"]) > 0
    )
    if not study_dates:
        return 0

    longest = 1
    run = 1
    for i in range(1, len(study_dates)):
        if study_dates[i] - study_dates[i - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


def get_study_hours_summary():
    """All-time study hours overview (past effort stays visible even after gaps)."""
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            "SELECT log_date, hours FROM daily_study_hours WHERE hours > 0 ORDER BY log_date ASC",
            conn,
        )
    empty = {
        "total_hours": 0.0,
        "study_days": 0,
        "best_hours": 0.0,
        "best_date": None,
        "avg_hours": 0.0,
        "first_date": None,
        "last_date": None,
    }
    if df.empty:
        return empty

    df = df.copy()
    df["log_date"] = df["log_date"].map(_parse_log_date)
    df["hours"] = df["hours"].astype(float)
    best_idx = df["hours"].idxmax()
    return {
        "total_hours": round(float(df["hours"].sum()), 2),
        "study_days": int(len(df)),
        "best_hours": round(float(df.loc[best_idx, "hours"]), 2),
        "best_date": df.loc[best_idx, "log_date"],
        "avg_hours": round(float(df["hours"].mean()), 2),
        "first_date": df["log_date"].iloc[0],
        "last_date": df["log_date"].iloc[-1],
    }


def get_study_hours_range(start_date, end_date=None, *, fill_zeros=True):
    """Daily hours series for charts. Optionally fill missing calendar days with 0."""
    if end_date is None:
        end_date = date.today()
    start_date = _parse_log_date(start_date) if not isinstance(start_date, date) else start_date
    end_date = _parse_log_date(end_date) if not isinstance(end_date, date) else end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    hours_by_date = get_study_hours_map(start_date, end_date)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = date.today()

    if fill_zeros:
        dates = [
            start_date + timedelta(days=i)
            for i in range((end_date - start_date).days + 1)
        ]
    else:
        dates = sorted(d for d, h in hours_by_date.items() if h > 0)
        if not dates:
            return pd.DataFrame(
                columns=["day", "log_date", "hours", "notes", "is_today", "cumulative"]
            )

    rows = []
    cumulative = 0.0
    for d in dates:
        hours = float(hours_by_date.get(d, 0) or 0)
        cumulative += hours
        rows.append(
            {
                "day": day_names[d.weekday()],
                "log_date": d,
                "hours": hours,
                "notes": "",
                "is_today": d == today,
                "cumulative": round(cumulative, 2),
            }
        )
    return pd.DataFrame(rows)


def get_export_dataframes():
    with db_connection(commit=False) as conn:
        hours = pd.read_sql(
            "SELECT log_date, hours, notes, updated_at FROM daily_study_hours ORDER BY log_date",
            conn,
        )
        tests = pd.read_sql("SELECT * FROM scheduled_tests ORDER BY test_no", conn)
        prelims = pd.read_sql(
            "SELECT * FROM prelims_scheduled_tests ORDER BY test_no", conn
        )
        targets = pd.read_sql(
            """SELECT p.plan_date, t.description, t.status, t.planned_hours, t.actual_hours
               FROM daily_target_items t
               JOIN daily_plans p ON p.id = t.plan_id
               ORDER BY p.plan_date, t.order_index""",
            conn,
        )
        atlas_nodes = pd.read_sql(
            "SELECT * FROM atlas_nodes ORDER BY kind, sort_order, id", conn
        )
        atlas_progress = pd.read_sql(
            "SELECT * FROM atlas_progress ORDER BY node_id", conn
        )
        atlas_study_log = pd.read_sql(
            "SELECT * FROM atlas_study_log ORDER BY id", conn
        )
    from logbook import get_activity_logs_export

    activity_logs = get_activity_logs_export()
    return {
        "study_hours": hours,
        "scheduled_tests": tests,
        "prelims_scheduled_tests": prelims,
        "daily_targets": targets,
        "activity_logs": activity_logs,
        "atlas_nodes": atlas_nodes,
        "atlas_progress": atlas_progress,
        "atlas_study_log": atlas_study_log,
    }


def _get_or_create_plan_id(plan_date, conn):
    c = conn.cursor()
    date_str = _date_str(plan_date)
    c.execute("SELECT id FROM daily_plans WHERE plan_date = ?", (date_str,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute("INSERT INTO daily_plans (plan_date) VALUES (?)", (date_str,))
    return c.lastrowid


def get_daily_plan(plan_date):
    date_str = _date_str(plan_date)
    with db_connection(commit=False) as conn:
        plan_df = pd.read_sql(
            "SELECT * FROM daily_plans WHERE plan_date = ?",
            conn,
            params=(date_str,),
        )
        if plan_df.empty:
            return None
        plan = plan_df.iloc[0].to_dict()
        items_df = pd.read_sql(
            """SELECT * FROM daily_target_items
               WHERE plan_id = ?
               ORDER BY order_index, id""",
            conn,
            params=(int(plan["id"]),),
        )
    plan["items"] = items_df.to_dict("records") if not items_df.empty else []
    return plan


def save_daily_targets(plan_date, targets, evening_reflection=None):
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn)

        c.execute(
            """SELECT order_index, status, actual_hours, completion_notes
               FROM daily_target_items
               WHERE plan_id = ?
               ORDER BY order_index, id""",
            (plan_id,),
        )
        existing_by_index = {
            row[0]: {
                "status": row[1],
                "actual_hours": row[2],
                "completion_notes": row[3],
            }
            for row in c.fetchall()
        }

        c.execute("DELETE FROM daily_target_items WHERE plan_id = ?", (plan_id,))
        for idx, target in enumerate(targets):
            desc = (target.get("description") or "").strip()
            if not desc:
                continue
            prev = existing_by_index.get(idx, {})
            c.execute(
                """INSERT INTO daily_target_items
                   (plan_id, description, planned_hours, order_index, status,
                    actual_hours, completion_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan_id,
                    desc,
                    float(target.get("planned_hours") or 0),
                    idx,
                    prev.get("status", "Pending"),
                    float(prev.get("actual_hours") or 0),
                    prev.get("completion_notes") or "",
                ),
            )

        if evening_reflection is not None:
            c.execute(
                """UPDATE daily_plans
                   SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (evening_reflection, plan_id),
            )
        else:
            c.execute(
                "UPDATE daily_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (plan_id,),
            )


def add_daily_target(plan_date, description, planned_hours=0):
    """Append a single target to an existing or new daily plan."""
    desc = (description or "").strip()
    if not desc:
        raise DatabaseError("Target description cannot be empty.")
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn)
        c.execute(
            "SELECT COALESCE(MAX(order_index), -1) FROM daily_target_items WHERE plan_id = ?",
            (plan_id,),
        )
        next_index = int(c.fetchone()[0]) + 1
        c.execute(
            """INSERT INTO daily_target_items
               (plan_id, description, planned_hours, order_index, status)
               VALUES (?, ?, ?, ?, 'Pending')""",
            (plan_id, desc, float(planned_hours or 0), next_index),
        )
        c.execute(
            "UPDATE daily_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (plan_id,),
        )


def update_target_status(item_id, status):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE daily_target_items SET status = ? WHERE id = ?",
            (status, int(item_id)),
        )


def save_evening_reflection(plan_date, reflection):
    with db_connection() as conn:
        c = conn.cursor()
        plan_id = _get_or_create_plan_id(plan_date, conn)
        c.execute(
            """UPDATE daily_plans
               SET evening_reflection = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (reflection or "", plan_id),
        )


UNFINISHED_TARGET_STATUSES = frozenset({"Pending", "Partial"})


def get_unfinished_targets(plan_date):
    """Return Pending/Partial targets for a day (for carry-over prompts)."""
    plan = get_daily_plan(plan_date)
    if not plan or not plan["items"]:
        return []
    unfinished = []
    for item in plan["items"]:
        desc = (item.get("description") or "").strip()
        if not desc:
            continue
        if item.get("status") not in UNFINISHED_TARGET_STATUSES:
            continue
        unfinished.append(
            {
                "description": desc,
                "planned_hours": float(item.get("planned_hours") or 0),
                "status": item.get("status") or "Pending",
            }
        )
    return unfinished


def carry_over_unfinished_targets(from_date, to_date):
    """Copy unfinished targets from one day onto another as Pending.

    Raises DatabaseError if ``to_date`` already has targets or there is
    nothing unfinished to copy. Returns the number of targets carried over.
    """
    existing = get_daily_plan(to_date)
    if existing and existing.get("items"):
        raise DatabaseError("That day already has targets.")
    unfinished = get_unfinished_targets(from_date)
    if not unfinished:
        raise DatabaseError("No unfinished targets to carry over.")
    targets = [
        {
            "description": item["description"],
            "planned_hours": item["planned_hours"],
        }
        for item in unfinished
    ]
    save_daily_targets(to_date, targets)
    return len(targets)


def get_daily_plan_summary(plan_date):
    plan = get_daily_plan(plan_date)
    if not plan or not plan["items"]:
        return {
            "has_plan": False,
            "total_targets": 0,
            "done": 0,
            "partial": 0,
            "pending": 0,
            "skipped": 0,
            "planned_hours": 0,
            "actual_hours": 0,
            "completion_pct": 0,
            "resolved_pct": 0,
        }
    items = plan["items"]
    done = sum(1 for i in items if i["status"] == "Done")
    partial = sum(1 for i in items if i["status"] == "Partial")
    pending = sum(1 for i in items if i["status"] == "Pending")
    skipped = sum(1 for i in items if i["status"] == "Skipped")
    planned = sum(float(i.get("planned_hours") or 0) for i in items)
    actual = sum(float(i.get("actual_hours") or 0) for i in items)
    total = len(items)
    resolved = done + skipped
    return {
        "has_plan": True,
        "total_targets": total,
        "done": done,
        "partial": partial,
        "pending": pending,
        "skipped": skipped,
        "planned_hours": round(planned, 1),
        "actual_hours": round(actual, 1),
        "completion_pct": round((done / total) * 100) if total else 0,
        "resolved_pct": round((resolved / total) * 100) if total else 0,
    }


def get_scheduled_tests():
    with db_connection(commit=False) as conn:
        return pd.read_sql("SELECT * FROM scheduled_tests ORDER BY test_no", conn)


def get_prelims_tests():
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            "SELECT * FROM prelims_scheduled_tests ORDER BY test_no", conn
        )


def _next_unattempted_test(table, *, require_date=False):
    """Shared next-test lookup for mains / prelims series tables."""
    today_str = date.today().isoformat()
    with db_connection(commit=False) as conn:
        date_filter = "AND scheduled_date IS NOT NULL AND scheduled_date != ''"
        df = pd.read_sql(
            f"""SELECT * FROM {table}
               WHERE (status != 'Attempted' OR status IS NULL)
                 AND scheduled_date >= ?
                 {date_filter}
               ORDER BY scheduled_date ASC
               LIMIT 1""",
            conn,
            params=(today_str,),
        )
        if df.empty:
            df = pd.read_sql(
                f"""SELECT * FROM {table}
                   WHERE (status != 'Attempted' OR status IS NULL)
                     AND scheduled_date IS NOT NULL AND scheduled_date != ''
                   ORDER BY scheduled_date ASC
                   LIMIT 1""",
                conn,
            )
        if df.empty and not require_date:
            df = pd.read_sql(
                f"""SELECT * FROM {table}
                   WHERE status != 'Attempted' OR status IS NULL
                   ORDER BY test_no ASC
                   LIMIT 1""",
                conn,
            )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_next_scheduled_test():
    return _next_unattempted_test("scheduled_tests", require_date=True)


def get_next_prelims_test():
    """Next dated prelims test; falls back to first unscheduled slot."""
    return _next_unattempted_test("prelims_scheduled_tests", require_date=False)


def _series_progress(df):
    attempted = df[df["status"] == "Attempted"].copy()
    if not attempted.empty:
        if "max_score" not in attempted.columns:
            attempted["max_score"] = None
        attempted["score_pct"] = attempted.apply(
            lambda r: score_percentage(r.get("score"), r.get("max_score")),
            axis=1,
        )
    else:
        attempted["score_pct"] = pd.Series(dtype=float)

    pcts = attempted["score_pct"].dropna() if not attempted.empty else pd.Series(dtype=float)
    raw_scores = attempted["score"].dropna() if not attempted.empty else pd.Series(dtype=float)
    score_cols = ["test_no", "subject", "scheduled_date", "score", "max_score", "score_pct"]
    available = [c for c in score_cols if c in attempted.columns]
    dated = 0
    if not df.empty and "scheduled_date" in df.columns:
        dated = int(df["scheduled_date"].notna().sum())
        # treat empty strings as undated
        if dated:
            dated = int(
                df["scheduled_date"].apply(
                    lambda v: pd.notna(v) and str(v).strip() not in ("", "None", "NaT")
                ).sum()
            )
    return {
        "total": len(df),
        "attempted": len(attempted),
        "dated": dated,
        "avg_score": float(round(pcts.mean(), 1)) if not pcts.empty else (
            float(round(raw_scores.mean(), 1)) if not raw_scores.empty else None
        ),
        "avg_is_pct": not pcts.empty,
        "scores": attempted[available].copy() if available else attempted,
    }


def get_test_series_progress():
    return _series_progress(get_scheduled_tests())


def get_prelims_series_progress():
    return _series_progress(get_prelims_tests())


def get_garden_xp():
    raw = get_setting("garden_xp", "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _set_garden_xp(xp):
    set_setting("garden_xp", max(0, int(xp)))


def _log_garden_event(event_type, xp_amount, message):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO garden_events (event_type, xp_amount, message)
               VALUES (?, ?, ?)""",
            (event_type, int(xp_amount), message),
        )


def add_garden_xp(amount, event_type, message):
    if amount <= 0:
        return 0
    old_xp = get_garden_xp()
    new_xp = old_xp + amount
    _set_garden_xp(new_xp)
    _log_garden_event(event_type, amount, message)
    return amount


def get_garden_events(limit=12):
    with db_connection(commit=False) as conn:
        return pd.read_sql(
            """SELECT event_date, event_type, xp_amount, message
               FROM garden_events
               ORDER BY id DESC
               LIMIT ?""",
            conn,
            params=(limit,),
        )


def _bonus_already_today(setting_key):
    return get_setting(setting_key) == date.today().isoformat()


def _mark_bonus_today(setting_key):
    set_setting(setting_key, date.today().isoformat())


def process_daily_checkin(streak=0):
    """Award daily open-app XP once per day. Returns list of reward dicts."""
    rewards = []
    if _bonus_already_today("last_garden_checkin"):
        return rewards

    from garden import XP_REWARDS

    xp = add_garden_xp(
        XP_REWARDS["daily_checkin"],
        "checkin",
        f"Daily check-in — {FIRST_NAME} showed up!",
    )
    rewards.append({"xp": xp, "message": f"{FIRST_NAME} checked in today! 🌱"})

    streak_bonus = min(streak * XP_REWARDS["streak_per_day"], XP_REWARDS["streak_cap"])
    if streak_bonus > 0:
        xp = add_garden_xp(
            streak_bonus,
            "streak",
            f"{streak}-day study streak bonus",
        )
        rewards.append({"xp": xp, "message": f"{FIRST_NAME}'s {streak}-day streak bonus 🔥"})

    _mark_bonus_today("last_garden_checkin")
    return rewards


def award_hours_garden_xp(hours):
    from garden import XP_REWARDS

    amount = int(float(hours) * XP_REWARDS["per_hour"])
    if amount <= 0:
        return None
    xp = add_garden_xp(amount, "hours", f"Logged {hours}h of study")
    return {"xp": xp, "message": f"{FIRST_NAME} logged {hours}h of study 💪"}


def backfill_hours_garden_xp():
    """One-time: credit garden XP for study hours logged before XP was wired up.

    Skips if already run, or if any hours XP events already exist.
    """
    if get_setting("hours_xp_backfilled") == "1":
        return 0
    with db_connection(commit=False) as conn:
        c = conn.cursor()
        existing_hours_xp = c.execute(
            "SELECT COUNT(*) FROM garden_events WHERE event_type = 'hours'"
        ).fetchone()[0]
        if existing_hours_xp > 0:
            set_setting("hours_xp_backfilled", "1")
            return 0
        row = c.execute("SELECT COALESCE(SUM(hours), 0) FROM daily_study_hours").fetchone()
        total_hours = float(row[0] or 0)
    if total_hours <= 0:
        set_setting("hours_xp_backfilled", "1")
        return 0
    from garden import XP_REWARDS

    amount = int(total_hours * XP_REWARDS["per_hour"])
    if amount <= 0:
        set_setting("hours_xp_backfilled", "1")
        return 0
    add_garden_xp(
        amount,
        "hours",
        f"Backfill: credited {total_hours:g}h of past study",
    )
    set_setting("hours_xp_backfilled", "1")
    return amount


def award_target_done_xp():
    from garden import XP_REWARDS

    xp = add_garden_xp(XP_REWARDS["target_done"], "target", "Target completed!")
    return {"xp": xp, "message": f"{FIRST_NAME} crushed a target ✅"}


def sync_daily_garden_bonuses(today=None):
    """Award once-per-day bonuses for all-targets and daily-goal milestones."""
    if today is None:
        today = date.today()

    from garden import XP_REWARDS

    rewards = []
    summary = get_daily_plan_summary(today)
    items = summary.get("total_targets", 0)
    done = summary.get("done", 0)
    skipped = summary.get("skipped", 0)

    if items > 0 and (done + skipped) >= items:
        if not _bonus_already_today("last_garden_all_targets"):
            xp = add_garden_xp(
                XP_REWARDS["all_targets"],
                "all_targets",
                "All targets resolved today!",
            )
            rewards.append({"xp": xp, "message": f"All targets done today, {FIRST_NAME}! 🎉"})
            _mark_bonus_today("last_garden_all_targets")

    hours = get_study_hours_for_date(today)
    goal = get_daily_study_goal()
    if hours >= goal:
        if not _bonus_already_today("last_garden_daily_goal"):
            xp = add_garden_xp(
                XP_REWARDS["daily_goal"],
                "daily_goal",
                f"Hit your {goal:g}h daily goal!",
            )
            rewards.append({"xp": xp, "message": f"{FIRST_NAME} hit the {goal:g}h goal! 🎯"})
            _mark_bonus_today("last_garden_daily_goal")

    return rewards


def get_garden_state(streak=0, today=None):
    from garden import get_stage_info
    from garden_life import sync_garden_life

    if today is None:
        today = date.today()
    # Credit any pre-XP study hours once
    try:
        backfill_hours_garden_xp()
    except Exception:
        pass
    xp = get_garden_xp()
    life = sync_garden_life(today)
    return {
        "xp": xp,
        "streak": streak,
        "stage_info": get_stage_info(xp),
        "events": get_garden_events(8),
        "life": life,
        "vitality": life,
    }


def update_scheduled_test(
    test_no,
    status=None,
    hours_studied=_UNSET,
    score=_UNSET,
    max_score=_UNSET,
    remarks=_UNSET,
):
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if hours_studied is not _UNSET:
        updates.append("hours_studied = ?")
        params.append(hours_studied)
    if score is not _UNSET:
        updates.append("score = ?")
        params.append(score)
    if max_score is not _UNSET:
        updates.append("max_score = ?")
        params.append(max_score)
    if remarks is not _UNSET:
        updates.append("remarks = ?")
        params.append(remarks)
    if not updates:
        return

    params.append(test_no)
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE scheduled_tests SET {', '.join(updates)} WHERE test_no = ?",
            params,
        )


def _normalize_optional_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    text = str(value).strip()
    if not text or text.lower() in ("none", "nat", "nan", "tbd", "-"):
        return None
    return text[:10]


def update_prelims_test(
    test_no,
    *,
    status=_UNSET,
    hours_studied=_UNSET,
    score=_UNSET,
    max_score=_UNSET,
    remarks=_UNSET,
    paper=_UNSET,
    test_type=_UNSET,
    subject=_UNSET,
    scheduled_date=_UNSET,
    topic_focus=_UNSET,
):
    """Update prelims schedule fields and/or results for one test row."""
    updates = []
    params = []
    field_map = {
        "status": status,
        "hours_studied": hours_studied,
        "score": score,
        "max_score": max_score,
        "remarks": remarks,
        "paper": paper,
        "test_type": test_type,
        "subject": subject,
        "topic_focus": topic_focus,
    }
    for col, val in field_map.items():
        if val is _UNSET:
            continue
        updates.append(f"{col} = ?")
        params.append(val)
    if scheduled_date is not _UNSET:
        updates.append("scheduled_date = ?")
        params.append(_normalize_optional_date(scheduled_date))
    if not updates:
        return

    params.append(int(test_no))
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE prelims_scheduled_tests SET {', '.join(updates)} WHERE test_no = ?",
            params,
        )


def add_prelims_test(
    *,
    subject,
    paper="GS",
    test_type="Sectional",
    scheduled_date=None,
    topic_focus="",
    max_score=None,
):
    """Append a new prelims test (next test_no). Returns new test_no."""
    subject = (subject or "").strip()
    if not subject:
        raise DatabaseError("Subject is required.")
    if max_score is None:
        max_score = default_max_score(test_type, series="prelims")
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COALESCE(MAX(test_no), 0) + 1 FROM prelims_scheduled_tests")
        test_no = int(c.fetchone()[0])
        c.execute(
            """INSERT INTO prelims_scheduled_tests
               (test_no, paper, test_type, subject, scheduled_date, topic_focus, max_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                test_no,
                (paper or "GS").strip(),
                (test_type or "Sectional").strip(),
                subject,
                _normalize_optional_date(scheduled_date),
                (topic_focus or "").strip(),
                float(max_score),
            ),
        )
    return test_no


def delete_prelims_test(test_no):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM prelims_scheduled_tests WHERE test_no = ?",
            (int(test_no),),
        )
        return c.rowcount > 0