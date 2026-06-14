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


def make_domain_chart(tasks: list) -> go.Figure:
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
def get_priorities(tasks: list, action: str) -> tuple:
    from utils import DOMAIN_PRIORITY
    sorted_tasks = sorted(
        tasks,
        key=lambda t: DOMAIN_PRIORITY.index(t.get("domain", "Personal"))
        if t.get("domain", "Personal") in DOMAIN_PRIORITY else 4
    )
    top   = [t["name"] for t in sorted_tasks if t.get("domain") in ["Academic", "Admin"]][:3]
    defer = [t["name"] for t in sorted_tasks if t.get("domain") in ["Social", "Personal"]
             and action in ["REDUCE", "DEFER"]][:3]
    # Fill top if less than 3
    for t in sorted_tasks:
        if t["name"] not in top and len(top) < 3:
            top.append(t["name"])
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
        <div style="display:flex; gap:24px; flex-wrap:wrap;">
            <span style="color:#22c55e; font-size:0.85rem; font-weight:600;">✓ Overload Detection</span>
            <span style="color:#22c55e; font-size:0.85rem; font-weight:600;">✓ Attention Fragmentation Analysis</span>
            <span style="color:#22c55e; font-size:0.85rem; font-weight:600;">✓ Smart Prioritization</span>
            <span style="color:#22c55e; font-size:0.85rem; font-weight:600;">✓ AI-Powered Day Planning</span>
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

                # ── SCORES ──
                st.markdown("---")
                st.markdown("### 📊 Your 3-Score Diagnostic")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("🔥 Overload Score",
                              f"{scores['overload']:.0f} / 100",
                              colored_label(scores["overload_label"], "overload"))
                with c2:
                    st.metric("🧩 AFI Score",
                              f"{scores['afi']:.0f} / 100",
                              colored_label(scores["afi_label"], "afi"))
                with c3:
                    st.metric("⏱️ Capacity Fit",
                              f"{scores['capacity']:.0f}%",
                              colored_label(scores["capacity_label"], "capacity"))

                # ── SCORE DRIVERS ──
                normed = scores["normed"]
                task_contrib    = round(normed["task_count_norm"]       * 0.35 * 100)
                urgency_contrib = round(normed["urgency_signals_norm"]  * 0.35 * 100)
                energy_contrib  = round((1 - normed["energy_norm"])     * 0.30 * 100)
                domain_contrib  = round(normed["unique_domains_norm"]   * 0.50 * 100)
                switch_contrib  = round(normed["context_switches_norm"] * 0.30 * 100)
                msg_contrib     = round(normed["pending_messages_norm"] * 0.20 * 100)

                st.markdown("### 📊 Score Drivers")
                sd1, sd2, sd3 = st.columns(3)
                with sd1:
                    st.markdown(f"""
                    <div style="background:#1e293b;border-radius:10px;padding:14px 16px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:12px;font-weight:600;margin:0 0 8px 0;">🔥 OVERLOAD CONTRIBUTORS</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#ef4444;font-weight:700;">+{task_contrib}</span> &nbsp;Task Volume</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#f97316;font-weight:700;">+{urgency_contrib}</span> &nbsp;Deadline Pressure</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#eab308;font-weight:700;">+{energy_contrib}</span> &nbsp;Low Energy Penalty</p>
                    </div>
                    """, unsafe_allow_html=True)
                with sd2:
                    st.markdown(f"""
                    <div style="background:#1e293b;border-radius:10px;padding:14px 16px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:12px;font-weight:600;margin:0 0 8px 0;">🧩 AFI CONTRIBUTORS</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#ef4444;font-weight:700;">+{domain_contrib}</span> &nbsp;Domain Spread</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#f97316;font-weight:700;">+{switch_contrib}</span> &nbsp;Context Switches</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;"><span style="color:#eab308;font-weight:700;">+{msg_contrib}</span> &nbsp;Communication Load</p>
                    </div>
                    """, unsafe_allow_html=True)
                with sd3:
                    free = features.get("free_hours", 0)
                    est  = features.get("estimated_hours", 0)
                    gap  = round(est - free, 1)
                    st.markdown(f"""
                    <div style="background:#1e293b;border-radius:10px;padding:14px 16px;border:1px solid #334155;">
                        <p style="color:#94a3b8;font-size:12px;font-weight:600;margin:0 0 8px 0;">⏱️ CAPACITY FIT</p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;">Available: <span style="color:#22c55e;font-weight:700;">{free}h</span></p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;">Estimated: <span style="color:#ef4444;font-weight:700;">{est}h</span></p>
                        <p style="color:#f8fafc;margin:4px 0;font-size:14px;">Gap: <span style="color:#f97316;font-weight:700;">{"+" if gap > 0 else ""}{gap}h</span></p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── DETECTED OVERLOAD SIGNALS ──
                signals = get_overload_signals(features, scores)
                if signals:
                    st.markdown("---")
                    st.markdown("### 🔍 Detected Overload Signals")
                    for emoji, title, detail in signals:
                        st.markdown(f"""
                        <div style="background:#1e293b;border-left:4px solid {'#ef4444' if emoji=='🔴' else '#f97316' if emoji=='🟠' else '#eab308'};
                             border-radius:0 8px 8px 0;padding:10px 16px;margin-bottom:8px;">
                            <span style="color:#f8fafc;font-weight:700;font-size:14px;">{emoji} {title}</span>
                            <span style="color:#94a3b8;font-size:13px;"> — {detail}</span>
                        </div>
                        """, unsafe_allow_html=True)

                # ── AI ANALYSIS SUMMARY ──
                st.markdown("---")
                st.markdown("### 🧠 AI Analysis Summary")
                summary = generate_ai_summary(features, scores)
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;
                     border-left:4px solid #3b82f6;border-radius:0 12px 12px 0;padding:20px 24px;">
                    <p style="color:#e2e8f0;font-size:15px;line-height:1.8;margin:0;">{summary}</p>
                </div>
                """, unsafe_allow_html=True)

                # ── WORKLOAD VS CAPACITY ──
                st.markdown("---")
                st.markdown("### ⏱️ Workload vs Capacity")
                free_h = features.get("free_hours", 0)
                est_h  = features.get("estimated_hours", 0)
                gap_h  = round(est_h - free_h, 1)
                cap_status = scores["capacity_label"]
                cap_color  = {"Good Fit": "#22c55e", "Tight": "#eab308",
                              "Poor Fit": "#f97316", "Overcommitted": "#ef4444"}.get(cap_status, "#64748b")
                wc1, wc2, wc3, wc4 = st.columns(4)
                wc1.metric("Estimated Workload", f"{est_h}h")
                wc2.metric("Available Time", f"{free_h}h")
                wc3.metric("Time Gap", f"{gap_h:+.1f}h")
                wc4.metric("Status", cap_status)

                # ── AFI EXPLANATION ──
                st.markdown("---")
                afi_val = scores["afi"]
                afi_label = scores["afi_label"]
                afi_color = {"Severe": "#ef4444", "High": "#f97316", "Moderate": "#eab308", "Low": "#22c55e"}.get(afi_label, "#64748b")
                st.markdown(f"""
                <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 20px;">
                    <p style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:1px;margin:0 0 6px 0;">🧩 ATTENTION FRAGMENTATION INDEX (AFI)</p>
                    <p style="color:#f8fafc;font-size:15px;font-weight:700;margin:0 0 4px 0;">
                        Score: <span style="color:{afi_color};">{afi_val:.0f}/100 — {afi_label}</span>
                    </p>
                    <p style="color:#94a3b8;font-size:13px;margin:0;">
                        AFI measures cognitive scatter caused by switching between unrelated task domains.
                        High AFI means your brain is being pulled in too many directions simultaneously —
                        reducing domain switches is the fastest way to regain focus.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # ── CAPACITY FIT HIGHLIGHT ──
                cap_val   = scores["capacity"]
                cap_label = scores["capacity_label"]
                cap_color = {"Good Fit": "#22c55e", "Tight": "#eab308", "Poor Fit": "#f97316", "Overcommitted": "#ef4444"}.get(cap_label, "#64748b")
                st.markdown(f"""
                <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 20px;margin-top:10px;">
                    <p style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:1px;margin:0 0 6px 0;">⏱️ CAPACITY FIT</p>
                    <p style="color:#f8fafc;font-size:15px;font-weight:700;margin:0 0 4px 0;">
                        Score: <span style="color:{cap_color};">{cap_val:.0f}% — {cap_label}</span>
                    </p>
                    <p style="color:#94a3b8;font-size:13px;margin:0;">
                        Capacity Fit checks whether your planned workload fits your available time and energy level.
                        Below 70% means you need to defer or drop tasks before starting — not after.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # ── OPE — OVERLOAD PREDICTION ENGINE ──
                st.markdown("---")
                ope = (scores["overload"] > 65 and scores["capacity"] < 70) or scores["afi"] > 80
                ope_status = "AT CAPACITY" if ope else "MANAGEABLE"
                ope_color  = "#ef4444" if ope else "#22c55e"
                st.markdown(f"""
                <div style="background:#1e293b;border:1px solid {ope_color};border-radius:12px;padding:16px 20px;">
                    <p style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:1px;margin:0 0 6px 0;">🔮 OVERLOAD PREDICTION ENGINE (OPE)</p>
                    <p style="color:{ope_color};font-size:16px;font-weight:800;margin:0 0 4px 0;">
                        Status: {ope_status}
                    </p>
                    <p style="color:#94a3b8;font-size:13px;margin:0;">
                        {"⚠️ System at capacity. Accepting any new task today will push you into critical overload. Do NOT say yes to new commitments." if ope
                        else "✅ Current load is manageable. You have some buffer — but monitor scores before accepting new tasks."}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # ── CHARTS ──
                st.markdown("---")
                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown("#### Overload Gauge")
                    st.plotly_chart(
                        make_gauge(scores["overload"], scores["overload_label"], "overload"),
                        width='stretch',
                    )
                with col_r:
                    st.markdown("#### Domain Breakdown")
                    if tasks:
                        st.plotly_chart(
                            make_domain_chart(tasks),
                            width='stretch',
                        )

                # ── ACTION PLAN ──
                st.markdown("---")
                action_color = ACTION_COLORS.get(action, "#64748b")
                st.markdown(
                    f'### 📋 Action Plan &nbsp; <span style="background:{action_color};color:white;'
                    f'padding:4px 14px;border-radius:6px;font-size:14px;font-weight:700;">'
                    f'Primary Strategy: {action}</span>',
                    unsafe_allow_html=True,
                )
                for item in plan:
                    if item["action"] == "ALERT":
                        st.warning(f"⚠️ {item['instruction']}")
                    else:
                        st.markdown(
                            f'<div style="background:#1e293b;border-radius:8px;padding:10px 16px;'
                            f'margin-bottom:6px;border:1px solid #334155;">'
                            f'<span style="color:#94a3b8;font-size:12px;font-weight:700;">{item["priority"]}</span>'
                            f'&nbsp;&nbsp;<span style="color:#e2e8f0;font-size:14px;">{item["instruction"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                # ── TOP PRIORITIES + SAFE TO DEFER ──
                top_p, safe_d = get_priorities(tasks, action)
                pr_col, df_col = st.columns(2)
                with pr_col:
                    st.markdown("#### 🎯 Today's Top Priorities")
                    if top_p:
                        for i, t in enumerate(top_p, 1):
                            st.markdown(
                                f'<div style="background:#1e293b;border-left:4px solid #22c55e;'
                                f'border-radius:0 8px 8px 0;padding:8px 14px;margin-bottom:6px;">'
                                f'<span style="color:#22c55e;font-weight:700;">{i}.</span> '
                                f'<span style="color:#e2e8f0;">{t}</span></div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No tasks extracted.")
                with df_col:
                    st.markdown("#### 🕒 Safe to Defer")
                    if safe_d:
                        for t in safe_d:
                            st.markdown(
                                f'<div style="background:#1e293b;border-left:4px solid #64748b;'
                                f'border-radius:0 8px 8px 0;padding:8px 14px;margin-bottom:6px;">'
                                f'<span style="color:#94a3b8;">→</span> '
                                f'<span style="color:#94a3b8;">{t}</span></div>',
                                unsafe_allow_html=True,
                            )
                    elif action in ["REDUCE", "DEFER"]:
                        st.caption("No deferrable tasks identified — all tasks appear urgent.")
                    else:
                        st.caption("Current load is manageable — no deferral needed.")

                # ── DAY PLAN ──
                if day_plan:
                    st.markdown("---")
                    st.markdown("### 🗓️ Suggested Day Structure")
                    df = pd.DataFrame(day_plan)[["time", "domain", "activity", "duration"]]
                    df.columns = ["Time Slot", "Domain", "Activity", "Duration"]
                    st.dataframe(df, width='stretch', hide_index=True)

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
                st.info("Please check your GROQ_API_KEY in the .env file and try again.")

    elif analyze:
        st.warning("Please describe your situation before clicking Analyze.")

    # ── SESSION HISTORY ──
    history = get_history()
    if history:
        st.markdown("---")
        st.markdown("### 📜 Session History (Last 5)")
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