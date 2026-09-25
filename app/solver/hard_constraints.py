from ortools.sat.python import cp_model
from app.solver.variables import SolverVariables

class HardConstraintsBuilder:
    """
    Applies all mandatory mathematical hard invariants to the CP-SAT model.
    """

    def __init__(self, model: cp_model.CpModel, variables: SolverVariables):
        self.model = model
        self.variables = variables

    def apply_all(self):
        self.apply_teacher_non_overlap()
        self.apply_room_non_overlap()
        self.apply_section_non_overlap()
        self.apply_course_period_requirements()

    def apply_teacher_non_overlap(self):
        """Constraint 8.1: A teacher cannot teach two sections during the same period."""
        for (_tch_id, _date, _period), var_list in self.variables.vars_by_teacher.items():
            if len(var_list) > 1:
                self.model.add_at_most_one(var_list)

    def apply_room_non_overlap(self):
        """Constraint 8.2: A room cannot host two classes during the same period."""
        for (_room_id, _date, _period), var_list in self.variables.vars_by_room.items():
            if len(var_list) > 1:
                self.model.add_at_most_one(var_list)

    def apply_section_non_overlap(self):
        """Constraint 8.3: A section cannot attend two courses during the same period."""
        for (_sec_id, _date, _period), var_list in self.variables.vars_by_section.items():
            if len(var_list) > 1:
                self.model.add_at_most_one(var_list)

    def apply_course_period_requirements(self):
        """Constraint 8.9: Satisfy total required periods per week for each section course assignment."""
        for assignment in self.variables.input.assignments:
            var_list = self.variables.vars_by_assignment.get(assignment.id, [])
            # Must ALWAYS enforce sum(var_list) == periods_required (even if var_list is empty -> 0 == req)
            self.model.add(sum(var_list) == assignment.periods_required)
