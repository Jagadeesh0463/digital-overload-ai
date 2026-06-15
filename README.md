# 🧠 Digital Overload AI
### AI-Powered Student Workload Analyzer

> Understand your workload pressure before your day falls apart — not after.

[![Run Tests](https://github.com/Jagadeesh0463/digital-overload-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/Jagadeesh0463/digital-overload-ai/actions/workflows/tests.yml)
![Tests](https://img.shields.io/badge/tests-37%20passed-22c55e?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-3b82f6?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)

🌐 **Live App:** https://digital-overload-ai.streamlit.app

---

## What It Does

Paste a plain-text description of your day. The app uses **Groq's Llama 3.3 70B** to extract 8 workload signals, computes 3 diagnostic scores, and returns a structured action plan — no forms, no dropdowns.

```
"4 assignments due this week. 18 WhatsApp messages pending.
Club meeting tomorrow. Low energy. Only 3 free hours tonight."
```

→ Overload Score · AFI · Capacity Fit → **REDUCE / DEFER / SPLIT / FOCUS**

---

## Screenshots

<p align="center">
  <img src="docs/screenshots/01-workload-dashboard.png" alt="Full Dashboard" width="800"/>
  <br/>
  <sub>Full workload dashboard — input, scores, signals, recommendations, and day plan</sub>
</p>

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/02-diagnostics.png" width="100%"/>
      <br/>
      <sub><b>3-Score Diagnostic</b> — Overload · AFI · Capacity Fit</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/03-analysis.png" width="100%"/>
      <br/>
      <sub><b>Signal Detection & AI Summary</b></sub>
    </td>
  </tr>
</table>

<p align="center">
  <img src="docs/screenshots/04-planner.png" alt="Day Planner" width="800"/>
  <br/>
  <sub>AI Day Planner — urgency-sorted time blocks with smart breaks</sub>
</p>

---

## Features

- **3 diagnostic scores** — Overload Score, Attention Fragmentation Index (AFI), Capacity Fit
- **Explainable recommendations** — 16-row deterministic rule matrix → FOCUS / DEFER / SPLIT / REDUCE
- **Overload Prediction Engine (OPE)** — pre-acceptance capacity check across all 3 scores
- **AI Day Planner** — domain-grouped, energy-adjusted time blocks with urgency sorting
- **Session history** — last 5 analyses with trend tracking
- **CSV export** — download full analysis results
- **37 automated tests** — scoring, recommender, and planner coverage

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| AI / NLP | Groq API (Llama 3.3 70B) |
| Charts | Plotly |
| Testing | pytest |
| CI | GitHub Actions |
| Deployment | Streamlit Cloud |

---

## Run Locally

```bash
git clone https://github.com/Jagadeesh0463/digital-overload-ai.git
cd digital-overload-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
streamlit run app.py
```

> First visit on Streamlit Cloud may take 30–60 seconds to wake up.

---

## Tests

```bash
pytest tests/ -v
# 37 passed in 0.03s
```

---

## Project Structure

```
digital-overload-ai/
├── app.py                 Streamlit dashboard
├── groq_client.py         Groq API — extracts 8 features from plain text
├── scoring_engine.py      Overload, AFI, Capacity Fit formulas
├── recommender.py         16-row rule matrix + action plan
├── day_planner.py         Time-block schedule builder
├── session_store.py       Session history (last 5 analyses)
├── utils.py               Constants, thresholds, colour maps
├── tests/                 37 unit tests
└── docs/                  Architecture, design, and extension docs
```

---

## Docs

- [Project Overview](docs/PROJECT_OVERVIEW.md) — scoring formulas, AFI, OPE explained
- [System Design](docs/SYSTEM_DESIGN.md) — architecture and data flow
- [Sample Inputs](docs/SAMPLE_INPUTS.md) — 3 student personas with expected outputs
- [Extension Ideas](docs/EXTENSION_IDEAS.md) — Gmail, Calendar, ML engine upgrades

---

## Limitations

- Input is self-reported — accuracy depends on honest description
- Session history resets on browser close
- Requires internet for Groq API calls
- Rule matrix is deterministic, not personalised ML

---

## Author

**S Jagadeesh** — [GitHub @Jagadeesh0463](https://github.com/Jagadeesh0463)
