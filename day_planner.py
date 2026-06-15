from utils import DOMAIN_PRIORITY, DOMAIN_COLORS

# Keywords that indicate a task is urgent
_URGENCY_KEYWORDS = [
    "due today", "due tonight", "due tomorrow", "tonight", "today",
    "urgent", "asap", "exam", "quiz", "test", "submit", "deadline",
    "presentation", "interview",
]


def _urgency_score(task: dict) -> int:
    """Return 0 (urgent) or 1 (normal) based on task name keywords.

    Lower score = scheduled earlier.

    Args:
        task: task dict with key 'name'.

    Returns:
        0 if the task name contains an urgency keyword, else 1.
    """
    name = task.get("name", "").lower()
    return 0 if any(kw in name for kw in _URGENCY_KEYWORDS) else 1


def _sort_tasks(tasks: list) -> list:
    """Sort tasks by: urgency first, then domain priority, then hours ascending.

    Scheduling order:
      1. Urgent tasks (name contains deadline/exam/tonight etc.)
      2. Domain priority: Academic > Admin > Social > Personal
      3. Shorter tasks first within the same urgency + domain group
         (clear short tasks quickly to reduce cognitive load)

    Args:
        tasks: raw list of task dicts.

    Returns:
        Sorted list of task dicts.
    """
    def sort_key(t: dict) -> tuple:
        urgency = _urgency_score(t)
        domain  = t.get("domain", "Personal")
        d_rank  = DOMAIN_PRIORITY.index(domain) if domain in DOMAIN_PRIORITY else 4
        hours   = float(t.get("hours", 1.0))
        return (urgency, d_rank, hours)

    return sorted(tasks, key=sort_key)


def parse_start_time(start_time_str: str) -> float:
    """Convert a start-time string to a 24-hour float (e.g. "9 PM" → 21.0).

    Handles AM/PM strings and the special value "Now" (uses current hour).
    Defaults to 18.0 (6 PM) if parsing fails.

    Args:
        start_time_str: string like "9 AM", "10 PM", or "Now".

    Returns:
        Hour as a float in 24-hour format.
    """
    s = start_time_str.strip().upper()
    try:
        if "AM" in s:
            hour = int(s.replace("AM", "").replace(" ", ""))
            return float(hour if hour != 12 else 0)
        elif "PM" in s:
            hour = int(s.replace("PM", "").replace(" ", ""))
            return float(hour if hour == 12 else hour + 12)
        elif "NOW" in s:
            from datetime import datetime
            now = datetime.now()
            return now.hour + now.minute / 60.0
        else:
            return 18.0
    except Exception:
        return 18.0


def format_hour(hour_float: float) -> str:
    """Convert a 24-hour float to a 12-hour AM/PM display string.

    Args:
        hour_float: hour in 24-hour format, e.g. 13.5 → "1:30 PM".

    Returns:
        Formatted time string like "9:00 AM" or "1:30 PM".
    """
    hour_float = hour_float % 24
    h = int(hour_float)
    m = int((hour_float - h) * 60)
    period    = "AM" if h < 12 else "PM"
    display_h = h % 12 or 12
    return f"{display_h}:{m:02d} {period}"


def build_day_plan(tasks: list, free_hours: float,
                   energy_level: str, start_time_str: str) -> list:
    """Build a practical, urgency-aware time-block schedule from extracted tasks.

    Scheduling rules:
      - Tasks sorted by urgency → domain priority → hours ascending
      - Each task uses its actual estimated hours, capped at max_block
      - Tasks longer than max_block are split: Part 1 scheduled, remainder deferred
      - Breaks only after blocks ≥ 45 min, and only if ≥ 30 min remains after
      - Break length scales with energy: Low=10 min, Medium=12 min, High=15 min
      - Scheduling stops when free_hours are consumed
      - Deferred tasks listed at the end with reason

    Block caps by energy level:
      High   → 90 min  (sustained focus)
      Medium → 60 min  (moderate session)
      Low    → 45 min  (short bursts)

    Args:
        tasks: list of task dicts with keys: name, domain, hours.
        free_hours: total available hours for scheduling.
        energy_level: "High", "Medium", or "Low".
        start_time_str: string like "9 AM", "8 PM", or "Now".

    Returns:
        List of time-block dicts with keys: time, domain, activity, duration, color.
    """
    # ── Guard: nothing to plan ──
    if not tasks:
        return [{
            "time":     "—",
            "domain":   "Rest",
            "activity": "No tasks detected. Describe your workload in more detail.",
            "duration": "—",
            "color":    "#334155",
        }]

    if free_hours < 0.25:
        return [{
            "time":     "Now",
            "domain":   "Rest",
            "activity": "Less than 15 minutes available. Rest and recover first.",
            "duration": "—",
            "color":    "#334155",
        }]

    # ── Settings by energy level ──
    if energy_level == "Low":
        max_block_min  = 45
        break_min      = 10
    elif energy_level == "High":
        max_block_min  = 90
        break_min      = 15
    else:  # Medium (default — catches unexpected values)
        max_block_min  = 60
        break_min      = 12

    max_block_h  = max_block_min / 60.0
    break_h      = break_min / 60.0
    MIN_BREAK_THRESHOLD_H = 0.75  # only add break after blocks ≥ 45 min
    MIN_REMAINING_FOR_BREAK = 0.5  # skip break if < 30 min remaining after task

    # ── Sort tasks ──
    sorted_tasks = _sort_tasks(tasks)

    current   = parse_start_time(start_time_str)
    remaining = float(free_hours)
    plan      = []
    deferred  = []  # tasks/parts that didn't fit

    for task in sorted_tasks:
        if remaining <= 0.1:
            deferred.append(task["name"])
            continue

        task_h  = float(task.get("hours", 1.0))
        domain  = task.get("domain", "Academic")
        if domain not in DOMAIN_PRIORITY:
            domain = "Academic"
        color   = DOMAIN_COLORS.get(domain, "#64748b")
        is_urgent = _urgency_score(task) == 0

        # Cap block at max_block and available time
        scheduled_h = min(task_h, max_block_h, remaining)
        end         = current + scheduled_h
        label_suffix = " ⚡" if is_urgent else ""

        # If task is longer than the block → remainder goes to deferred
        if task_h > scheduled_h + 0.05:
            leftover_h    = task_h - scheduled_h
            leftover_min  = int(leftover_h * 60)
            activity_name = f"{task['name']}{label_suffix} (Part 1)"
            deferred.append(f"{task['name']} — {leftover_min} min remaining")
        else:
            activity_name = f"{task['name']}{label_suffix}"

        plan.append({
            "time":     f"{format_hour(current)} – {format_hour(end)}",
            "domain":   domain,
            "activity": activity_name,
            "duration": f"{int(scheduled_h * 60)} min",
            "color":    color,
        })

        current   = end
        remaining -= scheduled_h

        # ── Break logic ──
        # Add break only after long blocks and only if enough time remains
        if (scheduled_h >= MIN_BREAK_THRESHOLD_H
                and remaining >= MIN_REMAINING_FOR_BREAK):
            break_end = current + break_h
            plan.append({
                "time":     f"{format_hour(current)} – {format_hour(break_end)}",
                "domain":   "Break",
                "activity": "Step away — no phone, no messages",
                "duration": f"{break_min} min",
                "color":    "#334155",
            })
            current    = break_end
            remaining -= break_h

    # ── End row ──
    if deferred:
        deferred_str = " · ".join(deferred)
        plan.append({
            "time":     f"{format_hour(current)} onwards",
            "domain":   "Rest",
            "activity": f"Stop work. Rest and recover.",
            "duration": "—",
            "color":    "#1e293b",
        })
        plan.append({
            "time":     "⏭ Deferred",
            "domain":   "Deferred",
            "activity": deferred_str,
            "duration": "Next session",
            "color":    "#475569",
        })
    else:
        plan.append({
            "time":     f"{format_hour(current)} onwards",
            "domain":   "Rest",
            "activity": "All tasks scheduled. Stop work and recover.",
            "duration": "—",
            "color":    "#1e293b",
        })

    return plan
