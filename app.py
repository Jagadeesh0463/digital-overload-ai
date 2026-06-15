import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from groq_client import extract_features
from scoring_engine import run_scoring
from recommender import get_action, generate_plan
from day_planner import build_day_plan
from session_store import init_history, add_to_history, get_history
from utils import ACTION_COLORS, DOMAIN_COLORS

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="Digital Overload AI",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
/* ── BACKGROUND ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
}
[data-testid="stHeader"] { background: transparent; }

/* ── TITLE (hide default st.title — we use hero card) ── */
h1 {
    color: #f8fafc !important;
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px;
    margin-bottom: 4px !important;
}

/* ── HEADINGS ── */
h2, h3, h4 {
    color: #e2e8f0 !important;
}

/* ── BODY TEXT & CAPTIONS ── */
p, .stMarkdown p {
    color: #cbd5e1 !important;
}
[data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: #1e293b;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #334155;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 13px !important;
    font-weight: 700 !important;
}

/* ── BUTTONS ── */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 12px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35) !important;
    width: 100% !important;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #1e40af, #2563eb) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
}

/* ── TEXT AREA ── */
[data-testid="stTextArea"] textarea {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #475569 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}
[data-testid="stTextArea"] textarea::placeholder {
    color: #64748b !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}

/* ── DIVIDER ── */
hr { border-color: #1e293b !important; }

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
}

/* ── FOOTER ── */
.footer-text {
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──
def colored_label(label: str, kind: str) -> str:
    """Prepend a colour emoji to a score label for display in st.metric delta.

    Args:
        label: the text label, e.g. "High", "Good Fit".
        kind: score type — "overload", "afi", or "capacity".

    Returns:
        Label string with colour emoji prefix, e.g. "🟠 High".
    """
    if kind == "overload":
        m = {"Critical": "🔴 Critical", "High": "🟠 High", "Moderate": "🟡 Moderate", "Low": "🟢 Low"}
    elif kind == "afi":
        m = {"Severe": "🔴 Severe", "High": "🟠 High", "Moderate": "🟡 Moderate", "Low": "🟢 Low"}
    elif kind == "capacity":
        m = {"Good Fit": "🟢 Good Fit", "Tight": "🟡 Tight", "Poor Fit": "🟠 Poor Fit", "Overcommitted": "🔴 Overcommitted"}
    else:
        m = {}
    return m.get(label, label)


def score_color(score: float, kind: str) -> str:
    if kind == "overload":
        if score >= 86: return "#ef4444"
        if score >= 66: return "#f97316"
        if score >= 41: return "#eab308"
        return "#22c55e"
    if kind == "afi":
        if score >= 81: return "#ef4444"
        if score >= 61: return "#f97316"
        if score >= 36: return "#eab308"
        return "#22c55e"
    if kind == "capacity":
        if score >= 100: return "#22c55e"
        if score >= 70:  return "#eab308"
        if score >= 40:  return "#f97316"
        return "#ef4444"
    return "#64748b"


def make_gauge(value: float, label: str, kind: str) -> go.Figure:
    """Build a Plotly gauge chart for a single score.

    Args:
        value: numeric score (0–100).
        label: text label shown below the gauge needle.
        kind: score type — used for colour mapping ("overload", "afi", "capacity").

    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    color = score_color(value, kind)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"<b>{label}</b>", "font": {"size": 13}},
        number={"font": {"size": 32}, "suffix": "/100"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": color, "thickness": 0.3},
            "steps": [
                {"range": [0,  40],  "color": "#dcfce7"},
                {"range": [40, 66],  "color": "#fef9c3"},
                {"range": [66, 86],  "color": "#ffedd5"},
                {"range": [86, 100], "color": "#fee2e2"},
            ],
        }
    ))
    fig.update_layout(height=230, margin=dict(t=40, b=10, l=20, r=20))
    return fig


def make_capacity_chart(free_h: float, est_h: float, cap_status: str) -> go.Figure:
    """Build a Plotly horizontal bar chart comparing estimated workload vs available time.

    Workload bar is colour-coded by capacity status (green→yellow→orange→red).
    Available Time bar is always blue. A vertical dashed reference line marks
    the capacity limit when workload exceeds available time.

    Args:
        free_h: available hours today.
        est_h: estimated total hours of work.
        cap_status: capacity label — "Good Fit", "Tight", "Poor Fit", "Overcommitted".

    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    workload_color = {
        "Good Fit":     "#22c55e",
        "Tight":        "#eab308",
        "Poor Fit":     "#f97316",
        "Overcommitted":"#ef4444",
    }.get(cap_status, "#64748b")

    max_val = max(est_h, free_h, 1) * 1.2  # 20% right padding for labels

    fig = go.Figure()

    # Available Time bar — always blue
    fig.add_trace(go.Bar(
        x=[free_h],
        y=["Available Time"],
        orientation="h",
        marker=dict(color="#3b82f6", line=dict(width=0)),
        text=[f"  {free_h}h"],
        textposition="outside",
        textfont=dict(color="#93c5fd", size=12, family="Arial"),
        showlegend=False,
    ))

    # Estimated Workload bar — colour by severity
    fig.add_trace(go.Bar(
        x=[est_h],
        y=["Estimated Workload"],
        orientation="h",
        marker=dict(color=workload_color, line=dict(width=0)),
        text=[f"  {est_h}h"],
        textposition="outside",
        textfont=dict(color=workload_color, size=12, family="Arial"),
        showlegend=False,
    ))

    # Vertical dashed line at capacity limit (only when workload exceeds it)
    if est_h > free_h and free_h > 0:
        fig.add_vline(
            x=free_h,
            line_dash="dash",
            line_color="#3b82f6",
            line_width=1.5,
            annotation_text="capacity limit",
            annotation_font_color="#3b82f6",
            annotation_font_size=10,
            annotation_position="top right",
        )

    fig.update_layout(
        height=160,
        margin=dict(l=0, r=60, t=16, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            range=[0, max_val],
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            ticksuffix="h",
            tickfont=dict(color="#64748b", size=11),
            color="#64748b",
            zeroline=False,
        ),
        yaxis=dict(
            tickfont=dict(color="#94a3b8", size=11),
            color="#94a3b8",
        ),
        bargap=0.35,
    )
    return fig


def make_domain_chart(tasks: list) -> go.Figure:
    """Build a Plotly horizontal bar chart showing estimated hours per task domain.

    Args:
        tasks: list of task dicts with keys: domain, hours.

    Returns:
        Plotly Figure object ready for st.plotly_chart().
    """
    domain_hours = {}
    for task in tasks:
        d = task.get("domain", "Academic")
        domain_hours[d] = domain_hours.get(d, 0) + task.get("hours", 1)

    total   = sum(domain_hours.values()) or 1
    domains = list(domain_hours.keys())
    pcts    = [round(h / total * 100) for h in domain_hours.values()]
    colors  = [DOMAIN_COLORS.get(d, "#64748b") for d in domains]

    fig = go.Figure(go.Bar(
        x=pcts, y=domains,
        orientation="h",
        marker_color=colors,
        text=[f"{p}%" for p in pcts],
        textposition="auto",
    ))
    fig.update_layout(
        height=230,
        margin=dict(t=20, b=20, l=10, r=20),
        xaxis_title="% of task hours",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── OVERLOAD SIGNAL DETECTOR ──
def get_overload_signals(features: dict, scores: dict) -> list:
    """Detect named overload patterns from features and scores.

    Returns a list of (emoji, title, detail) tuples for each triggered signal.
    Signals cover: deadline clusters, communication overload, energy deficit,
    domain fragmentation, and critical capacity thresholds.

    Args:
        features: raw feature dict from Groq extraction.
        scores: output dict from run_scoring().

    Returns:
        List of (emoji str, title str, detail str) tuples.
    """
    signals = []
    if features.get("task_count", 0) >= 4 and features.get("urgency_signals", 0) >= 2:
        signals.append(("🔴", "Multiple Assignment Deadlines", "High task count with urgent deadlines detected"))
    if features.get("pending_messages", 0) >= 10:
        signals.append(("🟠", "High Communication Load", f"{features['pending_messages']} pending messages competing for attention"))
    if features.get("context_switches", 0) >= 3 or features.get("unique_domains", 0) >= 3:
        signals.append(("🟠", "Context Switching Risk", "Frequent domain shifts detected — academic, social, and admin tasks overlapping"))
    if features.get("free_hours", 10) <= 4:
        signals.append(("🔴", "Limited Available Hours", f"Only {features.get('free_hours', 0)}h free — very tight for planned workload"))
    if features.get("energy_level", "Medium") == "Low":
        signals.append(("🟡", "Low Energy Level", "Reduced effective capacity — longer tasks will feel harder than estimated"))
    if scores.get("capacity", 100) < 70:
        signals.append(("🔴", "Capacity Mismatch", "Planned work exceeds available time and energy"))
    if scores.get("afi", 0) > 60:
        signals.append(("🟠", "Attention Fragmentation Detected", f"AFI of {scores['afi']:.0f}/100 — cognitive scatter across multiple domains"))
    return signals


# ── AI ANALYSIS SUMMARY GENERATOR ──
def generate_ai_summary(features: dict, scores: dict) -> str:
    """Generate a plain-English workload summary from features and scores.

    Produces a two-sentence natural-language explanation of the dominant
    overload driver and recommended focus area. No additional API call —
    derived entirely from the already-extracted features and computed scores.

    Args:
        features: raw feature dict from Groq extraction.
        scores: output dict from run_scoring().

    Returns:
        Summary string suitable for display in the Analysis section.
    """
    overload_label  = scores["overload_label"]
    afi_label       = scores["afi_label"]
    capacity_label  = scores["capacity_label"]
    energy          = features.get("energy_level", "Medium")
    task_count      = features.get("task_count", 0)
    pending_msgs    = features.get("pending_messages", 0)
    free_hours      = features.get("free_hours", 0)
    est_hours       = features.get("estimated_hours", 0)
    domains         = features.get("unique_domains", 1)

    parts = []

    # Opening sentence based on overload level
    if overload_label == "Critical":
        parts.append(f"Your workload is critically overloaded — {task_count} active tasks with high deadline pressure leave very little room to operate.")
    elif overload_label == "High":
        parts.append(f"Your workload is heavily loaded with {task_count} tasks competing for your attention across multiple domains.")
    elif overload_label == "Moderate":
        parts.append(f"Your workload is moderately overloaded with {task_count} active tasks and some deadline pressure.")
    else:
        parts.append(f"Your workload appears manageable with {task_count} active tasks and limited urgency signals.")

    # AFI context
    if afi_label in ["Severe", "High"]:
        parts.append(f"Attention is fragmented across {domains} domains — switching between academic, social, and administrative tasks simultaneously increases cognitive load significantly.")
    elif afi_label == "Moderate":
        parts.append(f"Some attention fragmentation detected across {domains} domains — grouping similar tasks will help maintain focus.")

    # Messages
    if pending_msgs >= 20:
        parts.append(f"{pending_msgs} unread messages are creating a significant communication backlog on top of your academic load.")
    elif pending_msgs >= 10:
        parts.append(f"{pending_msgs} pending messages are adding background pressure to your day.")

    # Capacity
    if capacity_label == "Overcommitted":
        parts.append(f"With only {free_hours}h available against an estimated {est_hours}h of work, completing everything today without prioritization is unrealistic.")
    elif capacity_label == "Poor Fit":
        parts.append(f"Available time ({free_hours}h) is significantly less than estimated workload ({est_hours}h) — deferral is necessary.")
    elif capacity_label == "Tight":
        parts.append(f"Time is tight — {free_hours}h available for approximately {est_hours}h of work. Stay focused and avoid new commitments.")

    # Energy
    if energy == "Low":
        parts.append("Low energy further reduces effective capacity — plan for shorter focus blocks with recovery time between sessions.")

    return " ".join(parts)


# ── TOP PRIORITIES + SAFE TO DEFER ──
def _priority_reason(task: dict, features: dict) -> str:
    """Generate a short reason string explaining why a task is high priority.

    Args:
        task: task dict with keys: name, domain, hours.
        features: raw feature dict from Groq extraction.

    Returns:
        Short reason string, e.g. "High urgency · Academic".
    """
    domain = task.get("domain", "Academic")
    hours  = float(task.get("hours", 1.0))
    name   = task.get("name", "").lower()

    urgency_words = ["due", "tomorrow", "tonight", "today", "urgent", "asap",
                     "exam", "quiz", "test", "deadline", "submit"]
    is_urgent = any(w in name for w in urgency_words)

    if is_urgent:
        return "Due soon"
    elif hours >= 3:
        return "High effort · plan ahead"
    elif domain == "Academic":
        return "Academic priority"
    elif domain == "Admin":
        return "Admin — blocks other work"
    else:
        return f"{domain} task"


def get_priorities(tasks: list, action: str, features: dict | None = None) -> tuple:
    """Split tasks into top priorities and safe-to-defer lists with reasoning.

    Academic and Admin tasks are treated as high priority.
    Social and Personal tasks are moved to the defer list when action
    is REDUCE or DEFER.

    Args:
        tasks: list of task dicts with keys: name, domain, hours.
        action: recommendation action string — FOCUS, DEFER, SPLIT, or REDUCE.
        features: raw feature dict used to generate priority reasons (optional).

    Returns:
        Tuple of (top_priorities[:3], safe_to_defer[:3])
        where each item is a dict with keys: name, reason.
    """
    from utils import DOMAIN_PRIORITY
    features = features or {}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: DOMAIN_PRIORITY.index(t.get("domain", "Personal"))
        if t.get("domain", "Personal") in DOMAIN_PRIORITY else 4
    )
    top_tasks   = [t for t in sorted_tasks if t.get("domain") in ["Academic", "Admin"]][:3]
    defer_tasks = [t for t in sorted_tasks if t.get("domain") in ["Social", "Personal"]
                   and action in ["REDUCE", "DEFER"]][:3]
    # Fill top if less than 3
    top_names = {t["name"] for t in top_tasks}
    for t in sorted_tasks:
        if t["name"] not in top_names and len(top_tasks) < 3:
            top_tasks.append(t)
            top_names.add(t["name"])

    top   = [{"name": t["name"], "reason": _priority_reason(t, features)} for t in top_tasks]
    defer = [{"name": t["name"], "reason": f"{t.get('domain','')}"} for t in defer_tasks]
    return top, defer


# ── MAIN ──
def main():
    init_history()

    # ── HERO CARD ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 36px 40px 28px 40px;
        margin-bottom: 8px;
    ">
        <h1 style="color:#f8fafc; margin:0 0 8px 0; font-size:2.4rem; font-weight:900; letter-spacing:-0.5px;">
            🧠 Digital Overload AI
        </h1>
        <p style="color:#94a3b8; font-size:1.1rem; font-weight:600; margin:0 0 4px 0;">
            AI-Powered Workload &amp; Focus Analyzer
        </p>
        <p style="color:#64748b; font-size:0.95rem; margin:0 0 16px 0;">
            Transform unstructured schedules into actionable daily plans.
        </p>
        <p style="color:#7dd3fc; font-size:0.88rem; margin:0 0 16px 0; font-weight:600; letter-spacing:0.3px;">
            ⚡ Powered by Groq API &nbsp;·&nbsp; Natural Language Workload Analysis
        </p>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            <span style="background:#0f2d1a;border:1px solid #22c55e;color:#22c55e;font-size:0.78rem;font-weight:700;padding:3px 12px;border-radius:20px;">✓ 3-Score Workload Diagnostic</span>
            <span style="background:#0f2d1a;border:1px solid #22c55e;color:#22c55e;font-size:0.78rem;font-weight:700;padding:3px 12px;border-radius:20px;">✓ Attention Fragmentation Index (AFI)</span>
            <span style="background:#0f2d1a;border:1px solid #22c55e;color:#22c55e;font-size:0.78rem;font-weight:700;padding:3px 12px;border-radius:20px;">✓ Smart Task Prioritization</span>
            <span style="background:#0f2d1a;border:1px solid #22c55e;color:#22c55e;font-size:0.78rem;font-weight:700;padding:3px 12px;border-radius:20px;">✓ AI Day Planner · Groq Llama 3.3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DISCLAIMER CARD ──
    st.markdown("""
    <div style="
        background: #1c1000;
        border: 1px solid #92400e;
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 20px;
    ">
        <span style="color:#fbbf24; font-weight:700; font-size:0.9rem;">⚠ Educational productivity tool only.</span>
        <span style="color:#fcd34d; font-size:0.88rem;"> Not a medical or mental health diagnostic system.</span>
    </div>
    """, unsafe_allow_html=True)

    # ── HOW IT WORKS ──
    st.markdown("""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px 24px;margin-bottom:20px;">
        <p style="color:#64748b;font-size:12px;font-weight:700;letter-spacing:1px;margin:0 0 10px 0;">HOW IT WORKS</p>
        <div style="display:flex;gap:0;align-items:center;flex-wrap:wrap;">
            <span style="color:#94a3b8;font-size:13px;">📝 Describe your day</span>
            <span style="color:#334155;margin:0 10px;">→</span>
            <span style="color:#94a3b8;font-size:13px;">🤖 AI extracts workload signals</span>
            <span style="color:#334155;margin:0 10px;">→</span>
            <span style="color:#94a3b8;font-size:13px;">📊 3-score diagnostic runs</span>
            <span style="color:#334155;margin:0 10px;">→</span>
            <span style="color:#94a3b8;font-size:13px;">🎯 Prioritization guidance delivered</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Input
    st.markdown("### Describe Your Day")
    st.markdown('<p style="color:#94a3b8; font-size:0.9rem; margin-top:-12px; margin-bottom:8px;">Include tasks, deadlines, pending messages, available study hours, and energy level.</p>', unsafe_allow_html=True)

    # ── DEMO PROFILES ──
    st.markdown('<p style="color:#cbd5e1; font-weight:700; font-size:0.9rem; margin-bottom:4px;">Quick Start Examples</p>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("😵 Overloaded Student"):
            st.session_state["demo_text"] = """4 assignments due this week — OS on Wednesday, DBMS on Thursday, Web Dev and ML both on Friday. 18 WhatsApp messages from classmates pending. Club meeting tomorrow at 5 PM for 2 hours. Feeling low energy today. Only 3 free hours tonight after 9 PM."""

    with col_b:
        if st.button("📚 Exam Sprint"):
            st.session_state["demo_text"] = """5 subject exams in the next 4 days — Computer Networks today, Operating Systems tomorrow, DBMS the day after, then Web Dev and Cloud Computing on day 4. Zero pending messages — switched off notifications completely. Energy is medium. I have about 8 free hours today. No club commitments this week."""

    with col_c:
        if st.button("💼 Club Leader"):
            st.session_state["demo_text"] = """I am in 3 college clubs — Robotics, Cultural Committee, and NSS. All three have events this week. I also have 2 assignments due Friday and a lab record submission on Thursday. About 50 WhatsApp messages unread across 6 groups. Feeling low energy — been staying up late all week. Only 2 free hours today."""

    demo_value = st.session_state.get("demo_text", "")

    input_text = st.text_area(
        label="input",
        placeholder="Example:\n3 assignments due this week.\n18 messages pending.\nClub meeting tomorrow.\nEnergy level: low.\nAvailable time today: 3 hours.",
        height=120,
        label_visibility="collapsed",
        value=demo_value,
    )

    analyze = st.button("🔍 Analyze Workload", type="primary", width='stretch')

    if analyze and input_text.strip():
        with st.spinner("Analyzing your workload with Groq AI..."):
            try:
                # Step 1 — Extract
                features = extract_features(input_text)

                # Step 2 — Score
                scores = run_scoring(features)

                # Step 3 — Recommend
                action = get_action(
                    scores["overload_label"],
                    scores["afi_label"],
                    scores["capacity_label"],
                )
                plan = generate_plan(action, scores)

                # Step 4 — Day plan
                tasks      = features.get("tasks", [])
                start_time = features.get("start_time", "Now")
                day_plan   = build_day_plan(
                    tasks,
                    features.get("free_hours", 3),
                    scores["normed"]["energy_level"],
                    start_time,
                )

                # Step 5 — Save history
                add_to_history({
                    "scores":     scores,
                    "action":     action,
                    "input_text": input_text,
                })

                # ═══════════════════════════════════════════
                # 📊 DIAGNOSTICS
                # ═══════════════════════════════════════════
                st.markdown("""
                <div style="border-left:4px solid #3b82f6;padding:6px 0 6px 14px;margin:28px 0 14px 0;">
                    <span style="color:#7dd3fc;font-size:13px;font-weight:800;letter-spacing:2px;">📊 DIAGNOSTICS</span>
                </div>""", unsafe_allow_html=True)

                # 3-score card with severity-colored HTML progress bars (Fix 7)
                o_col = score_color(scores["overload"], "overload")
                a_col = score_color(scores["afi"],      "afi")
                c_col = score_color(scores["capacity"], "capacity")
                o_pct = min(int(scores["overload"]), 100)
                a_pct = min(int(scores["afi"]),      100)
                c_pct = min(int(scores["capacity"]), 100)

                st.markdown('<div style="background:#1e293b;border:1px solid #334155;border-radius:14px;padding:18px 20px;">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("🔥 Overload Score", f"{scores['overload']:.0f} / 100",
                              colored_label(scores["overload_label"], "overload"))
                    st.markdown(
                        f'<div style="background:#0f172a;border-radius:4px;height:6px;margin-top:2px;">'
                        f'<div style="background:{o_col};width:{o_pct}%;height:6px;border-radius:4px;"></div>'
                        f'</div>', unsafe_allow_html=True)
                with c2:
                    st.metric("🧩 AFI Score", f"{scores['afi']:.0f} / 100",
                              colored_label(scores["afi_label"], "afi"))
                    st.markdown(
                        f'<div style="background:#0f172a;border-radius:4px;height:6px;margin-top:2px;">'
                        f'<div style="background:{a_col};width:{a_pct}%;height:6px;border-radius:4px;"></div>'
                        f'</div>', unsafe_allow_html=True)
                with c3:
                    st.metric("⏱️ Capacity Fit", f"{scores['capacity']:.0f}%",
                              colored_label(scores["capacity_label"], "capacity"))
                    st.markdown(
                        f'<div style="background:#0f172a;border-radius:4px;height:6px;margin-top:2px;">'
                        f'<div style="background:{c_col};width:{c_pct}%;height:6px;border-radius:4px;"></div>'
                        f'</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # OPE — moved directly after scores (Fix 4: highest-priority actionable output)
                cap_pct     = scores["capacity"]
                afi_val_ope = scores["afi"]
                if cap_pct < 40 or afi_val_ope > 80:
                    ope_status  = "🔴 AT CAPACITY"
                    ope_color   = "#ef4444"
                    ope_border  = "#ef4444"
                    ope_message = "⚠️ Do NOT accept any new tasks. Your available time and energy cannot absorb additional load."
                elif cap_pct < 70 or scores["overload"] > 65:
                    ope_status  = "🟠 AT RISK"
                    ope_color   = "#f97316"
                    ope_border  = "#f97316"
                    ope_message = "⚡ Proceed carefully. You have minimal buffer — one extra task could tip you into overload."
                else:
                    ope_status  = "🟢 MANAGEABLE"
                    ope_color   = "#22c55e"
                    ope_border  = "#334155"
                    ope_message = "✅ Load is within range. You have capacity — monitor scores before accepting new tasks."
                st.markdown(f"""<div style="background:#1e293b;border:1px solid {ope_border};border-radius:12px;padding:12px 18px;margin-top:10px;">
                    <p style="color:#64748b;font-size:10px;font-weight:700;letter-spacing:1px;margin:0 0 4px 0;">🔮 OVERLOAD PREDICTION ENGINE (OPE)</p>
                    <p style="color:{ope_color};font-size:15px;font-weight:800;margin:0 0 3px 0;">Status: {ope_status}</p>
                    <p style="color:#94a3b8;font-size:12px;margin:0;">{ope_message}</p>
                </div>""", unsafe_allow_html=True)

                # Score Drivers — dynamic contribution colors (Fix 9)
                normed = scores["normed"]
                task_contrib    = round(normed["task_count_norm"]            * 0.15 * 100)
                urgency_contrib = round(normed["urgency_signals_norm"]      * 0.20 * 100)
                energy_contrib  = round((1 - normed["energy_norm"])         * 0.15 * 100)
                time_contrib    = round(normed.get("time_pressure_norm", 0) * 0.50 * 100)
                domain_contrib  = round(normed["unique_domains_norm"]   * 0.50 * 100)
                switch_contrib  = round(normed["context_switches_norm"] * 0.30 * 100)
                msg_contrib     = round(normed["pending_messages_norm"] * 0.20 * 100)
                free            = features.get("free_hours", 0)
                est             = features.get("estimated_hours", 0)
                gap             = round(est - free, 1)

                def _dc(val: int, high: str) -> str:
                    """Color a driver contribution by magnitude: high=signal color, mid=muted, low=dim."""
                    if val >= 8: return high
                    if val >= 4: return "#94a3b8"
                    return "#475569"

                st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:14px 0 6px 0;">SCORE DRIVERS</p>', unsafe_allow_html=True)
                sd1, sd2, sd3 = st.columns(3)
                with sd1:
                    st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:10px;font-weight:700;margin:0 0 6px 0;letter-spacing:1px;">🔥 OVERLOAD</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(task_contrib,'#ef4444')};font-weight:700;">+{task_contrib}</span> &nbsp;Task Volume</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(urgency_contrib,'#f97316')};font-weight:700;">+{urgency_contrib}</span> &nbsp;Deadline Pressure</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(energy_contrib,'#eab308')};font-weight:700;">+{energy_contrib}</span> &nbsp;Low Energy</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(time_contrib,'#a78bfa')};font-weight:700;">+{time_contrib}</span> &nbsp;Time Pressure</p>
                    </div>""", unsafe_allow_html=True)
                with sd2:
                    st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:10px;font-weight:700;margin:0 0 6px 0;letter-spacing:1px;">🧩 AFI</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(domain_contrib,'#ef4444')};font-weight:700;">+{domain_contrib}</span> &nbsp;Domain Spread</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(switch_contrib,'#f97316')};font-weight:700;">+{switch_contrib}</span> &nbsp;Context Switches</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;"><span style="color:{_dc(msg_contrib,'#eab308')};font-weight:700;">+{msg_contrib}</span> &nbsp;Comm Load</p>
                    </div>""", unsafe_allow_html=True)
                with sd3:
                    gap_col = "#ef4444" if gap > 0 else "#22c55e"
                    st.markdown(f"""<div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:10px;font-weight:700;margin:0 0 6px 0;letter-spacing:1px;">⏱️ CAPACITY</p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;">Available: <span style="color:#22c55e;font-weight:700;">{free}h</span></p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;">Estimated: <span style="color:#ef4444;font-weight:700;">{est}h</span></p>
                        <p style="color:#f8fafc;margin:3px 0;font-size:13px;">Gap: <span style="color:{gap_col};font-weight:700;">{"+" if gap > 0 else ""}{gap}h</span></p>
                    </div>""", unsafe_allow_html=True)

                # Detected Signals — wrapped in card container (Fix 5), headers 12px (Fix 6)
                signals = get_overload_signals(features, scores)
                if signals:
                    critical  = [(t, d) for e, t, d in signals if e == '🔴']
                    warning   = [(t, d) for e, t, d in signals if e == '🟠']
                    attention = [(t, d) for e, t, d in signals if e == '🟡']

                    st.markdown('<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:14px 16px;margin-top:10px;">', unsafe_allow_html=True)
                    st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:0 0 8px 0;">DETECTED SIGNALS</p>', unsafe_allow_html=True)

                    def _render_group(label: str, color: str, items: list) -> None:
                        if not items:
                            return
                        st.markdown(
                            f'<p style="color:{color};font-size:12px;font-weight:800;'
                            f'letter-spacing:1px;margin:8px 0 4px 0;">{label}</p>',
                            unsafe_allow_html=True,
                        )
                        for title, detail in items:
                            st.markdown(
                                f'<div style="background:#1e293b;border-left:4px solid {color};'
                                f'border-radius:0 8px 8px 0;padding:7px 12px;margin-bottom:4px;">'
                                f'<span style="color:#f8fafc;font-weight:700;font-size:12px;">{title}</span>'
                                f'<span style="color:#64748b;font-size:11px;"> — {detail}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    _render_group("🔴 CRITICAL SIGNALS", "#ef4444", critical)
                    _render_group("🟠 WARNING SIGNALS",  "#f97316", warning)
                    _render_group("🟡 ATTENTION SIGNALS","#eab308", attention)
                    st.markdown('</div>', unsafe_allow_html=True)

                # ═══════════════════════════════════════════
                # 🧠 ANALYSIS
                # ═══════════════════════════════════════════
                st.markdown("""
                <div style="border-left:4px solid #8b5cf6;padding:6px 0 6px 14px;margin:28px 0 14px 0;">
                    <span style="color:#c4b5fd;font-size:13px;font-weight:800;letter-spacing:2px;">🧠 ANALYSIS</span>
                </div>""", unsafe_allow_html=True)

                # AI Summary — collapsed by default (Fix 8: always-expanded expander removed)
                summary = generate_ai_summary(features, scores)
                with st.expander("🧠 AI Analysis Summary — click to expand", expanded=False):
                    st.markdown(f'<p style="color:#e2e8f0;font-size:13px;line-height:1.7;margin:0;">{summary}</p>', unsafe_allow_html=True)

                # Workload vs Capacity chart (Fix 1: use_container_width)
                free_h     = features.get("free_hours", 0)
                est_h      = features.get("estimated_hours", 0)
                gap_h      = round(est_h - free_h, 1)
                cap_status = scores["capacity_label"]
                cap_color  = {"Good Fit":"#22c55e","Tight":"#eab308","Poor Fit":"#f97316","Overcommitted":"#ef4444"}.get(cap_status,"#64748b")

                st.markdown('<p style="color:#64748b;font-size:10px;font-weight:700;letter-spacing:1px;margin:10px 0 2px 0;">⏱️ WORKLOAD vs CAPACITY</p>', unsafe_allow_html=True)
                st.plotly_chart(make_capacity_chart(free_h, est_h, cap_status), use_container_width=True)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:-8px;margin-bottom:10px;">'
                    f'<span style="color:#94a3b8;font-size:12px;">Gap: <span style="color:{cap_color};font-weight:700;">{gap_h:+.1f}h</span></span>'
                    f'<span style="background:{cap_color};color:white;font-size:10px;font-weight:700;padding:2px 10px;border-radius:4px;">{cap_status}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Fix 2: duplicate AFI + Capacity Fit cards removed — scores already in Diagnostics

                # ═══════════════════════════════════════════
                # 🎯 RECOMMENDATIONS
                # ═══════════════════════════════════════════
                st.markdown("""
                <div style="border-left:4px solid #22c55e;padding:6px 0 6px 14px;margin:28px 0 14px 0;">
                    <span style="color:#86efac;font-size:13px;font-weight:800;letter-spacing:2px;">🎯 RECOMMENDATIONS</span>
                </div>""", unsafe_allow_html=True)

                # Action Plan
                action_color = ACTION_COLORS.get(action, "#64748b")
                st.markdown(
                    f'<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:0 0 8px 0;">'
                    f'PRIMARY STRATEGY &nbsp;<span style="background:{action_color};color:white;'
                    f'padding:2px 12px;border-radius:4px;font-size:11px;">{action}</span></p>',
                    unsafe_allow_html=True,
                )
                for item in plan:
                    if item["action"] == "ALERT":
                        st.warning(f"⚠️ {item['instruction']}")
                    else:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:9px 14px;'
                            f'margin-bottom:5px;border:1px solid #334155;">'
                            f'<span style="color:#475569;font-size:11px;font-weight:700;">{item["priority"]}</span>'
                            f'&nbsp;&nbsp;<span style="color:#e2e8f0;font-size:13px;">{item["instruction"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                # Priorities — Fix 10: hide Safe to Defer column for FOCUS strategy
                top_p, safe_d = get_priorities(tasks, action, features)
                show_defer    = action in ["REDUCE", "DEFER", "SPLIT"]

                if show_defer:
                    pr_col, df_col = st.columns(2)
                else:
                    pr_col = st.columns(1)[0]

                with pr_col:
                    st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:12px 0 6px 0;">🎯 TODAY\'S TOP PRIORITIES</p>', unsafe_allow_html=True)
                    if top_p:
                        for i, item in enumerate(top_p, 1):
                            st.markdown(
                                f'<div style="background:#1e293b;border-left:4px solid #22c55e;'
                                f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:5px;">'
                                f'<span style="color:#22c55e;font-weight:700;font-size:13px;">{i}. {item["name"]}</span><br>'
                                f'<span style="color:#64748b;font-size:11px;">{item["reason"]}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No tasks extracted.")

                if show_defer:
                    with df_col:
                        st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:12px 0 6px 0;">🕒 SAFE TO DEFER</p>', unsafe_allow_html=True)
                        if safe_d:
                            for item in safe_d:
                                st.markdown(
                                    f'<div style="background:#1e293b;border-left:4px solid #475569;'
                                    f'border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:5px;">'
                                    f'<span style="color:#94a3b8;font-size:13px;">→ {item["name"]}</span><br>'
                                    f'<span style="color:#64748b;font-size:11px;">{item["reason"]}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("No deferrable tasks identified.")

                # ═══════════════════════════════════════════
                # 📅 PLANNING
                # ═══════════════════════════════════════════
                st.markdown("""
                <div style="border-left:4px solid #f59e0b;padding:6px 0 6px 14px;margin:28px 0 14px 0;">
                    <span style="color:#fcd34d;font-size:13px;font-weight:800;letter-spacing:2px;">📅 PLANNING</span>
                </div>""", unsafe_allow_html=True)

                # Fix 3: Overload Gauge removed — score already shown in Diagnostics card
                # Domain Breakdown — full width (Fix 1: use_container_width)
                if tasks:
                    st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:0 0 4px 0;">DOMAIN BREAKDOWN</p>', unsafe_allow_html=True)
                    st.plotly_chart(make_domain_chart(tasks), use_container_width=True)

                # Day Plan
                if day_plan:
                    energy_lbl   = scores["normed"]["energy_level"]
                    block_cap    = {"Low": "45 min", "Medium": "60 min", "High": "90 min"}.get(energy_lbl, "60 min")
                    work_rows    = [r for r in day_plan if r["domain"] not in ("Break", "Rest", "Deferred")]
                    total_sched  = sum(
                        int(r["duration"].replace(" min", ""))
                        for r in work_rows if r.get("duration", "—") != "—"
                    )
                    total_avail  = int(features.get("free_hours", 0) * 60)

                    st.markdown(
                        f'<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;'
                        f'margin:14px 0 4px 0;">🗓️ SUGGESTED DAY STRUCTURE</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<p style="color:#475569;font-size:11px;margin:0 0 8px 0;">'
                        f'Energy: <span style="color:#e2e8f0;font-weight:700;">{energy_lbl}</span>'
                        f' &nbsp;·&nbsp; Block cap: <span style="color:#e2e8f0;font-weight:700;">{block_cap}</span>'
                        f' &nbsp;·&nbsp; Scheduled: <span style="color:#22c55e;font-weight:700;">{total_sched} min</span>'
                        f' of <span style="color:#94a3b8;">{total_avail} min</span> available</p>',
                        unsafe_allow_html=True,
                    )

                    for row in day_plan:
                        dom     = row.get("domain", "")
                        color   = row.get("color", "#334155")
                        time_s  = row.get("time", "")
                        act     = row.get("activity", "")
                        dur     = row.get("duration", "—")

                        if dom == "Break":
                            st.markdown(
                                f'<div style="background:#1a2332;border-left:3px solid #334155;'
                                f'border-radius:0 6px 6px 0;padding:6px 12px;margin-bottom:3px;'
                                f'display:flex;justify-content:space-between;">'
                                f'<span style="color:#475569;font-size:11px;font-style:italic;">'
                                f'{time_s} &nbsp;·&nbsp; {act}</span>'
                                f'<span style="color:#334155;font-size:11px;">{dur}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        elif dom == "Deferred":
                            st.markdown(
                                f'<div style="background:#1e293b;border:1px dashed #475569;'
                                f'border-radius:6px;padding:7px 12px;margin-top:4px;">'
                                f'<span style="color:#64748b;font-size:10px;font-weight:700;'
                                f'letter-spacing:1px;">⏭ DEFERRED — NEXT SESSION</span><br/>'
                                f'<span style="color:#94a3b8;font-size:12px;">{act}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        elif dom == "Rest":
                            st.markdown(
                                f'<div style="background:#1e293b;border-top:1px solid #334155;'
                                f'padding:6px 12px;margin-top:4px;border-radius:6px;">'
                                f'<span style="color:#475569;font-size:11px;">{time_s} &nbsp;·&nbsp; {act}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            is_urgent = "⚡" in act
                            time_color = "#fbbf24" if is_urgent else "#64748b"
                            st.markdown(
                                f'<div style="background:#1e293b;border-left:4px solid {color};'
                                f'border-radius:0 8px 8px 0;padding:8px 14px;margin-bottom:3px;">'
                                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                                f'<span style="color:{time_color};font-size:11px;font-weight:600;">{time_s}</span>'
                                f'<span style="color:#475569;font-size:10px;font-weight:700;'
                                f'background:#0f172a;padding:2px 8px;border-radius:4px;">{dom.upper()}</span>'
                                f'</div>'
                                f'<span style="color:#e2e8f0;font-size:13px;font-weight:600;">{act}</span>'
                                f'<span style="color:#64748b;font-size:11px;"> &nbsp;·&nbsp; {dur}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                # ── CSV EXPORT ──
                import io
                export_rows = {
                    "Overload Score":    [f"{scores['overload']:.0f}"],
                    "Overload Label":    [scores["overload_label"]],
                    "AFI Score":         [f"{scores['afi']:.0f}"],
                    "AFI Label":         [scores["afi_label"]],
                    "Capacity Fit (%)":  [f"{scores['capacity']:.0f}"],
                    "Capacity Label":    [scores["capacity_label"]],
                    "Action":            [action],
                    "Free Hours":        [features.get("free_hours", "")],
                    "Estimated Hours":   [features.get("estimated_hours", "")],
                    "Energy Level":      [features.get("energy_level", "")],
                    "Task Count":        [features.get("task_count", "")],
                    "Urgency Signals":   [features.get("urgency_signals", "")],
                }
                export_df  = pd.DataFrame(export_rows)
                csv_buffer = io.StringIO()
                export_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="⬇️ Download Analysis (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="digital_overload_analysis.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
                st.info("Please check your GROQ_API_KEY in the .env file and try again.")

    elif analyze:
        st.warning("Please describe your situation before clicking Analyze.")

    # ── SESSION HISTORY ──
    history = get_history()
    if history:
        st.markdown("---")
        st.markdown("""
        <div style="border-left:4px solid #475569;padding:4px 0 4px 14px;margin:8px 0 14px 0;">
            <span style="color:#94a3b8;font-size:11px;font-weight:800;letter-spacing:2px;">📜 SESSION HISTORY</span>
        </div>""", unsafe_allow_html=True)

        # Overload trend sparkline
        if len(history) > 1:
            overload_trend = [h["overload"] for h in reversed(history)]
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                y=overload_trend,
                mode="lines+markers",
                line=dict(color="#3b82f6", width=2),
                marker=dict(color="#60a5fa", size=6),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.08)",
            ))
            fig_trend.update_layout(
                height=100,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False, range=[0, 100]),
                showlegend=False,
            )
            st.markdown('<p style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;margin:0 0 4px 0;">OVERLOAD TREND (oldest → latest)</p>', unsafe_allow_html=True)
            st.plotly_chart(fig_trend, use_container_width=True)

        for i, h in enumerate(history):
            with st.expander(
                f"Analysis {i+1} · {h['timestamp']} · "
                f"O:{h['overload']:.0f} · AFI:{h['afi']:.0f} · C:{h['capacity']:.0f}%"
            ):
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Overload", f"{h['overload']:.0f}/100", h["overload_label"])
                cc2.metric("AFI",      f"{h['afi']:.0f}/100",      h["afi_label"])
                cc3.metric("Capacity", f"{h['capacity']:.0f}%",    h["capacity_label"])
                st.caption(f"Input: {h['input_preview']}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer-text">
        Built with Python &nbsp;•&nbsp; Groq API &nbsp;•&nbsp; Streamlit &nbsp;•&nbsp; Pytest<br>
        Digital Overload AI &copy; 2026
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()