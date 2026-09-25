import time
from ortools.sat.python import cp_model
from app.solver.models import SolverInput, SolverResult, SolverStatus, ScheduledEntryDTO
from app.solver.variables import SolverVariables
from app.solver.hard_constraints import HardConstraintsBuilder
from app.solver.soft_constraints import SoftConstraintsBuilder
from app.solver.objective import ObjectiveBuilder

class TimetableSolver:
    """
    CP-SAT Engine for deterministic school scheduling.
    """

    def solve(self, solver_input: SolverInput) -> SolverResult:
        start_time = time.time()
        model = cp_model.CpModel()

        # 1. Build Decision Variables
        variables = SolverVariables(model, solver_input)

        # 2. Apply Hard Constraints
        hard_builder = HardConstraintsBuilder(model, variables)
        hard_builder.apply_all()

        # 3. Apply Soft Constraints
        soft_builder = SoftConstraintsBuilder(model, variables)
        soft_builder.apply_all()

        # 4. Formulate Objective Function
        obj_builder = ObjectiveBuilder(model, soft_builder)
        obj_builder.build_and_set_objective()

        # 5. Configure Solver Parameters
        solver = cp_model.CpSolver()
        cfg = solver_input.config
        solver.parameters.max_time_in_seconds = cfg.time_limit_seconds
        solver.parameters.num_workers = cfg.num_workers
        solver.parameters.random_seed = cfg.random_seed

        # 6. Execute Search
        cp_status = solver.solve(model)
        elapsed_ms = (time.time() - start_time) * 1000.0

        # Map CP-SAT status
        status_map = {
            cp_model.OPTIMAL: SolverStatus.OPTIMAL,
            cp_model.FEASIBLE: SolverStatus.FEASIBLE,
            cp_model.INFEASIBLE: SolverStatus.INFEASIBLE,
            cp_model.UNKNOWN: SolverStatus.UNKNOWN,
        }
        res_status = status_map.get(cp_status, SolverStatus.UNKNOWN)

        if cp_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            entries = []
            period_map = {p.code: p.id for p in solver_input.periods}
            
            # Subject-family color palette mapping for frontend visualization
            color_cycle = ['blue', 'teal', 'green', 'amber', 'rose', 'yellow', 'sky']

            for (tch_id, crs_id, r_id, sec_id, p_code, date_str), var in variables.vars.items():
                if solver.value(var) == 1:
                    idx = hash(crs_id) % len(color_cycle)
                    entries.append(ScheduledEntryDTO(
                        school_date=date_str,
                        period_code=p_code,
                        period_id=period_map.get(p_code, p_code),
                        section_id=sec_id,
                        course_id=crs_id,
                        teacher_id=tch_id,
                        room_id=r_id,
                        color_code=color_cycle[idx],
                        flag=None,
                        status="SCHEDULED"
                    ))

            return SolverResult(
                status=res_status,
                timetable_entries=entries,
                objective_value=float(solver.objective_value),
                solver_runtime_ms=elapsed_ms,
                explanation=f"Successfully computed timetable ({res_status.value}) in {elapsed_ms:.1f}ms. Total scheduled classes: {len(entries)}.",
                metadata={
                    "variables_count": len(variables.vars),
                    "branches": solver.num_branches,
                    "conflicts": solver.num_conflicts,
                }
            )
        elif cp_status == cp_model.INFEASIBLE:
            return SolverResult(
                status=SolverStatus.INFEASIBLE,
                timetable_entries=[],
                solver_runtime_ms=elapsed_ms,
                hard_constraint_violations=["CP-SAT proved problem is mathematically INFEASIBLE under current constraints."],
                explanation="Unable to find a valid schedule. Over-constrained teacher availability, room capacity, or required period slots."
            )
        else:
            return SolverResult(
                status=SolverStatus.TIME_LIMIT,
                timetable_entries=[],
                solver_runtime_ms=elapsed_ms,
                explanation="Solver reached time limit without finding a feasible solution."
            )
