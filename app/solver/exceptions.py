class SolverException(Exception):
    """Base exception for solver errors."""
    pass

class InfeasibleScheduleException(SolverException):
    """Raised when the constraint solver proves the problem is mathematically infeasible."""
    def __init__(self, message: str, conflict_categories: list[str] = None):
        super().__init__(message)
        self.conflict_categories = conflict_categories or []

class SolverTimeoutException(SolverException):
    """Raised when the solver exceeds configured maximum runtime limit."""
    pass

class InvalidSolverInputException(SolverException):
    """Raised when input parameters fail structural validation prior to solver execution."""
    pass
