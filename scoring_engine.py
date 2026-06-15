from utils import FEATURE_CAPS, ENERGY_NORM, ENERGY_MULT, OVERLOAD_LABELS, AFI_LABELS, CAPACITY_LABELS


def normalise(features: dict) -> dict:
    """Normalise raw feature values to [0, 1] range using per-feature caps.

    Also computes derived normalised values:
    - energy_norm: maps energy level string to a 0–1 float
    - time_pressure_norm: how much estimated work exceeds available time (0=under, 1=2x over)

    Args:
        features: raw feature dict from Groq extraction.

    Returns:
        normed: dict of normalised values used by scoring functions.
    """
    normed: dict = {}
    for key, cap in FEATURE_CAPS.items():
        raw = float(features.get(key, 0))
        clamped = min(raw, cap)
        normed[key + "_norm"] = clamped / cap

    normed["energy_level"] = features.get("energy_level", "Medium")
    normed["energy_norm"]  = ENERGY_NORM.get(normed["energy_level"], 0.6)

    # Time pressure: linear scale from 0 (est <= free) to 1.0 at est = 4× free.
    # Using ratio/4.0 instead of (ratio-1) so that:
    #   2:1 (est=6, free=3) → 0.5  (moderate pressure)
    #   4:1 (est=12, free=3) → 1.0 (maximum pressure)
    # This prevents severe mismatches from being masked by low task/urgency counts.
    free = float(features.get("free_hours", 1))
    est  = float(features.get("estimated_hours", 0))
    if est == 0:
        normed["time_pressure_norm"] = 0.0
    elif free == 0:
        normed["time_pressure_norm"] = 1.0
    else:
        normed["time_pressure_norm"] = min((est / max(free, 0.5)) / 4.0, 1.0)

    return normed


def overload_score(normed: dict) -> float:
    """Compute Overload Score (0–100) from normalised features.

    Weights:
        task_count      × 0.15  — volume of pending tasks
        urgency_signals × 0.20  — deadline pressure
        (1 - energy)    × 0.15  — fatigue penalty
        time_pressure   × 0.50  — capacity gap (dominant factor)

    time_pressure carries 50% weight because the ratio of estimated work
    to available time is the most objective and severe overload signal.
    A 4:1 mismatch (12h work, 3h free) should always produce High/Critical
    overload regardless of task count or urgency.

    Args:
        normed: output of normalise().

    Returns:
        Overload score clamped to [0, 100].
    """
    score = (
        normed["task_count_norm"]      * 0.15 +
        normed["urgency_signals_norm"] * 0.20 +
        (1 - normed["energy_norm"])    * 0.15 +
        normed["time_pressure_norm"]   * 0.50
    ) * 100
    return round(min(score, 100), 1)


def afi_score(normed: dict) -> float:
    """Compute Attention Fragmentation Index (0–100) from normalised features.

    Weights:
        unique_domains    × 0.50  — breadth of task domains (Academic/Social/Admin/Personal)
        context_switches  × 0.30  — number of mid-session topic switches
        pending_messages  × 0.20  — communication load adding cognitive interruption

    Args:
        normed: output of normalise().

    Returns:
        AFI score clamped to [0, 100].
    """
    score = (
        normed["unique_domains_norm"]   * 0.50 +
        normed["context_switches_norm"] * 0.30 +
        normed["pending_messages_norm"] * 0.20
    ) * 100
    return round(min(score, 100), 1)


def capacity_fit(features: dict, normed: dict) -> float:
    """Compute Capacity Fit percentage (0–100%).

    Formula: (free_hours / estimated_hours) × energy_multiplier × 100

    Energy multipliers: High=1.0, Medium=0.75, Low=0.5 — because low energy
    reduces effective working capacity even within the available hours.

    Args:
        features: raw feature dict.
        normed: output of normalise() (used for energy level).

    Returns:
        Capacity Fit score clamped to [0, 100].
    """
    free = float(features.get("free_hours", 1))
    est  = float(features.get("estimated_hours", 1))
    if est == 0:
        return 100.0
    mult  = ENERGY_MULT.get(normed["energy_level"], 0.75)
    score = (free / est) * mult * 100
    return round(min(score, 100), 1)


def get_label(score: float, label_table: list) -> str:
    """Map a numeric score to a label string using a descending threshold table.

    Args:
        score: numeric value to classify.
        label_table: list of (threshold, label) pairs, sorted highest first.

    Returns:
        The label string for the first threshold the score meets or exceeds.
    """
    for threshold, label in label_table:
        if score >= threshold:
            return label
    return label_table[-1][1]


def run_scoring(features: dict) -> dict:
    """Run the full 3-score diagnostic pipeline on extracted features.

    Args:
        features: dict with keys: task_count, urgency_signals, unique_domains,
                  context_switches, pending_messages, free_hours,
                  estimated_hours, energy_level.

    Returns:
        dict with keys: overload, afi, capacity (floats),
        overload_label, afi_label, capacity_label (strings),
        and normed (dict of normalised input values).
    """
    normed   = normalise(features)
    overload = overload_score(normed)
    afi      = afi_score(normed)
    capacity = capacity_fit(features, normed)

    return {
        "overload":        overload,
        "afi":             afi,
        "capacity":        capacity,
        "overload_label":  get_label(overload,  OVERLOAD_LABELS),
        "afi_label":       get_label(afi,        AFI_LABELS),
        "capacity_label":  get_label(capacity,   CAPACITY_LABELS),
        "normed":          normed,
    }