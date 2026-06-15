# User Flow — Digital Overload AI

## Simple User Journey

    Student opens app
        |
        v
    Sees 3 demo buttons
    [👩 Try Priya] [👨 Try Ravi] [👩 Try Divya]
        |
        v
    Clicks demo OR types own situation in text box
        |
        v
    Clicks [🔍 Analyze My Workload]
        |
        v
    Groq AI reads text — takes 2-3 seconds
        |
        v
    3 Score Cards appear
    🔥 Overload Score | 🧩 AFI Score | ⏱️ Capacity Fit
        |
        v
    OPE Alert fires
    ✅ Safe to proceed OR ⚠️ Do NOT accept new tasks
        |
        v
    Overload Gauge chart + Domain Breakdown chart
        |
        v
    Action Plan P1-P5
    Primary action: FOCUS / DEFER / SPLIT / REDUCE
        |
        v
    Suggested Day Structure table
    Hour-by-hour time blocks grouped by domain
        |
        v
    Analysis saved to Session History
        |
        v
    Student can click another demo or type new situation
    Session History shows last 5 analyses for comparison

---

## Detailed Step-by-Step Flow

### Step 1 — Input

Student types naturally in one text box:

    "4 assignments due this week — OS on Wednesday, DBMS on Thursday,
    Web Dev and ML both on Friday. 18 WhatsApp messages pending.
    Club meeting tomorrow at 5 PM. Low energy. 3 free hours tonight."

Or clicks a demo button to auto-fill.

No forms. No dropdowns. No sliders.
Just plain text — messy is fine.

---

### Step 2 — AI Extraction

groq_client.py sends text to Groq Llama 3.3 70B.

Groq returns JSON:

    {
      "task_count": 5,
      "urgency_signals": 5,
      "unique_domains": 3,
      "context_switches": 4,
      "pending_messages": 18,
      "energy_level": "Low",
      "free_hours": 3.0,
      "estimated_hours": 10.0,
      "start_time": "9 PM",
      "tasks": [
        {"name": "OS assignment", "domain": "Academic", "hours": 2.5},
        {"name": "DBMS assignment", "domain": "Academic", "hours": 2.5},
        {"name": "Club meeting", "domain": "Social", "hours": 2.0}
      ]
    }

---

### Step 3 — Normalisation

scoring_engine.py clamps each value to its hard cap:

    task_count      5  / 10 = 0.50
    urgency_signals 5  / 8  = 0.625
    unique_domains  3  / 4  = 0.75
    context_switches 4 / 6  = 0.667
    pending_messages 18/ 50 = 0.36
    energy_level    Low     = 0.2

---

### Step 4 — Scoring

Three formulas run on normalised values:

    Overload = 63.4 → Moderate
    AFI      = 64.7 → High
    Capacity = 18.8% → Overcommitted

---

### Step 5 — Recommendation

Rule matrix looks up (Moderate, High, Overcommitted):

    → Primary Action: REDUCE

OPE checks:
    Overload > 65? No
    AFI > 80? No
    Capacity < 70? Yes + Overload > 40
    → OPE: Monitor carefully

---

### Step 6 — Day Plan

day_planner.py groups tasks by domain:

    Academic first (highest priority)
    Social second
    Breaks inserted after every block
    Stops when free_hours exhausted

Output:

    9:00 PM – 10:00 PM  Academic  OS assignment    60 min
    10:00 PM – 10:15 PM Break     Short rest       15 min
    10:15 PM – 11:15 PM Academic  DBMS assignment  60 min
    11:15 PM – 11:30 PM Break     Short rest       15 min
    11:30 PM – 12:00 AM Academic  Web Dev          30 min
    12:00 AM onwards    Rest      Stop work

---

### Step 7 — Session History

Result saved to st.session_state:

    {
      "timestamp": "10:09 PM",
      "overload": 63.4,
      "afi": 64.7,
      "capacity": 18.8,
      "action": "REDUCE"
    }

Last 5 analyses shown at bottom of dashboard.
Student can compare scores before and after dropping a task.

---

## Error Flow

    Groq API fails
        |
        v
    Retry up to 3 times with 1 second wait
        |
        v
    If still fails → show error message
    "Something went wrong. Check your GROQ_API_KEY."

---

## What Happens With Each Action

### FOCUS
Student works single-task mode.
No switching. Notifications off.
45–90 min blocks depending on energy level. Highest urgency first.

### DEFER
Student moves non-urgent tasks to tomorrow.
Communicates early with anyone waiting.
Only today's must-do items remain.

### SPLIT
Student groups tasks by domain.
Never switches domains mid-block.
One domain block at a time with breaks.

### REDUCE
Student drops lowest-priority items.
Does NOT accept any new tasks.
Identifies 1-2 must-do items only.