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
    award_hours_garden_xp,
    award_target_done_xp,
    get_daily_plan,
    get_daily_plan_summary,
    get_daily_study_goal,
    get_export_dataframes,
    get_garden_state,
    get_garden_xp,
    get_longest_streak,
    get_next_scheduled_test,
    get_recent_study_hours,
    get_scheduled_tests,
    get_study_hours_for_date,
    get_study_streak,
    get_test_series_progress,
    get_week_study_hours,
    init_db,
    process_daily_checkin,
    save_daily_targets,
    save_evening_reflection,
    seed_sample_tests,
    set_daily_study_goal,
    sync_daily_garden_bonuses,
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
    render_interactive_garden,
)
from profile import EXAM, EXAM_YEAR, FIRST_NAME, FULL_NAME, MOTTO, greeting, period_nudge, possessive
from app_styles import APP_CSS
import importlib
import showup_grid

importlib.reload(showup_grid)
load_showup_hours = showup_grid.load_showup_hours
render_github_heatmap = showup_grid.render_github_heatmap
from break_games_config import GAME_GROUPS
import relax_games

MAX_TARGETS_PER_DAY = 99
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
    page_title=f"{FIRST_NAME}'s CGPSC Mains Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GARDEN_CSS + APP_CSS, unsafe_allow_html=True)

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


def render_sidebar():
    st.markdown(f"### {FULL_NAME}")
    st.caption(f"{EXAM} {EXAM_YEAR}")
    st.caption(MOTTO)
    st.divider()
    st.markdown("**Daily study goal**")
    if "daily_goal_input" not in st.session_state:
        st.session_state.daily_goal_input = float(daily_goal)
    new_goal = st.number_input(
        "Hours per day",
        min_value=0.5,
        max_value=16.0,
        step=0.5,
        key="daily_goal_input",
        label_visibility="collapsed",
    )
    if st.button("Save goal", key="save_goal_main", use_container_width=True):
        if run_db(
            lambda: set_daily_study_goal(new_goal),
            "Could not save study goal",
        ) is not None:
            st.success("Goal saved!")
            st.rerun()
    st.divider()
    st.markdown("**Sync from phone**")
    st.caption(
        "Log on your phone daily. When you connect to this PC, export from the "
        "phone app and import the file here."
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
        use_container_width=True,
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

    st.divider()
    st.markdown("**GitHub backup**")
    st.caption(
        "Pushes to GitHub when you save data (or tap Sync now). "
        "Background check runs every 10 hours only."
    )
    git_status = get_sync_status()
    if git_status["online"]:
        st.caption("Internet: connected")
    else:
        st.caption("Internet: offline — sync resumes when connected")
    if git_status.get("last_success"):
        st.caption(f"Last pushed: {git_status['last_success']}")
    st.caption(git_status["message"])
    if st.button("Sync to GitHub now", key="git_sync_now", use_container_width=True):
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

    st.divider()
    st.markdown("**Study sticker**")
    st.caption(
        "Vader, Yoda, Mando, or Dooku floats top-right on your screen "
        "while you read PDFs. Launch via `Start Tracker.bat`."
    )
    if st.button("Install sticker on Windows startup", key="install_startup", use_container_width=True):
        script = os.path.join(os.path.dirname(__file__), "scripts", "install_startup.ps1")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
            check=False,
        )
        st.success("Sticker + app auto-start on login.")
    if st.button("Stop / remove old sticker", key="stop_sticker", use_container_width=True):
        script = os.path.join(os.path.dirname(__file__), "scripts", "stop_sticker.ps1")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
            check=False,
        )
        st.success("Old sticker processes stopped.")
    st.caption("Or double-click `Stop Sticker.bat` in the project folder.")
    st.divider()
    st.markdown("**Quick launch**")
    st.caption("Double-click `Start Tracker.bat` in the project folder.")
    if st.button("Create / refresh desktop shortcut", key="make_shortcut", use_container_width=True):
        script = os.path.join(os.path.dirname(__file__), "scripts", "create_desktop_shortcut.ps1")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
            check=False,
        )
        st.success("Shortcut updated on your Desktop.")
    st.divider()
    st.markdown("**Android APK**")
    st.caption(
        "Mobile app code is ready (Flet). No APK built on this PC yet — "
        "run `scripts\\build_apk.ps1` after JDK 17 + Android SDK are installed."
    )
    st.divider()
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
                if st.button("Skip", key=f"skip_{item_id}", use_container_width=True):
                    on_target_skip(item_id)
                    st.rerun()
            elif is_skipped:
                if st.button("Undo", key=f"unskip_{item_id}", use_container_width=True):
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


def validate_test_rows(edit_df):
    errors = []
    for _, row in edit_df.iterrows():
        test_no = int(row["test_no"])
        if row["status"] == "Attempted" and pd.isna(row["score"]):
            errors.append(f"Test #{test_no}: enter a score when marked Attempted.")
    return errors


def test_row_changed(original_df, edited_row):
    test_no = int(edited_row["test_no"])
    original = original_df[original_df["test_no"] == test_no].iloc[0]
    for col in ("status", "score", "remarks"):
        orig_val = original[col]
        edit_val = edited_row[col]
        if pd.isna(orig_val):
            orig_val = None
        if pd.isna(edit_val):
            edit_val = None
        if orig_val != edit_val:
            return True
    return False


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

with st.sidebar:
    render_sidebar()

st.markdown(
    f"""
    <div class="app-hero">
        <p class="app-hero-title">{html.escape(possessive("CGPSC Mains Tracker"))}</p>
        <p class="app-hero-greeting">{html.escape(greeting(period_key))}</p>
        <p class="app-hero-motto">{html.escape(period_nudge(period_key))}</p>
        <p class="app-hero-meta">
            {now.strftime("%A, %d %B %Y")} · {now.strftime("%I:%M %p")}
            · <span class="period-badge {PERIOD_BADGES[period_key]}">{period_label}</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Study streak", f"{streak} days")
m2.metric("Daily goal", f"{daily_goal:g} h")
m3.metric("Garden XP", f"{garden_state['xp']:,}")
m4.metric("Best streak", f"{longest_streak} days")

heatmap_start = today - timedelta(days=400)
try:
    showup_hours = load_showup_hours(heatmap_start, today)
except DatabaseError:
    showup_hours = {}
st.markdown(
    render_github_heatmap(
        showup_hours,
        streak=streak,
        daily_goal=daily_goal,
    ),
    unsafe_allow_html=True,
)

tab_daily, tab_hours, tab_logbook, tab_tests, tab_garden, tab_break = st.tabs(
    ["Targets", "Hours", "Logbook", "Tests", "Garden", "Break"]
)

if st.query_params.get("view") == "garden":
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function selectGardenTab() {
          const doc = window.parent.document;
          const tabs = [...doc.querySelectorAll('button[data-baseweb="tab"]')];
          const garden = tabs.find((b) => (b.innerText || "").includes("Garden"));
          if (garden) { garden.click(); return; }
          setTimeout(selectGardenTab, 400);
        })();
        </script>
        """,
        height=0,
    )

with tab_daily:
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

    if summary["has_plan"] and not st.session_state.show_target_form:
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown(
                f'<p class="section-label">Today</p>'
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
                if st.button("Add", key="quick_add_btn", use_container_width=True):
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
                [("Done", f"{summary['done']}/{summary['total_targets']}"), ("Pending", str(summary["pending"]))],
                [third_metric, ("Resolved", f"{summary['resolved_pct']}%")],
            ]
        )
        st.progress(summary["resolved_pct"] / 100)

        target_cols = st.columns(2)
        for index, item in enumerate(plan["items"]):
            with target_cols[index % 2]:
                render_target_item(item)

        if all_targets_resolved(plan["items"]):
            st.success(f"All targets resolved — great work, {FIRST_NAME}!")
            show_tomorrow_prompt = (
                not tomorrow_summary["has_plan"]
                and st.session_state.tomorrow_prompt_dismissed_date != today.isoformat()
                and not st.session_state.show_target_form
            )
            if show_tomorrow_prompt:
                t1, t2 = st.columns(2)
                with t1:
                    if st.button("Plan tomorrow", type="primary", key="tomorrow_yes"):
                        st.session_state.show_target_form = True
                        st.session_state.planning_date = tomorrow
                        init_draft_form(tomorrow)
                        st.rerun()
                with t2:
                    if st.button("Not now", key="tomorrow_no"):
                        st.session_state.tomorrow_prompt_dismissed_date = today.isoformat()
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
        st.markdown(
            f'<p class="section-label">No plan yet</p>'
            f'<p class="section-title">{greeting(period_key)}</p>',
            unsafe_allow_html=True,
        )
        st.caption(period_nudge(period_key))
        if st.button("Set today's targets", type="primary", key="set_today_targets"):
            st.session_state.show_target_form = True
            st.session_state.planning_date = today
            init_draft_form(today)
            st.rerun()

    if st.session_state.show_target_form and st.session_state.planning_date:
        plan_label = (
            "Set today's targets"
            if st.session_state.planning_date == today
            else f"Set targets for {st.session_state.planning_date.strftime('%A, %d %b')}"
        )
        render_target_form(st.session_state.planning_date, plan_label)
        if st.button("Cancel", key="cancel_form"):
            clear_draft_form(st.session_state.planning_date)
            st.session_state.show_target_form = False
            st.session_state.planning_date = None
            st.rerun()

with tab_hours:
    try:
        today_hours = get_study_hours_for_date(today)
        week_df = get_week_study_hours(today)
    except DatabaseError as exc:
        st.error(f"Could not load study hours: {exc}")
        st.stop()
    week_total = round(week_df["hours"].sum(), 1)
    goal_progress = min(today_hours / daily_goal, 1.0) if daily_goal else 0

    hours_left, hours_right = st.columns([1, 1.8])

    with hours_left:
        st.subheader(possessive("Study Hours"))
        h1, h2, h3 = st.columns(3)
        h1.metric("Today", f"{today_hours}h", f"Goal {daily_goal:g}h")
        h2.metric("This week", f"{week_total}h")
        h3.metric("Goal progress", f"{round(goal_progress * 100)}%")
        st.progress(goal_progress)

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
            if st.form_submit_button("Save Hours", type="primary", use_container_width=True):
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
                use_container_width=True,
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
                    use_container_width=True,
                )

    with hours_right:
        chart_df = week_df.copy()
        chart_df["label"] = chart_df.apply(
            lambda r: f"{r['day']}<br>{r['log_date'].strftime('%d %b')}",
            axis=1,
        )
        chart_df["goal_met"] = chart_df["hours"] >= daily_goal
        colors = [
            "#48BB78" if r["is_today"] else "#38A169" if r["goal_met"] else "#4299E1"
            for _, r in chart_df.iterrows()
        ]
        fig = px.bar(
            chart_df,
            x="label",
            y="hours",
            text="hours",
            title=f"{FIRST_NAME}'s weekly study hours",
            labels={"label": "Day", "hours": "Hours"},
        )
        fig.update_traces(
            marker_color=colors, texttemplate="%{text:.1f}h", textposition="outside"
        )
        fig.add_hline(
            y=daily_goal,
            line_dash="dash",
            line_color="#E53E3E",
            annotation_text=f"Goal ({daily_goal:g}h)",
        )
        fig.update_layout(
            height=480,
            margin=dict(l=20, r=20, t=48, b=20),
            showlegend=False,
            font=dict(size=13),
        )
        fig.update_yaxes(range=[0, max(chart_df["hours"].max() * 1.2, daily_goal * 1.2, 4)])
        st.plotly_chart(fig, use_container_width=True)

with tab_logbook:
    st.markdown(
        f'<p class="section-label">Logbook</p>'
        f'<p class="section-title">What did you study?</p>',
        unsafe_allow_html=True,
    )
    st.caption("One line is enough — saved locally, kept forever.")

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
                use_container_width=True,
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
        save_log = st.button("Log it", type="primary", use_container_width=True, key="quick_log_save")

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
            if st.form_submit_button("Save detailed entry", use_container_width=True):
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
                use_container_width=True,
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
                use_container_width=True,
            )

with tab_tests:
    st.subheader(f"Monsoon Test Series {EXAM_YEAR}")

    try:
        next_test = get_next_scheduled_test()
        progress = get_test_series_progress()
    except DatabaseError as exc:
        st.error(f"Could not load test series: {exc}")
        st.stop()

    if next_test:
        test_date = pd.to_datetime(next_test["scheduled_date"]).strftime("%d %b %Y")
        days_left = (pd.to_datetime(next_test["scheduled_date"]).date() - today).days
        if days_left > 0:
            countdown = f" · {days_left} day(s) away"
        elif days_left == 0:
            countdown = " · Today!"
        else:
            countdown = " · Overdue"
        safe_subject = html.escape(str(next_test["subject"]))
        safe_type = html.escape(str(next_test["test_type"]))
        safe_topic = html.escape(str(next_test["topic_focus"]))
        st.markdown(
            f"""
        <div class="next-test-card">
            <h3>{FIRST_NAME}'s Next Test</h3>
            <p class="test-title">Test #{int(next_test['test_no'])} — {safe_subject}</p>
            <p class="test-date">{test_date}{countdown} · {safe_type} · {safe_topic}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    elif progress["total"] > 0:
        st.success(f"Outstanding, {FIRST_NAME}! All {progress['total']} tests completed! 🎉")
    else:
        st.info("No tests scheduled yet.")

    completion_pct = (
        round(progress["attempted"] / progress["total"] * 100)
        if progress["total"]
        else None
    )
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Attempted", f"{progress['attempted']}/{progress['total']}")
    t2.metric("Avg score", f"{progress['avg_score']}" if progress["avg_score"] else "—")
    t3.metric("Completion", f"{completion_pct}%" if completion_pct is not None else "—")
    t4.metric("Remaining", progress["total"] - progress["attempted"])

    tests_chart_col, tests_table_col = st.columns([1, 1.4])

    with tests_chart_col:
        if not progress["scores"].empty:
            chart_df = progress["scores"].copy()
            chart_df["scheduled_date"] = pd.to_datetime(chart_df["scheduled_date"])
            fig = px.line(
                chart_df,
                x="test_no",
                y="score",
                markers=True,
                title=f"{FIRST_NAME}'s score trend",
                labels={"test_no": "Test #", "score": "Score"},
            )
            fig.update_layout(height=360, margin=dict(l=20, r=20, t=48, b=20), font=dict(size=13))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Score trend will appear after your first attempted test.")

    df = get_scheduled_tests()
    with tests_table_col:
        if df.empty:
            st.caption("Test schedule will appear here once data is seeded.")
        else:
            st.markdown("**Test schedule & results**")
            original_df = df[["test_no", "subject", "scheduled_date", "status", "score", "remarks"]]
            edit_df = st.data_editor(
                original_df,
                column_config={
                    "test_no": st.column_config.NumberColumn("Test #", disabled=True),
                    "subject": st.column_config.TextColumn("Subject", disabled=True),
                    "scheduled_date": st.column_config.DateColumn("Date", disabled=True),
                    "status": st.column_config.SelectboxColumn(
                        "Status", options=["Not Attempted", "Attempted"]
                    ),
                    "score": st.column_config.NumberColumn("Score", min_value=0, step=1),
                    "remarks": st.column_config.TextColumn("Notes / Weak Areas"),
                },
                hide_index=True,
                use_container_width=True,
                height=360,
                key="tests_editor",
            )

    if not df.empty:
        if st.button("Save test results", type="primary", key="save_tests"):
            errors = validate_test_rows(edit_df)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                changed = 0
                for _, row in edit_df.iterrows():
                    if not test_row_changed(original_df, row):
                        continue
                    score = float(row["score"]) if pd.notna(row["score"]) else None
                    if row["status"] == "Not Attempted":
                        score = None
                    if run_db(
                        lambda r=row, s=score: update_scheduled_test(
                            int(r["test_no"]),
                            status=r["status"],
                            score=s,
                            remarks=r["remarks"] if pd.notna(r["remarks"]) else "",
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
                    st.info("No changes to save.")

with tab_garden:
    st.markdown(
        f'<p class="section-label">Study Garden</p>'
        f'<p class="section-title">220-day path — up to 55 prelims trees + mains sprint</p>',
        unsafe_allow_html=True,
    )
    life = garden_state.get("life") or {}
    st.caption(life.get("hint", "Log hours daily — 4 days grows trees, 6 days brings fruit."))

    week = life.get("week_days") or []
    if week:
        dots = '<div class="week-dots"><span style="font-size:0.8rem;color:#558B2F;font-weight:600">This week</span>'
        for d in week:
            dots += f'<span class="week-dot {d["status"]}" title="{d["date"]}: {d["hours"]}h"></span>'
        dots += "</div>"
        st.markdown(dots, unsafe_allow_html=True)

    render_interactive_garden(garden_state, height=780)

    info = garden_state["stage_info"]
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Trees planted", f"🌳 {life.get('tree_count', 1)} / {life.get('max_trees', 77)}")
    g2.metric("Prelims path", f"{life.get('prelims_trees', 1)} / {life.get('prelims_target', 55)}")
    g3.metric("Study streak", f"{life.get('goal_streak', 0)} days")
    g4.metric("Sakura blooms", f"🌸 {life.get('sakura_count', 0)}")

    st.markdown("**Your 220-day → mains journey**")
    st.info(
        f"🌳 **Start** — 1 tree. Every **4 complete study days** ({daily_goal:g}h each) plants the next tree.\n\n"
        f"📅 **~55 trees** by prelims day (220 days ÷ 4) — drag the map to walk your path.\n\n"
        f"🍎 **6-day streak** — fruit on your trees.\n\n"
        f"🌸 **Score >60% on a mains test** — that test's tree (T#) blooms sakura permanently.\n\n"
        f"🏁 **After prelims** — trees 56–77 are your **3-month mains sprint** grove."
    )
    trees = life.get("trees") or []
    if trees:
        show = trees[-8:] if len(trees) > 8 else trees
        if len(trees) > 8:
            st.caption(f"Showing latest 8 of {len(trees)} trees — drag the map to see all.")
        rows = []
        for tr in show:
            status = "🌸 Sakura" if tr.get("has_sakura") else ("🍎 Fruit" if tr.get("has_fruit") else "🌿 Growing")
            score = f"{tr['score']}%" if tr.get("score") is not None else "—"
            tag = f"T{tr['test_no']}" if tr.get("test_no") else f"#{tr['tree_no']}"
            phase = tr.get("phase", "prelims").title()
            rows.append(f"**{tag}** · {phase} · {tr.get('subject', '')} · {status} · Score: {score}")
        st.markdown("**Latest trees**\n\n" + "\n\n".join(rows))
    if life.get("days_to_next_tier", 0) > 0:
        st.caption(
            f"{life['days_to_next_tier']} more complete day(s) until **{life.get('next_tier_label', 'next tier')}**."
        )

    garden_left, garden_right = st.columns([1, 1])

    with garden_left:
        st.markdown("**How to earn Growth XP**")
        st.info(
            f"🌅 Daily check-in — +{XP_REWARDS['daily_checkin']} XP "
            f"(streak bonus up to +{XP_REWARDS['streak_cap']})\n\n"
            f"⏱️ Study — +{XP_REWARDS['per_hour']} XP/hr · "
            f"🎯 Hit goal — +{XP_REWARDS['daily_goal']} XP\n\n"
            f"✅ Complete target — +{XP_REWARDS['target_done']} XP · "
            f"🏆 All targets — +{XP_REWARDS['all_targets']} XP"
        )

        st.markdown("**Year-long evolution**")
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
            st.markdown("**Recent growth**")
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
                use_container_width=True,
                height=320,
            )
        else:
            st.caption(
                f"{FIRST_NAME}, your growth log is empty. Log study hours or complete "
                "a target to start growing your map!"
            )

with tab_break:
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
            use_container_width=False,
        )

    relax_games.render_break_game(game_pick)