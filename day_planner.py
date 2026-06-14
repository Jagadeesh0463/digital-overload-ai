from utils import DOMAIN_PRIORITY, DOMAIN_COLORS


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
            return float(datetime.now().hour)
        else:
            return 18.0
    except:
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
    period = "AM" if h < 12 else "PM"
    display_h = h % 12
    if display_h == 0:
        display_h = 12
    return f"{display_h}:{m:02d} {period}"


def build_day_plan(tasks: list, free_hours: float,
                   energy_level: str, start_time_str: str) -> list:
    """Build a domain-grouped time-block schedule from extracted tasks.

    Tasks are sorted by domain priority (Academic → Admin → Social → Personal).
    Block length is adjusted by energy level: Low=60 min, Medium=75, High=90.
    A 15-minute break is inserted after each task block.

    Args:
        tasks: list of task dicts with keys: name, domain, hours.
        free_hours: total available hours for scheduling.
        energy_level: "High", "Medium", or "Low" — controls block duration.
        start_time_str: string like "9 AM", "8 PM", or "Now".

    Returns:
        List of time-block dicts with keys: time, domain, activity, duration, color.
    """
    if not tasks:
        return []

    # Block length by energy level
    if energy_level == "Low":
        block_minutes = 60
    elif energy_level == "Medium":
        block_minutes = 75
    else:
        block_minutes = 90

    break_minutes = 15

    # Group tasks by domain in priority order
    domain_groups = {d: [] for d in DOMAIN_PRIORITY}
    for task in tasks:
        domain = task.get("domain", "Academic")
        if domain not in domain_groups:
            domain = "Academic"
        domain_groups[domain].append(task)

    # Build time blocks
    current       = parse_start_time(start_time_str)
    remaining     = free_hours
    plan          = []

    for domain in DOMAIN_PRIORITY:
        domain_tasks = domain_groups[domain]
        if not domain_tasks:
            continue

        for task in domain_tasks:
            if remaining <= 0:
                break

            task_hours   = float(task.get("hours", 1.0))
            actual_hours = min(task_hours, remaining, block_minutes / 60)
            end          = current + actual_hours

            plan.append({
                "time":     f"{format_hour(current)} – {format_hour(end)}",
                "domain":   domain,
                "activity": task["name"],
                "duration": f"{int(actual_hours * 60)} min",
                "color":    DOMAIN_COLORS.get(domain, "#64748b"),
            })

            current   = end
            remaining -= actual_hours

            # Add break if time remains
            if remaining > 0.25:
                plan.append({
                    "time":     f"{format_hour(current)} – {format_hour(current + break_minutes / 60)}",
                    "domain":   "Break",
                    "activity": "Short rest — no phone or messages",
                    "duration": f"{break_minutes} min",
                    "color":    "#334155",
                })
                current   += break_minutes / 60
                remaining -= break_minutes / 60

    # End note
    plan.append({
        "time":     f"{format_hour(current)} onwards",
        "domain":   "Rest",
        "activity": "Stop work. Rest is part of recovery.",
        "duration": "—",
        "color":    "#1e293b",
    })

    return plan