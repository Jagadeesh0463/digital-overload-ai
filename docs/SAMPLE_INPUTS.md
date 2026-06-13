# Sample Inputs — Three Student Personas

## Why Three Personas?

The same surface symptom — feeling overwhelmed — maps to three completely
different diagnostic profiles. Use these to test the system and verify
scoring produces correct output.

---

## Persona 1 — Priya (Mid-Semester Student)

### Input Text

    4 assignments due this week — OS on Wednesday, DBMS on Thursday,
    Web Dev and ML both on Friday. 18 WhatsApp messages from classmates
    pending. Club meeting tomorrow at 5 PM for 2 hours.
    Feeling low energy today. Only 3 free hours tonight after 9 PM.

### Expected Scores

| Score | Value | Label |
|---|---|---|
| Overload | 42–82 / 100 | Moderate to High |
| AFI | 55–71 / 100 | Moderate to High |
| Capacity Fit | 15–19% | Overcommitted |

### Expected Action

REDUCE + DEFER

### Expected Day Plan

    9:00 PM – 10:00 PM  Academic  OS assignment       60 min
    10:00 PM – 10:15 PM Break     Short rest          15 min
    10:15 PM – 11:15 PM Academic  DBMS assignment     60 min
    11:15 PM – 11:30 PM Break     Short rest          15 min
    11:30 PM – 12:00 AM Academic  Web Dev assignment  30 min
    12:00 AM onwards    Rest      Stop work

---

## Persona 2 — Ravi (Exam Sprinter)

### Input Text

    5 subject exams in the next 4 days — Computer Networks today,
    Operating Systems tomorrow, DBMS the day after, then Web Dev and
    Cloud Computing on day 4. Zero pending messages — switched off
    notifications completely. Energy is medium. I have about 8 free
    hours today. No club commitments this week.

### Expected Scores

| Score | Value | Label |
|---|---|---|
| Overload | 60–67 / 100 | Moderate to High |
| AFI | 17–28 / 100 | Low |
| Capacity Fit | 60–91% | Poor Fit to Tight |

### Expected Action

FOCUS + DEFER

### Key Insight

Ravi has similar overload to Priya but AFI is LOW — all tasks are
Academic. The system correctly recommends FOCUS not SPLIT.
This proves why AFI is needed as a separate dimension.

---

## Persona 3 — Divya (Overcommitted Fresher)

### Input Text

    I am in 3 college clubs — Robotics, Cultural Committee, and NSS.
    All three have events this week. I also have 2 assignments due Friday
    and a lab record submission on Thursday. About 50 WhatsApp messages
    unread across 6 groups. Feeling low energy — been staying up late
    all week. Only 2 free hours today.

### Expected Scores

| Score | Value | Label |
|---|---|---|
| Overload | 83–91 / 100 | High to Critical |
| AFI | 88–100 / 100 | Severe |
| Capacity Fit | 10–22% | Overcommitted |

### Expected Action

REDUCE + SPLIT (Severe AFI override fires)

### Key Insight

Divya hits maximum fragmentation — all 4 domains present, all message
caps hit. The Severe AFI override in the rule matrix fires regardless
of other scores. She gets SPLIT not just REDUCE.

---

## Persona Comparison

| Persona | Overload | AFI | Capacity | Action |
|---|---|---|---|---|
| Priya | Moderate/High | High | Overcommitted | REDUCE + DEFER |
| Ravi | Moderate | Low | Tight | FOCUS + DEFER |
| Divya | Critical | Severe | Overcommitted | REDUCE + SPLIT |

## The Central Point

All three say they are overwhelmed.
A single score gives similar advice to all three.
The 3-score system gives different diagnoses and different actions.
This is why AFI and Capacity Fit exist as separate dimensions.

---

## How to Use for Testing

1. Click demo button in app — Try Priya / Try Ravi / Try Divya
2. Click Analyze My Workload
3. Compare output scores against expected values above
4. Verify action plan matches expected action
5. Check day plan groups tasks by domain correctly