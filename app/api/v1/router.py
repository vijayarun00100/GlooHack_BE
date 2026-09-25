from fastapi import APIRouter, HTTPException, Status, Query
from datetime import date
from typing import Any
from app.schemas.domain import (
    UserResponse, TeacherResponse, StudentResponse, GradeResponse,
    SectionResponse, SubjectResponse, CourseResponse, RoomResponse,
    RoomUtilizationResponse, TimetableEntryResponse, GenerateTimetableRequest,
    SolverResultResponse, ConflictReportResponse, DisruptionCreate, DisruptionResponse,
    RecoveryPlanResponse, AgentEventResponse, AgentRunResponse,
    AgentDecisionResponse, ApprovalRequestResponse, DecisionMemoryCreate
)
from app.services.timetable_service import TimetableService
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, TeacherAvailabilityDTO,
    RoomAvailabilityDTO, AssignmentRequirementDTO, ScheduledEntryDTO
)

api_router = APIRouter()
timetable_service = TimetableService()

# Simulated in-memory database store for Phase 1 demo endpoints
DEMO_TIMETABLE_ENTRIES: list[ScheduledEntryDTO] = [
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8A", course_id="c_lit", teacher_id="Cooper", room_id="Room 201", color_code="blue"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="8B", course_id="c_lit", teacher_id="Cooper", room_id="Room 207", color_code="blue"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P1", period_id="p1", section_id="7A", course_id="c_alg", teacher_id="Foster", room_id="Room 101", color_code="teal"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="8A", course_id="c_sci", teacher_id="Ross", room_id="Science Lab 1", color_code="green"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="7A", course_id="c_lit", teacher_id="Cooper", room_id="Room 102", color_code="blue"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P2", period_id="p2", section_id="9A", course_id="c_phy", teacher_id="Yuen", room_id="Science Lab 3", color_code="teal", flag="updated"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P3", period_id="p3", section_id="8A", course_id="c_alg", teacher_id="Smith", room_id="Room 202", color_code="teal"),
    ScheduledEntryDTO(school_date="2026-08-25", period_code="P3", period_id="p3", section_id="8B", course_id="c_alg", teacher_id="Smith", room_id="Room 208", color_code="teal", flag="warning"),
]

def build_default_solver_input() -> SolverInput:
    days = [
        SchoolDayDTO(date_str="2026-08-25", day_of_week=1, is_instructional=True),
        SchoolDayDTO(date_str="2026-08-26", day_of_week=2, is_instructional=True),
        SchoolDayDTO(date_str="2026-08-27", day_of_week=3, is_instructional=True),
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
        RoomDTO(id="Room 201", room_number="Room 201", building="Humanities", capacity=30),
        RoomDTO(id="Room 207", room_number="Room 207", building="Humanities", capacity=30),
        RoomDTO(id="Science Lab 1", room_number="Science Lab 1", building="Science", capacity=30, room_type="LAB"),
        RoomDTO(id="Room 202", room_number="Room 202", building="Humanities", capacity=35),
    ]
    capabilities = [
        TeacherCapabilityDTO(teacher_id="Cooper", subject_id="subj_lit"),
        TeacherCapabilityDTO(teacher_id="Ross", subject_id="subj_sci"),
        TeacherCapabilityDTO(teacher_id="Smith", subject_id="subj_math"),
        TeacherCapabilityDTO(teacher_id="Foster", subject_id="subj_math"),
    ]
    assignments = [
        AssignmentRequirementDTO(id="a1", section_id="8A", course_id="c_lit", teacher_id="Cooper", periods_required=2),
        AssignmentRequirementDTO(id="a2", section_id="8B", course_id="c_lit", teacher_id="Cooper", periods_required=2),
        AssignmentRequirementDTO(id="a3", section_id="8A", course_id="c_sci", teacher_id="Ross", periods_required=2),
        AssignmentRequirementDTO(id="a4", section_id="8A", course_id="c_alg", teacher_id="Smith", periods_required=2),
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
        config=SolverConfig(time_limit_seconds=5.0)
    )

# ==========================================
# TIMETABLE & SOLVER ENDPOINTS
# ==========================================

@api_router.get("/timetable", response_model=list[TimetableEntryResponse], tags=["Timetable"])
def get_timetable():
    return DEMO_TIMETABLE_ENTRIES

@api_router.get("/timetable/date/{school_date}", response_model=list[TimetableEntryResponse], tags=["Timetable"])
def get_timetable_by_date(school_date: str):
    filtered = [e for e in DEMO_TIMETABLE_ENTRIES if e.school_date == school_date]
    return filtered if filtered else DEMO_TIMETABLE_ENTRIES

@api_router.get("/timetable/section/{section_id}", response_model=list[TimetableEntryResponse], tags=["Timetable"])
def get_timetable_by_section(section_id: str):
    return [e for e in DEMO_TIMETABLE_ENTRIES if e.section_id == section_id]

@api_router.get("/timetable/teacher/{teacher_id}", response_model=list[TimetableEntryResponse], tags=["Timetable"])
def get_timetable_by_teacher(teacher_id: str):
    return [e for e in DEMO_TIMETABLE_ENTRIES if e.teacher_id == teacher_id]

@api_router.get("/timetable/versions", tags=["Timetable"])
def list_timetable_versions():
    return [
        {"id": "v1", "title": "Full School Schedule", "year": "2026–2027", "term": "Fall Term", "status": "DRAFT", "updated": "Sep 10, 2026"},
        {"id": "v2", "title": "Full School Schedule", "year": "2026–2027", "term": "Spring Term", "status": "PUBLISHED", "updated": "Aug 10, 2026"},
    ]

@api_router.post("/timetable/generate", response_model=SolverResultResponse, tags=["Timetable Solver"])
def generate_timetable(req: GenerateTimetableRequest):
    inp = build_default_solver_input()
    inp.config.time_limit_seconds = req.time_limit_seconds
    res = timetable_service.generate_timetable(inp)
    
    if res.timetable_entries:
        global DEMO_TIMETABLE_ENTRIES
        DEMO_TIMETABLE_ENTRIES = res.timetable_entries

    return SolverResultResponse(
        status=res.status.value,
        timetable_entries=[TimetableEntryResponse(**e.__dict__) for e in res.timetable_entries],
        objective_value=res.objective_value,
        hard_constraint_violations=res.hard_constraint_violations,
        soft_constraint_penalties=res.soft_constraint_penalties,
        solver_runtime_ms=res.solver_runtime_ms,
        explanation=res.explanation
    )

@api_router.post("/timetable/validate", response_model=ConflictReportResponse, tags=["Timetable Solver"])
def validate_timetable():
    inp = build_default_solver_input()
    report = timetable_service.validate_timetable(inp, DEMO_TIMETABLE_ENTRIES)
    return ConflictReportResponse(
        is_valid=report.is_valid,
        total_conflicts=report.total_conflicts,
        hard_conflicts=[c.__dict__ for c in report.hard_conflicts],
        soft_conflicts=[c.__dict__ for c in report.soft_conflicts]
    )

# ==========================================
# ROOMS & UTILIZATION ENDPOINTS
# ==========================================

@api_router.get("/rooms", response_model=list[RoomResponse], tags=["Rooms"])
def list_rooms():
    return [
        RoomResponse(id="r201", room_number="Room 201", building="Humanities Wing", capacity=30, room_type="STANDARD", status="AVAILABLE"),
        RoomResponse(id="r202", room_number="Room 202", building="Humanities Wing", capacity=35, room_type="STANDARD", status="AVAILABLE"),
        RoomResponse(id="r207", room_number="Room 207", building="Humanities Wing", capacity=25, room_type="STANDARD", status="AVAILABLE"),
        RoomResponse(id="lab1", room_number="Science Lab 1", building="Science Wing", capacity=30, room_type="LAB", status="AVAILABLE"),
    ]

@api_router.get("/rooms/{room_id}/utilization", response_model=RoomUtilizationResponse, tags=["Rooms"])
def get_room_utilization(room_id: str, date_str: str = Query("2026-08-25")):
    entries_dict = [e.__dict__ for e in DEMO_TIMETABLE_ENTRIES]
    res = timetable_service.calculate_room_utilization(room_id, date_str, total_periods=5, scheduled_entries=entries_dict)
    return RoomUtilizationResponse(**res)

# ==========================================
# USERS & ACADEMIC
# ==========================================

@api_router.get("/users", tags=["Users"])
def list_users():
    return []

@api_router.get("/students", tags=["Users"])
def list_students():
    return []

@api_router.get("/teachers", tags=["Users"])
def list_teachers():
    return []

@api_router.get("/academic/grades", tags=["Academic"])
def list_grades():
    return []

@api_router.get("/academic/sections", tags=["Academic"])
def list_sections():
    return []

# ==========================================
# DISRUPTIONS & AGENTS
# ==========================================

@api_router.get("/disruptions", response_model=list[DisruptionResponse], tags=["Disruptions"])
def list_disruptions():
    return []

@api_router.get("/agents/events", response_model=list[AgentEventResponse], tags=["Agents"])
def list_agent_events():
    return []

@api_router.get("/agents/runs", response_model=list[AgentRunResponse], tags=["Agents"])
def list_agent_runs():
    return []

@api_router.get("/approvals/pending", response_model=list[ApprovalRequestResponse], tags=["Approvals"])
def list_pending_approvals():
    return []
