from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

class SolverStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNKNOWN = "UNKNOWN"
    TIME_LIMIT = "TIME_LIMIT"

class ConflictSeverity(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"

@dataclass
class SolverConfig:
    time_limit_seconds: float = 10.0
    num_workers: int = 4
    random_seed: int = 42
    max_consecutive_threshold: int = 3
    # Soft constraint weights
    weight_consecutive_periods: float = 10.0
    weight_teacher_preference: float = 5.0
    weight_room_hopping: float = 3.0
    weight_sibling_alignment: float = 8.0
    weight_workload_balance: float = 4.0

@dataclass
class PeriodDTO:
    id: str
    code: str
    name: str
    start_time: str
    end_time: str
    period_order: int

@dataclass
class SchoolDayDTO:
    date_str: str  # YYYY-MM-DD
    day_of_week: int  # 1=Mon, 2=Tue, ..., 7=Sun
    is_instructional: bool = True

@dataclass
class SectionDTO:
    id: str
    name: str  # e.g. "8A"
    grade_level: int  # e.g. 8
    student_count: int = 30
    household_ids: list[str] = field(default_factory=list)

@dataclass
class CourseDTO:
    id: str
    code: str  # e.g. "MATH101"
    title: str
    subject_id: str
    periods_per_week: int = 5
    requires_lab: bool = False
    required_equipment: list[str] = field(default_factory=list)

@dataclass
class TeacherDTO:
    id: str
    name: str
    employee_code: str
    department: str
    max_weekly_hours: int = 40
    max_consecutive_periods: int = 3

@dataclass
class RoomDTO:
    id: str
    room_number: str
    building: str
    capacity: int
    room_type: str = "STANDARD"  # STANDARD, LAB, GYM, AUDITORIUM
    equipment: list[str] = field(default_factory=list)
    status: str = "AVAILABLE"  # AVAILABLE, UNAVAILABLE, UNDER_MAINTENANCE, RESERVED

@dataclass
class TeacherCapabilityDTO:
    teacher_id: str
    subject_id: str
    qualification_level: str = "QUALIFIED"

@dataclass
class TeacherAvailabilityDTO:
    teacher_id: str
    day_of_week: int
    period_code: str
    is_available: bool = True
    preference_weight: float = 1.0

@dataclass
class RoomAvailabilityDTO:
    room_id: str
    date_str: str
    period_code: str
    is_available: bool = True
    reason: Optional[str] = None

@dataclass
class AssignmentRequirementDTO:
    id: str
    section_id: str
    course_id: str
    teacher_id: str
    periods_required: int

@dataclass
class ExistingEntryDTO:
    id: str
    school_date: str
    period_code: str
    section_id: str
    course_id: str
    teacher_id: str
    room_id: str

@dataclass
class SolverInput:
    school_days: list[SchoolDayDTO]
    periods: list[PeriodDTO]
    sections: list[SectionDTO]
    courses: list[CourseDTO]
    teachers: list[TeacherDTO]
    rooms: list[RoomDTO]
    capabilities: list[TeacherCapabilityDTO]
    teacher_availability: list[TeacherAvailabilityDTO]
    room_availability: list[RoomAvailabilityDTO]
    assignments: list[AssignmentRequirementDTO]
    existing_entries: list[ExistingEntryDTO] = field(default_factory=list)
    config: SolverConfig = field(default_factory=SolverConfig)

@dataclass
class ScheduledEntryDTO:
    school_date: str
    period_code: str
    period_id: str
    section_id: str
    course_id: str
    teacher_id: str
    room_id: str
    color_code: str = "blue"
    flag: Optional[str] = None
    status: str = "SCHEDULED"

@dataclass
class SolverResult:
    status: SolverStatus
    timetable_entries: list[ScheduledEntryDTO] = field(default_factory=list)
    objective_value: float = 0.0
    hard_constraint_violations: list[str] = field(default_factory=list)
    soft_constraint_penalties: dict[str, float] = field(default_factory=dict)
    solver_runtime_ms: float = 0.0
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictItem:
    conflict_type: str  # e.g., TEACHER_OVERLAP, ROOM_OVERLAP, ROOM_CAPACITY
    severity: ConflictSeverity
    description: str
    entity_ids: list[str]
    period_code: Optional[str] = None
    school_date: Optional[str] = None

@dataclass
class ConflictReport:
    is_valid: bool
    total_conflicts: int
    hard_conflicts: list[ConflictItem] = field(default_factory=list)
    soft_conflicts: list[ConflictItem] = field(default_factory=list)
