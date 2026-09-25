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
    summary: str
    explanation: str
    created_at: str


# ==========================================
# PHASE 7 — PLANLY STUDY PLANNING SCHEMAS
# ==========================================

class StudyGoalCreateRequest(BaseModel):
    student_id: str = "student-101"
    title: str
    description: Optional[str] = None
    target_date: str
    priority: str = "HIGH"
    subjects: list[str] = ["Mathematics"]
    focus_topics: list[str] = ["Algebra", "Quadratic Equations", "Functions"]
    natural_language_prompt: Optional[str] = None

class StudyPlanningRequest(BaseModel):
    student_id: str = "student-101"
    goal_id: Optional[str] = None
    goal: Optional[str] = "Prepare for Mathematics midterm"
    target_date: Optional[str] = "2026-10-15"
    subjects: list[str] = ["Mathematics"]
    priority: str = "HIGH"
    available_study_hours_per_week: float = 10.0
    preferred_session_minutes: int = 50
    preferred_days: list[str] = ["MONDAY", "TUESDAY", "THURSDAY", "SATURDAY"]
    energy_preference: str = "NORMAL" # "LOW", "NORMAL", "HIGH"
    learning_preferences: list[str] = ["PRACTICE", "REVISION"]
    natural_language_prompt: Optional[str] = None

class StudyTaskResponse(BaseModel):
    id: str
    sprint_id: str
    title: str
    description: Optional[str] = None
    task_type: str = "PRACTICE_PROBLEMS"
    estimated_minutes: int = 30
    actual_minutes: int = 0
    priority: str = "HIGH"
    status: str = "PLANNED"

class StudySprintResponse(BaseModel):
    id: str
    plan_id: str
    school_date: str
    start_time: str
    end_time: str
    duration_minutes: int
    subject: str
    focus_area: str
    sprint_type: str
    status: str = "PLANNED"
    tasks: list[StudyTaskResponse] = []

class StudyGoalResponse(BaseModel):
    id: str
    student_id: str
    title: str
    description: Optional[str] = None
    target_date: str
    priority: str
    status: str
    subjects: list[str]
    focus_topics: list[str]
    created_at: str

class StudyPlanResponse(BaseModel):
    id: str
    student_id: str
    goal_id: Optional[str] = None
    goal_title: str = ""
    start_date: str
    end_date: str
    status: str
    total_hours: float
    planned_hours: float
    completed_hours: float
    completion_percentage: float
    feasibility_score: float = 100.0
    goal_coverage_score: float = 92.0
    time_utilization_score: float = 88.0
    deadline_safety_score: float = 95.0
    workload_balance_score: float = 90.0
    overall_quality_score: float = 92.0
    energy_preference: str = "NORMAL"
    sprints: list[StudySprintResponse] = []
    created_at: str

class StudyProgressResponse(BaseModel):
    student_id: str
    total_goals: int = 1
    total_plans: int = 1
    total_sprints: int = 0
    completed_sprints: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    missed_tasks: int = 0
    completed_hours: float = 0.0
    overall_completion_percentage: float = 0.0
    subject_progress: dict[str, float] = {}

class PlanlyAgentResultResponse(BaseModel):
    agent: str = "PLANLY"
    goal: StudyGoalResponse
    plan: StudyPlanResponse
    daily_sprints: list[StudySprintResponse] = []
    weekly_summary: dict[str, Any] = {}
    plan_health: dict[str, float] = {}
    explanation: str
    status: str = "SUCCESS"


# ==========================================
# PHASE 8 — GAMIFICATION & SOCIAL SCHEMAS
# ==========================================

class GamificationProfileResponse(BaseModel):
    student_id: str = "student-101"
    total_xp: int = 2840
    current_level: int = 8
    xp_for_next_level: int = 3500
    xp_progress_percentage: float = 81.1
    coins: int = 420
    current_streak: int = 7
    longest_streak: int = 12
    total_study_minutes: int = 600
    total_tasks_completed: int = 14
    last_activity_date: Optional[str] = "2026-10-05"

class AchievementResponse(BaseModel):
    code: str
    name: str
    description: str
    category: str = "GENERAL"
    icon: str = "🏆"
    xp_reward: int = 100
    coin_reward: int = 10
    unlocked: bool = False
    progress_percentage: float = 0.0
    unlocked_at: Optional[str] = None

class StudentAchievementResponse(BaseModel):
    id: str
    student_id: str
    achievement_code: str
    unlocked_at: str
    progress: float = 100.0

class GamificationEventRequest(BaseModel):
    student_id: str = "student-101"
    event_type: str
    source: str = "PLANLY"
    source_id: str
    metadata: dict[str, Any] = {}

class SocialPostCreateRequest(BaseModel):
    student_id: str = "student-101"
    student_name: str = "Student A"
    post_type: str = "ACHIEVEMENT" # 'ACHIEVEMENT', 'STREAK', 'MILESTONE', 'GOAL_COMPLETION'
    achievement_code: Optional[str] = "SEVEN_DAY_STREAK"
    title: str = "Unlocked 7-Day Study Streak!"
    content: str = "🎉 I completed a 7-day study streak on Planly!"
    visibility: str = "CLASS" # 'PRIVATE', 'FRIENDS', 'CLASS', 'PUBLIC'

class SocialPostResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    post_type: str
    achievement_code: Optional[str] = None
    title: str
    content: str
    visibility: str
    reactions_count: int = 0
    reactions_breakdown: dict[str, int] = {"🔥": 0, "👏": 0, "🎉": 0}
    created_at: str

class SocialReactionRequest(BaseModel):
    student_id: str = "student-101"
    reaction_type: str = "🔥" # '👏', '🔥', '🎉', '⭐'

class SocialPrivacySettingsRequest(BaseModel):
    student_id: str = "student-101"
    achievement_visibility: str = "CLASS"
    profile_visibility: str = "CLASS"
    social_enabled: bool = True

class SocialPrivacySettingsResponse(BaseModel):
    student_id: str
    achievement_visibility: str
    profile_visibility: str
    social_enabled: bool
    updated_at: str


# ==========================================
# PHASE 9 — STRIVER RAG LEARNING SCHEMAS
# ==========================================

class StriverDocumentCreateRequest(BaseModel):
    title: str
    subject: str = "Mathematics"
    grade: int = 9
    course: str = "Mathematics"
    uploaded_by: str = "teacher-001"
    source_type: str = "CHAPTER_NOTES"
    content: str

class StriverDocumentResponse(BaseModel):
    id: str
    title: str
    subject: str
    grade: int
    course: str
    source_type: str
    status: str = "READY"
    chunk_count: int = 0
    created_at: str

class StriverSessionStartRequest(BaseModel):
    student_id: str = "student-101"
    planly_task_id: Optional[str] = "task-1"
    subject: str = "Mathematics"
    topic: str = "Quadratic Equations"
    mode: str = "EXPLAIN"

class StriverSessionResponse(BaseModel):
    id: str
    student_id: str
    planly_task_id: Optional[str] = None
    subject: str
    topic: str
    mode: str
    started_at: str
    completed_at: Optional[str] = None
    mastery_before: float = 60.0
    mastery_after: float = 71.0

class StriverSourceCitation(BaseModel):
    document_title: str
    page_number: int = 1
    chapter: str = ""
    relevance_score: float = 0.92

class StriverExplainRequest(BaseModel):
    session_id: Optional[str] = None
    student_id: str = "student-101"
    subject: str = "Mathematics"
    topic: str = "Quadratic Equations"
    prompt: str = "Explain quadratic equations simply."
    mode: str = "EXPLAIN" # 'EXPLAIN', 'SIMPLE', 'DEEP_DIVE', 'EXAMPLE', 'ANALOGY', 'STEP_BY_STEP', 'REVISION', 'EXAM_PREP', 'SOCRATIC'

class StriverExplainResponse(BaseModel):
    session_id: str
    question: str
    explanation: str
    sources: list[StriverSourceCitation] = []
    mode: str = "EXPLAIN"
    grounded_in_materials: bool = True

class StriverPracticeQuestionResponse(BaseModel):
    question_id: str
    topic: str
    question: str
    hints: list[str] = []
    expected_answer: str

class StriverPracticeAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    student_answer: str

class StriverPracticeResultResponse(BaseModel):
    question_id: str
    is_correct: bool
    feedback: str
    explanation: str
    sources: list[StriverSourceCitation] = []
    updated_mastery: float

class StriverQuizQuestionResponse(BaseModel):
    question_id: str
    question: str
    options: list[str] = []
    expected_answer: str

class StriverQuizAnswerRequest(BaseModel):
    session_id: str
    answers: dict[str, str] # question_id -> student_answer

class StriverQuizResultResponse(BaseModel):
    session_id: str
    score: int
    total_questions: int = 5
    accuracy_percentage: float
    mastery_before: float
    mastery_after: float
    mastery_level: str = "PRACTICING"
    gamification_xp_earned: int = 50
    recommendation: str

class StriverMasteryResponse(BaseModel):
    student_id: str
    subject: str
    topic: str
    mastery_score: float = 71.0
    mastery_level: str = "PRACTICING" # 'NEEDS_SUPPORT', 'DEVELOPING', 'PRACTICING', 'STRONG', 'MASTERED'
    confidence: str = "MEDIUM"
    attempts: int = 8
    correct_attempts: int = 6
    last_practiced_at: str






