"""Streamlit UI for the Syllabus Atlas."""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

from atlas import (
    STATE_META,
    add_custom_topic,
    add_custom_unit,
    archive_custom_node,
    get_all_topics,
    get_atlas_overview,
    get_blind_units,
    get_due_topics,
    get_expedition,
    get_recent_atlas_log,
    get_region_summaries,
    get_topics,
    get_unit_summaries,
    record_study,
    reset_topic,
    save_topic_details,
    snooze_topic,
)
from atlas_map import build_subject_web, color_ramp_html, parse_web_click
from database import DatabaseError, add_daily_target
from profile import FIRST_NAME

LOG_ACTIONS = {
    "scout": "First reading — lift the fog",
    "map": "Made notes / outline",
    "revise": "Revised from memory",
    "fortify": "I can write a 10-mark answer",
    "save": "Only save notes (don't change status)",
}

CONF_LABELS = {1: "Blank", 2: "Hazy", 3: "Okay", 4: "Clear", 5: "Fluent"}


def _esc(value):
    return html.escape(str(value or ""))


def _due_label(topic, today):
    due = topic.get("next_due")
    if not due or topic.get("state") == "unseen":
        return ""
    delta = (due - today).days
    if delta < 0:
        return f"{abs(delta)}d overdue"
    if delta == 0:
        return "due today"
    return f"due in {delta}d"


def _topic_label(topic, today=None):
    state = STATE_META.get(topic.get("state") or "unseen", {}).get("label", "Fog")
    due = _due_label(topic, today) if today else ""
    tail = f" · {due}" if due else ""
    return f"{topic['title']}  ·  {state}{tail}"


def _full_label(topic, today=None):
    region = topic.get("region_title") or ""
    unit = topic.get("unit_title") or topic.get("parent_title") or ""
    return f"{region}  /  {unit}  /  {_topic_label(topic, today)}"


def focus_topic(topic):
    """Point every picker at this topic."""
    st.session_state.atlas_region = topic.get("region_slug") or st.session_state.get(
        "atlas_region"
    )
    st.session_state.atlas_unit = topic.get("unit_slug") or topic.get("parent_slug")
    st.session_state.atlas_topic = topic["slug"]
    st.session_state.atlas_global_pick = topic["slug"]


def render_overview_strip(overview):
    return f"""
    <div class="atlas-strip">
        <div class="atlas-tile">
            <p class="atlas-tile-label">Syllabus lit</p>
            <p class="atlas-tile-value">{overview['coverage']:.0f}%</p>
            <p class="atlas-tile-hint">{overview['touched']}/{overview['total']} topics touched</p>
        </div>
        <div class="atlas-tile">
            <p class="atlas-tile-label">Mastery</p>
            <p class="atlas-tile-value">{overview['mastery']:.0f}%</p>
            <p class="atlas-tile-hint">Weighted by how well you hold it</p>
        </div>
        <div class="atlas-tile atlas-tile-due">
            <p class="atlas-tile-label">Due today</p>
            <p class="atlas-tile-value">{overview['due_today']}</p>
            <p class="atlas-tile-hint">{overview['overdue']} overdue</p>
        </div>
        <div class="atlas-tile">
            <p class="atlas-tile-label">Fortified</p>
            <p class="atlas-tile-value">{overview['fortified']}</p>
            <p class="atlas-tile-hint">10-mark ready</p>
        </div>
        <div class="atlas-tile">
            <p class="atlas-tile-label">Blind units</p>
            <p class="atlas-tile-value">{overview['blind_units']}</p>
            <p class="atlas-tile-hint">Never opened</p>
        </div>
    </div>
    """


def _is_paper():
    return st.session_state.get("ui_theme") == "paper"


def render_subject_web(units, today, selected_slug, region_title):
    """Whole-subject topic web. Click a node to log it."""
    st.markdown(
        f'<p class="section-label">Map</p>'
        f'<p class="section-title">{_esc(region_title)} — living web</p>'
        f'<p class="workspace-hint">'
        f"Yellow is a first reading. Darker green means you can write it. "
        f"Leave a node alone and it bleaches back toward fog. Click a topic to open it."
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown(color_ramp_html(paper=_is_paper()), unsafe_allow_html=True)
    fig = build_subject_web(
        region_title,
        units,
        today=today,
        selected_slug=selected_slug,
        paper=_is_paper(),
    )
    event = st.plotly_chart(
        fig,
        width="stretch",
        theme=None,
        on_select="rerun",
        selection_mode="points",
        key=f"atlas_web_{st.session_state.get('atlas_region')}",
        config={"displayModeBar": False, "scrollZoom": True},
    )
    slug = parse_web_click(event)
    if slug and slug != selected_slug:
        for unit in units:
            for topic in unit.get("topics") or []:
                if topic["slug"] == slug:
                    focus_topic(topic)
                    st.rerun()


def _apply_study(run_db, queue_reward, slug, action, confidence=3, note=""):
    result = run_db(
        lambda: record_study(slug, action, confidence=confidence, note=note),
        "Could not update the Atlas",
    )
    if result is None:
        return False
    if result.get("reward"):
        queue_reward(result["reward"])
    node = result["node"]
    label = STATE_META[node["state"]]["label"]
    st.toast(f"{node['title']} → {label}", icon="🗺")
    return True


def _topic_caption(topic, today):
    bits = [topic.get("region_title") or "", topic.get("unit_title") or ""]
    bits = [b for b in bits if b]
    due = _due_label(topic, today)
    if due:
        bits.append(due)
    return " · ".join(bits)


def render_expedition(today):
    trip = get_expedition(today)
    st.markdown(
        '<p class="section-label">Suggestions</p>'
        '<p class="section-title">Expedition</p>'
        '<p class="workspace-hint">'
        "Pick one of these, or ignore them and choose your own topic above."
        "</p>",
        unsafe_allow_html=True,
    )

    explore_col, hold_col = st.columns(2, gap="large")
    with explore_col:
        st.markdown(
            "<p class='atlas-col-label'>Still in fog</p>",
            unsafe_allow_html=True,
        )
        if not trip["explore"]:
            st.success(f"The map is fully lit, {FIRST_NAME}. Hold what you have.")
        else:
            for topic in trip["explore"]:
                st.markdown(
                    f"<div class='atlas-quest'>"
                    f"<p class='atlas-quest-title'>{_esc(topic['title'])}</p>"
                    f"<p class='atlas-quest-meta'>{_esc(_topic_caption(topic, today))}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Select this topic",
                    key=f"exp_pick_{topic['slug']}",
                    width="stretch",
                ):
                    focus_topic(topic)
                    st.rerun()
            if trip["explore_left"]:
                st.caption(f"{trip['explore_left']} more unseen in darker units")

    with hold_col:
        st.markdown(
            "<p class='atlas-col-label'>Due to hold</p>",
            unsafe_allow_html=True,
        )
        if not trip["hold"]:
            st.info("Nothing is due. Pick any topic from the dropdowns.")
        else:
            for topic in trip["hold"]:
                st.markdown(
                    f"<div class='atlas-quest is-hold'>"
                    f"<p class='atlas-quest-title'>{_esc(topic['title'])}</p>"
                    f"<p class='atlas-quest-meta'>{_esc(_topic_caption(topic, today))} · "
                    f"{_esc(STATE_META[topic['state']]['label'])}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Select this topic",
                    key=f"exp_hold_{topic['slug']}",
                    type="primary",
                    width="stretch",
                ):
                    focus_topic(topic)
                    st.rerun()
            if trip["hold_left"]:
                st.caption(f"{trip['hold_left']} more waiting in the queue")


def render_log_form(run_db, queue_reward, topic, today):
    slug = topic["slug"]
    state = topic["state"]
    due = _due_label(topic, today)
    last = (
        topic["last_studied"].strftime("%d %b %Y")
        if topic.get("last_studied")
        else "never"
    )
    st.markdown(
        f"<div class='atlas-focus'>"
        f"<p class='atlas-focus-kicker'>{_esc(topic.get('region_title') or '')} · "
        f"{_esc(topic.get('unit_title') or topic.get('parent_title') or '')}</p>"
        f"<p class='atlas-focus-title'>{_esc(topic['title'])}</p>"
        f"<p class='atlas-focus-meta'>"
        f"<span class='atlas-legend-chip st-{_esc(state)}'>{_esc(STATE_META[state]['label'])}</span>"
        f" last studied { _esc(last) }"
        f"{' · ' + _esc(due) if due else ''}"
        f" · {int(topic.get('study_count') or 0)} visits"
        f"</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.form(f"atlas_log_form_{slug}", clear_on_submit=False):
        action = st.selectbox(
            "What did you do with this topic?",
            list(LOG_ACTIONS),
            format_func=lambda a: LOG_ACTIONS[a],
            key=f"atlas_action_{slug}",
        )
        note = st.text_area(
            "Notes — book, chapter, PYQ angle, what you keep forgetting",
            value=topic.get("last_note") or "",
            height=140,
            placeholder="e.g. Spectrum ch.12 · causes of 1857 stronger than course of the revolt · "
            "write land-revenue + sepoys + Bahadur Shah as the 10-marker spine",
            key=f"atlas_note_{slug}",
        )
        confidence = st.select_slider(
            "How easily can you recall it right now?",
            options=[1, 2, 3, 4, 5],
            value=max(1, int(topic.get("confidence") or 3)),
            format_func=lambda n: CONF_LABELS[n],
            key=f"atlas_conf_{slug}",
        )
        save_col, pin_col = st.columns(2)
        saved = save_col.form_submit_button("Save to Atlas", type="primary", width="stretch")
        pinned = pin_col.form_submit_button("Save + add to Today", width="stretch")

    if saved or pinned:
        if action == "save":
            ok = run_db(
                lambda: save_topic_details(slug, note=note, confidence=confidence),
                "Could not save notes",
            )
            if ok is not None:
                st.toast(f"Notes saved · {topic['title']}", icon="✎")
        else:
            ok = _apply_study(run_db, queue_reward, slug, action, confidence, note)
            if not ok:
                return
        if pinned:
            if run_db(
                lambda: add_daily_target(today, f"Atlas · {topic['title']}"),
                "Could not add target",
            ) is not None:
                st.toast("Pinned to Today", icon="◎")
        st.rerun()

    extra = st.columns(3)
    if extra[0].button("Snooze 1 day", key=f"log_snz1_{slug}", width="stretch"):
        if run_db(lambda: snooze_topic(slug, 1, today), "Could not snooze") is not None:
            st.toast("Pushed to tomorrow", icon="⏭")
            st.rerun()
    if extra[1].button("Snooze 3 days", key=f"log_snz3_{slug}", width="stretch"):
        if run_db(lambda: snooze_topic(slug, 3, today), "Could not snooze") is not None:
            st.toast("Snoozed 3 days", icon="⏭")
            st.rerun()
    if topic.get("is_custom"):
        if extra[2].button("Remove custom topic", key=f"log_del_{slug}", width="stretch"):
            if run_db(lambda: archive_custom_node(slug), "Could not remove") is not None:
                st.session_state.pop("atlas_topic", None)
                st.toast("Removed from map", icon="🗑")
                st.rerun()
    else:
        if extra[2].button("Reset this topic", key=f"log_rst_{slug}", width="stretch"):
            if run_db(lambda: reset_topic(slug), "Could not reset") is not None:
                st.toast("Back to fog", icon="🌫")
                st.rerun()


def _on_region_change():
    st.session_state.pop("atlas_unit", None)
    st.session_state.pop("atlas_topic", None)


def _on_unit_change():
    st.session_state.pop("atlas_topic", None)


def _on_topic_change():
    slug = st.session_state.get("atlas_topic")
    if slug:
        st.session_state.atlas_global_pick = slug


def _on_global_pick(topics_by_slug):
    slug = st.session_state.get("atlas_global_pick")
    topic = topics_by_slug.get(slug)
    if topic:
        focus_topic(topic)


def render_topic_pickers(regions, all_topics, today):
    """Realm / unit / topic dropdowns + a type-to-search list of every topic."""
    topics_by_slug = {t["slug"]: t for t in all_topics}
    region_by_slug = {r["slug"]: r for r in regions}
    region_slugs = [r["slug"] for r in regions]

    if st.session_state.get("atlas_region") not in region_by_slug:
        default = all_topics[0] if all_topics else None
        if default:
            focus_topic(default)
        elif region_slugs:
            st.session_state.atlas_region = region_slugs[0]

    region_slug = st.session_state.get("atlas_region") or (region_slugs[0] if region_slugs else "")
    units = get_unit_summaries(region_slug) if region_slug else []
    unit_slugs = [u["slug"] for u in units]
    if st.session_state.get("atlas_unit") not in unit_slugs:
        due_units = [u for u in units if u["due"]]
        st.session_state.atlas_unit = (
            due_units[0]["slug"]
            if due_units
            else (min(units, key=lambda u: u["coverage"])["slug"] if units else "")
        )

    unit_slug = st.session_state.get("atlas_unit") or ""
    topics = get_topics(unit_slug) if unit_slug else []
    unit_meta = next((u for u in units if u["slug"] == unit_slug), None)
    for topic in topics:
        if unit_meta:
            topic["unit_title"] = unit_meta["title"]
            topic["region_title"] = unit_meta["region_title"]
            topic["unit_slug"] = unit_meta["slug"]
            topic["region_slug"] = unit_meta["region_slug"]

    topic_slugs = [t["slug"] for t in topics]
    if st.session_state.get("atlas_topic") not in topic_slugs:
        due_first = next(
            (t for t in topics if t.get("next_due") and t["next_due"] <= today),
            None,
        )
        fog_first = next((t for t in topics if t["state"] == "unseen"), None)
        st.session_state.atlas_topic = (
            (due_first or fog_first or topics[0])["slug"] if topics else ""
        )

    # Keep the search box pointed at the cascade — must happen before the widget.
    if st.session_state.get("atlas_topic"):
        st.session_state.atlas_global_pick = st.session_state.atlas_topic

    st.markdown(
        '<p class="section-label">Log</p>'
        '<p class="section-title">Pick a topic, then write what you know</p>'
        '<p class="workspace-hint">'
        "Type in the top box to jump anywhere, or scroll Realm → Unit → Topic. "
        "Then fill the form — nothing is saved until you hit Save."
        "</p>",
        unsafe_allow_html=True,
    )

    st.selectbox(
        "Find any topic (type to search)",
        [t["slug"] for t in all_topics],
        format_func=lambda s: _full_label(topics_by_slug[s], today),
        key="atlas_global_pick",
        on_change=_on_global_pick,
        args=(topics_by_slug,),
        help="Click, then type 1857 or Gupta or monsoon — the list filters as you type.",
    )

    rcol, ucol, tcol = st.columns(3)
    with rcol:
        st.selectbox(
            "Realm",
            region_slugs,
            format_func=lambda s: (
                f"{region_by_slug[s]['title']}  ·  "
                f"{region_by_slug[s]['coverage']:.0f}% lit"
            ),
            key="atlas_region",
            on_change=_on_region_change,
        )

    with ucol:
        if unit_slugs:
            st.selectbox(
                "Unit",
                unit_slugs,
                format_func=lambda s: next(
                    (
                        f"{u['title']}  ·  {u['touched']}/{u['total']}"
                        + (f"  ·  {u['due']} due" if u["due"] else "")
                        for u in units
                        if u["slug"] == s
                    ),
                    s,
                ),
                key="atlas_unit",
                on_change=_on_unit_change,
            )
        else:
            st.selectbox("Unit", ["—"], disabled=True, key="atlas_unit_empty")

    with tcol:
        if topic_slugs:
            st.selectbox(
                "Topic",
                topic_slugs,
                format_func=lambda s: next(
                    (_topic_label(t, today) for t in topics if t["slug"] == s),
                    s,
                ),
                key="atlas_topic",
                on_change=_on_topic_change,
            )
        else:
            st.selectbox("Topic", ["—"], disabled=True, key="atlas_topic_empty")

    chosen_slug = st.session_state.get("atlas_topic")
    chosen = next((t for t in topics if t["slug"] == chosen_slug), None)
    if chosen is None and chosen_slug in topics_by_slug:
        chosen = topics_by_slug[chosen_slug]
    return chosen, units, topics


def render_atlas_page(run_db, queue_reward, today=None):
    today = today or date.today()
    try:
        overview = get_atlas_overview(today)
        regions = get_region_summaries()
        all_topics = get_all_topics()
    except DatabaseError as exc:
        st.error(f"Could not open the Atlas: {exc}")
        return

    st.markdown(
        f'<p class="section-label">Syllabus</p>'
        f'<p class="section-title">Atlas</p>'
        f'<p class="workspace-hint">'
        f"Indian History is not a checklist, {FIRST_NAME} — it is territory. "
        f"Fog is what you have never opened. Gold is what you can still write."
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown(render_overview_strip(overview), unsafe_allow_html=True)

    if not regions:
        st.warning("The atlas seed is empty.")
        return

    chosen, units, _topics = render_topic_pickers(regions, all_topics, today)
    region_meta = next(
        (r for r in regions if r["slug"] == st.session_state.get("atlas_region")),
        regions[0],
    )
    render_subject_web(
        units,
        today,
        st.session_state.get("atlas_topic"),
        region_meta["title"],
    )

    if chosen:
        render_log_form(run_db, queue_reward, chosen, today)
    else:
        st.info("Pick a topic from the dropdowns above, or click a node on the web.")

    st.divider()
    render_expedition(today)

    region_slug = st.session_state.get("atlas_region")
    unit_slug = st.session_state.get("atlas_unit")

    with st.expander("Add a missing topic"):
        st.caption("The seed is exam-shaped, not complete. Drop anything you actually study.")
        custom_title = st.text_input("Topic title", key="atlas_custom_title")
        if st.button("Add under this unit", key="atlas_add_topic", type="primary"):
            if not unit_slug:
                st.error("Pick a unit first.")
            elif run_db(
                lambda: add_custom_topic(custom_title, unit_slug),
                "Could not add topic",
            ) is not None:
                st.toast("Pinned on the map", icon="📌")
                st.rerun()
        new_unit = st.text_input("Or create a new unit in this realm", key="atlas_custom_unit")
        if st.button("Add unit", key="atlas_add_unit"):
            if not region_slug:
                st.error("Pick a realm first.")
            elif run_db(
                lambda: add_custom_unit(new_unit, region_slug),
                "Could not add unit",
            ) is not None:
                st.toast("New unit on the map", icon="🗺")
                st.rerun()

    blinds = get_blind_units()
    recent = get_recent_atlas_log(8)
    due_more = get_due_topics(today, limit=8)
    side_l, side_r = st.columns(2, gap="large")
    with side_l:
        with st.expander("Blind spots — never opened", expanded=False):
            if not blinds:
                st.caption("Every unit has at least one lit cell.")
            else:
                for unit in blinds:
                    st.markdown(
                        f"- **{unit['title']}** · {unit['region_title']} · {unit['total']} topics still in fog"
                    )
        with st.expander("Due queue"):
            if not due_more:
                st.caption("Clear. Come back after you scout.")
            else:
                for topic in due_more:
                    if st.button(
                        f"{topic['title']} · {_due_label(topic, today)}",
                        key=f"due_pick_{topic['slug']}",
                    ):
                        focus_topic(topic)
                        st.rerun()
    with side_r:
        with st.expander("Recent atlas moves"):
            if not recent:
                st.caption("Your first save will show up here.")
            else:
                for row in recent:
                    verb = {
                        "scout": "scouted",
                        "map": "mapped",
                        "revise": "revised",
                        "fortify": "fortified",
                        "save": "updated notes",
                    }.get(row["action"], row["action"])
                    st.markdown(
                        f"- {row['log_date']} · **{row['title']}** {verb}"
                    )
        with st.expander("How the Atlas works"):
            st.markdown(
                """
- Each **subject** is a web. Diamonds are units. Dots are topics.
- **Fog / grey** — never opened.
- **Yellow** — first reading.
- **Lime → green** — notes, then a real revision.
- **Dark forest** — you can write a 10-mark answer.
- Stop touching a topic and its colour **bleaches** back toward fog
  (half its green is gone after ~18 days overdue).
- Click a node, or use the dropdowns. Nothing saves until you hit **Save**.
                """
            )
