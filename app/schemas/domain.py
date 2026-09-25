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
# ROOM DISRUPTION & ALLOCATION AGENT SCHEMAS
# ==========================================

class RoomDisruptionRequest(BaseModel):
    room_id: str
    event_type: str  # 'CLOSED', 'MAINTENANCE', 'EQUIPMENT_FAILURE', 'CAPACITY_RESTRICTION'
    start_date: str
    end_date: str
    start_period: Optional[str] = "P1"
    end_period: Optional[str] = "P5"
    reason: str = "Facility disruption"
    required_equipment_impact: list[str] = []
    capacity_restriction: Optional[int] = None
    source: str = "ADMIN"

class RoomCandidateResponse(BaseModel):
    room_id: str
    room_number: str
    capacity: int
    capacity_waste: int
    equipment_ok: bool
    available_ok: bool
    hard_conflicts_count: int
    penalty_score: float
    status: str
    explanation: str

class RoomReallocationRequirementResponse(BaseModel):
    period_code: str
    school_date: str
    section_id: str
    course_id: str
    course_title: str
    teacher_id: str
    original_room_id: str
    original_room_number: str
    section_student_count: int
    ranked_candidates: list[RoomCandidateResponse] = []
    selected_candidate: Optional[RoomCandidateResponse] = None

class RoomAllocationAgentResultResponse(BaseModel):
    agent_run_id: str
    event_id: str
    status: str
    execution_mode: str
    disrupted_room_id: str
    disrupted_room_number: str
    event_type: str
    affected_classes_count: int
    requirements: list[RoomReallocationRequirementResponse] = []
    summary: str
    explanation: str
    approval_request_id: Optional[str] = None
    created_at: str

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
# TEACHER SUBSTITUTION SCHEMAS
# ==========================================

class IngestEmailRequest(BaseModel):
    raw_email: str
    sender_email: Optional[str] = "cooper@school.edu"

class CandidateOptionResponse(BaseModel):
    teacher_id: str
    teacher_name: str
    qualification_ok: bool
    available_ok: bool
    hard_conflicts_count: int
    penalty_score: float
    status: str
    explanation: str

class SubstitutionRequirementResponse(BaseModel):
    period_code: str
    school_date: str
    section_id: str
    course_id: str
    course_title: str
    original_teacher_id: str
    original_teacher_name: str
    room_id: str
    ranked_candidates: list[CandidateOptionResponse] = []
    selected_candidate: Optional[CandidateOptionResponse] = None

class SubstitutionAgentResultResponse(BaseModel):
    agent_run_id: str
    event_id: str
    status: str
    execution_mode: str
    absence_date: str
    absent_teacher_id: Optional[str] = None
    absent_teacher_name: str
    affected_classes_count: int
    requirements: list[SubstitutionRequirementResponse] = []
    summary: str
    explanation: str
    approval_request_id: Optional[str] = None
    created_at: str

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

# ==========================================
# DISRUPTION RECOVERY AGENT SCHEMAS
# ==========================================

class CampusDisruptionRequest(BaseModel):
    event_type: str = "CAMPUS_DISRUPTION"
    title: str
    description: str = ""
    start_date: str
    end_date: str
    start_period: str = "P1"
    end_period: str = "P5"
    affected_rooms: list[str] = []
    affected_teachers: list[str] = []
    affected_sections: list[str] = []
    severity: str = "HIGH"
    source: str = "ADMIN"

class RecoveryPlanChangeResponse(BaseModel):
    timetable_entry_id: str
    school_date: str
    old_teacher_id: str
    new_teacher_id: str
    old_room_id: str
    new_room_id: str
    old_period_code: str
    new_period_code: str
    change_reason: str = ""

class RecoveryPlanResponse(BaseModel):
    plan_id: str
    disruption_id: str
    timetable_version: str
    plan_title: str
    ranking_category: str
    changes: list[RecoveryPlanChangeResponse] = []
    hard_conflicts: int = 0
    soft_penalty: float = 0.0
    affected_classes: int = 0
    affected_teachers: int = 0
    affected_rooms: int = 0
    status: str
    explanation: str
    created_at: str

class DisruptionRecoveryResultResponse(BaseModel):
    agent_run_id: str
    event_id: str
    status: str
    execution_mode: str
    disruption_title: str
    affected_classes_count: int
    affected_teachers_count: int
    affected_rooms_count: int
    timetable_version: str
    plans: list[RecoveryPlanResponse] = []
    selected_plan_id: Optional[str] = None
    summary: str
    explanation: str
    approval_request_id: Optional[str] = None
    notifications_sent: int = 0
    created_at: str

# ==========================================
# FAMILY DAY ALIGNMENT AGENT SCHEMAS
# ==========================================

class FamilyAlignmentRequestSchema(BaseModel):
    family_id: str = "family-001"
    family_name: str = "Arun Family"
    requested_by: str = "parent-001"
    student_ids: list[str] = ["student-101", "student-202", "student-303"]
    target_alignment: str = "MAXIMIZE"
    preferred_days: list[str] = ["WEDNESDAY", "FRIDAY"]
    effective_start_date: str = "2026-10-01"
    effective_end_date: str = "2026-10-31"
    reason: str = "Sibling transportation"

class AlignmentChangeItemResponse(BaseModel):
    student_id: str
    student_name: str
    grade_section: str
    school_date: str
    day_of_week: str
    old_state: str
    new_state: str
    change_reason: str = ""

class FamilyAlignmentPlanResponse(BaseModel):
    plan_id: str
    request_id: str
    family_id: str
    family_name: str
    timetable_version: str
    plan_title: str
    ranking_category: str
    changes: list[AlignmentChangeItemResponse] = []
    alignment_before: int = 0
    alignment_after: int = 0
    total_days: int = 5
    hard_conflicts: int = 0
    soft_penalty: float = 0.0
    status: str
    explanation: str
    created_at: str

class FamilyAlignmentResultResponse(BaseModel):
    agent_run_id: str
    request_id: str
    family_id: str
    family_name: str
    status: str
    execution_mode: str
    siblings_count: int
    alignment_before: int
    alignment_after: int
    timetable_version: str
    plans: list[FamilyAlignmentPlanResponse] = []
    selected_plan_id: Optional[str] = None
    summary: str
    explanation: str
    approval_request_id: Optional[str] = None
    notifications_sent: int = 0
    created_at: str

# ==========================================
# SCHEDULE QUALITY REVIEW AGENT SCHEMAS
# ==========================================

class QualityReviewRequestSchema(BaseModel):
    timetable_version: str = "v1.0"
    scope: str = "FULL_SCHOOL"
    start_date: Optional[str] = "2026-08-25"
    end_date: Optional[str] = "2026-08-25"
    target_entity_id: Optional[str] = None
    include_teachers: bool = True
    include_sections: bool = True
    include_rooms: bool = True
    generate_recommendations: bool = True

class TeacherWorkloadMetricsResponse(BaseModel):
    teacher_id: str
    teacher_name: str
    department: str
    total_teaching_periods: int = 0
    max_consecutive_periods: int = 0
    idle_gaps: int = 0
    schedule_span: int = 0
    room_changes: int = 0
    preference_violations: int = 0
    daily_loads: dict[str, int] = {}

class RoomUtilizationMetricsResponse(BaseModel):
    room_id: str
    room_number: str
    building: str
    total_periods: int = 5
    occupied_periods: int = 0
    free_periods: int = 5
    utilization_percentage: float = 0.0
    status: str = "OPTIMAL"

class SectionQualityMetricsResponse(BaseModel):
    section_id: str
    section_name: str
    total_periods: int = 0
    max_subject_consecutive: int = 0
    room_changes: int = 0

class QualityIssueResponse(BaseModel):
    id: str
    issue_type: str
    severity: str
    entity_type: str
    entity_id: str
    entity_name: str
    metric_name: str
    observed_value: float
    threshold_value: float
    description: str

class QualityRecommendationResponse(BaseModel):
    id: str
    issue_id: Optional[str] = None
    category: str
    recommendation_text: str
    expected_improvement: str
    feasibility_status: str = "FEASIBLE"

class OptimizationPlanChangeResponse(BaseModel):
    timetable_entry_id: str
    school_date: str
    period_code: str
    old_teacher_id: str
    new_teacher_id: str
    old_room_id: str
    new_room_id: str
    old_period_code: str
    new_period_code: str
    change_reason: str = ""

class ScheduleOptimizationPlanResponse(BaseModel):
    plan_id: str
    review_id: str
    timetable_version: str
    plan_title: str
    ranking_category: str
    changes: list[OptimizationPlanChangeResponse] = []
    affected_teachers: int = 0
    affected_sections: int = 0
    affected_rooms: int = 0
    quality_before: float = 0.0
    quality_after: float = 0.0
    hard_conflicts: int = 0
    soft_penalty: float = 0.0
    status: str
    explanation: str
    created_at: str

class QualityReviewResultResponse(BaseModel):
    review_id: str
    timetable_version: str
    scope: str
    overall_quality_score: float
    teacher_balance_score: float
    section_balance_score: float
    room_utilization_score: float
    preference_alignment_score: float
    hard_conflicts_count: int
    issues_count: int
    recommendations_count: int
    teacher_metrics: list[TeacherWorkloadMetricsResponse] = []
    room_metrics: list[RoomUtilizationMetricsResponse] = []
    section_metrics: list[SectionQualityMetricsResponse] = []
    issues: list[QualityIssueResponse] = []
    recommendations: list[QualityRecommendationResponse] = []
    optimization_plans: list[ScheduleOptimizationPlanResponse] = []
    status: str
    summary: str
    explanation: str
    created_at: str



