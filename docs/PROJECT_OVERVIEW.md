# Project Overview — Digital Overload AI

## The Core Problem

Students fail not because they are lazy — they fail because they cannot
see overload coming.

When a student agrees to help organise a department event on top of four
assignments and two club meetings, she does not feel overloaded at that
moment. She just feels busy. The feeling of overload arrives on Thursday
night when nothing is ready.

The gap is pre-acceptance awareness — knowing before you say yes whether
you have the capacity to deliver.

Every existing tool operates after the decision is made:
- Todoist reminds you what to do
- Motion schedules when to do it
- RescueTime tells you what you spent time on

None of them answer: Should I accept this task?

Digital Overload AI answers that question by running a three-score
diagnostic on your current state before any planning begins.

---

## Why Three Scores?

A single overload number hides important differences.

Consider two students who both feel overwhelmed:

| Student | Situation | What They Need |
|---|---|---|
| Ravi | 5 exams in 4 days, all same subject, zero messages | Focus protection |
| Divya | 3 clubs + 2 assignments + 50 WhatsApp messages | Commitment reduction |

The three-score system separates these cases:

    Ravi:  Overload 67 HIGH  | AFI 28 LOW    | Capacity 91% TIGHT
    Divya: Overload 91 CRIT  | AFI 88 SEVERE | Capacity 22% OVERCOMMITTED

Now the recommendations are different.
Ravi gets FOCUS. Divya gets REDUCE + SPLIT.

---

## The Three Scores

### Score 1 — Overload Score (0–100)

    Overload = (task_count      × 0.15)
             + (urgency_signals × 0.20)
             + ((1 - energy)    × 0.15)
             + (time_pressure   × 0.50)   ← est_hours / free_hours, capped at 1.0

Weights justified:
- time_pressure = 0.50 (dominant factor — ratio of work to available time)
- urgency = 0.20 (deadline pressure)
- task_count and energy_penalty = 0.15 each (volume and fatigue modifiers)

Labels: 0-40 Low | 41-65 Moderate | 66-85 High | 86-100 Critical

### Score 2 — Attention Fragmentation Index — AFI (0–100)

    AFI = (unique_domains x 0.50) + (context_switches x 0.30) + (messages x 0.20) x 100

Original metric. No existing tool measures this.
Mark et al. (2008) showed domain-switching costs ~23 minutes recovery per switch.

Labels: 0-35 Low | 36-60 Moderate | 61-80 High | 81-100 Severe

### Score 3 — Capacity Fit (0–100%)

    Capacity Fit = (free_hours / estimated_hours) x energy_multiplier x 100

Energy multiplier: High=1.0 | Medium=0.75 | Low=0.5

Labels: >=100% Good Fit | 70-99% Tight | 40-69% Poor Fit | <40% Overcommitted

---

## The Overload Prediction Engine (OPE)

The OPE reads all three scores together and answers:
"If I accept one more task right now, will I fail?"

    IF Overload > 65 AND Capacity < 70%:
        OPE fires: Do NOT accept new tasks

    IF AFI > 80 (Severe):
        OPE fires: Domain batching must happen first

    IF all scores healthy:
        OPE clears: Safe to accept one moderate task

---

## Feature Extraction

Groq Llama 3.3 70B reads student text and returns 8 fields:

| Field | Type | Description |
|---|---|---|
| task_count | int | Total distinct tasks |
| urgency_signals | int | Urgent keywords count |
| unique_domains | int | Distinct domains (max 4) |
| context_switches | int | Domain-shift transitions |
| pending_messages | int | Unread messages |
| energy_level | str | High / Medium / Low |
| free_hours | float | Available hours today |
| estimated_hours | float | Total hours needed |

---

## Normalisation

Every field is clamped to a hard MAX before dividing:

| Variable | MAX |
|---|---|
| task_count | 10 |
| urgency_signals | 8 |
| unique_domains | 4 |
| context_switches | 6 |
| pending_messages | 50 |
| free_hours | 16 |
| estimated_hours | 24 |

No normalised value can exceed 1.0 or fall below 0.0.

---

## Recommendation Rule Matrix

16 rows mapping (overload_label x capacity_label) to action.
AFI Severe overrides everything with SPLIT.

4 actions: FOCUS | DEFER | SPLIT | REDUCE

---

## Architecture

    INPUT       → Student plain text
    AI LAYER    → Groq extracts 8 fields as JSON
    LOGIC       → scoring_engine + recommender + day_planner
    OUTPUT      → Streamlit dashboard

---

## References

- Cowan (2010) — working memory item count
- Sweller (1988) — cognitive load during problem solving
- Mark et al. (2008) — cost of interrupted work, CHI 08