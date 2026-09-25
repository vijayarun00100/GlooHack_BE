from ortools.sat.python import cp_model
from app.solver.models import SolverInput

class SolverVariables:
    """
    Creates and indexes CP-SAT boolean decision variables for timetable assignments:
    X[t, c, r, s, p, d] = 1 if teacher 't' teaches course 'c' in room 'r' to section 's' during period 'p' on date 'd'.
    """

    def __init__(self, model: cp_model.CpModel, solver_input: SolverInput):
        self.model = model
        self.input = solver_input
        self.vars = {}  # tuple key -> cp_model.IntVar
        self.vars_by_teacher = {}
        self.vars_by_room = {}
        self.vars_by_section = {}
        self.vars_by_assignment = {}
        self.vars_by_slot = {}

        self._build_variables()

    def _build_variables(self):
        # Maps for quick domain lookup
        teacher_map = {t.id: t for t in self.input.teachers}
        room_map = {r.id: r for r in self.input.rooms}
        course_map = {c.id: c for c in self.input.courses}
        section_map = {s.id: s for s in self.input.sections}

        # Subject qualification map
        capable_pairs = {(cap.teacher_id, cap.subject_id) for cap in self.input.capabilities}
        
        # Teacher availability map
        unavail_teacher = {
            (ta.teacher_id, ta.day_of_week, ta.period_code)
            for ta in self.input.teacher_availability
            if not ta.is_available
        }

        # Room availability map
        unavail_room = {
            (ra.room_id, ra.date_str, ra.period_code)
            for ra in self.input.room_availability
            if not ra.is_available
        }

        for assignment in self.input.assignments:
            sec = section_map.get(assignment.section_id)
            crs = course_map.get(assignment.course_id)
            tch = teacher_map.get(assignment.teacher_id)

            if not sec or not crs or not tch:
                continue

            # Hard Constraint pre-filter 1: Teacher capability
            if self.input.capabilities and (tch.id, crs.subject_id) not in capable_pairs:
                continue

            for day in self.input.school_days:
                if not day.is_instructional:
                    continue

                for period in self.input.periods:
                    # Hard Constraint pre-filter 2: Teacher availability
                    if (tch.id, day.day_of_week, period.code) in unavail_teacher:
                        continue

                    for room in self.input.rooms:
                        # Hard Constraint pre-filter 3: Room availability & status
                        if room.status != "AVAILABLE" or (room.id, day.date_str, period.code) in unavail_room:
                            continue

                        # Hard Constraint pre-filter 4: Room capacity vs section size
                        if room.capacity < sec.student_count:
                            continue

                        # Hard Constraint pre-filter 5: Required equipment
                        if crs.required_equipment:
                            room_eq = set(room.equipment)
                            if not all(eq in room_eq for eq in crs.required_equipment):
                                continue

                        # Create decision variable
                        var_name = f"X_{tch.id}_{crs.id}_{room.id}_{sec.id}_{period.code}_{day.date_str}"
                        var = self.model.new_bool_var(var_name)

                        key = (tch.id, crs.id, room.id, sec.id, period.code, day.date_str)
                        self.vars[key] = var

                        # Indexing for constraint construction
                        self.vars_by_teacher.setdefault((tch.id, day.date_str, period.code), []).append(var)
                        self.vars_by_room.setdefault((room.id, day.date_str, period.code), []).append(var)
                        self.vars_by_section.setdefault((sec.id, day.date_str, period.code), []).append(var)
                        self.vars_by_assignment.setdefault(assignment.id, []).append(var)
                        self.vars_by_slot.setdefault((day.date_str, period.code), []).append(var)
