import html
import os
import subprocess
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    DB_PATH,
    DatabaseError,
    add_daily_study_hours,
    add_daily_target,
    add_prelims_test,
    award_hours_garden_xp,
    award_target_done_xp,
    carry_over_unfinished_targets,
    default_max_score,
    delete_prelims_test,
    get_daily_plan,
    get_daily_plan_summary,
    get_daily_study_goal,
    get_export_dataframes,
    get_garden_state,
    get_garden_xp,
    get_longest_streak,
    get_next_prelims_test,
    get_next_scheduled_test,
    get_prelims_series_progress,
    get_prelims_series_title,
    get_prelims_tests,
    get_recent_study_hours,
    get_scheduled_tests,
    get_setting,
    get_study_hours_for_date,
    get_study_hours_range,
    get_study_hours_summary,
    get_study_streak,
    get_test_series_progress,
    get_unfinished_targets,
    get_week_study_hours,
    init_db,
    process_daily_checkin,
    save_daily_targets,
    save_evening_reflection,
    seed_prelims_placeholders,
    seed_sample_tests,
    set_daily_study_goal,
    set_prelims_series_title,
    set_setting,
    sync_daily_garden_bonuses,
    update_prelims_test,
    update_scheduled_test,
    update_target_status,
)
from logbook import (
    add_activity_log,
    delete_activity_log,
    get_activity_log_stats,
    get_activity_logs,
)
from git_sync import get_sync_status, notify_data_changed, start_background_sync, sync_to_github
from sync import get_sync_metadata, import_database
from garden_life import pop_harvest_unlocks
from garden import (
    GARDEN_CSS,
    GARDEN_STAGES,
    XP_REWARDS,
    get_stage_info,
    render_garden_stats_strip,
    render_interactive_garden,
)
from profile import EXAM, EXAM_YEAR, FIRST_NAME, FULL_NAME, MOTTO, greeting, period_nudge, possessive
from app_styles import (
    DEFAULT_THEME,
    THEME_OPTIONS,
    get_app_css,
    resolve_theme,
)
import importlib
import showup_grid

importlib.reload(showup_grid)
load_showup_hours = showup_grid.load_showup_hours
render_github_heatmap = showup_grid.render_github_heatmap
from break_games_config import GAME_GROUPS
import relax_games
from atlas_ui import render_atlas_page

MAX_TARGETS_PER_DAY = 99
UI_THEME_KEY = "ui_theme"
NAV_MODULES = [
    ("today", "Today", "Daily targets & logging"),
    ("atlas", "Atlas", "Syllabus map & revision"),
    ("hours", "Hours", "Charts & study time"),
    ("logbook", "Logbook", "What you studied"),
    ("tests", "Tests", "Mains & prelims"),
    ("garden", "Garden", "Growth map"),
    ("break", "Break", "Short reset games"),
]
NAV_KEYS = {m[0] for m in NAV_MODULES}
NAV_ICONS = {
    "today": "◎",
    "atlas": "◈",
    "hours": "◷",
    "logbook": "✎",
    "tests": "▣",
    "garden": "❀",
    "break": "☾",
}
NAV_LABELS = {m[0]: m[1] for m in NAV_MODULES}
LOG_SUBJECTS = [
    "",
    "Paper-1 (Language)",
    "Paper-2 (Essay)",
    "Paper-3 (GS-I)",
    "Paper-4 (GS-II)",
    "Paper-5 (GS-III)",
    "Paper-6 (GS-IV)",
    "Paper-7 (GS-V)",
    "General / Mixed",
]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

st.set_page_config(
    page_title=f"{FIRST_NAME}'s CGPSC Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_ui_theme():
    """Persisted UI theme; defaults to Nova with Classic as fallback."""
    try:
        stored = get_setting(UI_THEME_KEY, DEFAULT_THEME)
    except Exception:
        stored = DEFAULT_THEME
    return resolve_theme(stored)


def apply_theme_css(theme_name):
    st.markdown(GARDEN_CSS + get_app_css(theme_name), unsafe_allow_html=True)


def chart_theme_tokens(theme_name=None):
    """Plotly colors that match the active UI theme (Paper is light)."""
    theme = resolve_theme(theme_name or st.session_state.get("ui_theme", DEFAULT_THEME))
    if theme == "paper":
        return {
            "font": "#1a1c22",
            "muted": "#6a7080",
            "plot_bg": "rgba(255, 255, 255, 0.94)",
            "grid": "rgba(40, 48, 72, 0.1)",
            "zero": "rgba(40, 48, 72, 0.16)",
            "line": "#4f5fd6",
            "marker": "#3b82c4",
            "today": "#0284c7",
            "goal_met": "#0f766e",
            "logged": "#4f5fd6",
            "empty": "rgba(40, 48, 72, 0.1)",
            "goal_line": "#dc4b64",
            "text_on_bar": "#1a1c22",
            "fill": "rgba(79, 95, 214, 0.12)",
        }
    return {
        "font": "#f1f4fb",
        "muted": "#8e9ab3",
        "plot_bg": "rgba(18, 24, 38, 0.9)",
        "grid": "rgba(148,168,210,0.12)",
        "zero": "rgba(148,168,210,0.18)",
        "line": "#5ec8ff",
        "marker": "#7c8cff",
        "today": "#5ec8ff",
        "goal_met": "#3ecfad",
        "logged": "#7c8cff",
        "empty": "rgba(148,168,210,0.16)",
        "goal_line": "#fb7185",
        "text_on_bar": "#f1f4fb",
        "fill": "rgba(94, 200, 255, 0.14)",
    }


def apply_plotly_layout(fig, *, height=360, tokens=None):
    tokens = tokens or chart_theme_tokens()
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=48, b=20),
        font=dict(size=13, color=tokens["font"], family="IBM Plex Sans, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tokens["plot_bg"],
        title_font_color=tokens["font"],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=tokens["muted"]),
        ),
    )
    fig.update_xaxes(
        gridcolor=tokens["grid"],
        zerolinecolor=tokens["zero"],
        color=tokens["muted"],
    )
    fig.update_yaxes(
        gridcolor=tokens["grid"],
        zerolinecolor=tokens["zero"],
        color=tokens["muted"],
    )
    return fig

MORNING_END_HOUR = 12
EVENING_START_HOUR = 17
PERIOD_BADGES = {
    "morning": "morning-badge",
    "afternoon": "afternoon-badge",
    "evening": "evening-badge",
}


def ensure_db_ready():
    try:
        if not st.session_state.get("schema_ready"):
            init_db()
            st.session_state.schema_ready = True
        if not st.session_state.get("data_seeded"):
            seed_sample_tests()
            seed_prelims_placeholders()
            st.session_state.data_seeded = True
        if not st.session_state.get("git_sync_started"):
            start_background_sync()
            st.session_state.git_sync_started = True
    except DatabaseError as exc:
        st.error(f"Could not initialize the database: {exc}")
        st.stop()


def run_db(action, error_message="Something went wrong. Please try again."):
    try:
        result = action()
        notify_data_changed()
        return result
    except DatabaseError as exc:
        st.error(f"{error_message} ({exc})")
        return None


def queue_garden_reward(reward):
    if reward:
        st.session_state.setdefault("pending_garden_toasts", []).append(reward)


def show_garden_rewards(rewards, xp_before):
    if not rewards:
        return
    xp_after = get_garden_xp()
    leveled_up = get_stage_info(xp_after)["index"] > get_stage_info(xp_before)["index"]
    for reward in rewards:
        st.toast(f"+{reward['xp']} XP — {reward['message']}", icon="🌳")
    if leveled_up:
        new_stage = get_stage_info(xp_after)["current"]
        st.balloons()
        st.toast(
            f"LEVEL UP, {FIRST_NAME}! Your tree is now a {new_stage['name']} {new_stage['emoji']}!",
            icon="🎉",
        )


def flush_pending_garden_toasts():
    pending = st.session_state.pop("pending_garden_toasts", [])
    for reward in pending:
        st.toast(f"+{reward['xp']} XP — {reward['message']}", icon="🌳")


def show_harvest_unlock(today=None):
    unlock = pop_harvest_unlocks(today)
    if unlock:
        st.toast(unlock["message"], icon=unlock["emoji"])
        if unlock["tier"] == "golden":
            st.balloons()


def render_metric_rows(metric_rows):
    """Render metrics in multi-column rows."""
    for row in metric_rows:
        cols = st.columns(len(row))
        for col, item in zip(cols, row):
            if len(item) == 3:
                col.metric(item[0], item[1], item[2])
            else:
                col.metric(item[0], item[1])


def resolve_nav_page():
    """Keep URL ?page= and session nav in sync."""
    if st.query_params.get("view") == "garden":
        st.session_state.nav_page = "garden"
    qp_page = st.query_params.get("page")
    if isinstance(qp_page, list):
        qp_page = qp_page[0] if qp_page else None
    if qp_page in NAV_KEYS:
        st.session_state.nav_page = qp_page
    if "nav_page" not in st.session_state or st.session_state.nav_page not in NAV_KEYS:
        st.session_state.nav_page = "today"
    return st.session_state.nav_page


def set_nav_page(key):
    st.session_state.nav_page = key
    try:
        st.query_params["page"] = key
    except Exception:
        pass
    st.rerun()


def render_sidebar(theme_name, active_page):
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <p class="sidebar-brand-name">{html.escape(FULL_NAME)}</p>
            <p class="sidebar-brand-sub">{html.escape(EXAM)} {EXAM_YEAR}<br/>{html.escape(MOTTO)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if theme_name == "classic":
        st.markdown(f"### {FULL_NAME}")
        st.caption(f"{EXAM} {EXAM_YEAR}")
        st.caption(MOTTO)

    # ── Primary module navigation ─────────────────────────
    st.markdown(
        '<p class="sidebar-nav-label">Navigate</p>'
        '<div class="sidebar-nav-marker" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    for key, label, hint in NAV_MODULES:
        is_active = active_page == key
        icon = NAV_ICONS.get(key, "·")
        display = f"{icon}  {label}"
        if st.button(
            display,
            key=f"side_nav_{key}",
            type="primary" if is_active else "secondary",
            width="stretch",
            help=hint,
        ):
            if not is_active:
                set_nav_page(key)

    st.markdown(
        f'<p class="sidebar-nav-active-hint">Viewing · '
        f'{html.escape(NAV_LABELS.get(active_page, "Today"))}</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Appearance ────────────────────────────────────────
    st.markdown('<p class="sidebar-nav-label">Appearance</p>', unsafe_allow_html=True)
    theme_labels = [THEME_OPTIONS[k]["label"] for k in THEME_OPTIONS]
    theme_keys = list(THEME_OPTIONS.keys())
    try:
        current_idx = theme_keys.index(theme_name)
    except ValueError:
        current_idx = theme_keys.index(DEFAULT_THEME)
    picked_label = st.selectbox(
        "UI theme",
        theme_labels,
        index=current_idx,
        key="ui_theme_select",
        label_visibility="collapsed",
    )
    picked_key = theme_keys[theme_labels.index(picked_label)]
    st.caption(THEME_OPTIONS[picked_key]["description"])
    if picked_key != theme_name:
        try:
            set_setting(UI_THEME_KEY, picked_key)
        except Exception:
            pass
        st.session_state.ui_theme = picked_key
        st.rerun()

    # ── Collapsed utilities so nav stays primary ──────────
    with st.expander("Study goal", expanded=False):
        if "daily_goal_input" not in st.session_state:
            st.session_state.daily_goal_input = float(daily_goal)
        new_goal = st.number_input(
            "Hours per day",
            min_value=0.5,
            max_value=16.0,
            step=0.5,
            key="daily_goal_input",
        )
        if st.button("Save goal", key="save_goal_main", width="stretch"):
            if run_db(
                lambda: set_daily_study_goal(new_goal),
                "Could not save study goal",
            ) is not None:
                st.success("Goal saved!")
                st.rerun()

    with st.expander("Sync & backup", expanded=False):
        st.markdown("**Phone → PC**")
        st.caption(
            "Export from the phone app, then import the .db here."
        )
        sync_meta = get_sync_metadata()
        if sync_meta["exists"]:
            st.caption(
                f"PC database · {sync_meta['size_kb']} KB · "
                f"updated {sync_meta['modified']}"
            )
        else:
            st.caption("No data on this PC yet — import from your phone.")

        uploaded_db = st.file_uploader(
            "Phone sync file (.db)",
            type=["db"],
            key="phone_sync_upload",
            label_visibility="collapsed",
        )
        if uploaded_db is not None:
            st.caption(f"Selected: {uploaded_db.name} ({uploaded_db.size / 1024:.1f} KB)")
        if uploaded_db is not None and st.button(
            "Import phone data",
            type="primary",
            key="import_phone_sync",
            width="stretch",
        ):
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                tmp.write(uploaded_db.getvalue())
                tmp_path = tmp.name
            result = run_db(
                lambda: import_database(tmp_path),
                "Could not import phone data",
            )
            if result is not None:
                st.session_state.pop("phone_sync_upload", None)
                st.success("Phone data synced to this computer!")
                if result.get("backup_path"):
                    st.caption(f"Previous PC copy backed up to:\n`{result['backup_path']}`")
                st.rerun()

        st.markdown("**GitHub**")
        st.caption(
            "Pushes when you save data (or tap Sync now). "
            "Your phone app can **Pull from GitHub** on the Sync tab to load the same hours & tests."
        )
        git_status = get_sync_status()
        st.caption(
            "Internet: connected" if git_status["online"] else "Internet: offline"
        )
        if git_status.get("last_success"):
            st.caption(f"Last pushed: {git_status['last_success']}")
        st.caption(git_status["message"])
        if st.button("Sync to GitHub now", key="git_sync_now", width="stretch"):
            with st.spinner("Pushing to GitHub..."):
                result = sync_to_github(force=True)
            if result.get("ok"):
                if result.get("reason") == "unchanged":
                    st.info("Already up to date on GitHub.")
                else:
                    st.success("Data pushed to GitHub!")
            else:
                st.error(result.get("error") or result.get("reason", "Sync failed"))
            st.rerun()

    with st.expander("Desktop & tools", expanded=False):
        st.markdown("**Study sticker**")
        st.caption(
            "Floating sticker while you read PDFs. Launch via Start Tracker.bat."
        )
        if st.button("Install sticker on Windows startup", key="install_startup", width="stretch"):
            script = os.path.join(os.path.dirname(__file__), "scripts", "install_startup.ps1")
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
                check=False,
            )
            st.success("Sticker + app auto-start on login.")
        if st.button("Stop / remove old sticker", key="stop_sticker", width="stretch"):
            script = os.path.join(os.path.dirname(__file__), "scripts", "stop_sticker.ps1")
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
                check=False,
            )
            st.success("Old sticker processes stopped.")

        st.markdown("**Quick launch**")
        if st.button("Create / refresh desktop shortcut", key="make_shortcut", width="stretch"):
            script = os.path.join(
                os.path.dirname(__file__), "scripts", "create_desktop_shortcut.ps1"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
                check=False,
            )
            st.success("Shortcut updated on your Desktop.")

        st.markdown("**Android APK**")
        st.caption("Run scripts\\build_apk.ps1 after JDK 17 + Android SDK.")

        st.markdown("**Data storage**")
        st.caption("Saved locally — persists year-round.")
        st.code(DB_PATH, language=None)


def render_target_item(item):
    """Desktop target row with inline actions."""
    item_id = int(item["id"])
    status = item.get("status", "Pending")
    is_done = status == "Done"
    is_skipped = status == "Skipped"
    safe_desc = html.escape(item["description"])

    with st.container(border=True):
        row = st.columns([0.06, 0.74, 0.2])
        with row[0]:
            if not is_skipped:
                st.checkbox(
                    "done",
                    value=is_done,
                    key=f"chk_{item_id}",
                    label_visibility="collapsed",
                    on_change=on_target_toggle,
                    args=(item_id,),
                )
            else:
                st.markdown("⏭️")
        with row[1]:
            if is_done:
                st.markdown(
                    f'<p class="target-card-text target-done">✅ {safe_desc}</p>',
                    unsafe_allow_html=True,
                )
            elif is_skipped:
                st.markdown(
                    f'<p class="target-card-text target-skipped">⏭️ {safe_desc} (skipped)</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p class="target-card-text">⬜ {safe_desc}</p>',
                    unsafe_allow_html=True,
                )
        with row[2]:
            if not is_done and not is_skipped:
                if st.button("Skip", key=f"skip_{item_id}", width="stretch"):
                    on_target_skip(item_id)
                    st.rerun()
            elif is_skipped:
                if st.button("Undo", key=f"unskip_{item_id}", width="stretch"):
                    on_target_unskip(item_id)
                    st.rerun()


def period_of_day(now):
    if now.hour < MORNING_END_HOUR:
        return "morning", "🌅 Morning"
    if now.hour < EVENING_START_HOUR:
        return "afternoon", "☀️ Afternoon"
    return "evening", "🌙 Evening"


def all_targets_resolved(items):
    if not items:
        return False
    return all(i.get("status") in ("Done", "Skipped") for i in items)


def has_duplicate_descriptions(targets):
    descriptions = [t.strip().lower() for t in targets if t.strip()]
    return len(descriptions) != len(set(descriptions))


def _is_missing(value):
    """True for None / NaN / blank / placeholder empty strings from the data editor."""
    if value is None:
        return True
    try:
        if bool(pd.isna(value)):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip().lower() in ("", "none", "nan", "nat", "-"):
        return True
    return False


def parse_optional_number(value):
    """Return float, None if blank, or raise ValueError if non-numeric junk."""
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("not a number") from exc


def normalize_test_status(value):
    text = "" if _is_missing(value) else str(value).strip()
    if text.lower() in ("attempted", "done", "given"):
        return "Attempted"
    return "Not Attempted"


def validate_test_rows(edit_df):
    """Validate schedule/result rows.

    Attempted + no score is allowed (evaluation often lags the attempt).
    Score is only required/checked when the user actually typed marks.
    """
    errors = []
    for _, row in edit_df.iterrows():
        test_no = int(row["test_no"])
        status = normalize_test_status(row["status"] if "status" in row.index else None)

        if "subject" in row.index:
            subject = row["subject"]
            if _is_missing(subject) or not str(subject).strip():
                errors.append(f"Test #{test_no}: subject is required.")

        try:
            max_score = parse_optional_number(
                row["max_score"] if "max_score" in row.index else None
            )
        except ValueError:
            errors.append(f"Test #{test_no}: Out of (total marks) must be a number.")
            continue
        if max_score is not None and max_score <= 0:
            errors.append(f"Test #{test_no}: Out of (total marks) must be > 0.")
            max_score = None

        # Marks optional for Attempted — only validate when a score is present.
        try:
            score = parse_optional_number(row["score"] if "score" in row.index else None)
        except ValueError:
            errors.append(f"Test #{test_no}: score must be a number (or leave blank).")
            continue

        if score is None:
            continue
        if status != "Attempted":
            # Score typed while still Not Attempted — still check bounds if Out of is set.
            pass
        if max_score is None:
            errors.append(f"Test #{test_no}: set Out of (total marks) when entering a score.")
        elif score > max_score:
            errors.append(
                f"Test #{test_no}: score cannot exceed Out of ({max_score:g})."
            )
    return errors


def _values_equal(a, b):
    if _is_missing(a):
        a = None
    if _is_missing(b):
        b = None
    if a is not None and hasattr(a, "isoformat"):
        a = str(a.isoformat())[:10]
    if b is not None and hasattr(b, "isoformat"):
        b = str(b.isoformat())[:10]
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # Numeric equality (100 vs 100.0) and trimmed strings for status/text.
    try:
        if float(a) == float(b):
            return True
    except (TypeError, ValueError):
        pass
    return str(a).strip() == str(b).strip()


def test_row_changed(original_df, edited_row, cols=None):
    test_no = int(edited_row["test_no"])
    original = original_df[original_df["test_no"] == test_no].iloc[0]
    cols = cols or ("status", "score", "max_score", "remarks")
    for col in cols:
        if col not in original.index or col not in edited_row.index:
            continue
        left, right = original[col], edited_row[col]
        if col == "status":
            left = normalize_test_status(left)
            right = normalize_test_status(right)
        if not _values_equal(left, right):
            return True
    return False


def parse_test_result_fields(row):
    """Status + optional score/max/remarks for DB writes (score may be empty)."""
    status = normalize_test_status(row["status"] if "status" in row.index else None)
    try:
        score = parse_optional_number(row["score"] if "score" in row.index else None)
    except ValueError:
        score = None
    try:
        max_score = parse_optional_number(
            row["max_score"] if "max_score" in row.index else None
        )
    except ValueError:
        max_score = None
    if status == "Not Attempted":
        score = None
    remarks = ""
    if "remarks" in row.index and not _is_missing(row["remarks"]):
        remarks = str(row["remarks"])
    return status, score, max_score, remarks


PRELIMS_EDIT_COLS = (
    "test_no",
    "paper",
    "test_type",
    "subject",
    "scheduled_date",
    "topic_focus",
    "max_score",
    "status",
    "score",
    "remarks",
)
PRELIMS_COMPARE_COLS = (
    "paper",
    "test_type",
    "subject",
    "scheduled_date",
    "topic_focus",
    "max_score",
    "status",
    "score",
    "remarks",
)


def render_score_trend_chart(progress, title):
    if progress["scores"].empty:
        st.info("Score trend will appear after you log marks for an attempted test.")
        return
    chart_df = progress["scores"].copy()
    if "scheduled_date" in chart_df.columns:
        chart_df["scheduled_date"] = pd.to_datetime(chart_df["scheduled_date"], errors="coerce")
    y_col = (
        "score_pct"
        if "score_pct" in chart_df.columns and chart_df["score_pct"].notna().any()
        else "score"
    )
    # Skip attempted tests still awaiting evaluation (no marks yet)
    if y_col in chart_df.columns:
        chart_df = chart_df[chart_df[y_col].notna()]
    if chart_df.empty:
        st.info(
            "You've marked tests as Attempted — add scores when evaluation is out "
            "to see the trend."
        )
        return
    y_label = "Score %" if y_col == "score_pct" else "Score"
    fig = px.line(
        chart_df,
        x="test_no",
        y=y_col,
        markers=True,
        title=title,
        labels={"test_no": "Test #", y_col: y_label},
    )
    tokens = chart_theme_tokens()
    fig.update_traces(line_color=tokens["line"], marker_color=tokens["marker"])
    apply_plotly_layout(fig, height=360, tokens=tokens)
    st.plotly_chart(fig, width="stretch")


def render_next_test_card(next_test, *, heading="Next Test", undated_label=None):
    if not next_test:
        return
    raw_date = next_test.get("scheduled_date")
    has_date = (
        raw_date is not None
        and not (isinstance(raw_date, float) and pd.isna(raw_date))
        and str(raw_date).strip() not in ("", "None", "NaT", "nan")
    )
    if has_date:
        test_date = pd.to_datetime(raw_date).strftime("%d %b %Y")
        days_left = (pd.to_datetime(raw_date).date() - today).days
        if days_left > 0:
            countdown = f" · {days_left} day(s) away"
        elif days_left == 0:
            countdown = " · Today!"
        else:
            countdown = " · Overdue"
        date_line = f"{test_date}{countdown}"
    else:
        date_line = undated_label or "Date TBD — fill schedule when released"

    safe_subject = html.escape(str(next_test.get("subject") or ""))
    safe_type = html.escape(str(next_test.get("test_type") or ""))
    safe_topic = html.escape(str(next_test.get("topic_focus") or ""))
    paper = next_test.get("paper") or next_test.get("level") or ""
    paper_bit = f" · {html.escape(str(paper))}" if paper else ""
    st.markdown(
        f"""
    <div class="next-test-card">
        <h3>{html.escape(heading)}</h3>
        <p class="test-title">Test #{int(next_test['test_no'])} — {safe_subject}</p>
        <p class="test-date">{html.escape(date_line)}{paper_bit} · {safe_type} · {safe_topic}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_series_metrics(progress):
    completion_pct = (
        round(progress["attempted"] / progress["total"] * 100)
        if progress["total"]
        else None
    )
    avg_label = "—"
    if progress["avg_score"] is not None:
        avg_label = (
            f"{progress['avg_score']}%"
            if progress.get("avg_is_pct")
            else str(progress["avg_score"])
        )
    cols = st.columns(5 if "dated" in progress else 4)
    cols[0].metric("Attempted", f"{progress['attempted']}/{progress['total']}")
    cols[1].metric("Avg score", avg_label)
    cols[2].metric("Completion", f"{completion_pct}%" if completion_pct is not None else "—")
    cols[3].metric("Remaining", progress["total"] - progress["attempted"])
    if "dated" in progress and len(cols) > 4:
        cols[4].metric("Dates set", f"{progress['dated']}/{progress['total']}")


def draft_count_key(plan_date):
    return f"draft_count_{plan_date.isoformat()}"


def draft_field_key(plan_date, index):
    return f"draft_{plan_date.isoformat()}_{index}"


def init_draft_form(plan_date, descriptions=None):
    items = list(descriptions) if descriptions else ["", ""]
    st.session_state[draft_count_key(plan_date)] = len(items)
    for index, text in enumerate(items):
        st.session_state[draft_field_key(plan_date, index)] = text


def read_draft_targets(plan_date):
    count = st.session_state.get(draft_count_key(plan_date), 2)
    return [
        st.session_state.get(draft_field_key(plan_date, index), "").strip()
        for index in range(count)
    ]


def clear_draft_form(plan_date):
    init_draft_form(plan_date)


def render_target_form(plan_date, label):
    st.markdown(f"**{label}**")
    if draft_count_key(plan_date) not in st.session_state:
        init_draft_form(plan_date)

    count = st.session_state[draft_count_key(plan_date)]
    for index in range(count):
        st.text_input(
            f"Target {index + 1}",
            key=draft_field_key(plan_date, index),
            placeholder="e.g. Paper-7 welfare notes + 10 PYQs",
        )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("＋ Add target", key=f"add_{plan_date}"):
            if count >= MAX_TARGETS_PER_DAY:
                st.warning(f"You can add up to {MAX_TARGETS_PER_DAY} targets per day.")
            else:
                next_index = st.session_state[draft_count_key(plan_date)]
                st.session_state[draft_count_key(plan_date)] = next_index + 1
                st.session_state[draft_field_key(plan_date, next_index)] = ""
                st.rerun()
    with b2:
        if count > 1 and st.button("－ Remove last", key=f"remove_{plan_date}"):
            st.session_state[draft_count_key(plan_date)] = count - 1
            st.rerun()
    if st.button("Save Targets", type="primary", key=f"save_{plan_date}"):
        descriptions = read_draft_targets(plan_date)
        targets = [
            {"description": text, "planned_hours": 0}
            for text in descriptions
            if text
        ]
        if not targets:
            st.error("Add at least one target before saving.")
        elif len(targets) > MAX_TARGETS_PER_DAY:
            st.error(f"You can save up to {MAX_TARGETS_PER_DAY} targets per day.")
        elif has_duplicate_descriptions([t["description"] for t in targets]):
            st.error("Each target must have a unique description.")
        elif run_db(
            lambda: save_daily_targets(plan_date, targets),
            "Could not save targets",
        ) is None:
            pass
        else:
            clear_draft_form(plan_date)
            st.session_state.show_target_form = False
            st.session_state.planning_date = None
            st.success(
                f"Saved {len(targets)} target(s) for {FIRST_NAME} on "
                f"{plan_date.strftime('%d %b %Y')}!"
            )
            st.rerun()


def on_target_toggle(item_id):
    checked = st.session_state[f"chk_{item_id}"]
    if run_db(
        lambda: update_target_status(item_id, "Done" if checked else "Pending"),
        "Could not update target",
    ) is not None and checked:
        queue_garden_reward(award_target_done_xp())


def on_target_skip(item_id):
    run_db(
        lambda: update_target_status(item_id, "Skipped"),
        "Could not skip target",
    )


def on_target_unskip(item_id):
    run_db(
        lambda: update_target_status(item_id, "Pending"),
        "Could not restore target",
    )


def render_today_action_rail(today_date, goal_hours):
    """Right rail for the Today workspace: quick hours + logbook."""
    try:
        today_hours = get_study_hours_for_date(today_date)
    except DatabaseError:
        today_hours = 0.0

    progress = min(today_hours / goal_hours, 1.0) if goal_hours else 0.0
    st.markdown(
        f'<p class="section-label">Hours</p>'
        f'<p class="section-title rail-title">{today_hours:g}h '
        f'<span class="rail-muted">/ {goal_hours:g}h goal</span></p>',
        unsafe_allow_html=True,
    )
    st.progress(progress)
    st.markdown(
        '<p class="dash-rail-note">Log time as you study. Full charts live in the Hours tab.</p>',
        unsafe_allow_html=True,
    )
    with st.form("today_rail_hours_form", clear_on_submit=True):
        hours = st.number_input(
            "Hours to add",
            min_value=0.25,
            max_value=16.0,
            step=0.25,
            value=1.0,
            key="rail_hours_value",
        )
        notes = st.text_input(
            "Notes",
            placeholder="Optional note",
            key="rail_hours_notes",
            label_visibility="collapsed",
        )
        if st.form_submit_button("Save hours", type="primary", width="stretch"):
            if run_db(
                lambda: add_daily_study_hours(today_date, hours, notes),
                "Could not log study hours",
            ) is not None:
                queue_garden_reward(award_hours_garden_xp(hours))
                show_harvest_unlock(today_date)
                st.toast(f"Logged {hours}h", icon="⏱️")
                st.rerun()

    st.divider()

    try:
        from atlas import get_atlas_overview

        atlas_now = get_atlas_overview(today_date)
    except Exception:
        atlas_now = None
    if atlas_now and (atlas_now["due_today"] or atlas_now["unseen"]):
        due_n = atlas_now["due_today"]
        fog_n = atlas_now["unseen"]
        bits = []
        if due_n:
            bits.append(f"{due_n} due for revision")
        if fog_n:
            bits.append(f"{fog_n} still in fog")
        st.markdown(
            f'<div class="atlas-due-rail">'
            f'<p class="atlas-due-kicker">Atlas</p>'
            f'<p class="atlas-due-body">{html.escape(" · ".join(bits))}. '
            f'Scout one dark cell, hold one old one.</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Open Atlas", key="rail_open_atlas", width="stretch"):
            set_nav_page("atlas")

    st.markdown(
        f'<p class="section-label">Logbook</p>'
        f'<p class="section-title rail-title">What did you study?</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="dash-rail-note">One line is enough. Browse history in the Logbook tab.</p>',
        unsafe_allow_html=True,
    )

    paper_options = [s for s in LOG_SUBJECTS if s]
    if "rail_logbook_paper" not in st.session_state:
        st.session_state.rail_logbook_paper = paper_options[0] if paper_options else ""

    rail_paper = st.selectbox(
        "Paper",
        paper_options,
        index=max(
            0,
            paper_options.index(st.session_state.rail_logbook_paper)
            if st.session_state.rail_logbook_paper in paper_options
            else 0,
        ),
        key="rail_paper_select",
        label_visibility="collapsed",
    )
    st.session_state.rail_logbook_paper = rail_paper

    rail_text = st.text_input(
        "Quick log",
        placeholder="e.g. Welfare schemes + 5 PYQs",
        key="rail_quick_log_text",
        label_visibility="collapsed",
    )
    if st.button("Log it", type="primary", width="stretch", key="rail_quick_log_save"):
        if not rail_text.strip():
            st.error("Write what you studied.")
        elif run_db(
            lambda: add_activity_log(
                today_date,
                rail_text,
                st.session_state.rail_logbook_paper,
                None,
            ),
            "Could not save log entry",
        ) is not None:
            st.session_state.pop("rail_quick_log_text", None)
            st.toast("Logged!", icon="📓")
            st.rerun()

    try:
        recent_entries = get_activity_logs(year=today_date.year, limit=4)
    except DatabaseError:
        recent_entries = pd.DataFrame()

    if recent_entries is not None and not getattr(recent_entries, "empty", True):
        st.caption("Recent")
        for _, row in recent_entries.head(4).iterrows():
            entry_date = pd.to_datetime(row["log_date"]).strftime("%d %b")
            subject_label = row["subject"] or "General"
            safe_activity = html.escape(str(row["activity"]))
            safe_subject = html.escape(str(subject_label))
            st.markdown(
                f'<div class="log-entry">'
                f'<div class="log-entry-meta">{entry_date} · {safe_subject}</div>'
                f'<div class="log-entry-body">{safe_activity}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


ensure_db_ready()
flush_pending_garden_toasts()

now = datetime.now()
today = date.today()
show_harvest_unlock(today)
tomorrow = today + timedelta(days=1)
period_key, period_label = period_of_day(now)
try:
    daily_goal = get_daily_study_goal()
    streak = get_study_streak()
    longest_streak = get_longest_streak()
    garden_state = get_garden_state(streak)
    garden_state["stage_info"] = get_stage_info(garden_state["xp"])
except DatabaseError:
    daily_goal = 6.0
    streak = 0
    longest_streak = None
    garden_state = {"xp": 0, "stage_info": get_stage_info(0), "events": pd.DataFrame()}

if "garden_session_awarded" not in st.session_state:
    xp_before = garden_state["xp"]
    session_rewards = process_daily_checkin(streak)
    session_rewards += sync_daily_garden_bonuses(today)
    show_garden_rewards(session_rewards, xp_before)
    garden_state = get_garden_state(streak)
    garden_state["stage_info"] = get_stage_info(garden_state["xp"])
    st.session_state.garden_session_awarded = True
else:
    xp_before = garden_state["xp"]
    milestone_rewards = sync_daily_garden_bonuses(today)
    if milestone_rewards:
        show_garden_rewards(milestone_rewards, xp_before)
        garden_state = get_garden_state(streak)
        garden_state["stage_info"] = get_stage_info(garden_state["xp"])

# Theme + nav before chrome so CSS and sidebar apply first
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = load_ui_theme()
ui_theme = resolve_theme(st.session_state.ui_theme)
apply_theme_css(ui_theme)
active_page = resolve_nav_page()

with st.sidebar:
    render_sidebar(ui_theme, active_page)

st.markdown(
    f"""
    <div class="app-hero">
        <div class="app-hero-top">
            <span class="app-hero-chip">{html.escape(EXAM)} · {EXAM_YEAR}</span>
            <span class="period-badge {PERIOD_BADGES[period_key]}">{html.escape(period_label)}</span>
        </div>
        <p class="app-hero-title">{html.escape(possessive("CGPSC Tracker"))}</p>
        <p class="app-hero-greeting">{html.escape(greeting(period_key))}</p>
        <p class="app-hero-motto">{html.escape(period_nudge(period_key))}</p>
        <p class="app-hero-meta">
            {now.strftime("%A, %d %B %Y")} · {now.strftime("%I:%M %p")}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Custom metric strip (clearer hierarchy than bare st.metric row)
best_streak_val = longest_streak if longest_streak is not None else 0
st.markdown(
    f"""
    <div class="metric-strip">
        <div class="metric-tile m-streak">
            <p class="metric-tile-label">Study streak</p>
            <p class="metric-tile-value">{streak} days</p>
            <p class="metric-tile-hint">Keep showing up</p>
        </div>
        <div class="metric-tile m-goal">
            <p class="metric-tile-label">Daily goal</p>
            <p class="metric-tile-value">{daily_goal:g} h</p>
            <p class="metric-tile-hint">Hours target</p>
        </div>
        <div class="metric-tile m-xp">
            <p class="metric-tile-label">Garden XP</p>
            <p class="metric-tile-value">{garden_state['xp']:,}</p>
            <p class="metric-tile-hint">Growth score</p>
        </div>
        <div class="metric-tile m-best">
            <p class="metric-tile-label">Best streak</p>
            <p class="metric-tile-value">{best_streak_val} days</p>
            <p class="metric-tile-hint">Personal record</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

heatmap_start = today - timedelta(days=400)
try:
    showup_hours = load_showup_hours(heatmap_start, today)
except DatabaseError:
    showup_hours = {}
# Always visible under the metrics (not tucked in an expander)
st.markdown(
    render_github_heatmap(
        showup_hours,
        streak=streak,
        daily_goal=daily_goal,
    ),
    unsafe_allow_html=True,
)

# Page context chip (nav lives in the sidebar)
active_label = NAV_LABELS.get(active_page, "Today")
active_icon = NAV_ICONS.get(active_page, "·")
st.markdown(
    f"""
    <div class="page-context">
        <span class="page-context-chip">{html.escape(active_icon)} {html.escape(active_label)}</span>
        <span class="page-context-hint">Use the sidebar to switch modules</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if active_page == "atlas":
    render_atlas_page(run_db, queue_garden_reward, today)

elif active_page == "today":
    try:
        summary = get_daily_plan_summary(today)
        plan = get_daily_plan(today)
        tomorrow_summary = get_daily_plan_summary(tomorrow)
    except DatabaseError as exc:
        st.error(f"Could not load daily targets: {exc}")
        st.stop()

    if "show_target_form" not in st.session_state:
        st.session_state.show_target_form = False
    if "planning_date" not in st.session_state:
        st.session_state.planning_date = None
    if "tomorrow_prompt_dismissed_date" not in st.session_state:
        st.session_state.tomorrow_prompt_dismissed_date = None

    # Full-width form when planning; otherwise split workspace (targets | actions).
    use_split_workspace = not (
        st.session_state.show_target_form and st.session_state.planning_date
    )

    if use_split_workspace:
        main_col, rail_col = st.columns([1.7, 1], gap="large")
    else:
        main_col = st.container()
        rail_col = None

    with main_col:
        if summary["has_plan"] and not st.session_state.show_target_form:
            head_l, head_r = st.columns([3, 1])
            with head_l:
                st.markdown(
                    f'<p class="section-label">Targets</p>'
                    f'<p class="section-title">{FIRST_NAME}\'s targets · '
                    f'{summary["done"]}/{summary["total_targets"]} done</p>',
                    unsafe_allow_html=True,
                )
            with head_r:
                with st.popover("＋ More"):
                    st.caption("Quick-add one target")
                    quick_desc = st.text_input(
                        "New target",
                        placeholder="e.g. Paper-5 economy PYQs",
                        key="quick_add_target",
                        label_visibility="collapsed",
                    )
                    if st.button("Add", key="quick_add_btn", width="stretch"):
                        if not quick_desc.strip():
                            st.error("Write a target first.")
                        elif run_db(
                            lambda: add_daily_target(today, quick_desc),
                            "Could not add target",
                        ) is not None:
                            st.session_state.pop("quick_add_target", None)
                            st.rerun()
                    if st.button("Replace all targets", key="replace_all_targets"):
                        st.session_state.show_target_form = True
                        st.session_state.planning_date = today
                        if plan and plan["items"]:
                            init_draft_form(
                                today,
                                [i["description"] for i in plan["items"]] + [""],
                            )
                        else:
                            init_draft_form(today)
                        st.rerun()

            third_metric = (
                ("Skipped", str(summary["skipped"]))
                if summary["skipped"]
                else ("Done %", f"{summary['completion_pct']}%")
            )
            render_metric_rows(
                [
                    [
                        ("Done", f"{summary['done']}/{summary['total_targets']}"),
                        ("Pending", str(summary["pending"])),
                    ],
                    [third_metric, ("Resolved", f"{summary['resolved_pct']}%")],
                ]
            )
            st.progress(summary["resolved_pct"] / 100)

            # Single column of targets reads better in the left pane.
            for item in plan["items"]:
                render_target_item(item)

            if all_targets_resolved(plan["items"]):
                st.success(f"All targets resolved — great work, {FIRST_NAME}!")
                show_tomorrow_prompt = (
                    not tomorrow_summary["has_plan"]
                    and st.session_state.tomorrow_prompt_dismissed_date
                    != today.isoformat()
                    and not st.session_state.show_target_form
                )
                if show_tomorrow_prompt:
                    t1, t2 = st.columns(2)
                    with t1:
                        if st.button(
                            "Plan tomorrow", type="primary", key="tomorrow_yes"
                        ):
                            st.session_state.show_target_form = True
                            st.session_state.planning_date = tomorrow
                            init_draft_form(tomorrow)
                            st.rerun()
                    with t2:
                        if st.button("Not now", key="tomorrow_no"):
                            st.session_state.tomorrow_prompt_dismissed_date = (
                                today.isoformat()
                            )
                            st.rerun()

                reflection = (plan.get("evening_reflection") or "") if plan else ""
                if "evening_reflection_input" not in st.session_state:
                    st.session_state.evening_reflection_input = reflection
                with st.expander("🌙 Evening reflection", expanded=False):
                    st.text_area(
                        "Quick note for tomorrow",
                        key="evening_reflection_input",
                        placeholder="What worked? What to fix tomorrow?",
                        height=80,
                    )
                    if st.button("Save reflection", key="save_reflection"):
                        if run_db(
                            lambda: save_evening_reflection(
                                today, st.session_state.evening_reflection_input
                            ),
                            "Could not save reflection",
                        ) is not None:
                            st.success("Saved!")
                            st.rerun()

        elif not st.session_state.show_target_form:
            yesterday = today - timedelta(days=1)
            try:
                unfinished_yesterday = get_unfinished_targets(yesterday)
            except DatabaseError:
                unfinished_yesterday = []

            st.markdown(
                f'<p class="section-label">No plan yet</p>'
                f'<p class="section-title">{greeting(period_key)}</p>',
                unsafe_allow_html=True,
            )
            st.caption(period_nudge(period_key))

            if unfinished_yesterday:
                count = len(unfinished_yesterday)
                label = "target" if count == 1 else "targets"
                bullet_list = "\n".join(
                    f"- {item['description']}" for item in unfinished_yesterday
                )
                st.info(
                    f"Yesterday left **{count} unfinished {label}**:\n\n"
                    f"{bullet_list}\n\n"
                    "Carry them into today in one click, or start fresh."
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "Carry over unfinished",
                        type="primary",
                        key="carry_over_yesterday",
                        width="stretch",
                    ):
                        carried = run_db(
                            lambda: carry_over_unfinished_targets(yesterday, today),
                            "Could not carry over targets",
                        )
                        if carried is not None:
                            st.success(
                                f"Carried over {carried} target(s) from yesterday."
                            )
                            st.rerun()
                with c2:
                    if st.button(
                        "Set today's targets",
                        key="set_today_targets",
                        width="stretch",
                    ):
                        st.session_state.show_target_form = True
                        st.session_state.planning_date = today
                        init_draft_form(
                            today,
                            [item["description"] for item in unfinished_yesterday]
                            + [""],
                        )
                        st.rerun()
            else:
                if st.button(
                    "Set today's targets", type="primary", key="set_today_targets"
                ):
                    st.session_state.show_target_form = True
                    st.session_state.planning_date = today
                    init_draft_form(today)
                    st.rerun()

        if st.session_state.show_target_form and st.session_state.planning_date:
            plan_label = (
                "Set today's targets"
                if st.session_state.planning_date == today
                else (
                    "Set targets for "
                    f"{st.session_state.planning_date.strftime('%A, %d %b')}"
                )
            )
            render_target_form(st.session_state.planning_date, plan_label)
            if st.button("Cancel", key="cancel_form"):
                clear_draft_form(st.session_state.planning_date)
                st.session_state.show_target_form = False
                st.session_state.planning_date = None
                st.rerun()

    if rail_col is not None:
        with rail_col:
            render_today_action_rail(today, daily_goal)

elif active_page == "hours":
    try:
        today_hours = get_study_hours_for_date(today)
        week_df = get_week_study_hours(today)
        hours_summary = get_study_hours_summary()
    except DatabaseError as exc:
        st.error(f"Could not load study hours: {exc}")
        st.stop()
    week_total = round(week_df["hours"].sum(), 1)
    goal_progress = min(today_hours / daily_goal, 1.0) if daily_goal else 0
    lifetime_total = hours_summary["total_hours"]
    study_days = hours_summary["study_days"]
    best_hours = hours_summary["best_hours"]
    avg_study_day = hours_summary["avg_hours"]

    st.markdown(
        f'<p class="section-label">Deep dive</p>'
        f'<p class="section-title">{html.escape(possessive("Study Hours"))}</p>'
        f'<p class="workspace-hint">Charts, history, and export. Quick logging lives on the Today right rail.</p>',
        unsafe_allow_html=True,
    )

    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("Today", f"{today_hours}h", f"Goal {daily_goal:g}h")
    o2.metric("This week", f"{week_total}h")
    o3.metric("All-time hours", f"{lifetime_total:g}h")
    o4.metric("Study days", f"{study_days}")
    o5.metric(
        "Best day",
        f"{best_hours:g}h" if best_hours else "—",
        (
            hours_summary["best_date"].strftime("%d %b")
            if hours_summary.get("best_date")
            else None
        ),
    )
    st.progress(goal_progress)
    if study_days:
        st.caption(
            f"Avg on days you showed up: **{avg_study_day:g}h** · "
            f"First log: {hours_summary['first_date'].strftime('%d %b %Y')} · "
            f"Last study day: {hours_summary['last_date'].strftime('%d %b %Y')}"
        )

    hours_left, hours_right = st.columns([1, 1.8])

    with hours_left:
        st.markdown("**Log study time**")
        with st.form("study_hours_form", clear_on_submit=True):
            log_date = st.date_input("Date", today)
            existing = get_study_hours_for_date(log_date)
            if existing > 0:
                st.caption(
                    f"Already logged **{existing}h** — new hours will be added."
                )
            hours = st.number_input(
                "Hours studied", min_value=0.25, max_value=16.0, step=0.25, value=2.0
            )
            notes = st.text_input(
                "Notes (optional)",
                placeholder="e.g. Paper-7 current affairs + answer writing",
            )
            if st.form_submit_button("Save Hours", type="primary", width="stretch"):
                if run_db(
                    lambda: add_daily_study_hours(log_date, hours, notes),
                    "Could not log study hours",
                ) is not None:
                    queue_garden_reward(award_hours_garden_xp(hours))
                    show_harvest_unlock(log_date)
                    st.success(
                        f"Nice work, {FIRST_NAME}! Logged {hours}h for "
                        f"{log_date.strftime('%d %b %Y')}."
                    )
                    st.rerun()

        try:
            recent = get_recent_study_hours()
        except DatabaseError as exc:
            st.error(f"Could not load recent study hours: {exc}")
            recent = pd.DataFrame()
        if not recent.empty:
            st.markdown("**Recent log**")
            recent = recent.copy()
            recent["log_date"] = pd.to_datetime(recent["log_date"]).dt.strftime("%d %b %Y")
            st.dataframe(
                recent[["log_date", "hours", "notes"]],
                column_config={
                    "log_date": "Date",
                    "hours": st.column_config.NumberColumn("Hours", format="%.1f h"),
                    "notes": "Notes",
                },
                hide_index=True,
                width="stretch",
            )
        else:
            st.caption(f"{FIRST_NAME}, no study hours logged yet.")

        st.markdown("**Export data**")
        export_frames = get_export_dataframes()
        exp_cols = st.columns(len(export_frames) or 1)
        for col, (name, frame) in zip(exp_cols, export_frames.items()):
            if frame.empty:
                continue
            with col:
                st.download_button(
                    label=f"{name}.csv",
                    data=frame.to_csv(index=False),
                    file_name=f"manish_{name}.csv",
                    mime="text/csv",
                    key=f"export_{name}",
                    width="stretch",
                )

    with hours_right:
        range_options = {
            "This week": "week",
            "Last 30 days": "30d",
            "Last 90 days": "90d",
            "All time": "all",
        }
        range_label = st.radio(
            "Chart range",
            list(range_options.keys()),
            horizontal=True,
            index=3 if lifetime_total > 0 else 0,
            key="hours_chart_range",
            help="Zoom out to see past effort when a quiet week feels heavy.",
        )
        range_key = range_options[range_label]
        chart_mode = st.radio(
            "View",
            ["Daily bars", "Cumulative effort", "Both"],
            horizontal=True,
            index=2 if range_key != "week" else 0,
            key="hours_chart_mode",
        )

        if range_key == "week":
            chart_start = today - timedelta(days=today.weekday())
            chart_end = chart_start + timedelta(days=6)
            fill_zeros = True
        elif range_key == "30d":
            chart_start = today - timedelta(days=29)
            chart_end = today
            fill_zeros = True
        elif range_key == "90d":
            chart_start = today - timedelta(days=89)
            chart_end = today
            fill_zeros = True
        else:
            first = hours_summary.get("first_date") or today
            chart_start = first
            chart_end = today
            # Sparse history looks better as study days only for long spans
            span_days = (chart_end - chart_start).days + 1
            fill_zeros = span_days <= 45

        try:
            if range_key == "week":
                chart_df = week_df.copy()
                cum = 0.0
                cum_vals = []
                for h in chart_df["hours"]:
                    cum += float(h)
                    cum_vals.append(round(cum, 2))
                chart_df["cumulative"] = cum_vals
            else:
                chart_df = get_study_hours_range(
                    chart_start, chart_end, fill_zeros=fill_zeros
                )
        except DatabaseError as exc:
            st.error(f"Could not load chart data: {exc}")
            chart_df = pd.DataFrame()

        if chart_df.empty:
            st.info(f"{FIRST_NAME}, no study hours in this range yet. Log some and watch the total grow.")
        else:
            range_total = round(float(chart_df["hours"].sum()), 1)
            active_days = int((chart_df["hours"] > 0).sum())
            st.caption(
                f"**{range_label}:** {range_total:g}h across {active_days} study day"
                f"{'' if active_days == 1 else 's'}"
                + (
                    " · calendar days with no log shown as 0h"
                    if fill_zeros and range_key != "week"
                    else " · only days you logged"
                    if not fill_zeros
                    else ""
                )
            )

            chart_tokens = chart_theme_tokens()

            def _hours_chart_layout(fig, height=420):
                return apply_plotly_layout(fig, height=height, tokens=chart_tokens)

            n_points = len(chart_df)
            if n_points <= 14:
                chart_df["label"] = chart_df.apply(
                    lambda r: f"{r['day']}<br>{r['log_date'].strftime('%d %b')}",
                    axis=1,
                )
            elif n_points <= 40:
                chart_df["label"] = chart_df["log_date"].map(
                    lambda d: d.strftime("%d %b")
                )
            else:
                chart_df["label"] = chart_df["log_date"].map(
                    lambda d: d.strftime("%d %b")
                )

            show_bars = chart_mode in ("Daily bars", "Both")
            show_cum = chart_mode in ("Cumulative effort", "Both")

            if show_bars:
                bar_df = chart_df.copy()
                bar_df["goal_met"] = bar_df["hours"] >= daily_goal
                colors = [
                    (
                        chart_tokens["today"]
                        if r["is_today"]
                        else chart_tokens["goal_met"]
                        if r["goal_met"]
                        else chart_tokens["logged"]
                        if r["hours"] > 0
                        else chart_tokens["empty"]
                    )
                    for _, r in bar_df.iterrows()
                ]
                fig_bar = px.bar(
                    bar_df,
                    x="label",
                    y="hours",
                    text="hours" if n_points <= 16 else None,
                    title=f"{FIRST_NAME}'s study hours · {range_label.lower()}",
                    labels={"label": "Day", "hours": "Hours"},
                )
                fig_bar.update_traces(
                    marker_color=colors,
                    texttemplate="%{text:.1f}h" if n_points <= 16 else None,
                    textposition="outside",
                    textfont_color=chart_tokens["text_on_bar"],
                )
                fig_bar.add_hline(
                    y=daily_goal,
                    line_dash="dash",
                    line_color=chart_tokens["goal_line"],
                    annotation_text=f"Goal ({daily_goal:g}h)",
                    annotation_font_color=chart_tokens["muted"],
                )
                y_max = max(
                    float(bar_df["hours"].max()) * 1.2 if bar_df["hours"].max() else 0,
                    daily_goal * 1.2,
                    4,
                )
                fig_bar.update_yaxes(range=[0, y_max])
                if n_points > 20:
                    fig_bar.update_xaxes(tickangle=-45)
                _hours_chart_layout(fig_bar, height=400 if show_cum else 480)
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, width="stretch")

            if show_cum:
                cum_df = chart_df.copy()
                # Start cumulative from all hours before this range so zoomed views
                # still show banked effort (a quiet week doesn't reset the climb).
                prior_total = 0.0
                first_log = hours_summary.get("first_date")
                if first_log and chart_start > first_log:
                    try:
                        prior_df = get_study_hours_range(
                            first_log,
                            chart_start - timedelta(days=1),
                            fill_zeros=False,
                        )
                        if not prior_df.empty:
                            prior_total = float(prior_df["hours"].sum())
                    except DatabaseError:
                        prior_total = 0.0
                running = prior_total
                rebuilt = []
                for h in cum_df["hours"]:
                    running += float(h)
                    rebuilt.append(round(running, 2))
                cum_df["cumulative"] = rebuilt

                fig_cum = px.area(
                    cum_df,
                    x="label",
                    y="cumulative",
                    title=f"{FIRST_NAME}'s cumulative effort · {range_label.lower()}",
                    labels={"label": "Day", "cumulative": "Total hours"},
                )
                fig_cum.update_traces(
                    line=dict(color=chart_tokens["line"], width=2.5),
                    fillcolor=chart_tokens["fill"],
                    hovertemplate="%{x}<br><b>%{y:.1f}h</b> total<extra></extra>",
                )
                if n_points > 20:
                    fig_cum.update_xaxes(tickangle=-45)
                _hours_chart_layout(fig_cum, height=360 if show_bars else 480)
                fig_cum.update_layout(showlegend=False)
                st.plotly_chart(fig_cum, width="stretch")
                final_cum = float(cum_df["cumulative"].iloc[-1]) if len(cum_df) else 0
                st.caption(
                    f"Total banked by end of range: **{final_cum:g}h** — quiet days don't take this away."
                )

elif active_page == "logbook":
    st.markdown(
        f'<p class="section-label">History</p>'
        f'<p class="section-title">Full logbook</p>'
        f'<p class="workspace-hint">Browse, export, and detailed entries. One-line logging is on Today.</p>',
        unsafe_allow_html=True,
    )

    try:
        year_stats = get_activity_log_stats(EXAM_YEAR)
        recent_entries = get_activity_logs(year=EXAM_YEAR, limit=20)
    except DatabaseError as exc:
        st.error(f"Could not load logbook: {exc}")
        st.stop()

    s1, s2 = st.columns(2)
    s1.metric(f"Days logged ({EXAM_YEAR})", year_stats["days_logged"])
    s2.metric(f"Entries ({EXAM_YEAR})", year_stats["total_entries"])

    paper_options = [s for s in LOG_SUBJECTS if s]
    if "logbook_paper" not in st.session_state:
        st.session_state.logbook_paper = paper_options[0] if paper_options else ""

    st.markdown("**Paper**")
    paper_cols = st.columns(min(len(paper_options), 4) or 1)
    for idx, paper in enumerate(paper_options):
        with paper_cols[idx % len(paper_cols)]:
            short = paper.split(" (")[0].replace("Paper-", "P") if paper else "Any"
            if st.button(
                short,
                key=f"log_paper_{idx}",
                width="stretch",
                type="primary" if st.session_state.logbook_paper == paper else "secondary",
            ):
                st.session_state.logbook_paper = paper
                st.rerun()

    log_cols = st.columns([4, 1])
    with log_cols[0]:
        quick_log = st.text_input(
            "Today's study",
            placeholder="e.g. Read welfare schemes + 5 PYQ notes",
            key="quick_log_text",
            label_visibility="collapsed",
        )
    with log_cols[1]:
        save_log = st.button("Log it", type="primary", width="stretch", key="quick_log_save")

    if save_log:
        if not quick_log.strip():
            st.error("Write what you studied.")
        elif run_db(
            lambda: add_activity_log(
                today,
                quick_log,
                st.session_state.logbook_paper,
                None,
            ),
            "Could not save log entry",
        ) is not None:
            st.session_state.pop("quick_log_text", None)
            st.toast("Logged!", icon="📓")
            st.rerun()

    st.markdown("**Recent**")
    if recent_entries.empty:
        st.info(f"No entries yet — log what you studied today, {FIRST_NAME}.")
    else:
        for _, row in recent_entries.iterrows():
            entry_id = int(row["id"])
            entry_date = pd.to_datetime(row["log_date"]).strftime("%d %b")
            subject_label = row["subject"] or "General"
            safe_activity = html.escape(str(row["activity"]))
            safe_subject = html.escape(str(subject_label))
            del_col, body_col = st.columns([0.12, 0.88])
            with del_col:
                if st.button("✕", key=f"del_log_{entry_id}", help="Delete"):
                    if run_db(
                        lambda eid=entry_id: delete_activity_log(eid),
                        "Could not delete entry",
                    ) is not None:
                        st.rerun()
            with body_col:
                st.markdown(
                    f'<div class="log-entry">'
                    f'<div class="log-entry-meta">{entry_date} · {safe_subject}</div>'
                    f'<div class="log-entry-body">{safe_activity}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with st.expander("More options — date, duration, export, browse"):
        with st.form("activity_log_advanced", clear_on_submit=True):
            adv_date = st.date_input("Date", today, key="logbook_entry_date")
            adv_subject = st.selectbox(
                "Paper",
                LOG_SUBJECTS,
                format_func=lambda s: "— Any —" if not s else s,
                key="logbook_entry_subject",
            )
            adv_activity = st.text_area("Details", key="logbook_entry_activity", height=80)
            adv_duration = st.number_input(
                "Hours (optional)", min_value=0.0, max_value=16.0, step=0.25, value=0.0,
                key="logbook_entry_duration",
            )
            if st.form_submit_button("Save detailed entry", width="stretch"):
                if not adv_activity.strip():
                    st.error("Write what you studied.")
                elif run_db(
                    lambda: add_activity_log(
                        adv_date,
                        adv_activity,
                        adv_subject,
                        adv_duration if adv_duration > 0 else None,
                    ),
                    "Could not save log entry",
                ) is not None:
                    st.rerun()

        export_frames = get_export_dataframes()
        activity_export = export_frames.get("activity_logs")
        if activity_export is not None and not activity_export.empty:
            st.download_button(
                label="Download activity_logs.csv",
                data=activity_export.to_csv(index=False),
                file_name=f"manish_activity_logs_{EXAM_YEAR}.csv",
                mime="text/csv",
                key="export_logbook_activity_logs",
                width="stretch",
            )

        browse_mode = st.radio(
            "Browse by", ["Month", "Full year"], horizontal=True, key="logbook_browse_mode"
        )
        if browse_mode == "Month":
            year_col, month_col = st.columns(2)
            view_year = year_col.number_input(
                "Year", min_value=2020, max_value=2035, value=EXAM_YEAR, key="logbook_year"
            )
            view_month = month_col.selectbox(
                "Month",
                list(range(1, 13)),
                format_func=lambda m: MONTH_NAMES[m - 1],
                index=today.month - 1,
                key="logbook_month",
            )
            entries = get_activity_logs(year=view_year, month=view_month, limit=500)
            st.caption(f"{MONTH_NAMES[view_month - 1]} {view_year} — {len(entries)} entries")
        else:
            view_year = st.number_input(
                "Year", min_value=2020, max_value=2035, value=EXAM_YEAR, key="logbook_full_year"
            )
            entries = get_activity_logs(year=view_year, limit=2000)
            st.caption(f"All of {view_year} — {len(entries)} entries")
        if not entries.empty:
            st.dataframe(
                entries[["log_date", "subject", "activity"]],
                hide_index=True,
                width="stretch",
            )

elif active_page == "tests":
    if "tests_series" not in st.session_state:
        st.session_state.tests_series = "mains"
    st.markdown(
        f'<p class="section-label">Exam prep</p>'
        f'<p class="section-title">{html.escape(possessive("Test Series"))}</p>'
        f'<p class="workspace-hint">Track mains and prelims schedules, scores, and progress in one place.</p>',
        unsafe_allow_html=True,
    )
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        if st.button(
            f"Mains · Monsoon {EXAM_YEAR}",
            key="tests_nav_mains",
            type="primary" if st.session_state.tests_series == "mains" else "secondary",
            width="stretch",
        ):
            st.session_state.tests_series = "mains"
            st.rerun()
    with tcol2:
        if st.button(
            "Prelims · Upcoming",
            key="tests_nav_prelims",
            type="primary" if st.session_state.tests_series == "prelims" else "secondary",
            width="stretch",
        ):
            st.session_state.tests_series = "prelims"
            st.rerun()

    if st.session_state.tests_series == "mains":
        st.subheader(f"Monsoon Test Series {EXAM_YEAR}")

        try:
            next_test = get_next_scheduled_test()
            progress = get_test_series_progress()
        except DatabaseError as exc:
            st.error(f"Could not load test series: {exc}")
            st.stop()

        if next_test:
            render_next_test_card(next_test, heading=f"{FIRST_NAME}'s Next Mains Test")
        elif progress["total"] > 0:
            st.success(f"Outstanding, {FIRST_NAME}! All {progress['total']} mains tests completed! 🎉")
        else:
            st.info("No mains tests scheduled yet.")

        render_series_metrics(progress)

        tests_chart_col, tests_table_col = st.columns([1, 1.4])

        with tests_chart_col:
            render_score_trend_chart(progress, f"{FIRST_NAME}'s mains score trend")

        df = get_scheduled_tests()
        with tests_table_col:
            if df.empty:
                st.caption("Test schedule will appear here once data is seeded.")
            else:
                st.markdown("**Test schedule & results**")
                st.caption(
                    "You can save **Status = Attempted** with **Score left blank** "
                    "(while evaluation is pending). Add marks later. "
                    "Defaults: Sectional 100 · FLT 200."
                )
                editor_cols = [
                    "test_no", "subject", "scheduled_date", "status", "score", "max_score", "remarks"
                ]
                display_df = df.copy()
                if "max_score" not in display_df.columns:
                    display_df["max_score"] = None
                display_df["max_score"] = display_df.apply(
                    lambda r: (
                        float(r["max_score"])
                        if pd.notna(r.get("max_score")) and float(r["max_score"]) > 0
                        else default_max_score(r.get("test_type"))
                    ),
                    axis=1,
                )
                # Keep empty scores as None so the editor does not force 0 / blank-string junk.
                if "score" in display_df.columns:
                    display_df["score"] = display_df["score"].where(
                        display_df["score"].notna(), other=None
                    )
                original_df = display_df[editor_cols].copy()
                edit_df = st.data_editor(
                    original_df,
                    column_config={
                        "test_no": st.column_config.NumberColumn("Test #", disabled=True),
                        "subject": st.column_config.TextColumn("Subject", disabled=True),
                        "scheduled_date": st.column_config.DateColumn("Date", disabled=True),
                        "status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Not Attempted", "Attempted"],
                            required=True,
                            help="Set Attempted as soon as you give the test — marks not required",
                        ),
                        "score": st.column_config.NumberColumn(
                            "Score",
                            min_value=0,
                            step=1,
                            help="Optional until evaluation. Leave empty if marks are pending.",
                        ),
                        "max_score": st.column_config.NumberColumn(
                            "Out of",
                            min_value=1,
                            step=1,
                            help="Total marks for this test",
                        ),
                        "remarks": st.column_config.TextColumn("Notes / Weak Areas"),
                    },
                    hide_index=True,
                    width="stretch",
                    height=360,
                    key="tests_editor",
                )

        if not df.empty:
            # Reliable path when data_editor status edits are flaky: mark given without marks.
            pending_mains = df[df["status"].fillna("Not Attempted") != "Attempted"]
            st.markdown("**Mark as Attempted (no marks yet)**")
            st.caption(
                "Use this right after you give a test. Enter Score later when the copy is evaluated."
            )
            if pending_mains.empty:
                st.caption("All mains tests are already marked Attempted.")
            else:
                qa1, qa2 = st.columns([2.4, 1])
                labels = {
                    f"#{int(r['test_no'])} — {r['subject']} ({str(r['scheduled_date'])[:10]})": int(
                        r["test_no"]
                    )
                    for _, r in pending_mains.iterrows()
                }
                with qa1:
                    pick_label = st.selectbox(
                        "Test you just gave",
                        options=list(labels.keys()),
                        key="mains_quick_attempt_pick",
                        label_visibility="collapsed",
                    )
                with qa2:
                    if st.button(
                        "Save as Attempted",
                        type="primary",
                        key="mains_quick_attempt_btn",
                        width="stretch",
                    ):
                        tn = labels[pick_label]
                        if (
                            run_db(
                                lambda: update_scheduled_test(
                                    tn, status="Attempted", score=None
                                ),
                                f"Could not mark test #{tn} as Attempted",
                            )
                            is not None
                        ):
                            st.success(
                                f"Test #{tn} marked Attempted (no marks yet). "
                                "Add score when evaluation is out."
                            )
                            st.rerun()

            if st.button("Save mains results", type="primary", key="save_tests"):
                errors = validate_test_rows(edit_df)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    changed = 0
                    for _, row in edit_df.iterrows():
                        if not test_row_changed(original_df, row):
                            continue
                        status, score, max_score, remarks = parse_test_result_fields(row)
                        if run_db(
                            lambda r=row, stt=status, s=score, ms=max_score, rm=remarks: (
                                update_scheduled_test(
                                    int(r["test_no"]),
                                    status=stt,
                                    score=s,
                                    max_score=ms,
                                    remarks=rm,
                                )
                            ),
                            f"Could not save test #{int(row['test_no'])}",
                        ) is None:
                            break
                        changed += 1
                    if changed:
                        st.success(
                            f"Saved {changed} test update(s)."
                            if changed > 1
                            else "Test results saved!"
                        )
                        st.rerun()
                    else:
                        st.info(
                            "No table changes to save. "
                            "To mark a test without marks, use **Save as Attempted** above."
                        )

    elif st.session_state.tests_series == "prelims":
        try:
            prelims_title = get_prelims_series_title()
            next_prelims = get_next_prelims_test()
            prelims_progress = get_prelims_series_progress()
            prelims_df = get_prelims_tests()
        except DatabaseError as exc:
            st.error(f"Could not load prelims series: {exc}")
            st.stop()

        st.subheader(prelims_title)
        st.caption(
            "CGPSC Prelims window is likely **October–November**. "
            "Placeholder slots are ready — fill **Date** / **Subject** when your institute "
            "releases the schedule. Track scores the same way as mains."
        )

        title_col, rename_col = st.columns([2, 1])
        with title_col:
            new_title = st.text_input(
                "Series name",
                value=prelims_title,
                key="prelims_series_title_input",
                help="e.g. Vision Prelims 2026, Insights PT, or keep Upcoming Prelims Test Series",
            )
        with rename_col:
            st.write("")
            st.write("")
            if st.button("Rename series", key="rename_prelims_series", width="stretch"):
                if run_db(
                    lambda: set_prelims_series_title(new_title),
                    "Could not rename series",
                ) is not None:
                    st.success("Series name saved.")
                    st.rerun()

        if next_prelims:
            render_next_test_card(
                next_prelims,
                heading=f"{FIRST_NAME}'s Next Prelims Test",
                undated_label="Date TBD — enter schedule below when released",
            )
        elif prelims_progress["total"] > 0 and prelims_progress["attempted"] >= prelims_progress["total"]:
            st.success(f"All {prelims_progress['total']} prelims tests attempted! 🎉")
        elif prelims_progress["total"] == 0:
            st.info("No prelims tests yet — seed placeholders or add your own below.")

        render_series_metrics(prelims_progress)

        p_chart, p_table = st.columns([1, 1.4])
        with p_chart:
            render_score_trend_chart(prelims_progress, f"{FIRST_NAME}'s prelims score trend")

        with p_table:
            if prelims_df.empty:
                st.caption("No rows yet.")
                if st.button("Seed placeholder prelims plan", type="primary", key="seed_prelims_now"):
                    if run_db(seed_prelims_placeholders, "Could not seed prelims plan") is not None:
                        st.success("Upcoming Prelims Test Series ready — fill dates when schedule is out.")
                        st.rerun()
            else:
                st.markdown("**Schedule + results**")
                st.caption(
                    "Edit **Date**, **Subject**, **Paper**, **Type** when the schedule is out. "
                    "You can save **Status = Attempted** with **Score blank** while evaluation "
                    "is pending. Add marks later. Leave date empty for TBD."
                )
                display_p = prelims_df.copy()
                if "max_score" not in display_p.columns:
                    display_p["max_score"] = None
                display_p["max_score"] = display_p.apply(
                    lambda r: (
                        float(r["max_score"])
                        if pd.notna(r.get("max_score")) and float(r["max_score"]) > 0
                        else default_max_score(r.get("test_type"), series="prelims")
                    ),
                    axis=1,
                )
                if "score" in display_p.columns:
                    display_p["score"] = display_p["score"].where(
                        display_p["score"].notna(), other=None
                    )
                # Normalize dates for the editor (None when TBD)
                def _as_date(v):
                    if v is None or (isinstance(v, float) and pd.isna(v)):
                        return None
                    text = str(v).strip()
                    if not text or text.lower() in ("none", "nat", "nan"):
                        return None
                    try:
                        return pd.to_datetime(v).date()
                    except (TypeError, ValueError):
                        return None

                display_p["scheduled_date"] = display_p["scheduled_date"].apply(_as_date)
                for col in PRELIMS_EDIT_COLS:
                    if col not in display_p.columns:
                        display_p[col] = None
                original_p = display_p[list(PRELIMS_EDIT_COLS)].copy()
                edit_p = st.data_editor(
                    original_p,
                    column_config={
                        "test_no": st.column_config.NumberColumn("Test #", disabled=True),
                        "paper": st.column_config.SelectboxColumn(
                            "Paper", options=["GS", "CSAT", "Mixed"]
                        ),
                        "test_type": st.column_config.SelectboxColumn(
                            "Type", options=["Sectional", "FLT", "Mock"]
                        ),
                        "subject": st.column_config.TextColumn("Subject"),
                        "scheduled_date": st.column_config.DateColumn(
                            "Date", help="Leave empty until schedule is released"
                        ),
                        "topic_focus": st.column_config.TextColumn("Focus / syllabus"),
                        "max_score": st.column_config.NumberColumn(
                            "Out of", min_value=1, step=1, help="GS/CSAT full = 200"
                        ),
                        "status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Not Attempted", "Attempted"],
                            required=True,
                            help="Attempted does not require marks",
                        ),
                        "score": st.column_config.NumberColumn(
                            "Score",
                            min_value=0,
                            step=1,
                            help="Optional until evaluation. Leave empty if marks are pending.",
                        ),
                        "remarks": st.column_config.TextColumn("Notes / weak areas"),
                    },
                    hide_index=True,
                    width="stretch",
                    height=420,
                    key="prelims_tests_editor",
                    num_rows="fixed",
                )

        if not prelims_df.empty:
            pending_prelims = prelims_df[
                prelims_df["status"].fillna("Not Attempted") != "Attempted"
            ]
            st.markdown("**Mark as Attempted (no marks yet)**")
            st.caption(
                "Use this right after you give a prelims test. Enter Score later when evaluated."
            )
            if pending_prelims.empty:
                st.caption("All prelims tests are already marked Attempted.")
            else:
                pq1, pq2 = st.columns([2.4, 1])
                p_labels = {
                    f"#{int(r['test_no'])} — {r['subject']}": int(r["test_no"])
                    for _, r in pending_prelims.iterrows()
                }
                with pq1:
                    p_pick = st.selectbox(
                        "Prelims test you just gave",
                        options=list(p_labels.keys()),
                        key="prelims_quick_attempt_pick",
                        label_visibility="collapsed",
                    )
                with pq2:
                    if st.button(
                        "Save as Attempted",
                        type="primary",
                        key="prelims_quick_attempt_btn",
                        width="stretch",
                    ):
                        tn = p_labels[p_pick]
                        if (
                            run_db(
                                lambda: update_prelims_test(
                                    tn, status="Attempted", score=None
                                ),
                                f"Could not mark prelims test #{tn} as Attempted",
                            )
                            is not None
                        ):
                            st.success(
                                f"Prelims test #{tn} marked Attempted (no marks yet)."
                            )
                            st.rerun()

            save_c, add_c = st.columns([1, 1])
            with save_c:
                if st.button("Save prelims schedule & results", type="primary", key="save_prelims"):
                    errors = validate_test_rows(edit_p)
                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        changed = 0
                        for _, row in edit_p.iterrows():
                            if not test_row_changed(original_p, row, cols=PRELIMS_COMPARE_COLS):
                                continue
                            status, score, max_score, remarks = parse_test_result_fields(row)
                            if run_db(
                                lambda r=row, stt=status, s=score, ms=max_score, rm=remarks: (
                                    update_prelims_test(
                                        int(r["test_no"]),
                                        status=stt,
                                        score=s,
                                        max_score=ms,
                                        remarks=rm,
                                        paper=r["paper"] if pd.notna(r["paper"]) else "GS",
                                        test_type=(
                                            r["test_type"]
                                            if pd.notna(r["test_type"])
                                            else "Sectional"
                                        ),
                                        subject=(
                                            str(r["subject"]).strip()
                                            if pd.notna(r["subject"])
                                            else ""
                                        ),
                                        scheduled_date=r["scheduled_date"],
                                        topic_focus=(
                                            r["topic_focus"]
                                            if pd.notna(r["topic_focus"])
                                            else ""
                                        ),
                                    )
                                ),
                                f"Could not save prelims test #{int(row['test_no'])}",
                            ) is None:
                                break
                            changed += 1
                        if changed:
                            st.success(
                                f"Saved {changed} prelims update(s)."
                                if changed > 1
                                else "Prelims row saved!"
                            )
                            st.rerun()
                        else:
                            st.info(
                                "No table changes to save. "
                                "To mark a test without marks, use **Save as Attempted** above."
                            )

            st.markdown("---")
            st.markdown("**Add or remove a test**")
            add_left, add_right = st.columns([2, 1])
            with add_left:
                with st.form("add_prelims_test_form", clear_on_submit=True):
                    a1, a2, a3 = st.columns(3)
                    new_subject = a1.text_input("Subject", placeholder="e.g. Polity full mock")
                    new_paper = a2.selectbox("Paper", ["GS", "CSAT", "Mixed"])
                    new_type = a3.selectbox("Type", ["Sectional", "FLT", "Mock"])
                    b1, b2, b3, b4 = st.columns(4)
                    date_mode = b1.selectbox(
                        "Date mode",
                        ["TBD (fill later)", "Set date"],
                        help="Use TBD until the institute schedule is out",
                    )
                    new_date = b2.date_input(
                        "Scheduled on",
                        help="Only used when Date mode is Set date",
                    )
                    new_focus = b3.text_input("Focus", placeholder="Optional syllabus note")
                    new_max = b4.number_input(
                        "Out of",
                        min_value=1.0,
                        value=200.0,
                        step=1.0,
                    )
                    submitted = st.form_submit_button("Add test", type="primary")
                    if submitted:
                        if not (new_subject or "").strip():
                            st.error("Subject is required.")
                        else:
                            result = run_db(
                                lambda: add_prelims_test(
                                    subject=new_subject,
                                    paper=new_paper,
                                    test_type=new_type,
                                    scheduled_date=new_date if date_mode == "Set date" else None,
                                    topic_focus=new_focus,
                                    max_score=new_max,
                                ),
                                "Could not add prelims test",
                            )
                            if result is not None:
                                st.success(f"Added prelims test #{result}.")
                                st.rerun()
            with add_right:
                if not prelims_df.empty:
                    del_no = st.selectbox(
                        "Delete test #",
                        options=prelims_df["test_no"].tolist(),
                        key="delete_prelims_test_no",
                    )
                    if st.button("Delete selected", key="delete_prelims_btn"):
                        if run_db(
                            lambda: delete_prelims_test(int(del_no)),
                            f"Could not delete test #{del_no}",
                        ):
                            st.success(f"Deleted prelims test #{int(del_no)}.")
                            st.rerun()

elif active_page == "garden":
    st.markdown(
        f'<p class="section-label">Study Garden</p>'
        f'<p class="section-title">Quiet garden — open meadow · permanent trees every 4 days</p>',
        unsafe_allow_html=True,
    )
    life = garden_state.get("life") or {}
    st.caption(
        life.get(
            "hint",
            "Log full goal hours daily — 4 days plant a tree, 6 days bloom, >60% tests fruit.",
        )
    )

    week = life.get("week_days") or []
    if week:
        dots = '<div class="week-dots"><span style="font-size:0.78rem;color:#5eead4;font-weight:600;font-family:Outfit,system-ui,sans-serif">This week</span>'
        for d in week:
            dots += f'<span class="week-dot {d["status"]}" title="{d["date"]}: {d["hours"]}h"></span>'
        dots += "</div>"
        st.markdown(dots, unsafe_allow_html=True)

    # Enchanted Grove is the default premium map. New key so old "Classic" session
    # state does not hide the upgrade after a refresh.
    if "garden_map_style_v5" not in st.session_state:
        st.session_state.garden_map_style_v5 = "Quiet Garden"
    map_mode_label = st.segmented_control(
        "Map style",
        options=["Quiet Garden", "Classic"],
        key="garden_map_style_v5",
        help="Quiet Garden = open meadow, rain, Garden of Words mood (default). Classic = original map.",
    )
    map_mode = "classic" if map_mode_label == "Classic" else "living"
    if map_mode == "living":
        st.markdown(
            '<p class="garden-mode-note">言の葉 — soft rain, deep greens, wet stone. Open meadow (not a path). '
            'Drag · zoom · click trees. Bloom · fruit &gt;60% · only active sprout wilts.</p>',
            unsafe_allow_html=True,
        )

    render_interactive_garden(garden_state, height=820, mode=map_mode)
    st.markdown(render_garden_stats_strip(life), unsafe_allow_html=True)

    trees = life.get("trees") or []
    if trees:
        show = trees[-8:] if len(trees) > 8 else trees
        rows = []
        for tr in show:
            if tr.get("has_fruit"):
                status = "🍎 Fruited"
            elif tr.get("has_flowers") or tr.get("has_sakura"):
                status = "🌸 Bloomed"
            else:
                status = "🌿 Growing"
            score = f"{tr['score']}%" if tr.get("score") is not None else "—"
            tag = f"T{tr['test_no']}" if tr.get("test_no") else f"#{tr['tree_no']}"
            phase = tr.get("phase", "prelims").title()
            rows.append(
                f"**{tag}** · {phase} · {tr.get('subject', '')} · {status} · Score: {score}"
            )
        with st.expander(
            f"Latest trees ({len(show)} of {len(trees)})",
            expanded=False,
        ):
            st.markdown("\n\n".join(rows))
    if life.get("days_to_next_tier", 0) > 0:
        st.caption(
            f"{life['days_to_next_tier']} more complete day(s) until **{life.get('next_tier_label', 'next tier')}**."
        )

    with st.expander("How the garden works", expanded=False):
        st.markdown(
            f"🌳 **Start** — 1 tree. Every **4 complete study days** ({daily_goal:g}h each) plants a **permanent** tree.\n\n"
            f"📅 **~55 trees** by prelims (220 ÷ 4). Drag the map to walk the path.\n\n"
            f"🌸 **6-day streak** — cherry blossoms + falling petals on your newest tree.\n\n"
            f"🍎 **>60% on a test** — shiny fruit on that T# tree.\n\n"
            f"🍂 **Streak breaks** — only the active sprout wilts; past trees stay beautiful.\n\n"
            f"🏁 Trees **56–77** = 3-month mains sprint grove."
        )

    garden_left, garden_right = st.columns([1, 1])

    with garden_left:
        with st.expander("Growth XP & stages", expanded=False):
            st.markdown(
                f"🌅 Daily check-in — +{XP_REWARDS['daily_checkin']} XP "
                f"(streak bonus up to +{XP_REWARDS['streak_cap']})\n\n"
                f"⏱️ Study — +{XP_REWARDS['per_hour']} XP/hr · "
                f"🎯 Hit goal — +{XP_REWARDS['daily_goal']} XP\n\n"
                f"✅ Complete target — +{XP_REWARDS['target_done']} XP · "
                f"🏆 All targets — +{XP_REWARDS['all_targets']} XP"
            )
            badge_html = '<div class="badge-grid">'
            for stage in GARDEN_STAGES:
                earned = garden_state["xp"] >= stage["min_xp"]
                css = "badge-earned" if earned else "badge-locked"
                lock = "" if earned else " 🔒"
                badge_html += (
                    f'<span class="badge {css}">{stage["emoji"]} {stage["name"]}{lock}</span>'
                )
            badge_html += "</div>"
            st.markdown(badge_html, unsafe_allow_html=True)

    with garden_right:
        events = garden_state.get("events")
        if events is not None and not events.empty:
            with st.expander("Recent growth", expanded=True):
                feed = events.copy()
                feed["event_date"] = pd.to_datetime(feed["event_date"]).dt.strftime(
                    "%d %b %H:%M"
                )
                feed["growth"] = feed.apply(
                    lambda r: f"+{int(r['xp_amount'])} XP — {r['message']}", axis=1
                )
                st.dataframe(
                    feed[["event_date", "growth"]],
                    column_config={"event_date": "When", "growth": "Event"},
                    hide_index=True,
                    width="stretch",
                    height=220,
                )
        else:
            st.caption(
                f"{FIRST_NAME}, your growth log is empty. Log study hours or complete "
                "a target to start growing your map!"
            )

elif active_page == "break":
    st.markdown(
        '<p class="section-label">Break</p>'
        '<p class="section-title">Five minutes, then back to prep</p>',
        unsafe_allow_html=True,
    )

    category = st.segmented_control(
        "Category",
        options=list(GAME_GROUPS.keys()),
        default="Pop",
        key="break_category",
    )
    games_in_cat = GAME_GROUPS[category]
    if st.session_state.get("break_game_pick") not in games_in_cat:
        st.session_state.break_game_pick = games_in_cat[0]

    game_pick = st.segmented_control(
        "Game",
        options=games_in_cat,
        key="break_game_pick",
    )

    if game_pick == "Chess Puzzles":
        st.link_button(
            "Full Lichess site",
            "https://lichess.org/training",
            width="content",
        )

    relax_games.render_break_game(game_pick)