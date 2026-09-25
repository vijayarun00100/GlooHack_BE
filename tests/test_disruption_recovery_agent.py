import pytest
import copy
from app.agents.disruption_recovery_agent import (
    DisruptionRecoveryAgent, DisruptionEvent, RecoveryPlan, RecoveryPlanChange
)
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, ScheduledEntryDTO
)

@pytest.fixture
def base_solver_input():
    days = [
        SchoolDayDTO(date_str="2026-09-28", day_of_week=1, is_instructional=True),
        SchoolDayDTO(date_str="2026-09-29", day_of_week=2, is_instructional=True),
    ]
    periods = [
        PeriodDTO(id="p1", code="P1", name="Period 1", start_time="08:00:00", end_time="08:50:00", period_order=1),
        PeriodDTO(id="p2", code="P2", name="Period 2", start_time="09:00:00", end_time="09:50:00", period_order=2),
        PeriodDTO(id="p3", code="P3", name="Period 3", start_time="10:00:00", end_time="10:50:00", period_order=3),
    ]
    sections = [
        SectionDTO(id="8A", name="8A", grade_level=8, student_count=25),
        SectionDTO(id="8B", name="8B", grade_level=8, student_count=25),
        SectionDTO(id="7A", name="7A", grade_level=7, student_count=20),
    ]
    courses = [
        CourseDTO(id="c_lit", code="LIT100", title="Medieval Literature", subject_id="subj_lit", periods_per_week=2),
        CourseDTO(id="c_sci", code="PHYS200", title="Physical Science", subject_id="subj_sci", periods_per_week=2, requires_lab=True),
        CourseDTO(id="c_alg", code="MATH101", title="Algebra I", subject_id="subj_math", periods_per_week=2),
    ]
    teachers = [
        TeacherDTO(id="Cooper", name="Cooper", employee_code="EMP-COOPER", department="English"),
        TeacherDTO(id="Ross", name="Ross", employee_code="EMP-ROSS", department="Science"),
        TeacherDTO(id="Smith", name="Smith", employee_code="EMP-SMITH", department="Math"),
        TeacherDTO(id="Foster", name="Foster", employee_code="EMP-FOSTER", department="Math"),
    ]
    rooms = [
        RoomDTO(id="Room 201", room_number="Room 201", building="Building A", capacity=30),
        RoomDTO(id="Room 202", room_number="Room 202", building="Building B", capacity=35),
        RoomDTO(id="Room 203", room_number="Room 203", building="Building B", capacity=30),
        RoomDTO(id="Science Lab 1", room_number="Science Lab 1", building="Building A", capacity=30, room_type="LAB"),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Ross", subject_id="subj_sci"),
        TeacherCapabilityDTO(teacher_id="Smith", subject_id="subj_math"),
        TeacherCapabilityDTO(teacher_id="Foster", subject_id="subj_math"),
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
def initial_timetable():
    return [
        ScheduledEntryDTO(school_date="2026-09-28", period_code="P1", period_id="p1", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-09-28", period_code="P1", period_id="p1", section_id="8B", course_id="c_alg", teacher_id="Smith", room_id="Room 202"),
        ScheduledEntryDTO(school_date="2026-09-28", period_code="P2", period_id="p2", section_id="7A", course_id="c_sci", teacher_id="Ross", room_id="Science Lab 1"),
        ScheduledEntryDTO(school_date="2026-09-29", period_code="P1", period_id="p1", section_id="8A", course_id="c_alg", teacher_id="Foster", room_id="Room 203"),
    ]

def test_single_room_disruption(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        event_type="BUILDING_CLOSURE",
        title="Room 202 Maintenance",
        start_date="2026-09-28",
        end_date="2026-09-28",
        start_period="P1",
        end_period="P2",
        affected_rooms=["Room 202"]
    )
    result = agent.process_disruption(event, base_solver_input, initial_timetable)
    assert result.affected_classes_count == 1
    assert len(result.plans) >= 1
    assert result.plans[0].hard_conflicts == 0

def test_multi_room_disruption(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        event_type="BUILDING_CLOSURE",
        title="Building B Closure",
        start_date="2026-09-28",
        end_date="2026-09-29",
        start_period="P1",
        end_period="P3",
        affected_rooms=["Room 202", "Room 203"]
    )
    result = agent.process_disruption(event, base_solver_input, initial_timetable)
    assert result.affected_classes_count == 2
    assert result.affected_rooms_count == 2

def test_multi_period_and_multi_day_disruption(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        event_type="WEATHER_EMERGENCY",
        title="Severe Weather Lockdown",
        start_date="2026-09-28",
        end_date="2026-09-29",
        start_period="P1",
        end_period="P3",
        affected_rooms=["Room 201", "Room 202", "Room 203"]
    )
    result = agent.process_disruption(event, base_solver_input, initial_timetable)
    assert result.affected_classes_count == 3
    assert len(result.plans) > 0

def test_teacher_and_room_simultaneous_disruption(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        event_type="CAMPUS_DISRUPTION",
        title="Teacher & Facility Emergency",
        start_date="2026-09-28",
        end_date="2026-09-28",
        start_period="P1",
        end_period="P2",
        affected_rooms=["Room 201"],
        affected_teachers=["Smith"]
    )
    result = agent.process_disruption(event, base_solver_input, initial_timetable)
    assert result.affected_classes_count == 2
    assert result.affected_teachers_count == 2

def test_deterministic_plan_ranking_and_governance(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        event_type="BUILDING_CLOSURE",
        title="Room 202 Power Outage",
        start_date="2026-09-28",
        end_date="2026-09-28",
        start_period="P1",
        end_period="P1",
        affected_rooms=["Room 202"]
    )
    result = agent.process_disruption(event, base_solver_input, initial_timetable)
    assert len(result.plans) >= 1
    top_plan = result.plans[0]
    assert top_plan.ranking_category in ["CLEAN_RECOVERY", "LOW_DISRUPTION", "MODERATE_DISRUPTION"]
    assert top_plan.hard_conflicts == 0

def test_atomic_execution_and_conflict_detector_validation(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    tt = copy.deepcopy(initial_timetable)
    plan = RecoveryPlan(
        plan_id="p-test-1",
        disruption_id="d-1",
        timetable_version="v1.0",
        plan_title="Test Plan",
        ranking_category="CLEAN_RECOVERY",
        changes=[
            RecoveryPlanChange(
                timetable_entry_id="2026-09-28_P1_8B",
                school_date="2026-09-28",
                old_teacher_id="Smith",
                new_teacher_id="Smith",
                old_room_id="Room 202",
                new_room_id="Room 201",
                old_period_code="P1",
                new_period_code="P1"
            )
        ]
    )
    # Attempting to assign Room 201 during P1 will cause a ROOM_OVERLAP (8A is already in Room 201 P1)
    success, updated, err = agent.execute_recovery_plan(plan, base_solver_input, tt, current_version="v1.0")
    assert success is False
    assert "ConflictDetector" in err or "hard conflict" in err.lower()
    assert plan.status == "INVALID"

def test_timetable_version_conflict_rollback(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    tt = copy.deepcopy(initial_timetable)
    plan = RecoveryPlan(
        plan_id="p-test-stale",
        disruption_id="d-stale",
        timetable_version="v1.0",
        plan_title="Stale Plan",
        ranking_category="CLEAN_RECOVERY",
        changes=[]
    )
    # Target current_version is v2.0 -> mismatch!
    success, updated, err = agent.execute_recovery_plan(plan, base_solver_input, tt, current_version="v2.0")
    assert success is False
    assert "version mismatch" in err.lower()
    assert plan.status == "STALE"

def test_notifications_and_decision_memory(base_solver_input, initial_timetable):
    agent = DisruptionRecoveryAgent()
    event = DisruptionEvent(
        title="Building B Maintenance",
        affected_rooms=["Room 202"]
    )
    plan = RecoveryPlan(
        plan_id="p-notif",
        disruption_id=event.id,
        timetable_version="v1.0",
        plan_title="Valid Recovery Plan",
        ranking_category="CLEAN_RECOVERY",
        changes=[
            RecoveryPlanChange(
                timetable_entry_id="2026-09-28_P1_8B",
                school_date="2026-09-28",
                old_teacher_id="Smith",
                new_teacher_id="Foster",
                old_room_id="Room 202",
                new_room_id="Science Lab 1",
                old_period_code="P1",
                new_period_code="P1"
            )
        ]
    )
    notif_count = agent._dispatch_notifications(plan, event, base_solver_input)
    assert notif_count >= 1

    mem = agent._record_decision_memory(plan, event, outcome="SUCCESS")
    assert mem["outcome"] == "SUCCESS"
    assert mem["disruption_event"] == "Building B Maintenance"
