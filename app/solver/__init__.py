"""
Deterministic Constraint Solver Engine for School Scheduling (CP-SAT based).
"""

from app.solver.models import SolverInput, SolverResult, SolverConfig, ConflictReport, ConflictItem
from app.solver.timetable_solver import TimetableSolver
from app.solver.conflict_detector import ConflictDetector

__all__ = [
    "SolverInput",
    "SolverResult",
    "SolverConfig",
    "ConflictReport",
    "ConflictItem",
    "TimetableSolver",
    "ConflictDetector",
]
