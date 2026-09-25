import pytest
import copy
from app.agents.schedule_quality_agent import (
    ScheduleQualityAgent, QualityReviewRequest, TeacherWorkloadMetrics,
    RoomUtilizationMetrics, SectionQualityMetrics, QualityIssue,
    QualityRecommendation, ScheduleOptimizationPlan, OptimizationPlanChange
)
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, ScheduledEntryDTO
)

@pytest.fixture
def base_solver_input():
    days = [
        SchoolDayDTO(date_str="2026-08-25", day_of_week=1, is_instructional=True),
        SchoolDayDTO(date_str="2026-08-26", day_of_week=2, is_instructional=True),
    ]
    periods = [
        PeriodDTO(id="p1", code="P1", name="Period 1", start_time="08:00:00", end_time="08:50:00", period_order=1),
        PeriodDTO(id="p2", code="P2", name="Period 2", start_time="09:00:00", end_time="09:50:00", period_order=2),
        PeriodDTO(id="p3", code="P3", name="Period 3", start_time="10:00:00", end_time="10:50:00", period_order=3),
        PeriodDTO(id="p4", code="P4", name="Period 4", start_time="11:00:00", end_time="11:50:00", period_order=4),
        PeriodDTO(id="p5", code="P5", name="Period 5", start_time="12:00:00", end_time="12:50:00", period_order=5),
    ]
    sections = [
        SectionDTO(id="8A", name="8A", grade_level=8, student_count=25),
        SectionDTO(id="8B", name="8B", grade_level=8, student_count=25),
    ]
    courses = [
        CourseDTO(id="c_lit", code="LIT100", title="Literature", subject_id="subj_lit", periods_per_week=2),
        CourseDTO(id="c_sci", code="PHYS200", title="Physical Science", subject_id="subj_sci", periods_per_week=2, requires_lab=True),
    ]
    teachers = [
        TeacherDTO(id="Cooper", name="Cooper", employee_code="EMP-COOPER", department="English", max_consecutive_periods=3),
        TeacherDTO(id="Ross", name="Ross", employee_code="EMP-ROSS", department="Science", max_consecutive_periods=3),
    ]
    rooms = [
        RoomDTO(id="Room 201", room_number="Room 201", building="Humanities", capacity=30),
        RoomDTO(id="Room 207", room_number="Room 207", building="Humanities", capacity=30),
        RoomDTO(id="Science Lab 1", room_number="Science Lab 1", building="Science", capacity=30, room_type="LAB"),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Ross", subject_id="subj_sci"),
    ]
    return SolverInput(
        school_days=days,
        periods=periods,
        sections=sections,
        courses=courses,
        teachers=teachers,
        rooms=rooms,
        capabilities=capabilities,
        teacher_availability=[],
        room_availability=[],
        assignments=[],
        config=SolverConfig(time_limit_seconds=5.0)
    )

@pytest.fixture
def sample_timetable():
    return [
        # Cooper has 4 consecutive periods on 2026-08-25: P1, P2, P3, P4 -> Consecutive load issue!
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="8B", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P3", period_id="p3", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P4", period_id="p4", section_id="8B", course_id="c_lit", teacher_id="Cooper", room_id="Room 207"),
        # Ross schedule
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8B", course_id="c_sci", teacher_id="Ross", room_id="Science Lab 1"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P5", period_id="p5", section_id="8A", course_id="c_sci", teacher_id="Ross", room_id="Science Lab 1"), # Idle gap between P1 and P5
    ]

def test_full_school_quality_review(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    req = QualityReviewRequest(scope="FULL_SCHOOL")
    res = agent.analyze_timetable_quality(req, base_solver_input, sample_timetable)

    assert res.overall_quality_score > 0.0
    assert res.hard_conflicts_count == 0
    assert len(res.teacher_metrics) == 2
    assert len(res.room_metrics) == 3
    assert len(res.issues) >= 1
    assert len(res.recommendations) >= 1

def test_teacher_quality_review_and_consecutive_detection(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    req = QualityReviewRequest(scope="TEACHER", target_entity_id="Cooper")
    res = agent.analyze_timetable_quality(req, base_solver_input, sample_timetable)

    assert len(res.teacher_metrics) == 1
    cooper_m = res.teacher_metrics[0]
    assert cooper_m.teacher_id == "Cooper"
    assert cooper_m.max_consecutive_periods == 4

    consec_issues = [i for i in res.issues if i.issue_type == "TEACHER_CONSECUTIVE_LOAD"]
    assert len(consec_issues) >= 1
    assert consec_issues[0].observed_value == 4.0

def test_room_utilization_review_and_underutilization(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    req = QualityReviewRequest(scope="ROOM")
    res = agent.analyze_timetable_quality(req, base_solver_input, sample_timetable)

    assert len(res.room_metrics) == 3
    r207_m = next((r for r in res.room_metrics if r.room_id == "Room 207"), None)
    assert r207_m is not None
    # Room 207 has 1 period occupied out of 10 capacity -> 10% utilization -> UNDERUTILIZED
    assert r207_m.status == "UNDERUTILIZED"

def test_deterministic_quality_score_formula(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    req = QualityReviewRequest()
    res = agent.analyze_timetable_quality(req, base_solver_input, sample_timetable)

    expected = round(
        0.35 * res.teacher_balance_score + 0.25 * res.section_balance_score + 0.25 * res.room_utilization_score + 0.15 * res.preference_alignment_score, 1
    )
    assert res.overall_quality_score == expected

def test_schedule_optimization_and_atomic_execution(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    review = agent.analyze_timetable_quality(QualityReviewRequest(), base_solver_input, sample_timetable)
    
    plans = agent.optimize_schedule(review.review_id, base_solver_input, sample_timetable, max_changes=5, current_version="v1.0")
    assert len(plans) >= 1
    plan = plans[0]
    assert plan.hard_conflicts == 0
    assert plan.quality_after >= plan.quality_before

    tt_copy = copy.deepcopy(sample_timetable)
    success, updated, err = agent.execute_optimization_plan(plan, base_solver_input, tt_copy, current_version="v1.0")
    assert success is True
    assert plan.status == "EXECUTED"

def test_version_conflict_atomic_rollback(base_solver_input, sample_timetable):
    agent = ScheduleQualityAgent()
    plan = ScheduleOptimizationPlan(
        plan_id="p-opt-stale",
        timetable_version="v1.0",
        changes=[]
    )
    success, updated, err = agent.execute_optimization_plan(plan, base_solver_input, sample_timetable, current_version="v2.0")
    assert success is False
    assert "version mismatch" in err.lower()
    assert plan.status == "STALE"
