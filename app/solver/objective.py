from ortools.sat.python import cp_model
from app.solver.soft_constraints import SoftConstraintsBuilder

class ObjectiveBuilder:
    """
    Minimizes the sum of soft penalty terms in the CP-SAT model.
    """

    def __init__(self, model: cp_model.CpModel, soft_constraints: SoftConstraintsBuilder):
        self.model = model
        self.soft_constraints = soft_constraints

    def build_and_set_objective(self):
        if self.soft_constraints.penalty_terms:
            self.model.minimize(sum(self.soft_constraints.penalty_terms))
        else:
            # Constant zero objective for pure feasibility search
            self.model.minimize(0)
