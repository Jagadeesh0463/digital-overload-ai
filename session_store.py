import streamlit as st
from datetime import datetime


def init_history() -> None:
    """Initialise the session history list if not already present in session state."""
    if "history" not in st.session_state:
        st.session_state["history"] = []


def add_to_history(result: dict) -> None:
    """Add a completed analysis result to the session history (capped at 5 entries).

    Args:
        result: dict containing keys: scores (dict), action (str), input_text (str).
    """
    init_history()
    entry = {
        "timestamp":      datetime.now().strftime("%I:%M %p"),
        "overload":       result["scores"]["overload"],
        "afi":            result["scores"]["afi"],
        "capacity":       result["scores"]["capacity"],
        "overload_label": result["scores"]["overload_label"],
        "afi_label":      result["scores"]["afi_label"],
        "capacity_label": result["scores"]["capacity_label"],
        "action":         result["action"],
        "input_preview":  result["input_text"][:60] + "..." if len(result["input_text"]) > 60 else result["input_text"],
    }
    st.session_state["history"].insert(0, entry)
    st.session_state["history"] = st.session_state["history"][:5]


def get_history() -> list:
    """Return the current session history list (up to 5 most recent analyses).

    Returns:
        List of history entry dicts, newest first.
    """
    init_history()
    return st.session_state["history"]