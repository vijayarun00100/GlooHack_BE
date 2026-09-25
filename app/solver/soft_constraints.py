from ortools.sat.python import cp_model
from app.solver.variables import SolverVariables

class SoftConstraintsBuilder:
    """
    Formulates penalty expressions for soft constraints to be minimized in the CP-SAT model.
    """

    def __init__(self, model: cp_model.CpModel, variables: SolverVariables):
        self.model = model
        self.variables = variables
        self.penalty_terms = []

    def apply_all(self):
        self.apply_teacher_consecutive_penalty()
        self.apply_teacher_preference_penalty()
        self.apply_room_hopping_penalty()

    def apply_teacher_consecutive_penalty(self):
        """Penalizes assigning a teacher more than max_consecutive_threshold periods in a row."""
        cfg = self.variables.input.config
        periods = sorted(self.variables.input.periods, key=lambda p: p.period_order)
        threshold = cfg.max_consecutive_threshold

        if len(periods) <= threshold:
            return

        for teacher in self.variables.input.teachers:
            for day in self.variables.input.school_days:
                # Sliding window of length (threshold + 1)
                for i in range(len(periods) - threshold):
                    window_periods = periods[i : i + threshold + 1]
                    window_vars = []
                    for p in window_periods:
                        vlist = self.variables.vars_by_teacher.get((teacher.id, day.date_str, p.code), [])
                        window_vars.extend(vlist)

                    if window_vars:
                        # Penalty variable triggered if all slots in window are active
                        pen_var = self.model.new_bool_var(f"pen_consec_{teacher.id}_{day.date_str}_{i}")
                        # pen_var == 1 iff sum(window_vars) > threshold
                        self.model.add(sum(window_vars) <= threshold).only_enforce_if(pen_var.Not())
                        self.penalty_terms.append(pen_var * int(cfg.weight_consecutive_periods * 100))

    def apply_teacher_preference_penalty(self):
        """Applies penalties when assigning a teacher to non-preferred period slots."""
        cfg = self.variables.input.config
        pref_map = {
            (ta.teacher_id, ta.day_of_week, ta.period_code): ta.preference_weight
            for ta in self.variables.input.teacher_availability
        }

        for (tch_id, crs_id, r_id, sec_id, p_code, date_str), var in self.variables.vars.items():
            # Find day_of_week
            day_obj = next((d for d in self.variables.input.school_days if d.date_str == date_str), None)
            if not day_obj:
                continue

            weight = pref_map.get((tch_id, day_obj.day_of_week, p_code), 1.0)
            if weight < 1.0:
                penalty_cost = int((1.0 - weight) * cfg.weight_teacher_preference * 100)
                self.penalty_terms.append(var * penalty_cost)

    def apply_room_hopping_penalty(self):
        """Penalizes switching rooms for the same section across consecutive periods on the same day."""
        cfg = self.variables.input.config
        periods = sorted(self.variables.input.periods, key=lambda p: p.period_order)

        for sec in self.variables.input.sections:
            for day in self.variables.input.school_days:
                for i in range(len(periods) - 1):
                    p1, p2 = periods[i], periods[i + 1]
                    for r1 in self.variables.input.rooms:
                        for r2 in self.variables.input.rooms:
                            if r1.id == r2.id:
                                continue

                            # Finds vars for p1 in r1 and p2 in r2
                            v1_list = [v for k, v in self.variables.vars.items() if k[3] == sec.id and k[2] == r1.id and k[4] == p1.code and k[5] == day.date_str]
                            v2_list = [v for k, v in self.variables.vars.items() if k[3] == sec.id and k[2] == r2.id and k[4] == p2.code and k[5] == day.date_str]

                            if v1_list and v2_list:
                                hop_var = self.model.new_bool_var(f"hop_{sec.id}_{r1.id}_{r2.id}_{day.date_str}_{p1.code}")
                                self.model.add_bool_and(v1_list + v2_list).only_enforce_if(hop_var)
                                self.penalty_terms.append(hop_var * int(cfg.weight_room_hopping * 100))
