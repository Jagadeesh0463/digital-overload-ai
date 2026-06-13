from utils import FEATURE_CAPS, ENERGY_NORM, ENERGY_MULT, OVERLOAD_LABELS, AFI_LABELS, CAPACITY_LABELS


def normalise(features: dict) -> dict:
    normed = {}
    for key, cap in FEATURE_CAPS.items():
        raw = float(features.get(key, 0))
        clamped = min(raw, cap)
        normed[key + "_norm"] = clamped / cap
    normed["energy_level"] = features.get("energy_level", "Medium")
    normed["energy_norm"] = ENERGY_NORM.get(normed["energy_level"], 0.6)
    return normed


def overload_score(normed: dict) -> float:
    score = (
        normed["task_count_norm"]      * 0.35 +
        normed["urgency_signals_norm"] * 0.35 +
        (1 - normed["energy_norm"])    * 0.30
    ) * 100
    return round(min(score, 100), 1)


def afi_score(normed: dict) -> float:
    score = (
        normed["unique_domains_norm"]   * 0.50 +
        normed["context_switches_norm"] * 0.30 +
        normed["pending_messages_norm"] * 0.20
    ) * 100
    return round(min(score, 100), 1)


def capacity_fit(features: dict, normed: dict) -> float:
    free = float(features.get("free_hours", 1))
    est  = float(features.get("estimated_hours", 1))
    if est == 0:
        return 100.0
    mult  = ENERGY_MULT.get(normed["energy_level"], 0.75)
    score = (free / est) * mult * 100
    return round(min(score, 100), 1)


def get_label(score: float, label_table: list) -> str:
    for threshold, label in label_table:
        if score >= threshold:
            return label
    return label_table[-1][1]


def run_scoring(features: dict) -> dict:
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