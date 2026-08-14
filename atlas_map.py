"""Living subject web — topics as a coloured network that darkens and fades."""

from __future__ import annotations

import hashlib
import math
from datetime import date

import plotly.graph_objects as go

from atlas import STATE_META, topic_vitality

# Fresh coverage ramp: fog → first-reading yellow → notes lime → held green → 10-mark forest
FRESH_STOPS = (
    (0.00, "#5a6274"),
    (0.22, "#f0c14d"),
    (0.48, "#c5d63c"),
    (0.74, "#2fbe6a"),
    (1.00, "#0a4a30"),
)
FOG_DARK = "#3a4152"
FOG_PAPER = "#d9d2c4"
# Neglect bleaches toward a pale khaki — lighter, not darker
WASH_DARK = "#c8c4ae"
WASH_PAPER = "#efe8d2"
HUB_DARK = "#8ea0c8"
HUB_PAPER = "#4a5568"


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        *(max(0, min(255, int(round(c)))) for c in rgb)
    )


def _lerp(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    return a + (b - a) * t


def _lerp_hex(a, b, t):
    ra, ga, ba = _hex_to_rgb(a)
    rb, gb, bb = _hex_to_rgb(b)
    return _rgb_to_hex((_lerp(ra, rb, t), _lerp(ga, gb, t), _lerp(ba, bb, t)))


def _color_along(stops, t):
    t = max(0.0, min(1.0, float(t)))
    for i in range(1, len(stops)):
        t0, c0 = stops[i - 1]
        t1, c1 = stops[i]
        if t <= t1:
            span = t1 - t0 or 1.0
            return _lerp_hex(c0, c1, (t - t0) / span)
    return stops[-1][1]


def topic_color(topic, today=None, *, paper=False):
    """Yellow on first pass, darker green as mastery rises, bleach if neglected."""
    today = today or date.today()
    vit = topic_vitality(topic, today)
    fog = FOG_PAPER if paper else FOG_DARK
    wash = WASH_PAPER if paper else WASH_DARK
    if vit["mastery"] <= 0:
        return {
            **vit,
            "hex": fog,
            "fresh_hex": fog,
            "line": "#8a7340" if _is_dueish(topic, today) else ("#b7a98c" if paper else "#6b7386"),
        }
    fresh = _color_along(FRESH_STOPS, vit["mastery"])
    washed = _lerp_hex(fresh, wash, 0.88)
    display = _lerp_hex(fresh, washed, 1.0 - vit["decay"])
    return {
        **vit,
        "hex": display,
        "fresh_hex": fresh,
        "line": "#e8b84a" if vit["fading"] or _is_dueish(topic, today) else _lerp_hex(display, "#ffffff", 0.2),
    }


def _is_dueish(topic, today):
    due = topic.get("next_due")
    state = topic.get("state") or "unseen"
    if state == "unseen" or not due:
        return False
    return due <= today


def _wrap_label(title, limit=16):
    if len(title) <= limit or " " not in title:
        return title
    mid = len(title) // 2
    cut = title.rfind(" ", 0, mid + 6)
    if cut <= 0:
        return title
    return title[:cut] + "<br>" + title[cut + 1 :]


def _slug_jitter(slug, amount=0.12):
    digest = hashlib.md5(slug.encode("utf-8")).hexdigest()
    a = int(digest[:8], 16) / 0xFFFFFFFF
    b = int(digest[8:16], 16) / 0xFFFFFFFF
    return (a - 0.5) * 2 * amount, (b - 0.5) * 2 * amount


def layout_subject_web(units):
    """Radial web: subject hub → units → topic clusters, with organic jitter."""
    positions = {"__hub__": (0.0, 0.0)}
    unit_pos = {}
    n_units = len(units)
    if n_units == 0:
        return positions, unit_pos

    for i, unit in enumerate(units):
        if n_units == 1:
            theta = -math.pi / 2
            ur = 1.15
        else:
            theta = -math.pi / 2 + 2 * math.pi * i / n_units
            ur = 2.15
        jx, jy = _slug_jitter(unit["slug"], 0.08)
        ux, uy = ur * math.cos(theta) + jx, ur * math.sin(theta) + jy
        positions[unit["slug"]] = (ux, uy)
        unit_pos[unit["slug"]] = (ux, uy, theta)

        topics = unit.get("topics") or []
        n = len(topics)
        if n == 0:
            continue
        if n_units == 1:
            for j, topic in enumerate(topics):
                a = -math.pi / 2 + 2 * math.pi * j / n
                r = 3.35 + 0.18 * math.sin(j * 1.31)
                tx, ty = _slug_jitter(topic["slug"], 0.1)
                positions[topic["slug"]] = (r * math.cos(a) + tx, r * math.sin(a) + ty)
        else:
            arc = min(1.85, 0.16 * n + 0.35)
            for j, topic in enumerate(topics):
                frac = 0.5 if n == 1 else j / (n - 1)
                a = theta - arc / 2 + arc * frac
                r = 3.55 + 0.22 * math.sin(j * 1.17 + i)
                tx, ty = _slug_jitter(topic["slug"], 0.11)
                positions[topic["slug"]] = (r * math.cos(a) + tx, r * math.sin(a) + ty)
    return positions, unit_pos


def _edge_trace(xs, ys, color, width, paper):
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        hoverinfo="skip",
        showlegend=False,
        line=dict(color=color, width=width),
    )


def build_subject_web(
    region_title,
    units,
    *,
    today=None,
    selected_slug=None,
    paper=False,
):
    """Plotly figure: clickable topic web for one subject."""
    today = today or date.today()
    units = [u for u in units if u.get("topics")]
    positions, _ = layout_subject_web(units)
    fog = FOG_PAPER if paper else FOG_DARK
    spoke = "rgba(90, 80, 50, 0.22)" if paper else "rgba(160, 176, 210, 0.18)"
    strand = "rgba(120, 100, 40, 0.28)" if paper else "rgba(200, 190, 140, 0.22)"
    font = "#1a1c22" if paper else "#eef2ff"
    muted = "#6a7080" if paper else "#8e9ab3"
    plot_bg = "rgba(255,248,236,0.55)" if paper else "rgba(10, 14, 22, 0.35)"

    edge_x, edge_y = [], []
    strand_x, strand_y = [], []
    hx, hy = positions["__hub__"]

    for unit in units:
        ux, uy = positions[unit["slug"]]
        edge_x += [hx, ux, None]
        edge_y += [hy, uy, None]
        topics = unit.get("topics") or []
        for topic in topics:
            tx, ty = positions[topic["slug"]]
            edge_x += [ux, tx, None]
            edge_y += [uy, ty, None]
        for a, b in zip(topics, topics[1:]):
            ax, ay = positions[a["slug"]]
            bx, by = positions[b["slug"]]
            strand_x += [ax, bx, None]
            strand_y += [ay, by, None]
        if len(topics) > 2 and len(units) == 1:
            ax, ay = positions[topics[-1]["slug"]]
            bx, by = positions[topics[0]["slug"]]
            strand_x += [ax, bx, None]
            strand_y += [ay, by, None]

    # Connect neighbouring units so the subject reads as one web
    if len(units) > 1:
        for a, b in zip(units, units[1:]):
            ax, ay = positions[a["slug"]]
            bx, by = positions[b["slug"]]
            edge_x += [ax, bx, None]
            edge_y += [ay, by, None]
        ax, ay = positions[units[-1]["slug"]]
        bx, by = positions[units[0]["slug"]]
        edge_x += [ax, bx, None]
        edge_y += [ay, by, None]

    traces = [
        _edge_trace(edge_x, edge_y, spoke, 1.1, paper),
        _edge_trace(strand_x, strand_y, strand, 0.9, paper),
    ]

    # Topic nodes
    xs, ys, colors, sizes, slugs, hovers, lines, line_w = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    sel_x = sel_y = sel_color = None
    for unit in units:
        for topic in unit.get("topics") or []:
            x, y = positions[topic["slug"]]
            paint = topic_color(topic, today, paper=paper)
            state = topic.get("state") or "unseen"
            last = topic.get("last_studied")
            last_s = last.strftime("%d %b %Y") if last else "never"
            due = topic.get("next_due")
            due_s = due.strftime("%d %b") if due else "—"
            fade = (
                f"fading {paint['overdue_days']}d"
                if paint["fading"]
                else ("fresh" if paint["fresh"] else "idle")
            )
            hover = (
                f"<b>{topic['title']}</b><br>"
                f"{unit['title']}<br>"
                f"{STATE_META[state]['label']} · {fade}<br>"
                f"last {last_s} · due {due_s}<br>"
                f"<i>Click to log this topic</i>"
            )
            size = 9 + 16 * paint["vitality"]
            if state == "unseen":
                size = 8
            if topic["slug"] == selected_slug:
                sel_x, sel_y, sel_color = x, y, paint["hex"]
                size += 5
            xs.append(x)
            ys.append(y)
            colors.append(paint["hex"])
            sizes.append(size)
            slugs.append(topic["slug"])
            hovers.append(hover)
            lines.append(paint["line"])
            line_w.append(2.4 if paint["fading"] or _is_dueish(topic, today) else 1.1)

    traces.append(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            hoverinfo="text",
            hovertext=hovers,
            customdata=slugs,
            showlegend=False,
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(color=lines, width=line_w),
                opacity=0.96,
            ),
        )
    )

    if sel_x is not None:
        traces.append(
            go.Scatter(
                x=[sel_x],
                y=[sel_y],
                mode="markers",
                hoverinfo="skip",
                showlegend=False,
                marker=dict(
                    size=28,
                    color="rgba(0,0,0,0)",
                    line=dict(color="#f0c14d" if not paper else "#b45309", width=2.4),
                ),
            )
        )

    # Unit + hub labels
    ux, uy, utext, ucolor = [], [], [], []
    for unit in units:
        x, y = positions[unit["slug"]]
        paints = [topic_color(t, today, paper=paper) for t in unit.get("topics") or []]
        avg = (
            sum(p["vitality"] for p in paints) / len(paints) if paints else 0.0
        )
        ux.append(x)
        uy.append(y)
        utext.append(_wrap_label(unit["title"], 14))
        ucolor.append(_color_along(FRESH_STOPS, avg) if avg else fog)
    traces.append(
        go.Scatter(
            x=ux,
            y=uy,
            mode="markers+text",
            text=utext,
            textposition="top center",
            textfont=dict(size=11, color=font, family="Outfit, IBM Plex Sans, sans-serif"),
            hoverinfo="skip",
            showlegend=False,
            marker=dict(
                size=28,
                color=ucolor,
                line=dict(color=font, width=1.2),
                opacity=0.92,
                symbol="diamond",
            ),
        )
    )
    traces.append(
        go.Scatter(
            x=[hx],
            y=[hy],
            mode="markers+text",
            text=[_wrap_label(region_title, 15)],
            textposition="middle center",
            textfont=dict(size=11, color=font, family="Outfit, IBM Plex Sans, sans-serif"),
            hoverinfo="skip",
            showlegend=False,
            marker=dict(
                size=64,
                color=HUB_PAPER if paper else "#1b2436",
                line=dict(color=HUB_PAPER if paper else HUB_DARK, width=1.6),
                symbol="circle",
            ),
        )
    )

    fig = go.Figure(data=traces)
    fig.update_layout(
        height=640,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111826" if not paper else "#fffdf6",
            font_size=12,
            font_family="IBM Plex Sans, sans-serif",
            font_color=font,
        ),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1, range=[-5.1, 5.1]),
        yaxis=dict(visible=False, range=[-5.1, 5.1]),
        dragmode="pan",
    )
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=False)
    return fig


def color_ramp_html(*, paper=False):
    """Legend strip matching the living colours."""
    samples = [
        (0.00, "Fog"),
        (0.22, "First reading"),
        (0.48, "Notes"),
        (0.74, "Revised"),
        (1.00, "10-mark ready"),
    ]
    cells = []
    for t, label in samples:
        color = _color_along(FRESH_STOPS, t)
        if t == 0:
            color = FOG_PAPER if paper else FOG_DARK
        cells.append(
            f"<span class='atlas-ramp-cell' style='--c:{color}'>"
            f"<i></i>{label}</span>"
        )
    fade = _lerp_hex(_color_along(FRESH_STOPS, 1.0), WASH_PAPER if paper else WASH_DARK, 0.75)
    return (
        "<div class='atlas-ramp'>"
        + "".join(cells)
        + f"<span class='atlas-ramp-cell fade' style='--c:{fade}'>"
        f"<i></i>Left untouched → bleaches</span>"
        + "</div>"
    )


def parse_web_click(event):
    """Return topic slug from a Streamlit plotly selection, or None."""
    if event is None:
        return None
    sel = getattr(event, "selection", None)
    if sel is None and isinstance(event, dict):
        sel = event.get("selection")
    if sel is None:
        return None
    points = getattr(sel, "points", None)
    if points is None and isinstance(sel, dict):
        points = sel.get("points")
    if not points:
        return None
    pt = points[0]
    if isinstance(pt, dict):
        custom = pt.get("customdata")
    else:
        custom = getattr(pt, "customdata", None)
    if isinstance(custom, (list, tuple)):
        custom = custom[0] if custom else None
    if isinstance(custom, str) and custom and not custom.startswith("__"):
        return custom
    return None
