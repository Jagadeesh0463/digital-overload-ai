import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scoring_engine import run_scoring, get_label
from utils import OVERLOAD_LABELS, AFI_LABELS, CAPACITY_LABELS

# ── PERSONA DATA ──
PRIYA = {
    "task_count": 5, "urgency_signals": 5,
    "unique_domains": 3, "context_switches": 4,
    "pending_messages": 18, "energy_level": "Low",
    "free_hours": 3, "estimated_hours": 8,
}

RAVI = {
    "task_count": 5, "urgency_signals": 7,
    "unique_domains": 1, "context_switches": 1,
    "pending_messages": 0, "energy_level": "Medium",
    "free_hours": 8, "estimated_hours": 10,
}

DIVYA = {
    "task_count": 8, "urgency_signals": 7,
    "unique_domains": 4, "context_switches": 6,
    "pending_messages": 50, "energy_level": "Low",
    "free_hours": 2.5, "estimated_hours": 12,
}


# ── NORMALISATION TESTS ──
def test_all_normalised_values_in_range():
    for persona in [PRIYA, RAVI, DIVYA]:
        result = run_scoring(persona)
        for key, val in result["normed"].items():
            if key.endswith("_norm"):
                assert 0.0 <= val <= 1.0, f"{key}={val} out of range"


def test_clamping_over_cap():
    data = {**PRIYA, "task_count": 99, "pending_messages": 999}
    result = run_scoring(data)
    assert result["normed"]["task_count_norm"] == 1.0
    assert result["normed"]["pending_messages_norm"] == 1.0


# ── OVERLOAD SCORE TESTS ──
def test_divya_overload_higher_than_ravi():
    assert run_scoring(DIVYA)["overload"] > run_scoring(RAVI)["overload"]


def test_overload_never_exceeds_100():
    for persona in [PRIYA, RAVI, DIVYA]:
        assert run_scoring(persona)["overload"] <= 100


def test_zero_input_gives_zero_overload():
    zero = {k: 0 for k in PRIYA}
    zero["energy_level"] = "High"
    assert run_scoring(zero)["overload"] == 0.0


# ── AFI SCORE TESTS ──
def test_ravi_afi_lower_than_divya():
    assert run_scoring(RAVI)["afi"] < run_scoring(DIVYA)["afi"]


def test_divya_afi_is_severe():
    assert run_scoring(DIVYA)["afi"] > 80


def test_ravi_afi_is_low():
    assert run_scoring(RAVI)["afi"] < 36


# ── CAPACITY FIT TESTS ──
def test_priya_is_overcommitted():
    assert run_scoring(PRIYA)["capacity"] < 40


def test_capacity_never_exceeds_100():
    easy = {**PRIYA, "free_hours": 20, "estimated_hours": 1, "energy_level": "High"}
    assert run_scoring(easy)["capacity"] == 100.0


# ── LABEL TESTS ──
def test_overload_labels():
    assert get_label(90, OVERLOAD_LABELS) == "Critical"
    assert get_label(70, OVERLOAD_LABELS) == "High"
    assert get_label(50, OVERLOAD_LABELS) == "Moderate"
    assert get_label(20, OVERLOAD_LABELS) == "Low"


def test_afi_labels():
    assert get_label(85, AFI_LABELS) == "Severe"
    assert get_label(65, AFI_LABELS) == "High"
    assert get_label(40, AFI_LABELS) == "Moderate"
    assert get_label(10, AFI_LABELS) == "Low"


def test_capacity_labels():
    assert get_label(100, CAPACITY_LABELS) == "Good Fit"
    assert get_label(80,  CAPACITY_LABELS) == "Tight"
    assert get_label(50,  CAPACITY_LABELS) == "Poor Fit"
    assert get_label(20,  CAPACITY_LABELS) == "Overcommitted"