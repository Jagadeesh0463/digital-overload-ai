# Changelog

All notable changes to Digital Overload AI are documented here.

---

## [v1.0.0] — 2026-06-14

### Initial Public Release

**Core Features**
- 3-Score diagnostic system: Overload Score, Attention Fragmentation Index (AFI), Capacity Fit
- Groq Llama 3.3 70B integration for natural-language feature extraction
- 16-row deterministic recommendation rule matrix (FOCUS / DEFER / SPLIT / REDUCE)
- Domain-grouped AI day planner with energy-adjusted time blocks
- Overload Prediction Engine (OPE) — pre-acceptance capacity check
- Detected overload signals with named pattern recognition
- AI Analysis Summary generated without additional API calls
- Session history — last 5 analyses tracked per session
- CSV export of analysis results
- 3 demo profiles for quick testing

**Testing**
- 32 automated tests (13 scoring + 19 recommender), all passing
- GitHub Actions CI configured on push/PR to main

**UI**
- Dark theme with custom CSS on Streamlit 1.58
- Results grouped into 4 sections: Diagnostics · Analysis · Recommendations · Planning
- Progress bars on all 3 score metrics
- Visual comparison bars for Workload vs Capacity
- Styled section dividers with colour-coded labels

**Scoring**
- Overload formula includes time pressure component (est_hours vs free_hours)
- All formulas include docstrings and type hints

---

[v1.0.0]: https://github.com/Jagadeesh0463/digital-overload-ai/releases/tag/v1.0.0
