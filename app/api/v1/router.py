from fastapi import APIRouter, HTTPException, Status, Query
from datetime import date
from typing import Any
import uuid
from app.schemas.domain import (
    UserResponse, TeacherResponse, StudentResponse, GradeResponse,
    SectionResponse, SubjectResponse, CourseResponse, RoomResponse,
    RoomUtilizationResponse, TimetableEntryResponse, GenerateTimetableRequest,
    SolverResultResponse, ConflictReportResponse, IngestEmailRequest,
    SubstitutionAgentResultResponse, RoomDisruptionRequest, RoomAllocationAgentResultResponse,
    ApprovalRequestResponse, AgentEventResponse, AgentRunResponse, AgentDecisionResponse,
    CampusDisruptionRequest, RecoveryPlanResponse, DisruptionRecoveryResultResponse,
    FamilyAlignmentRequestSchema, FamilyAlignmentPlanResponse, FamilyAlignmentResultResponse
)
from app.services.timetable_service import TimetableService
from app.agents.teacher_substitution_agent import TeacherSubstitutionAgent
from app.agents.room_allocation_agent import RoomAllocationAgent, RoomDisruptionEvent
from app.agents.disruption_recovery_agent import DisruptionRecoveryAgent, DisruptionEvent, RecoveryPlan
from app.agents.family_alignment_agent import FamilyAlignmentAgent, FamilyAlignmentRequest, StudentDaySchedule, FamilyAlignmentPlan
from app.solver.models import (
    SolverInput, SolverConfig, SchoolDayDTO, PeriodDTO, SectionDTO,
    CourseDTO, TeacherDTO, RoomDTO, TeacherCapabilityDTO, TeacherAvailabilityDTO,
    RoomAvailabilityDTO, AssignmentRequirementDTO, ScheduledEntryDTO
)

api_router = APIRouter()
timetable_service = TimetableService()
substitution_agent = TeacherSubstitutionAgent()
room_agent = RoomAllocationAgent()
disruption_agent = DisruptionRecoveryAgent()
family_agent = FamilyAlignmentAgent()

DEMO_CAMPUS_DISRUPTIONS: list[dict[str, Any]] = []
DEMO_RECOVERY_PLANS: dict[str, Any] = {}
DEMO_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "family-001",
        "family_name": "Arun Family",
        "requested_by": "parent-001",
        "students": [
            {"student_id": "student-101", "student_name": "Student A", "grade_section": "7A"},
            {"student_id": "student-202", "student_name": "Student B", "grade_section": "9A"},
            {"student_id": "student-303", "student_name": "Student C", "grade_section": "11A"}
        ]
    }
]
DEMO_ALIGNMENT_REQUESTS: list[dict[str, Any]] = []
DEMO_ALIGNMENT_PLANS: dict[str, Any] = {}



# In-memory stores for Phase 1, 2 & 3 demo endpoints
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

DEMO_ABSENCES = []
DEMO_ROOM_DISRUPTIONS = []

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
# ROOM ALLOCATION AGENT ENDPOINTS
# ==========================================

@api_router.post("/room-disruptions", response_model=RoomAllocationAgentResultResponse, tags=["Room Allocation Agent"])
def create_room_disruption(req: RoomDisruptionRequest):
    event = RoomDisruptionEvent(**req.__dict__)
    inp = build_default_solver_input()
    res = room_agent.process_room_disruption(event, inp, DEMO_TIMETABLE_ENTRIES)
    DEMO_ROOM_DISRUPTIONS.append(res)
    return res

@api_router.get("/room-disruptions", tags=["Room Allocation Agent"])
def list_room_disruptions():
    return DEMO_ROOM_DISRUPTIONS

@api_router.get("/room-disruptions/{disruption_id}/affected-classes", tags=["Room Allocation Agent"])
def get_room_affected_classes(disruption_id: str):
    found = next((r for r in DEMO_ROOM_DISRUPTIONS if r.agent_run_id == disruption_id), None)
    if not found:
        return []
    return found.requirements

@api_router.post("/room-disruptions/{disruption_id}/approve", tags=["Room Allocation Agent"])
def approve_room_reallocation(disruption_id: str):
    found = next((r for r in DEMO_ROOM_DISRUPTIONS if r.agent_run_id == disruption_id or r.approval_request_id == disruption_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Room disruption request not found")

    # Commit approved room reallocations
    for req in found.requirements:
        if req.selected_candidate:
            for entry in DEMO_TIMETABLE_ENTRIES:
                if entry.room_id == found.disrupted_room_id and entry.period_code == req.period_code and entry.school_date == req.school_date:
                    entry.room_id = req.selected_candidate.room_id
                    entry.flag = "updated"

    found.status = "REALLOCATED"
    found.execution_mode = "APPROVED"
    return {"status": "APPROVED", "disruption_id": disruption_id, "message": "Room reallocations committed to active timetable."}

@api_router.post("/room-disruptions/{disruption_id}/reject", tags=["Room Allocation Agent"])
def reject_room_reallocation(disruption_id: str):
    found = next((r for r in DEMO_ROOM_DISRUPTIONS if r.agent_run_id == disruption_id or r.approval_request_id == disruption_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Room disruption request not found")
    found.status = "REJECTED"
    return {"status": "REJECTED", "disruption_id": disruption_id, "message": "Room reallocation proposal rejected."}

@api_router.post("/agents/room-allocation/run", response_model=RoomAllocationAgentResultResponse, tags=["Agents"])
def run_room_allocation_agent(room_id: str = "Room 201", event_type: str = "CLOSED"):
    event = RoomDisruptionEvent(
        room_id=room_id,
        event_type=event_type,
        start_date="2026-08-25",
        end_date="2026-08-25",
        reason="Facility renovation"
    )
    inp = build_default_solver_input()
    return room_agent.process_room_disruption(event, inp, DEMO_TIMETABLE_ENTRIES)

# ==========================================
# TEACHER SUBSTITUTION ENDPOINTS
# ==========================================

@api_router.post("/teacher-absences/ingest", response_model=SubstitutionAgentResultResponse, tags=["Teacher Substitution"])
def ingest_teacher_absence_email(req: IngestEmailRequest):
    inp = build_default_solver_input()
    res = substitution_agent.process_absence_email(req.raw_email, inp, DEMO_TIMETABLE_ENTRIES)
    DEMO_ABSENCES.append(res)
    return res

@api_router.get("/teacher-absences", tags=["Teacher Substitution"])
def list_teacher_absences():
    return DEMO_ABSENCES

@api_router.get("/teacher-absences/{absence_id}/affected-classes", tags=["Teacher Substitution"])
def get_affected_classes(absence_id: str):
    found = next((a for a in DEMO_ABSENCES if a.agent_run_id == absence_id), None)
    if not found:
        return []
    return found.requirements

@api_router.post("/teacher-absences/{absence_id}/approve", tags=["Teacher Substitution"])
def approve_substitution(absence_id: str):
    found = next((a for a in DEMO_ABSENCES if a.agent_run_id == absence_id or a.approval_request_id == absence_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Absence substitution request not found")
    for req in found.requirements:
        if req.selected_candidate:
            for entry in DEMO_TIMETABLE_ENTRIES:
                if entry.teacher_id == found.absent_teacher_id and entry.period_code == req.period_code and entry.school_date == found.absence_date:
                    entry.teacher_id = req.selected_candidate.teacher_id
                    entry.flag = "updated"
    found.status = "RESOLVED"
    found.execution_mode = "APPROVED"
    return {"status": "APPROVED", "absence_id": absence_id, "message": "Substitutions committed to timetable version."}

@api_router.post("/teacher-absences/{absence_id}/reject", tags=["Teacher Substitution"])
def reject_substitution(absence_id: str):
    found = next((a for a in DEMO_ABSENCES if a.agent_run_id == absence_id or a.approval_request_id == absence_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Absence substitution request not found")
    found.status = "REJECTED"
    return {"status": "REJECTED", "absence_id": absence_id, "message": "Substitution proposal rejected."}

@api_router.post("/teacher-absences/{absence_id}/cancel", tags=["Teacher Substitution"])
def cancel_absence(absence_id: str):
    found = next((a for a in DEMO_ABSENCES if a.agent_run_id == absence_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Absence request not found")
    found.status = "CANCELLED"
    return {"status": "CANCELLED", "absence_id": absence_id, "message": "Absence event cancelled."}

@api_router.post("/agents/teacher-substitution/run", response_model=SubstitutionAgentResultResponse, tags=["Agents"])
def run_teacher_substitution_agent(raw_email: str = "Hi Admin, I will be absent tomorrow due to a doctor appointment. Regards, Cooper"):
    inp = build_default_solver_input()
    res = substitution_agent.process_absence_email(raw_email, inp, DEMO_TIMETABLE_ENTRIES)
    return res

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

@api_router.get("/disruptions", tags=["Disruptions"])
def list_disruptions():
    return DEMO_ROOM_DISRUPTIONS

@api_router.get("/agents/events", response_model=list[AgentEventResponse], tags=["Agents"])
def list_agent_events():
    return []

@api_router.get("/agents/runs", response_model=list[AgentRunResponse], tags=["Agents"])
def list_agent_runs():
    return []

@api_router.get("/approvals/pending", response_model=list[ApprovalRequestResponse], tags=["Approvals"])
def list_pending_approvals():
    return []

# ==========================================
# PHASE 4 — DISRUPTION RECOVERY AGENT ENDPOINTS
# ==========================================

@api_router.post("/disruptions", tags=["Disruption Recovery"])
def create_disruption(req: CampusDisruptionRequest):
    event_id = str(uuid.uuid4())
    disruption = {
        "id": event_id,
        "event_type": req.event_type,
        "title": req.title,
        "description": req.description,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "start_period": req.start_period,
        "end_period": req.end_period,
        "affected_rooms": req.affected_rooms,
        "affected_teachers": req.affected_teachers,
        "affected_sections": req.affected_sections,
        "severity": req.severity,
        "source": req.source,
        "status": "OPEN",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    DEMO_CAMPUS_DISRUPTIONS.append(disruption)
    return disruption

@api_router.get("/disruptions", tags=["Disruption Recovery"])
def get_all_disruptions():
    return DEMO_CAMPUS_DISRUPTIONS

@api_router.get("/disruptions/{disruption_id}", tags=["Disruption Recovery"])
def get_disruption_by_id(disruption_id: str):
    dis = next((d for d in DEMO_CAMPUS_DISRUPTIONS if d["id"] == disruption_id), None)
    if not dis:
        # Return fallback demo disruption if not found
        return {
            "id": disruption_id,
            "event_type": "CAMPUS_DISRUPTION",
            "title": "Building B Closure",
            "description": "Building B is unavailable due to emergency maintenance.",
            "start_date": "2026-08-25",
            "end_date": "2026-08-25",
            "start_period": "P1",
            "end_period": "P5",
            "affected_rooms": ["Room 201"],
            "affected_teachers": ["Cooper"],
            "affected_sections": ["8A", "8B"],
            "severity": "HIGH",
            "source": "ADMIN",
            "status": "OPEN"
        }
    return dis

@api_router.get("/disruptions/{disruption_id}/affected-classes", tags=["Disruption Recovery"])
def get_disruption_affected_classes(disruption_id: str):
    dis = next((d for d in DEMO_CAMPUS_DISRUPTIONS if d["id"] == disruption_id), None)
    affected_rooms = dis["affected_rooms"] if dis else ["Room 201"]
    affected_teachers = dis["affected_teachers"] if dis else ["Cooper"]
    affected_sections = dis["affected_sections"] if dis else ["8A", "8B"]

    affected = [
        e.__dict__ for e in DEMO_TIMETABLE_ENTRIES
        if e.room_id in affected_rooms or e.teacher_id in affected_teachers or e.section_id in affected_sections
    ]
    return {
        "disruption_id": disruption_id,
        "affected_classes_count": len(affected),
        "affected_classes": affected
    }

@api_router.post("/agents/disruption-recovery/run", response_model=DisruptionRecoveryResultResponse, tags=["Disruption Recovery"])
def run_disruption_recovery_agent(
    title: str = Query("Building B Closure"),
    affected_room: str = Query("Room 201"),
    affected_teacher: str = Query("Cooper")
):
    solver_input = build_default_solver_input()

    event = DisruptionEvent(
        event_type="BUILDING_CLOSURE",
        title=title,
        description="Emergency closure affecting facility wing.",
        start_date="2026-08-25",
        end_date="2026-08-25",
        start_period="P1",
        end_period="P5",
        affected_rooms=[affected_room],
        affected_teachers=[affected_teacher],
        affected_sections=["8A"],
        severity="HIGH",
        source="ADMIN"
    )

    result = disruption_agent.process_disruption(
        event=event,
        solver_input=solver_input,
        existing_timetable=DEMO_TIMETABLE_ENTRIES,
        current_version="v1.0"
    )

    # Store plans in demo memory store
    for p in result.plans:
        DEMO_RECOVERY_PLANS[p.plan_id] = p

    plans_res = [
        RecoveryPlanResponse(
            plan_id=p.plan_id,
            disruption_id=p.disruption_id,
            timetable_version=p.timetable_version,
            plan_title=p.plan_title,
            ranking_category=p.ranking_category,
            changes=[c.__dict__ for c in p.changes],
            hard_conflicts=p.hard_conflicts,
            soft_penalty=p.soft_penalty,
            affected_classes=p.affected_classes,
            affected_teachers=p.affected_teachers,
            affected_rooms=p.affected_rooms,
            status=p.status,
            explanation=p.explanation,
            created_at=p.created_at
        ) for p in result.plans
    ]

    return DisruptionRecoveryResultResponse(
        agent_run_id=result.agent_run_id,
        event_id=result.event_id,
        status=result.status,
        execution_mode=result.execution_mode,
        disruption_title=result.disruption_title,
        affected_classes_count=result.affected_classes_count,
        affected_teachers_count=result.affected_teachers_count,
        affected_rooms_count=result.affected_rooms_count,
        timetable_version=result.timetable_version,
        plans=plans_res,
        selected_plan_id=result.selected_plan_id,
        summary=result.summary,
        explanation=result.explanation,
        approval_request_id=result.approval_request_id,
        notifications_sent=result.notifications_sent,
        created_at=result.created_at
    )

@api_router.get("/disruptions/{disruption_id}/recovery-plans", tags=["Disruption Recovery"])
def get_recovery_plans_for_disruption(disruption_id: str):
    plans = [p for p in DEMO_RECOVERY_PLANS.values() if p.disruption_id == disruption_id]
    if not plans:
        # Generate demo candidate plan if empty
        demo_plan = RecoveryPlan(
            plan_id=str(uuid.uuid4()),
            disruption_id=disruption_id,
            timetable_version="v1.0",
            plan_title="Plan A: Room Reallocation & Substitute Matching",
            ranking_category="CLEAN_RECOVERY",
            changes=[],
            hard_conflicts=0,
            soft_penalty=0.0,
            affected_classes=2,
            affected_teachers=1,
            affected_rooms=1,
            status="PROPOSED",
            explanation="Reassigns Room 201 to Science Lab 1 cleanly.",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        DEMO_RECOVERY_PLANS[demo_plan.plan_id] = demo_plan
        plans = [demo_plan]
    return [p.__dict__ for p in plans]

@api_router.get("/recovery-plans/{plan_id}", tags=["Disruption Recovery"])
def get_recovery_plan_by_id(plan_id: str):
    plan = DEMO_RECOVERY_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")
    return plan.__dict__ if hasattr(plan, '__dict__') else plan

@api_router.post("/recovery-plans/{plan_id}/approve", tags=["Disruption Recovery"])
def approve_recovery_plan(plan_id: str):
    plan = DEMO_RECOVERY_PLANS.get(plan_id)
    solver_input = build_default_solver_input()

    if plan and hasattr(plan, 'changes'):
        success, updated, err = disruption_agent.execute_recovery_plan(
            plan=plan,
            solver_input=solver_input,
            existing_timetable=DEMO_TIMETABLE_ENTRIES,
            current_version="v1.0"
        )
        if not success:
            raise HTTPException(status_code=400, detail=f"Atomic execution failed: {err}")
        return {
            "status": "EXECUTED",
            "message": "Recovery plan approved and applied atomically to active timetable.",
            "plan_id": plan_id
        }

    # Demo fallback approval
    for entry in DEMO_TIMETABLE_ENTRIES:
        if entry.room_id == "Room 201":
            entry.room_id = "Science Lab 1"
            entry.flag = "recovered"
            entry.status = "RECOVERED"
    return {
        "status": "EXECUTED",
        "message": "Recovery plan approved and applied atomically to active timetable.",
        "plan_id": plan_id
    }

@api_router.post("/recovery-plans/{plan_id}/reject", tags=["Disruption Recovery"])
def reject_recovery_plan(plan_id: str):
    plan = DEMO_RECOVERY_PLANS.get(plan_id)
    if plan and hasattr(plan, 'status'):
        plan.status = "REJECTED"
    return {
        "status": "REJECTED",
        "message": "Recovery plan rejected by administrator.",
        "plan_id": plan_id
    }

@api_router.post("/recovery-plans/{plan_id}/cancel", tags=["Disruption Recovery"])
def cancel_recovery_plan(plan_id: str):
    plan = DEMO_RECOVERY_PLANS.get(plan_id)
    if plan and hasattr(plan, 'status'):
        plan.status = "CANCELLED"
    return {
        "status": "CANCELLED",
        "message": "Recovery plan cancelled.",
        "plan_id": plan_id
    }

# ==========================================
# PHASE 5 — FAMILY DAY ALIGNMENT AGENT ENDPOINTS
# ==========================================

@api_router.post("/families", tags=["Family Day Alignment"])
def create_family(family_name: str = Query("Arun Family"), requested_by: str = Query("parent-001")):
    fam_id = str(uuid.uuid4())
    family = {
        "id": fam_id,
        "family_name": family_name,
        "requested_by": requested_by,
        "students": [
            {"student_id": "student-101", "student_name": "Student A", "grade_section": "7A"},
            {"student_id": "student-202", "student_name": "Student B", "grade_section": "9A"},
            {"student_id": "student-303", "student_name": "Student C", "grade_section": "11A"}
        ],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    DEMO_FAMILIES.append(family)
    return family

@api_router.get("/families", tags=["Family Day Alignment"])
def get_all_families():
    return DEMO_FAMILIES

@api_router.get("/families/{family_id}", tags=["Family Day Alignment"])
def get_family_by_id(family_id: str):
    fam = next((f for f in DEMO_FAMILIES if f["id"] == family_id), None)
    if not fam:
        return DEMO_FAMILIES[0]
    return fam

@api_router.get("/families/{family_id}/students", tags=["Family Day Alignment"])
def get_family_students(family_id: str):
    fam = next((f for f in DEMO_FAMILIES if f["id"] == family_id), None)
    students = fam["students"] if fam else DEMO_FAMILIES[0]["students"]
    return {
        "family_id": family_id,
        "family_name": fam["family_name"] if fam else "Arun Family",
        "siblings_count": len(students),
        "students": students
    }

@api_router.post("/families/{family_id}/alignment-requests", tags=["Family Day Alignment"])
def create_family_alignment_request(family_id: str, req: FamilyAlignmentRequestSchema):
    req_id = str(uuid.uuid4())
    alignment_req = {
        "id": req_id,
        "family_id": family_id,
        "family_name": req.family_name,
        "requested_by": req.requested_by,
        "student_ids": req.student_ids,
        "target_alignment": req.target_alignment,
        "preferred_days": req.preferred_days,
        "effective_start_date": req.effective_start_date,
        "effective_end_date": req.effective_end_date,
        "reason": req.reason,
        "status": "OPEN",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    DEMO_ALIGNMENT_REQUESTS.append(alignment_req)
    return alignment_req

@api_router.get("/families/{family_id}/alignment-requests", tags=["Family Day Alignment"])
def get_alignment_requests_for_family(family_id: str):
    return [r for r in DEMO_ALIGNMENT_REQUESTS if r["family_id"] == family_id]

@api_router.get("/family-alignment/{request_id}", tags=["Family Day Alignment"])
def get_alignment_request_by_id(request_id: str):
    req = next((r for r in DEMO_ALIGNMENT_REQUESTS if r["id"] == request_id), None)
    if not req:
        return {
            "id": request_id,
            "family_id": "family-001",
            "family_name": "Arun Family",
            "requested_by": "parent-001",
            "student_ids": ["student-101", "student-202", "student-303"],
            "target_alignment": "MAXIMIZE",
            "status": "OPEN"
        }
    return req

@api_router.post("/agents/family-alignment/run", response_model=FamilyAlignmentResultResponse, tags=["Family Day Alignment"])
def run_family_alignment_agent(
    family_id: str = Query("family-001"),
    family_name: str = Query("Arun Family")
):
    solver_input = build_default_solver_input()

    req = FamilyAlignmentRequest(
        family_id=family_id,
        family_name=family_name,
        requested_by="parent-001",
        student_ids=["student-101", "student-202", "student-303"],
        target_alignment="MAXIMIZE"
    )

    # Demo student schedules across Mon-Fri
    demo_schedules = [
        # Student A (Grade 7A): MON Campus, TUE Campus, WED Home, THU Campus, FRI Home
        StudentDaySchedule(student_id="student-101", student_name="Student A", grade_section="7A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-101", student_name="Student A", grade_section="7A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-101", student_name="Student A", grade_section="7A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="student-101", student_name="Student A", grade_section="7A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-101", student_name="Student A", grade_section="7A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
        # Student B (Grade 9A): MON Campus, TUE Home, WED Campus, THU Campus, FRI Home
        StudentDaySchedule(student_id="student-202", student_name="Student B", grade_section="9A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-202", student_name="Student B", grade_section="9A", school_date="2026-10-06", day_of_week="TUE", attendance_state="HOME"),
        StudentDaySchedule(student_id="student-202", student_name="Student B", grade_section="9A", school_date="2026-10-07", day_of_week="WED", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-202", student_name="Student B", grade_section="9A", school_date="2026-10-08", day_of_week="THU", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-202", student_name="Student B", grade_section="9A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
        # Student C (Grade 11A): MON Campus, TUE Campus, WED Home, THU Home, FRI Home
        StudentDaySchedule(student_id="student-303", student_name="Student C", grade_section="11A", school_date="2026-10-05", day_of_week="MON", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-303", student_name="Student C", grade_section="11A", school_date="2026-10-06", day_of_week="TUE", attendance_state="CAMPUS"),
        StudentDaySchedule(student_id="student-303", student_name="Student C", grade_section="11A", school_date="2026-10-07", day_of_week="WED", attendance_state="HOME"),
        StudentDaySchedule(student_id="student-303", student_name="Student C", grade_section="11A", school_date="2026-10-08", day_of_week="THU", attendance_state="HOME"),
        StudentDaySchedule(student_id="student-303", student_name="Student C", grade_section="11A", school_date="2026-10-09", day_of_week="FRI", attendance_state="HOME"),
    ]

    result = family_agent.process_alignment_request(
        request=req,
        solver_input=solver_input,
        existing_timetable=DEMO_TIMETABLE_ENTRIES,
        family_student_schedules=demo_schedules,
        current_version="v1.0"
    )

    for p in result.plans:
        DEMO_ALIGNMENT_PLANS[p.plan_id] = p

    plans_res = [
        FamilyAlignmentPlanResponse(
            plan_id=p.plan_id,
            request_id=p.request_id,
            family_id=p.family_id,
            family_name=p.family_name,
            timetable_version=p.timetable_version,
            plan_title=p.plan_title,
            ranking_category=p.ranking_category,
            changes=[c.__dict__ for c in p.changes],
            alignment_before=p.alignment_before,
            alignment_after=p.alignment_after,
            total_days=p.total_days,
            hard_conflicts=p.hard_conflicts,
            soft_penalty=p.soft_penalty,
            status=p.status,
            explanation=p.explanation,
            created_at=p.created_at
        ) for p in result.plans
    ]

    return FamilyAlignmentResultResponse(
        agent_run_id=result.agent_run_id,
        request_id=result.request_id,
        family_id=result.family_id,
        family_name=result.family_name,
        status=result.status,
        execution_mode=result.execution_mode,
        siblings_count=result.siblings_count,
        alignment_before=result.alignment_before,
        alignment_after=result.alignment_after,
        timetable_version=result.timetable_version,
        plans=plans_res,
        selected_plan_id=result.selected_plan_id,
        summary=result.summary,
        explanation=result.explanation,
        approval_request_id=result.approval_request_id,
        notifications_sent=result.notifications_sent,
        created_at=result.created_at
    )

@api_router.get("/family-alignment/{request_id}/plans", tags=["Family Day Alignment"])
def get_alignment_plans_for_request(request_id: str):
    plans = [p for p in DEMO_ALIGNMENT_PLANS.values() if p.request_id == request_id]
    if not plans:
        demo_plan = FamilyAlignmentPlan(
            plan_id=str(uuid.uuid4()),
            request_id=request_id,
            family_id="family-001",
            family_name="Arun Family",
            timetable_version="v1.0",
            plan_title="Plan A: Full Family Day Alignment (5/5 Days Aligned)",
            ranking_category="FULL_ALIGNMENT",
            changes=[],
            alignment_before=3,
            alignment_after=5,
            total_days=5,
            hard_conflicts=0,
            soft_penalty=0.0,
            status="PROPOSED",
            explanation="Aligns all 3 siblings to Mon/Tue/Thu Campus and Wed/Fri Home.",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        DEMO_ALIGNMENT_PLANS[demo_plan.plan_id] = demo_plan
        plans = [demo_plan]
    return [p.__dict__ for p in plans]

@api_router.post("/family-alignment/plans/{plan_id}/approve", tags=["Family Day Alignment"])
def approve_alignment_plan(plan_id: str):
    plan = DEMO_ALIGNMENT_PLANS.get(plan_id)
    if plan and hasattr(plan, 'status'):
        plan.status = "EXECUTED"
    return {
        "status": "EXECUTED",
        "message": "Family Day Alignment Plan approved and applied atomically to active sibling schedules.",
        "plan_id": plan_id
    }

@api_router.post("/family-alignment/plans/{plan_id}/reject", tags=["Family Day Alignment"])
def reject_alignment_plan(plan_id: str):
    plan = DEMO_ALIGNMENT_PLANS.get(plan_id)
    if plan and hasattr(plan, 'status'):
        plan.status = "REJECTED"
    return {
        "status": "REJECTED",
        "message": "Family Day Alignment Plan rejected by administrator.",
        "plan_id": plan_id
    }

@api_router.post("/family-alignment/plans/{plan_id}/cancel", tags=["Family Day Alignment"])
def cancel_alignment_plan(plan_id: str):
    plan = DEMO_ALIGNMENT_PLANS.get(plan_id)
    if plan and hasattr(plan, 'status'):
        plan.status = "CANCELLED"
    return {
        "status": "CANCELLED",
        "message": "Family Day Alignment Plan cancelled.",
        "plan_id": plan_id
    }


