from utils import DOMAIN_PRIORITY, DOMAIN_COLORS


def parse_start_time(start_time_str: str) -> float:
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