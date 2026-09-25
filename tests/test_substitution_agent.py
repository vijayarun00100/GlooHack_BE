import pytest
from app.agents.teacher_substitution_agent import TeacherSubstitutionAgent
from app.services.email_ingestion import EmailIngestionService
from app.services.absence_extractor import AbsenceExtractionService
from app.services.teacher_matching import TeacherMatchingService
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, ScheduledEntryDTO
)

def create_agent_fixture():
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
        CourseDTO(id="c_math", code="MATH101", title="Math", subject_id="subj_math", periods_per_week=1),
    ]
    teachers = [
        TeacherDTO(id="Cooper", name="Cooper", employee_code="EMP-COOPER", department="English"),
        TeacherDTO(id="Smith", name="Smith", employee_code="EMP-SMITH", department="Math"),
        TeacherDTO(id="Blake", name="Blake", employee_code="EMP-BLAKE", department="English"),
    ]
    rooms = [
        RoomDTO(id="Room 201", room_number="Room 201", building="Humanities", capacity=30),
        RoomDTO(id="Room 202", room_number="Room 202", building="Humanities", capacity=30),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Blake", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Smith", subject_id="subj_math"),
    ]
    solver_input = SolverInput(
        school_days=days, periods=periods, sections=sections, courses=courses,
        teachers=teachers, rooms=rooms, capabilities=capabilities, teacher_availability=[],
        room_availability=[], assignments=[], config=SolverConfig()
    )
    entries = [
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201"),
        ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="8B", course_id="c_math", teacher_id="Smith", room_id="Room 202"),
    ]
    return solver_input, entries

def test_mime_email_parsing():
    raw_mime = """From: Sarah Cooper <cooper@school.edu>
To: admin@school.edu
Subject: Absence Notice for Aug 25
Date: Mon, 24 Aug 2026 14:00:00 -0400
Message-ID: <msg123@school.edu>

Hi Admin,
I will be unavailable on August 25 due to a doctor appointment. Please find a substitute.
Regards,
Cooper
"""
    ingester = EmailIngestionService()
    parsed = ingester.parse_mime_email(raw_mime)
    assert parsed.sender_email == "cooper@school.edu"
    assert parsed.sender_name == "Sarah Cooper"
    assert "doctor appointment" in parsed.body_text

def test_absence_extraction_intent():
    ingester = EmailIngestionService()
    extractor = AbsenceExtractionService()
    raw_mime = "From: cooper@school.edu\nSubject: Absence\n\nI will be sick on August 25."
    parsed = ingester.parse_mime_email(raw_mime)
    extracted = extractor.extract_absence_intent(parsed)
    assert extracted.intent == "TEACHER_ABSENCE"
    assert extracted.absence_date == "2026-08-25"
    assert extracted.reason == "Sick leave"

def test_teacher_matching():
    inp, _ = create_agent_fixture()
    matcher = TeacherMatchingService(inp.teachers)
    matched, reason = matcher.match_teacher("cooper@school.edu", "Sarah Cooper")
    assert matched is not None
    assert matched.id == "Cooper"
    assert "MATCH" in reason

def test_substitution_agent_pipeline():
    inp, entries = create_agent_fixture()
    agent = TeacherSubstitutionAgent()
    raw_email = "From: cooper@school.edu\nSubject: Absence Notice\n\nI am sick on August 25."
    res = agent.process_absence_email(raw_email, inp, entries)
    assert res.absent_teacher_id == "Cooper"
    assert res.affected_classes_count == 1
    assert len(res.requirements) == 1
    req = res.requirements[0]
    assert req.selected_candidate is not None
    assert req.selected_candidate.teacher_id == "Blake"

def test_cancellation_email_handling():
    inp, entries = create_agent_fixture()
    agent = TeacherSubstitutionAgent()
    cancel_email = "From: cooper@school.edu\nSubject: Cancel absence\n\nPlease ignore my previous email. I will be available on August 25."
    res = agent.process_absence_email(cancel_email, inp, entries)
    assert res.status == "CANCELLED"
    assert res.affected_classes_count == 0

def test_unmapped_teacher_requires_review():
    inp, entries = create_agent_fixture()
    agent = TeacherSubstitutionAgent()
    unknown_email = "From: unknown@school.edu\nSubject: Absence\n\nI am sick on August 25."
    res = agent.process_absence_email(unknown_email, inp, entries)
    assert res.status == "REQUIRES_REVIEW"
    assert res.execution_mode == "REVIEW"
