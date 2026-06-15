# ── 16-ROW RULE MATRIX ──
RULE_MATRIX = {
    ("Low",      "Good Fit"):      "FOCUS",
    ("Low",      "Tight"):         "FOCUS",
    ("Low",      "Poor Fit"):      "DEFER",
    ("Low",      "Overcommitted"): "REDUCE",
    ("Moderate", "Good Fit"):      "FOCUS",
    ("Moderate", "Tight"):         "DEFER",
    ("Moderate", "Poor Fit"):      "REDUCE",
    ("Moderate", "Overcommitted"): "REDUCE",
    ("High",     "Good Fit"):      "DEFER",
    ("High",     "Tight"):         "REDUCE",
    ("High",     "Poor Fit"):      "REDUCE",
    ("High",     "Overcommitted"): "REDUCE",
    ("Critical", "Good Fit"):      "REDUCE",
    ("Critical", "Tight"):         "REDUCE",
    ("Critical", "Poor Fit"):      "REDUCE",
    ("Critical", "Overcommitted"): "REDUCE",
}

# ── AFI SPLIT OVERRIDE ──
AFI_SPLIT_COMBOS = {
    ("Low",      "Tight"),
    ("Moderate", "Good Fit"),
    ("High",     "Good Fit"),
}

# ── ACTION INSTRUCTIONS ──
INSTRUCTIONS = {
    "FOCUS": [
        "Work in single-task mode — one task at a time, no switching.",
        "Start with the highest-urgency task first.",
        "Turn off all notifications during each work block.",
        "Use focused work blocks (45–90 min depending on energy) with short breaks between tasks.",
        "Your capacity is manageable — protect this state.",
    ],
    "DEFER": [
        "Identify tasks NOT due today or tomorrow — move them out.",
        "Write deferred items with new target dates so nothing is forgotten.",
        "Tell anyone waiting on deferred tasks early — don't wait.",
        "Focus only on today's highest-priority items.",
        "Do NOT accept any new tasks until deferred items are cleared.",
    ],
    "SPLIT": [
        "Group all tasks by domain — Academic together, Social together, Admin together.",
        "Work one domain block at a time — do not switch domains mid-block.",
        "Each domain block should be 45–90 minutes with a break before switching.",
        "Your Attention Fragmentation is high — domain-mixing is your biggest risk today.",
        "Reply to messages only in one dedicated Admin block — not throughout the day.",
    ],
    "REDUCE": [
        "Do NOT accept any new tasks or commitments today.",
        "Drop or delegate the lowest-priority items immediately.",
        "Your Capacity Fit is critically low — you cannot complete everything today.",
        "Identify 1–2 must-do items and treat everything else as optional.",
        "Communicate proactively about what will NOT get done today.",
    ],
}


def get_action(overload_label: str, afi_label: str, capacity_label: str) -> str:
    # Severe AFI always overrides everything
    if afi_label == "Severe":
        return "SPLIT"

    base = RULE_MATRIX.get((overload_label, capacity_label), "REDUCE")

    # High AFI upgrades certain combos to SPLIT
    if afi_label == "High":
        if (overload_label, capacity_label) in AFI_SPLIT_COMBOS:
            return "SPLIT"

    return base


def generate_plan(action: str, scores: dict) -> list:
    instructions = INSTRUCTIONS.get(action, INSTRUCTIONS["REDUCE"])
    plan = []

    for i, instruction in enumerate(instructions, 1):
        plan.append({
            "priority":    f"P{i}",
            "action":      action,
            "instruction": instruction,
        })

    # OPE Alert
    ope_fires = (
        scores["overload"] > 65 and scores["capacity"] < 70
    ) or scores["afi"] > 80

    if ope_fires:
        plan.append({
            "priority":    "⚠️ OPE",
            "action":      "ALERT",
            "instruction": f"OPE Alert: Overload={scores['overload']:.0f}, AFI={scores['afi']:.0f}, Capacity={scores['capacity']:.0f}%. Do NOT accept new tasks — your system is at capacity.",
        })

    return plan