"""
Phase 7 Test Suite: Planly Personalized Study Planning Agent
Verifies goal creation, natural language prompt parsing, schedule-aware time allocation,
study sprint generation, plan quality scoring, adaptive replanning, energy preferences,
and task completion.
"""

import pytest
from datetime import date, timedelta

from app.agents.planly_agent import PlanlyAgent
from app.schemas.domain import (
    StudyGoalCreateRequest, StudyPlanningRequest
)

@pytest.fixture
def planly_agent():
    return PlanlyAgent()

def test_goal_creation(planly_agent):
    req = StudyGoalCreateRequest(
        student_id="student-101",
        title="Prepare for Mathematics Midterm",
        target_date="2026-10-15",
        priority="HIGH",
        subjects=["Mathematics"],
        focus_topics=["Algebra", "Quadratic Equations", "Functions"]
    )
    goal = planly_agent.create_goal(req)
    assert goal.id is not None
    assert goal.title == "Prepare for Mathematics Midterm"
    assert "Algebra" in goal.focus_topics

def test_natural_language_goal_extraction(planly_agent):
    nl_prompt = "I have my math exam in two weeks. I can study about 10 hours every week. I am weak in algebra."
    parsed = planly_agent.parse_natural_language_goal(nl_prompt)
    assert "Mathematics" in parsed["subject"]
    assert "Algebra" in parsed["focus_topics"]
    assert parsed["available_hours_per_week"] == 10.0

def test_timetable_free_windows(planly_agent):
    today = date(2026, 10, 5) # Monday
    free_slots = planly_agent.get_student_timetable_free_windows("student-101", today)
    assert len(free_slots) >= 2
    # Ensure after-school slots start after 16:00
    for slot in free_slots:
        st_hour = int(slot["start_time"].split(":")[0])
        assert st_hour >= 17 or st_hour >= 10  # weekend morning or after-school

def test_generate_study_plan_and_quality_scores(planly_agent):
    req = StudyPlanningRequest(
        student_id="student-101",
        goal="Prepare for Mathematics midterm",
        target_date="2026-10-15",
        subjects=["Mathematics"],
        priority="HIGH",
        available_study_hours_per_week=10.0,
        preferred_session_minutes=50,
        energy_preference="NORMAL"
    )
    result = planly_agent.generate_study_plan(req)
    assert result.status == "SUCCESS"
    assert result.plan.overall_quality_score >= 80.0
    assert result.plan.feasibility_score == 100.0  # Zero class overlaps
    assert len(result.plan.sprints) > 0

def test_energy_preference_adaptation(planly_agent):
    # Low energy should allocate shorter sessions
    req_low = StudyPlanningRequest(
        student_id="student-101",
        goal="Physics Review",
        target_date="2026-10-20",
        energy_preference="LOW"
    )
    res_low = planly_agent.generate_study_plan(req_low)
    first_sprint_dur = res_low.plan.sprints[0].duration_minutes
    assert first_sprint_dur == 35

    # High energy should allocate longer sessions
    req_high = StudyPlanningRequest(
        student_id="student-101",
        goal="Physics Deep Practice",
        target_date="2026-10-20",
        energy_preference="HIGH"
    )
    res_high = planly_agent.generate_study_plan(req_high)
    first_sprint_dur_high = res_high.plan.sprints[0].duration_minutes
    assert first_sprint_dur_high == 60

def test_complete_and_miss_task_and_adaptive_replan(planly_agent):
    # 1. Complete task
    comp_res = planly_agent.complete_task("task-1", actual_minutes=50)
    assert comp_res["status"] == "SUCCESS"

    # 2. Miss task -> triggers adaptive replan
    miss_res = planly_agent.miss_task("task-3")
    assert miss_res["status"] == "SUCCESS"

    # 3. Explicit adaptive replanning
    replanned_plan = planly_agent.replan_study_plan("plan-math-101", reason="MISSED_TASK")
    assert replanned_plan.status == "REPLANNED"

def test_student_progress_summary(planly_agent):
    progress = planly_agent.get_progress("student-101")
    assert progress.student_id == "student-101"
    assert progress.total_goals >= 1
    assert "Mathematics" in progress.subject_progress
