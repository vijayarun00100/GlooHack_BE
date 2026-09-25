import pytest
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, TeacherAvailabilityDTO,
    RoomAvailabilityDTO, AssignmentRequirementDTO, ScheduledEntryDTO, SolverStatus
)
from app.solver.timetable_solver import TimetableSolver
from app.solver.conflict_detector import ConflictDetector

def create_base_fixture():
    days = [SchoolDayDTO(date_str="2026-08-25", day_of_week=1, is_instructional=True)]
    periods = [
        PeriodDTO(id="p1", code="P1", name="Period 1", start_time="08:00:00", end_time="08:50:00", period_order=1),
        PeriodDTO(id="p2", code="P2", name="Period 2", start_time="09:00:00", end_time="09:50:00", period_order=2),
    ]
    sections = [
        SectionDTO(id="sec8A", name="8A", grade_level=8, student_count=25),
        SectionDTO(id="sec8B", name="8B", grade_level=8, student_count=25),
    ]
    courses = [
        CourseDTO(id="c_lit", code="LIT100", title="Literature", subject_id="subj_lit", periods_per_week=1),
        CourseDTO(id="c_math", code="MATH101", title="Math", subject_id="subj_math", periods_per_week=1),
    ]
    teachers = [
        TeacherDTO(id="t_cooper", name="Cooper", employee_code="EMP1", department="English"),
        TeacherDTO(id="t_smith", name="Smith", employee_code="EMP2", department="Math"),
    ]
    rooms = [
        RoomDTO(id="r201", room_number="Room 201", building="A", capacity=30, room_type="STANDARD"),
        RoomDTO(id="r202", room_number="Room 202", building="A", capacity=30, room_type="STANDARD"),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="t_cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="t_smith", subject_id="subj_math"),
    ]
    assignments = [
        AssignmentRequirementDTO(id="asgn1", section_id="sec8A", course_id="c_lit", teacher_id="t_cooper", periods_required=1),
        AssignmentRequirementDTO(id="asgn2", section_id="sec8B", course_id="c_math", teacher_id="t_smith", periods_required=1),
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
        assignments=assignments,
        config=SolverConfig(time_limit_seconds=2.0)
    )

def test_1_teacher_cannot_overlap():
    inp = create_base_fixture()
    inp.periods = [inp.periods[0]]
    inp.assignments = [
        AssignmentRequirementDTO(id="asgn1", section_id="sec8A", course_id="c_lit", teacher_id="t_cooper", periods_required=1),
        AssignmentRequirementDTO(id="asgn2", section_id="sec8B", course_id="c_lit", teacher_id="t_cooper", periods_required=1),
    ]
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_2_room_cannot_overlap():
    inp = create_base_fixture()
    inp.periods = [inp.periods[0]]
    inp.rooms = [inp.rooms[0]]
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_3_section_cannot_overlap():
    inp = create_base_fixture()
    inp.periods = [inp.periods[0]]
    inp.assignments = [
        AssignmentRequirementDTO(id="asgn1", section_id="sec8A", course_id="c_lit", teacher_id="t_cooper", periods_required=1),
        AssignmentRequirementDTO(id="asgn2", section_id="sec8A", course_id="c_math", teacher_id="t_smith", periods_required=1),
    ]
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_4_room_capacity_is_enforced():
    inp = create_base_fixture()
    inp.sections[0].student_count = 50  # Exceeds room capacities of 30
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_5_required_equipment_is_enforced():
    inp = create_base_fixture()
    inp.courses[0].required_equipment = ["Chemistry Benches"]
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_6_teacher_qualification_is_enforced():
    inp = create_base_fixture()
    inp.assignments[0].course_id = "c_math"  # Cooper assigned to math without capability
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_7_teacher_availability_is_enforced():
    inp = create_base_fixture()
    inp.periods = [inp.periods[0]]
    inp.teacher_availability = [
        TeacherAvailabilityDTO(teacher_id="t_cooper", day_of_week=1, period_code="P1", is_available=False)
    ]
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_8_room_availability_is_enforced():
    inp = create_base_fixture()
    inp.rooms[0].status = "UNDER_MAINTENANCE"
    inp.rooms[1].status = "UNDER_MAINTENANCE"
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_9_course_period_requirements_satisfied():
    inp = create_base_fixture()
    res = TimetableSolver().solve(inp)
    assert res.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert len(res.timetable_entries) == 2

def test_10_soft_constraints_affect_objective_score():
    inp = create_base_fixture()
    # All periods for Cooper have preference weight < 1.0 to ensure penalty is incurred
    inp.teacher_availability = [
        TeacherAvailabilityDTO(teacher_id="t_cooper", day_of_week=1, period_code="P1", preference_weight=0.2),
        TeacherAvailabilityDTO(teacher_id="t_cooper", day_of_week=1, period_code="P2", preference_weight=0.2),
    ]
    res = TimetableSolver().solve(inp)
    assert res.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert res.objective_value > 0

def test_11_conflict_detector_identifies_invalid_timetable():
    inp = create_base_fixture()
    detector = ConflictDetector()
    invalid_entries = [
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="sec8A", course_id="c_lit", teacher_id="t_cooper", room_id="r201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="sec8B", course_id="c_math", teacher_id="t_cooper", room_id="r202"),
    ]
    report = detector.validate(inp, invalid_entries)
    assert report.is_valid is False
    assert any(c.conflict_type == "TEACHER_OVERLAP" for c in report.hard_conflicts)

def test_12_valid_timetable_passes_validation():
    inp = create_base_fixture()
    res = TimetableSolver().solve(inp)
    detector = ConflictDetector()
    report = detector.validate(inp, res.timetable_entries)
    assert report.is_valid is True

def test_13_infeasible_problem_returns_infeasible_status():
    inp = create_base_fixture()
    inp.rooms = []
    res = TimetableSolver().solve(inp)
    assert res.status == SolverStatus.INFEASIBLE

def test_14_deterministic_solver_reproducibility():
    inp1 = create_base_fixture()
    inp2 = create_base_fixture()
    res1 = TimetableSolver().solve(inp1)
    res2 = TimetableSolver().solve(inp2)
    assert len(res1.timetable_entries) == len(res2.timetable_entries)
    assert res1.objective_value == res2.objective_value
