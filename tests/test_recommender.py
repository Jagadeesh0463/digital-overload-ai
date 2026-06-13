import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recommender import get_action


# ── LOW OVERLOAD ──
def test_low_good_fit_any_afi():
    assert get_action("Low", "Low", "Good Fit") == "FOCUS"
    assert get_action("Low", "High", "Good Fit") == "FOCUS"

def test_low_tight_low_afi():
    assert get_action("Low", "Low", "Tight") == "FOCUS"

def test_low_tight_high_afi():
    assert get_action("Low", "High", "Tight") == "SPLIT"

def test_low_poor_fit():
    assert get_action("Low", "Low", "Poor Fit") == "DEFER"

def test_low_overcommitted():
    assert get_action("Low", "Low", "Overcommitted") == "REDUCE"


# ── MODERATE OVERLOAD ──
def test_moderate_good_fit_low_afi():
    assert get_action("Moderate", "Low", "Good Fit") == "FOCUS"

def test_moderate_good_fit_high_afi():
    assert get_action("Moderate", "High", "Good Fit") == "SPLIT"

def test_moderate_tight():
    assert get_action("Moderate", "Low", "Tight") == "DEFER"

def test_moderate_poor_fit():
    assert get_action("Moderate", "Low", "Poor Fit") == "REDUCE"

def test_moderate_overcommitted():
    assert get_action("Moderate", "Low", "Overcommitted") == "REDUCE"


# ── HIGH OVERLOAD ──
def test_high_good_fit_low_afi():
    assert get_action("High", "Low", "Good Fit") == "DEFER"

def test_high_good_fit_high_afi():
    assert get_action("High", "High", "Good Fit") == "SPLIT"

def test_high_tight():
    assert get_action("High", "Low", "Tight") == "REDUCE"

def test_high_overcommitted():
    assert get_action("High", "Low", "Overcommitted") == "REDUCE"


# ── CRITICAL OVERLOAD ──
def test_critical_always_reduce():
    assert get_action("Critical", "Low", "Good Fit") == "REDUCE"
    assert get_action("Critical", "Low", "Tight") == "REDUCE"
    assert get_action("Critical", "Low", "Overcommitted") == "REDUCE"


# ── SEVERE AFI OVERRIDE ──
def test_severe_afi_overrides_everything():
    assert get_action("Low",      "Severe", "Good Fit")      == "SPLIT"
    assert get_action("Moderate", "Severe", "Overcommitted") == "SPLIT"
    assert get_action("Critical", "Severe", "Good Fit")      == "SPLIT"


# ── 3 PERSONAS ──
def test_priya_gets_reduce():
    assert get_action("Moderate", "High", "Overcommitted") == "REDUCE"

def test_ravi_gets_defer():
    assert get_action("Moderate", "Low", "Tight") == "DEFER"

def test_divya_gets_split():
    assert get_action("Critical", "Severe", "Overcommitted") == "SPLIT"