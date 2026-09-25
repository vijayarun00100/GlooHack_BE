from datetime import date, time, datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

# ==========================================
# IDENTITY SCHEMAS
# ==========================================

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: str
    status: str = "ACTIVE"
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class TeacherBase(BaseModel):
    employee_code: str
    max_weekly_hours: int = 40
    max_consecutive_periods: int = 3
    department: str
    status: str = "ACTIVE"

class TeacherResponse(TeacherBase):
    id: UUID
    user_id: UUID
    user: Optional[UserResponse] = None

class StudentBase(BaseModel):
    student_code: str
    grade_level: int
    status: str = "ACTIVE"

class StudentResponse(StudentBase):
    id: UUID
    user_id: UUID
    household_id: Optional[UUID] = None

# ==========================================
# ACADEMIC SCHEMAS
# ==========================================

class GradeResponse(BaseModel):
    id: UUID
    level: int
    name: str
    description: Optional[str] = None

class SectionResponse(BaseModel):
    id: UUID
    grade_id: UUID
    name: str
    academic_year: str
    target_capacity: int = 30

class SubjectResponse(BaseModel):
    id: UUID
    code: str
    name: str
    department: str

class CourseResponse(BaseModel):
    id: UUID
    subject_id: UUID
    grade_id: UUID
    title: str
    periods_per_week: int = 5
    requires_lab: bool = False
    required_equipment: list[str] = []

# ==========================================
# ROOM SCHEMAS
# ==========================================

class RoomResponse(BaseModel):
    id: UUID
    room_number: str
    building: str
    capacity: int
    room_type: str
    status: str

class RoomUtilizationResponse(BaseModel):
    room_id: str
    date: str
    total_periods: int
    scheduled_periods: int
    free_periods: int
    utilization_percentage: float
    status: str

# ==========================================
# TIMETABLE SCHEMAS
# ==========================================

class PeriodResponse(BaseModel):
    id: UUID
    code: str
    name: str
    start_time: time
    end_time: time
    period_order: int

class TimetableEntryResponse(BaseModel):
    id: Optional[str] = None
    version_id: Optional[str] = None
    school_date: str
    period_code: str
    period_id: str
    section_id: str
    course_id: str
    teacher_id: str
    room_id: str
    color_code: Optional[str] = "blue"
    flag: Optional[str] = None
    status: str = "SCHEDULED"

# ==========================================
# SOLVER & CONFLICT SCHEMAS
# ==========================================

class GenerateTimetableRequest(BaseModel):
    academic_year: str = "2026-2027"
    term: str = "Fall Term"
    start_date: str = "2026-08-25"
    end_date: str = "2026-08-27"
    time_limit_seconds: float = 10.0

class ConflictItemResponse(BaseModel):
    conflict_type: str
    severity: str
    description: str
    entity_ids: list[str]
    period_code: Optional[str] = None
    school_date: Optional[str] = None

class ConflictReportResponse(BaseModel):
    is_valid: bool
    total_conflicts: int
    hard_conflicts: list[ConflictItemResponse] = []
    soft_conflicts: list[ConflictItemResponse] = []

class SolverResultResponse(BaseModel):
    status: str
    timetable_entries: list[TimetableEntryResponse] = []
    objective_value: float = 0.0
    hard_constraint_violations: list[str] = []
    soft_constraint_penalties: dict[str, float] = {}
    solver_runtime_ms: float = 0.0
    explanation: str = ""

# ==========================================
# DISRUPTION & RECOVERY SCHEMAS
# ==========================================

class DisruptionCreate(BaseModel):
    title: str
    type: str
    severity: str = "MEDIUM"
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None

class DisruptionResponse(DisruptionCreate):
    id: UUID
    status: str
    created_at: datetime

class RecoveryPlanResponse(BaseModel):
    id: UUID
    disruption_id: UUID
    plan_title: str
    score: Optional[float] = None
    status: str
    explanation: Optional[str] = None
    options: list[dict[str, Any]] = []

# ==========================================
# AGENT & APPROVAL SCHEMAS
# ==========================================

class AgentEventResponse(BaseModel):
    id: UUID
    event_type: str
    source: str
    payload: dict[str, Any]
    created_at: datetime

class AgentRunResponse(BaseModel):
    id: UUID
    event_id: Optional[UUID] = None
    agent_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None

class AgentDecisionResponse(BaseModel):
    id: UUID
    agent_run_id: UUID
    agent_name: str
    summary: str
    explanation: str
    confidence: float
    chosen_option: dict[str, Any]
    rejected_options: list[dict[str, Any]] = []
    is_executed: bool = False

class ApprovalRequestResponse(BaseModel):
    id: UUID
    agent_run_id: UUID
    agent_decision_id: UUID
    agent_name: str
    title: str
    description: str
    impact_assessment: dict[str, Any]
    status: str
    created_at: datetime

# ==========================================
# MEMORY SCHEMAS
# ==========================================

class DecisionMemoryCreate(BaseModel):
    agent_name: str
    event_context: str
    decision_summary: str
    outcome: str
    admin_feedback: Optional[str] = None
    tags: list[str] = []

class DecisionMemoryResponse(DecisionMemoryCreate):
    id: UUID
    created_at: datetime
