import pytest
from app.agents.room_allocation_agent import RoomAllocationAgent, RoomDisruptionEvent
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, ScheduledEntryDTO
)

def create_room_agent_fixture():
    days = [SchoolDayDTO(date_str="2026-08-25", day_of_week=1, is_instructional=True)]
    periods = [
        PeriodDTO(id="p1", code="P1", name="Period 1", start_time="08:00:00", end_time="08:50:00", period_order=1),
        PeriodDTO(id="p2", code="P2", name="Period 2", start_time="09:00:00", end_time="09:50:00", period_order=2),
    ]
    sections = [
        SectionDTO(id="8A", name="8A", grade_level=8, student_count=25),
        SectionDTO(id="8B", name="8B", grade_level=8, student_count=25),
    ]
    courses = [
        CourseDTO(id="c_lit", code="LIT100", title="Literature", subject_id="subj_lit", periods_per_week=1),
        CourseDTO(id="c_sci", code="PHYS200", title="Physical Science", subject_id="subj_sci", periods_per_week=1, requires_lab=True, required_equipment=["Chemistry Benches"]),
    ]
    teachers = [
        TeacherDTO(id="Cooper", name="Cooper", employee_code="EMP1", department="English"),
        TeacherDTO(id="Ross", name="Ross", employee_code="EMP2", department="Science"),
    ]
    rooms = [
        RoomDTO(id="Room 201", room_number="Room 201", building="Humanities", capacity=30, room_type="STANDARD"),
        RoomDTO(id="Room 202", room_number="Room 202", building="Humanities", capacity=35, room_type="STANDARD"),
        RoomDTO(id="Lab 1", room_number="Lab 1", building="Science", capacity=30, room_type="LAB", equipment=["Chemistry Benches"]),
        RoomDTO(id="Lab 2", room_number="Lab 2", building="Science", capacity=30, room_type="LAB", equipment=["Chemistry Benches"]),
        RoomDTO(id="Room Small", room_number="Room Small", building="Humanities", capacity=15, room_type="STANDARD"),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Ross", subject_id="subj_sci"),
    ]
    solver_input = SolverInput(
        school_days=days, periods=periods, sections=sections, courses=courses,
        teachers=teachers, rooms=rooms, capabilities=capabilities, teacher_availability=[],
        room_availability=[], assignments=[], config=SolverConfig()
    )
    entries = [
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="8B", course_id="c_sci", teacher_id="Ross", room_id="Lab 1"),
    ]
    return solver_input, entries

def test_room_closure_reallocation():
    inp, entries = create_room_agent_fixture()
    agent = RoomAllocationAgent()
    event = RoomDisruptionEvent(
        room_id="Room 201",
        event_type="CLOSED",
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Renovation"
    )
    res = agent.process_room_disruption(event, inp, entries)
    assert res.affected_classes_count == 1
    assert len(res.requirements) == 1
    req = res.requirements[0]
    assert req.selected_candidate is not None
    assert req.selected_candidate.room_id in ("Room 202", "Lab 1", "Lab 2")

def test_equipment_failure_reallocation():
    inp, entries = create_room_agent_fixture()
    agent = RoomAllocationAgent()
    event = RoomDisruptionEvent(
        room_id="Lab 1",
        event_type="EQUIPMENT_FAILURE",
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Broken lab ventilation",
        required_equipment_impact=["Chemistry Benches"]
    )
    res = agent.process_room_disruption(event, inp, entries)
    assert res.affected_classes_count == 1
    req = res.requirements[0]
    assert req.selected_candidate is not None
    assert req.selected_candidate.room_id == "Lab 2"

def test_insufficient_capacity_room_rejected():
    inp, entries = create_room_agent_fixture()
    agent = RoomAllocationAgent()
    inp.sections[0].student_count = 40
    event = RoomDisruptionEvent(
        room_id="Room 201",
        event_type="MAINTENANCE",
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Water leak"
    )
    res = agent.process_room_disruption(event, inp, entries)
    assert res.status == "INFEASIBLE"

def test_multi_period_disruption_handling():
    inp, entries = create_room_agent_fixture()
    entries.append(ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"))
    agent = RoomAllocationAgent()
    event = RoomDisruptionEvent(
        room_id="Room 201",
        event_type="CLOSED",
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Emergency repair"
    )
    res = agent.process_room_disruption(event, inp, entries)
    assert res.affected_classes_count == 2
    assert len(res.requirements) == 2

def test_auto_execute_governance():
    inp, entries = create_room_agent_fixture()
    inp.rooms = [r for r in inp.rooms if r.id in ("Room 201", "Room 202")]
    agent = RoomAllocationAgent()
    event = RoomDisruptionEvent(
        room_id="Room 201",
        event_type="CLOSED",
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Maintenance"
    )
    res = agent.process_room_disruption(event, inp, entries)
    assert res.execution_mode == "AUTO_EXECUTE"
    assert res.status == "REALLOCATED"
