import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from day_planner import build_day_plan, _urgency_score, _sort_tasks


def test_empty_tasks_returns_guard():
    plan = build_day_plan([], 3.0, "Medium", "9 AM")
    assert len(plan) == 1
    assert "No tasks" in plan[0]["activity"]


def test_low_time_returns_guard():
    tasks = [{"name": "ML Project", "domain": "Academic", "hours": 1}]
    plan = build_day_plan(tasks, 0.1, "Medium", "9 AM")
    assert len(plan) == 1
    assert "15 minutes" in plan[0]["activity"]


def test_urgent_task_scheduled_first():
    tasks = [
        {"name": "ML Project",              "domain": "Academic", "hours": 1},
        {"name": "OS Assignment due tomorrow", "domain": "Academic", "hours": 1},
    ]
    plan = build_day_plan(tasks, 3.0, "Medium", "9 AM")
    work_rows = [r for r in plan if r["domain"] not in ("Break", "Rest", "Deferred")]
    assert "due tomorrow" in work_rows[0]["activity"]


def test_urgency_score_detects_keywords():
    assert _urgency_score({"name": "exam prep"}) == 0
    assert _urgency_score({"name": "read chapter 3"}) == 1


def test_no_break_after_short_task():
    tasks = [{"name": "Quick task", "domain": "Academic", "hours": 0.3}]
    plan = build_day_plan(tasks, 3.0, "Medium", "9 AM")
    break_rows = [r for r in plan if r["domain"] == "Break"]
    assert len(break_rows) == 0
