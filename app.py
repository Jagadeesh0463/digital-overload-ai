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

/* ── TITLE ── */
h1 { 
    color: #7dd3fc !important; 
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px;
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
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 14px !important;
    transition: all 0.2s;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #1e40af, #2563eb) !important;
    transform: translateY(-1px);
}

/* ── TEXT AREA ── */
[data-testid="stTextArea"] textarea {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
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
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──
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


# ── MAIN ──
def main():
    init_history()

    # Header
    st.title("🧠 Digital Overload AI")
    st.caption("Intelligent Attention & Task Overload Analyzer · Diagnose overload BEFORE you plan · Jagadeesh · 2026")
    st.caption("⚠️ Disclaimer: This is a workload planning tool only. NOT a medical or mental health diagnostic system.")

    st.markdown("---")

    # Input
    st.markdown("### Describe your tasks, deadlines, messages, and energy level")
    st.caption("Type naturally — messy is fine. Include: tasks, deadlines, messages pending, energy level, free hours today.")

    # ── DEMO PROFILES ──
    st.markdown("**Try a demo profile:**")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("👩 Try Priya"):
            st.session_state["demo_text"] = """4 assignments due this week — OS on Wednesday, DBMS on Thursday, Web Dev and ML both on Friday. 18 WhatsApp messages from classmates pending. Club meeting tomorrow at 5 PM for 2 hours. Feeling low energy today. Only 3 free hours tonight after 9 PM."""

    with col_b:
        if st.button("👨 Try Ravi"):
            st.session_state["demo_text"] = """5 subject exams in the next 4 days — Computer Networks today, Operating Systems tomorrow, DBMS the day after, then Web Dev and Cloud Computing on day 4. Zero pending messages — switched off notifications completely. Energy is medium. I have about 8 free hours today. No club commitments this week."""

    with col_c:
        if st.button("👩 Try Divya"):
            st.session_state["demo_text"] = """I am in 3 college clubs — Robotics, Cultural Committee, and NSS. All three have events this week. I also have 2 assignments due Friday and a lab record submission on Thursday. About 50 WhatsApp messages unread across 6 groups. Feeling low energy — been staying up late all week. Only 2 free hours today."""

    demo_value = st.session_state.get("demo_text", "")

    input_text = st.text_area(
        label="input",
        placeholder="Example: 3 assignments due this week, 18 WhatsApp messages pending, club meeting tomorrow, low energy, only 3 free hours tonight...",
        height=150,
        label_visibility="collapsed",
        value=demo_value,
    )

    analyze = st.button("🔍 Analyze My Workload", type="primary", width='stretch')

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
                              scores["overload_label"])
                with c2:
                    st.metric("🧩 AFI Score",
                              f"{scores['afi']:.0f} / 100",
                              scores["afi_label"])
                with c3:
                    st.metric("⏱️ Capacity Fit",
                              f"{scores['capacity']:.0f}%",
                              scores["capacity_label"])

                # ── OPE ALERT ──
                ope = (scores["overload"] > 65 and scores["capacity"] < 70) \
                      or scores["afi"] > 80
                if ope:
                    st.error("⚠️ OPE Alert: System at capacity. Do NOT accept new tasks today.")
                else:
                    st.success("✅ OPE: Capacity is manageable. Monitor scores if you accept new tasks.")

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
                st.markdown(f"### 📋 Action Plan — Primary: **{action}**")

                for item in plan:
                    c_p, c_a, c_i = st.columns([0.5, 1, 6])
                    with c_p:
                        st.markdown(f"**{item['priority']}**")
                    with c_a:
                        color = ACTION_COLORS.get(item["action"], "#64748b")
                        st.markdown(
                            f'<span style="background:{color};color:white;'
                            f'padding:2px 8px;border-radius:4px;font-size:11px;'
                            f'font-weight:700">{item["action"]}</span>',
                            unsafe_allow_html=True,
                        )
                    with c_i:
                        st.write(item["instruction"])

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
    st.caption("Digital Overload AI · Not a medical tool · Jagadeesh · Hyderabad · 2026")


if __name__ == "__main__":
    main()