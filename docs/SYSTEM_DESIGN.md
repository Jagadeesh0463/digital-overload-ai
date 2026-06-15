# System Design — Digital Overload AI

## Architecture Overview

The system follows a clean 4-layer pipeline:

    INPUT LAYER
    Student types plain text — tasks, deadlines, messages, energy, free hours

    AI LAYER
    groq_client.py sends text to Groq Llama 3.3 70B
    Returns structured JSON with 8 fields

    LOGIC LAYER
    utils.py          — constants and thresholds
    scoring_engine.py — 3 scoring formulas
    recommender.py    — 16-row rule matrix
    day_planner.py    — time-block schedule builder
    session_store.py  — last 5 analyses

    OUTPUT LAYER
    app.py — Streamlit dashboard
    Score cards, Plotly charts, action plan, day plan, history

---

## Module Responsibilities

### groq_client.py
- Sends prompt to Groq API
- Receives JSON with 8 fields
- Retries up to 3 times on failure
- Strips markdown fences if model adds them

### utils.py
- FEATURE_CAPS — hard max values for normalisation
- ENERGY_NORM — maps High/Medium/Low to 1.0/0.6/0.2
- ENERGY_MULT — maps High/Medium/Low to 1.0/0.75/0.5
- OVERLOAD_LABELS — threshold table for labels
- AFI_LABELS — threshold table for labels
- CAPACITY_LABELS — threshold table for labels
- DOMAIN_COLORS — colour map for charts
- ACTION_COLORS — colour map for action badges
- DOMAIN_PRIORITY — order for day planner

### scoring_engine.py
- normalise(features) — clamps and divides all fields
- overload_score(normed) — weighted formula
- afi_score(normed) — weighted formula
- capacity_fit(features, normed) — ratio formula
- get_label(score, table) — looks up label from threshold table
- run_scoring(features) — orchestrates all above

### recommender.py
- RULE_MATRIX — 16-row dictionary
- AFI_SPLIT_COMBOS — combos that upgrade to SPLIT on High AFI
- INSTRUCTIONS — 5 instructions per action type
- get_action(overload_label, afi_label, capacity_label) — returns action
- generate_plan(action, scores) — returns P1-P5 list + OPE alert

### day_planner.py
- parse_start_time(str) — converts "9 PM" to float hour
- format_hour(float) — converts float to "9:00 PM" string
- build_day_plan(tasks, free_hours, energy, start_time) — builds blocks

### session_store.py
- init_history() — creates session_state key if missing
- add_to_history(result) — inserts at front, keeps last 5
- get_history() — returns list of past analyses

### app.py
- Page config and CSS styling
- Demo profile buttons
- Text input area
- Analyze button
- Calls all modules in order
- Renders all output sections
- Shows session history

---

## Data Flow

    Student text
        |
        v
    groq_client.extract_features(text)
        |
        v
    features dict (8 fields + tasks list)
        |
        v
    scoring_engine.run_scoring(features)
        |
        v
    scores dict (overload, afi, capacity, labels, normed)
        |
        v
    recommender.get_action(labels)
        |
        v
    action string (FOCUS/DEFER/SPLIT/REDUCE)
        |
        v
    recommender.generate_plan(action, scores)
        |
        v
    plan list (P1-P5 + OPE alert)
        |
        v
    day_planner.build_day_plan(tasks, free_hours, energy, start)
        |
        v
    day_plan list (time blocks)
        |
        v
    session_store.add_to_history(result)
        |
        v
    app.py renders everything on screen

---

## Normalisation Design

Every input variable has a hard MIN=0 and MAX cap.
Raw values are clamped to cap before dividing.
This guarantees all normalised values stay in [0, 1].
All score outputs stay in [0, 100].

    normalised = min(raw, cap) / cap

Example:
    18 messages / cap 50 = 0.36 — safely within [0, 1]
    99 tasks / cap 10 = clamped to 10 / 10 = 1.0

---

## Rule Matrix Design

16 rows cover every combination of:
- Overload label (4 levels) x Capacity label (4 levels)
- AFI used as tiebreaker and override

Special rule:
- AFI Severe (81+) always returns SPLIT regardless of other labels

    if afi_label == "Severe":
        return "SPLIT"

    base = RULE_MATRIX[(overload_label, capacity_label)]

    if afi_label == "High" and combo in AFI_SPLIT_COMBOS:
        return "SPLIT"

    return base

---

## Testing Strategy

Two test files covering core logic:

    test_scoring.py     — 13 tests
    - Normalisation range tests
    - Clamping tests
    - Score comparison tests (Divya > Ravi)
    - Label accuracy tests
    - Edge cases (zero input, over cap)

    test_recommender.py — 19 tests
    test_planner.py     — 5 tests
    - All overload levels
    - All capacity levels
    - AFI override tests
    - 3 persona verification tests

Total: 37 tests — all passing in 0.03s