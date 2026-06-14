# 🧠 Digital Overload AI
### AI-Powered Student Workload Intelligence Platform

> **Understand your workload pressure before your day falls apart — not after.**

[![Run Tests](https://github.com/Jagadeesh0463/digital-overload-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/Jagadeesh0463/digital-overload-ai/actions/workflows/tests.yml)
![Tests](https://img.shields.io/badge/tests-32%20passed-22c55e?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-3b82f6?style=flat-square)
![Streamlit](https://img.shields.io/badge/streamlit-1.58-ff4b4b?style=flat-square)
![Groq](https://img.shields.io/badge/groq-llama--3.3--70b-f97316?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)

🌐 **Live App:** https://digital-overload-ai.streamlit.app

📂 **GitHub:** https://github.com/Jagadeesh0463/digital-overload-ai

---

## Overview

Digital Overload AI is an AI-assisted workload analysis platform designed to help students
understand task pressure, fragmented attention, and planning risk before committing to their day.

The platform converts natural-language workload descriptions into measurable diagnostics
and provides structured prioritization recommendations — powered by Groq's Llama 3.3 70B model.

**Problem it solves:** Students often feel constantly busy but fail to make meaningful progress
due to excessive context switching, unrealistic scheduling, and fragmented digital attention.
This platform makes those hidden patterns visible and actionable.

**Target users:** College students juggling assignments, club commitments, messages, and
personal tasks with limited available hours.

---

## Unique Contributions

This project introduces three original metrics not commonly found in productivity tools:

- **Attention Fragmentation Index (AFI)** — measures cognitive scatter caused by switching
  between unrelated task domains (Academic, Social, Admin, Personal)
- **Capacity Fit** — checks whether planned work realistically fits available time and energy
- **Overload Prediction Engine (OPE)** — pre-acceptance check: would saying yes to one more
  task push you into overload?
- **16-Row Recommendation Rule Matrix** — deterministic mapping of every score combination
  to a Focus / Defer / Split / Reduce strategy
- **AI-powered feature extraction** — Groq LLM extracts 8 structured signals from free-text input
- **Multi-score workload assessment** — three independent scores give a complete picture

---

## Key Features

- **3-Score Diagnostic** — Overload Score + AFI + Capacity Fit computed independently
- **Detected Overload Signals** — pattern identification across task volume, messages, energy, capacity
- **AI Analysis Summary** — natural-language explanation of what's driving the scores
- **Score Drivers** — per-contributor breakdown showing exactly what pushed each score
- **Workload vs Capacity** — estimated hours vs available hours with gap analysis
- **Top Priorities + Safe to Defer** — AI-sorted task recommendations
- **Time-Block Day Planner** — domain-grouped schedule with energy-adjusted block lengths
- **OPE Alert** — real-time overload prediction before accepting new tasks
- **Session History** — last 5 analyses tracked within session
- **3 Demo Profiles** — one-click student scenarios

---

## Tech Stack

| Layer      | Technology                   |
|------------|------------------------------|
| Frontend   | Streamlit 1.58               |
| Backend    | Python 3.11+                 |
| AI / NLP   | Groq API — Llama 3.3 70B     |
| Charts     | Plotly                       |
| Testing    | pytest — 32 tests            |
| Deployment | Streamlit Cloud              |

---

## Architecture

```
User Input (natural language)
        ↓
Groq Llama 3.3 70B
        ↓
Signal Extraction (8 features)
        ↓
┌───────────────────────────────┐
│         Scoring Engine        │
│  Overload │ AFI │ Capacity    │
└───────────────────────────────┘
        ↓
16-Row Recommendation Matrix
        ↓
Action Plan + Day Planner
        ↓
Dashboard (Streamlit)
```

---

## Project Structure

```
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
```

---

## Screenshots

| Input Page | Analysis Results |
|------------|-----------------|
| ![Input](docs/screenshots/input.png) | ![Results](docs/screenshots/results.png) |

| Action Plan | Day Planner |
|-------------|-------------|
| ![Plan](docs/screenshots/action_plan.png) | ![Day](docs/screenshots/day_planner.png) |

> To add screenshots: run `streamlit run app.py`, take screenshots of each section, and save them to `docs/screenshots/`.

---

## How to Run Locally

**Step 1 — Clone the repo**
```bash
git clone https://github.com/Jagadeesh0463/digital-overload-ai.git
cd digital-overload-ai
```

**Step 2 — Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Add your Groq API key**
```bash
cp .env.example .env
# Open .env and paste your key:
# GROQ_API_KEY=your_groq_key_here
```

**Step 5 — Run the app**
```bash
streamlit run app.py
```

**Step 6 — Run all tests**
```bash
pytest tests/ -v
```

---

## Scoring System

**Overload Score (0–100)**
Measures total workload pressure relative to available time and energy.

```
Overload = [ (task_count × 0.35) + (urgency × 0.35) + ((1 - energy) × 0.30) ] × 100

0–40   = Low
41–65  = Moderate
66–85  = High
86–100 = Critical
```

**Attention Fragmentation Index — AFI (0–100)**
Original metric measuring cognitive scatter across unrelated task domains.

```
AFI = [ (unique_domains × 0.50) + (context_switches × 0.30) + (messages × 0.20) ] × 100

0–35   = Low
36–60  = Moderate
61–80  = High
81–100 = Severe
```

**Capacity Fit (0–100%)**
Checks whether planned work fits available time and energy.

```
Capacity Fit = (free_hours / estimated_hours) × energy_multiplier × 100

≥ 100% = Good Fit
70–99% = Tight
40–69% = Poor Fit
< 40%  = Overcommitted
```

---

## Test Results

```
pytest tests/ -v

test_scoring.py      — 13 passed
test_recommender.py  — 19 passed
─────────────────────────────────
Total                — 32 passed in 0.02s
```

---

## Limitations

- Results depend on honest self-reported input
- NOT a medical, psychological, or mental health diagnostic system
- Scores are estimates from weighted formulas — not exact cognitive measurements
- Recommendation engine uses a deterministic rule matrix, not personalised ML
- Session history resets when the browser tab is closed
- Requires internet connection for Groq API calls

---

## Future Enhancements

- Gmail and Calendar auto-import of daily commitments
- Weekly AFI trend tracking and overload reports
- Mobile app with push notification support
- ML-based recommendation engine replacing the rule matrix
- Persistent history with CSV export

---

## Disclaimer

This is a decision-support tool for workload planning only.
It is NOT a medical, psychological, or mental health diagnostic system.

---

## Author

**S Jagadeesh · 2026**
