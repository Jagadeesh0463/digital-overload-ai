# 🧠 Digital Overload AI
### Intelligent Attention & Task Overload Analyzer

> **Diagnose overload BEFORE you plan — not after deadlines are missed.**

---

## Project Title & Overview

**Title:** Digital Overload AI – Intelligent Attention & Task Overload Analyzer

**Description:**
An AI-powered system that helps college students understand and reduce digital overload
by analyzing their daily task descriptions, notifications, messages, and to-do inputs.
The system identifies patterns of overload, fragmented attention, and unrealistic task
planning, and provides structured insights to improve focus and prioritization.

The project addresses a growing issue where students feel constantly busy but struggle
to make meaningful progress due to excessive digital inputs.

**Target Users:**
College students and early-stage learners who feel overwhelmed by notifications,
assignments, messages, and multiple commitments, leading to poor focus and stress.

**Key Value Proposition:**
Helps users recognize hidden overload patterns and restructure tasks realistically,
improving focus, clarity, and productivity without adding more tools or reminders.

**Scope:**
MVP focuses on analyzing text-based task lists, daily plans, and message summaries
to detect overload signals and suggest structured prioritization.
Future scope includes habit trend analysis and weekly overload reports.

**Assumptions:**
Users provide honest descriptions of their daily tasks, commitments, and digital
interactions in text form.

---

## Example Use Case

A student inputs their daily plan:

- Classes
- Assignments
- Club work
- Messages to respond to
- Personal commitments

The system:

- Identifies excessive context switching
- Flags unrealistic scheduling
- Suggests a more balanced task structure
- Highlights what truly needs attention today

---

## Key Features

- **3-Score Diagnostic System** — Overload Score + AFI + Capacity Fit
- **Attention Fragmentation Index (AFI)** — original metric measuring cognitive domain switching
- **Overload Prediction Engine (OPE)** — pre-acceptance check before saying yes to new tasks
- **16-Row Recommendation Rule Matrix** — maps every score combination to Focus / Defer / Split / Reduce
- **Time-Block Day Planner** — groups tasks by domain into structured hour blocks
- **3 Demo Profiles** — Try Priya, Ravi, Divya with one click
- **Session History** — tracks last 5 analyses in the same session

---

## Tech Stack

| Layer        | Technology              |
|--------------|-------------------------|
| Frontend     | Streamlit               |
| Backend      | Python 3.11+            |
| AI / NLP     | Groq API — Llama 3.3 70B|
| Charts       | Plotly                  |
| Testing      | pytest (32 tests)       |
| Deployment   | Streamlit Cloud         |

---

## Project Structure

    digital-overload-ai/
    ├── app.py                   Main Streamlit dashboard
    ├── groq_client.py           Groq AI — extracts 8 features from plain text
    ├── scoring_engine.py        Overload, AFI, Capacity Fit formulas
    ├── recommender.py           16-row rule matrix + action plan generator
    ├── day_planner.py           Domain-grouped time-block schedule builder
    ├── session_store.py         Session history — last 5 analyses
    ├── utils.py                 Constants, thresholds, colour maps
    ├── tests/
    │   ├── test_scoring.py      13 unit tests for scoring formulas
    │   └── test_recommender.py  19 unit tests for rule matrix
    ├── docs/
    │   ├── PROJECT_OVERVIEW.md  Deep explanation of all concepts
    │   ├── SAMPLE_INPUTS.md     3 student personas with expected outputs
    │   └── EXTENSION_IDEAS.md   Future upgrade paths with code
    ├── requirements.txt
    └── .env.example

---

## How to Run Locally

Step 1 — Clone the repo

    git clone https://github.com/Jagadeesh0463/digital-overload-ai.git

Step 2 — Create virtual environment

    python3 -m venv venv
    source venv/bin/activate

Step 3 — Install dependencies

    pip install -r requirements.txt

Step 4 — Add your Groq API key

    cp .env.example .env

Open .env and paste your key:

    GROQ_API_KEY=your_groq_key_here

Step 5 — Run the app

    streamlit run app.py

Step 6 — Run all tests

    pytest tests/ -v

---

## Scoring System

**Overload Score (0–100)**
Measures total workload pressure relative to available time and energy.

    Overload = [ (task_count x 0.35) + (urgency x 0.35) + ((1 - energy) x 0.30) ] x 100

    0-40  = Low
    41-65 = Moderate
    66-85 = High
    86-100 = Critical

**Attention Fragmentation Index — AFI (0–100)**
Original metric measuring cognitive scatter across unrelated task domains.

    AFI = [ (unique_domains x 0.50) + (context_switches x 0.30) + (messages x 0.20) ] x 100

    0-35  = Low
    36-60 = Moderate
    61-80 = High
    81-100 = Severe

**Capacity Fit (0–100%)**
Checks whether planned work fits available time and energy.

    Capacity Fit = (free_hours / estimated_hours) x energy_multiplier x 100

    >= 100% = Good Fit
    70-99%  = Tight
    40-69%  = Poor Fit
    < 40%   = Overcommitted

---

## Test Results

    pytest tests/ -v

    test_scoring.py      — 13 passed
    test_recommender.py  — 19 passed
    Total                — 32 passed in 0.02s

---

## Limitations

- Results depend on honest self-reported input
- NOT a medical, psychological, or mental health diagnostic system
- Scores are estimates from weighted formulas — not exact cognitive measurements
- Recommendation engine uses a rule matrix, not personalised machine learning
- Session history resets when browser tab is closed
- Requires internet connection for Groq API

---

## Future Enhancements

- Gmail and Calendar auto-import of commitments
- Weekly AFI trend reports
- Mobile app with push notifications
- ML-based recommendation engine replacing rule matrix
- Persistent history with CSV export

---

## Disclaimer

This is a decision-support tool for workload planning only.
It is NOT a medical, psychological, or mental health diagnostic system.

---

## Author

**S Jagadeesh · Hyderabad · 2026**
