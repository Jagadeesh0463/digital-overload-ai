# ── FEATURE CAPS (maximum allowed values before normalisation) ──
FEATURE_CAPS = {
    "task_count":       10,
    "urgency_signals":  8,
    "unique_domains":   4,
    "context_switches": 6,
    "pending_messages": 50,
    "free_hours":       16,
    "estimated_hours":  24,
}

# ── ENERGY MAPPINGS ──
ENERGY_NORM = {"High": 1.0, "Medium": 0.6, "Low": 0.2}
ENERGY_MULT = {"High": 1.0, "Medium": 0.75, "Low": 0.5}

# ── SCORE LABEL THRESHOLDS ──
OVERLOAD_LABELS = [
    (86, "Critical"),
    (66, "High"),
    (41, "Moderate"),
    (0,  "Low"),
]

AFI_LABELS = [
    (81, "Severe"),
    (61, "High"),
    (36, "Moderate"),
    (0,  "Low"),
]

CAPACITY_LABELS = [
    (100, "Good Fit"),
    (70,  "Tight"),
    (40,  "Poor Fit"),
    (0,   "Overcommitted"),
]

# ── COLOURS ──
DOMAIN_COLORS = {
    "Academic": "#3b82f6",
    "Social":   "#f59e0b",
    "Personal": "#10b981",
    "Admin":    "#8b5cf6",
}

ACTION_COLORS = {
    "FOCUS":  "#22c55e",
    "DEFER":  "#f59e0b",
    "SPLIT":  "#3b82f6",
    "REDUCE": "#ef4444",
}

DOMAIN_PRIORITY = ["Academic", "Admin", "Social", "Personal"]