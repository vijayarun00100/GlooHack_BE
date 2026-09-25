from typing import Optional
from app.solver.models import (
    SolverInput, SolverResult, ConflictReport, RoomDTO, SchoolDayDTO, PeriodDTO,
    SectionDTO, CourseDTO, TeacherDTO, AssignmentRequirementDTO, SolverConfig
)
from app.solver.timetable_solver import TimetableSolver
from app.solver.conflict_detector import ConflictDetector

class TimetableService:
    """
    Application Service Layer mediating between FastAPI controllers, DB repositories, and the CP-SAT solver.
    """

    def __init__(self):
        self.solver = TimetableSolver()
        self.conflict_detector = ConflictDetector()

    def generate_timetable(self, solver_input: SolverInput) -> SolverResult:
        # 1. Run CP-SAT Solver
        result = self.solver.solve(solver_input)

        # 2. Validate resulting entries before persistence
        if result.timetable_entries:
            report = self.conflict_detector.validate(solver_input, result.timetable_entries)
            if not report.is_valid:
                result.hard_constraint_violations = [c.description for c in report.hard_conflicts]

        return result

    def validate_timetable(self, solver_input: SolverInput, entries: list) -> ConflictReport:
        return self.conflict_detector.validate(solver_input, entries)

    def calculate_room_utilization(
        self,
        room_id: str,
        target_date_str: str,
        total_periods: int,
        scheduled_entries: list
    ) -> dict:
        scheduled_count = len([e for e in scheduled_entries if e.get("room_id") == room_id and e.get("school_date") == target_date_str])
        free_periods = max(0, total_periods - scheduled_count)
        util_pct = (scheduled_count / total_periods * 100.0) if total_periods > 0 else 0.0

        return {
            "room_id": room_id,
            "date": target_date_str,
            "total_periods": total_periods,
            "scheduled_periods": scheduled_count,
            "free_periods": free_periods,
            "utilization_percentage": round(util_pct, 1),
            "status": "AVAILABLE" if scheduled_count < total_periods else "FULLY_BOOKED"
        }
