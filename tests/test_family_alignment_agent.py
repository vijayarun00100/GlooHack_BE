import pytest
import copy
from app.agents.family_alignment_agent import (
    FamilyAlignmentAgent, FamilyAlignmentRequest, StudentDaySchedule, FamilyAlignmentPlan, AlignmentChangeItem
)
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, ScheduledEntryDTO
)

@pytest.fixture
def base_solver_input():
    days = [
        SchoolDayDTO(date_str="2026-10-05", day_of_week=1, is_instructional=True),
        SchoolDayDTO(date_str="2026-10-06", day_of_week=2, is_instructional=True),
        SchoolDayDTO(date_str="2026-10-07", day_of_week=3, is_instructional=True),
        SchoolDayDTO(date_str="2026-10-08", day_of_week=4, is_instructional=True),
        SchoolDayDTO(date_str="2026-10-09", day_of_week=5, is_instructional=True),
    ]
    periods = [
        PeriodDTO(id="p1", code="P1", name="Period 1", start_time="08:00:00", end_time="08:50:00", period_order=1),
    ]
    sections = [
        SectionDTO(id="7A", name="7A", grade_level=7, student_count=20),
        SectionDTO(id="9A", name="9A", grade_level=9, student_count=25),
        SectionDTO(id="11A", name="11A", grade_level=11, student_count=25),
    ]
    courses = [
        CourseDTO(id="c_lit", code="LIT100", title="Literature", subject_id="subj_lit", periods_per_week=2),
    ]
    teachers = [
        TeacherDTO(id="Cooper", name="Cooper", employee_code="EMP-COOPER", department="English"),
    ]
    rooms = [
        RoomDTO(id="Room 201", room_number="Room 201", building="Building A", capacity=30),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
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
def two_sibling_schedules():
    return [
        StudentDaySchedule(student_id="s1", student_name="Student A", grade_section="7A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="Student A", grade_section="7A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="Student A", grade_section="7A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="s1", student_name="Student A", grade_section="7A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="Student A", grade_section="7A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
        
        StudentDaySchedule(student_id="s2", student_name="Student B", grade_section="9A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="Student B", grade_section="9A", school_date="2026-10-06", day_of_week="TUE", attendance_state="HOME"),
        StudentDaySchedule(student_id="s2", student_name="Student B", grade_section="9A", school_date="2026-10-07", day_of_week="WED", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="Student B", grade_section="9A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="Student B", grade_section="9A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
    ]

@pytest.fixture
def three_sibling_schedules(two_sibling_schedules):
    sch = copy.deepcopy(two_sibling_schedules)
    sch.extend([
        StudentDaySchedule(student_id="s3", student_name="Student C", grade_section="11A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s3", student_name="Student C", grade_section="11A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s3", student_name="Student C", grade_section="11A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="s3", student_name="Student C", grade_section="11A", school_date="2026-10-08", day_of_week="THU", attendance_state="HOME"),
        StudentDaySchedule(student_id="s3", student_name="Student C", grade_section="11A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
    ])
    return sch

def test_two_sibling_alignment(base_solver_input, two_sibling_schedules):
    agent = FamilyAlignmentAgent()
    req = FamilyAlignmentRequest(
        family_id="fam-2",
        family_name="Test Family 2",
        student_ids=["s1", "s2"]
    )
    result = agent.process_alignment_request(req, base_solver_input, [], two_sibling_schedules)
    assert result.siblings_count == 2
    assert result.alignment_after >= result.alignment_before
    assert len(result.plans) >= 1

def test_three_sibling_alignment(base_solver_input, three_sibling_schedules):
    agent = FamilyAlignmentAgent()
    req = FamilyAlignmentRequest(
        family_id="fam-3",
        family_name="Arun Family",
        student_ids=["s1", "s2", "s3"]
    )
    result = agent.process_alignment_request(req, base_solver_input, [], three_sibling_schedules)
    assert result.siblings_count == 3
    assert result.alignment_after >= 4

def test_already_aligned_family(base_solver_input):
    agent = FamilyAlignmentAgent()
    aligned_schedules = [
        StudentDaySchedule(student_id="s1", student_name="A", grade_section="7A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="B", grade_section="9A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="A", grade_section="7A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="B", grade_section="9A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="A", grade_section="7A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="s2", student_name="B", grade_section="9A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="s1", student_name="A", grade_section="7A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s2", student_name="B", grade_section="9A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="s1", student_name="A", grade_section="7A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
        StudentDaySchedule(student_id="s2", student_name="B", grade_section="9A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
    ]
    req = FamilyAlignmentRequest(family_id="fam-aligned", student_ids=["s1", "s2"])
    result = agent.process_alignment_request(req, base_solver_input, [], aligned_schedules)
    assert result.status == "RESOLVED"
    assert result.alignment_after == 5
    assert len(result.plans) == 0

def test_locked_day_preservation(base_solver_input, two_sibling_schedules):
    agent = FamilyAlignmentAgent()
    sch = copy.deepcopy(two_sibling_schedules)
    # Lock Wednesday for Student B due to mandatory Chemistry Lab Exam
    for item in sch:
        if item.student_id == "s2" and item.day_of_week == "WED":
            item.is_locked = True
            item.lock_reason = "Mandatory Chemistry Lab Exam"

    plan = FamilyAlignmentPlan(
        plan_id="p-locked",
        request_id="r-locked",
        family_id="fam-locked",
        timetable_version="v1.0",
        changes=[
            AlignmentChangeItem(
                student_id="s2",
                student_name="Student B",
                grade_section="9A",
                school_date="2026-10-07",
                day_of_week="WED",
                old_state="CAMPUS",
                new_state="HOME",
                change_reason="Test modification of locked day"
            )
        ]
    )
    success, updated, err = agent.execute_alignment_plan(plan, base_solver_input, sch, current_version="v1.0")
    assert success is False
    assert "locked academic day" in err.lower()
    assert plan.status == "INVALID"

def test_timetable_version_conflict_rollback(base_solver_input, two_sibling_schedules):
    agent = FamilyAlignmentAgent()
    plan = FamilyAlignmentPlan(
        plan_id="p-stale",
        timetable_version="v1.0",
        changes=[]
    )
    success, updated, err = agent.execute_alignment_plan(plan, base_solver_input, two_sibling_schedules, current_version="v2.0")
    assert success is False
    assert "version mismatch" in err.lower()
    assert plan.status == "STALE"

def test_notifications_and_decision_memory(base_solver_input, two_sibling_schedules):
    agent = FamilyAlignmentAgent()
    req = FamilyAlignmentRequest(family_id="fam-mem", student_ids=["s1", "s2"])
    plan = FamilyAlignmentPlan(
        plan_id="p-mem",
        request_id=req.id,
        family_id="fam-mem",
        timetable_version="v1.0",
        plan_title="Full Alignment",
        ranking_category="FULL_ALIGNMENT",
        changes=[
            AlignmentChangeItem(
                student_id="s2",
                student_name="Student B",
                grade_section="9A",
                school_date="2026-10-06",
                day_of_week="TUE",
                old_state="HOME",
                new_state="CAMPUS"
            )
        ]
    )
    notif_count = agent._dispatch_notifications(plan, req)
    assert notif_count >= 2

    mem = agent._record_decision_memory(plan, req, outcome="SUCCESS")
    assert mem["request_type"] == "FAMILY_DAY_ALIGNMENT"
    assert mem["outcome"] == "SUCCESS"
