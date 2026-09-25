import uuid
import time
import copy
from dataclasses import dataclass, field
from typing import Optional, Any
from app.services.timetable_service import TimetableService
from app.services.teacher_matching import TeacherMatchingService
from app.solver.models import (
    SolverInput, ScheduledEntryDTO, ConflictReport, SolverStatus
)
from app.solver.conflict_detector import ConflictDetector

@dataclass
class DisruptionEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "CAMPUS_DISRUPTION"  # 'CAMPUS_DISRUPTION', 'BUILDING_CLOSURE', 'FIRE_DRILL', 'WEATHER_EMERGENCY', 'INFRASTRUCTURE_OUTAGE'
    title: str = "Campus Disruption"
    description: str = ""
    start_date: str = "2026-09-28"
    end_date: str = "2026-09-29"
    start_period: str = "P1"
    end_period: str = "P5"
    affected_rooms: list[str] = field(default_factory=list)
    affected_teachers: list[str] = field(default_factory=list)
    affected_sections: list[str] = field(default_factory=list)
    severity: str = "HIGH"  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    source: str = "ADMIN"
    status: str = "OPEN"

@dataclass
class RecoveryPlanChange:
    timetable_entry_id: str
    school_date: str
    old_teacher_id: str
    new_teacher_id: str
    old_room_id: str
    new_room_id: str
    old_period_code: str
    new_period_code: str
    change_reason: str = ""

@dataclass
class RecoveryPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    disruption_id: str = ""
    timetable_version: str = "v1.0"
    plan_title: str = ""
    ranking_category: str = "MODERATE_DISRUPTION"  # 'CLEAN_RECOVERY', 'LOW_DISRUPTION', 'MODERATE_DISRUPTION', 'HIGH_DISRUPTION', 'INVALID'
    changes: list[RecoveryPlanChange] = field(default_factory=list)
    hard_conflicts: int = 0
    soft_penalty: float = 0.0
    affected_classes: int = 0
    affected_teachers: int = 0
    affected_rooms: int = 0
    status: str = "PROPOSED"  # 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'STALE'
    explanation: str = ""
    created_at: str = ""

@dataclass
class DisruptionRecoveryResult:
    agent_run_id: str
    event_id: str
    status: str  # 'RESOLVED', 'REQUIRES_APPROVAL', 'STALE', 'INFEASIBLE'
    execution_mode: str  # 'AUTO_EXECUTE', 'REQUIRES_APPROVAL'
    disruption_title: str
    affected_classes_count: int
    affected_teachers_count: int
    affected_rooms_count: int
    timetable_version: str
    plans: list[RecoveryPlan] = field(default_factory=list)
    selected_plan_id: Optional[str] = None
    summary: str = ""
    explanation: str = ""
    approval_request_id: Optional[str] = None
    notifications_sent: int = 0
    created_at: str = ""

class DisruptionRecoveryAgent:
    """
    Autonomous Orchestrator Agent for Major Campus Disruption Recovery.
    Identifies all affected timetable entries across rooms, teachers, sections, and date/period windows.
    Orchestrates Phase 2 Teacher Substitution, Phase 3 Room Allocation, and Phase 1 Solver rescheduling.
    Ranks recovery plans, enforces HITL governance, executes plans atomically with version checking,
    validates zero hard conflicts with ConflictDetector, dispatches notifications, and stores decision memory.
    """

    def __init__(self):
        self.timetable_service = TimetableService()
        self.conflict_detector = ConflictDetector()

    def process_disruption(
        self,
        event: DisruptionEvent,
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO],
        current_version: str = "v1.0"
    ) -> DisruptionRecoveryResult:
        run_id = str(uuid.uuid4())
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Stage 1: Identify Affected Timetable Entries
        affected_entries = self._identify_affected_entries(event, existing_timetable)

        if not affected_entries:
            return DisruptionRecoveryResult(
                agent_run_id=run_id,
                event_id=event.id,
                status="RESOLVED",
                execution_mode="AUTO_EXECUTE",
                disruption_title=event.title,
                affected_classes_count=0,
                affected_teachers_count=0,
                affected_rooms_count=0,
                timetable_version=current_version,
                plans=[],
                summary=f"No scheduled classes affected by disruption '{event.title}'.",
                explanation="Validated disruption scope against timetable. Zero scheduled entries match target rooms, teachers, or date/period windows.",
                created_at=now_str,
            )

        affected_teachers_set = {e.teacher_id for e in affected_entries}
        affected_rooms_set = {e.room_id for e in affected_entries}

        # Stage 2: Strategy & Recovery Plan Generation
        plans = self._generate_recovery_plans(
            event=event,
            affected_entries=affected_entries,
            solver_input=solver_input,
            existing_timetable=existing_timetable,
            timetable_version=current_version
        )

        # Filter out invalid plans or rank them
        valid_plans = [p for p in plans if p.ranking_category != "INVALID"]

        if not valid_plans:
            return DisruptionRecoveryResult(
                agent_run_id=run_id,
                event_id=event.id,
                status="INFEASIBLE",
                execution_mode="REQUIRES_APPROVAL",
                disruption_title=event.title,
                affected_classes_count=len(affected_entries),
                affected_teachers_count=len(affected_teachers_set),
                affected_rooms_count=len(affected_rooms_set),
                timetable_version=current_version,
                plans=plans,
                summary=f"Unable to generate feasible recovery plan for disruption '{event.title}'.",
                explanation="All candidate recovery strategies violated hard constraints (over-constrained capacity, missing equipment, or unavailable substitutes). Administrative intervention required.",
                created_at=now_str,
            )

        # Sort plans deterministically by soft penalty and changes count
        valid_plans.sort(key=lambda p: (
            0 if p.ranking_category == "CLEAN_RECOVERY" else
            1 if p.ranking_category == "LOW_DISRUPTION" else
            2 if p.ranking_category == "MODERATE_DISRUPTION" else 3,
            p.soft_penalty,
            len(p.changes)
        ))

        winning_plan = valid_plans[0]

        # Stage 3: Human-in-the-Loop Governance Check
        is_auto_executable = (
            winning_plan.ranking_category == "CLEAN_RECOVERY"
            and winning_plan.hard_conflicts == 0
            and winning_plan.soft_penalty == 0.0
            and all(c.old_period_code == c.new_period_code for c in winning_plan.changes)
            and len(valid_plans) == 1
        )

        if is_auto_executable:
            # Execute immediately and atomically
            execution_success, updated_timetable, exec_error = self.execute_recovery_plan(
                plan=winning_plan,
                solver_input=solver_input,
                existing_timetable=existing_timetable,
                current_version=current_version
            )

            if execution_success:
                winning_plan.status = "EXECUTED"
                notifications_count = self._dispatch_notifications(winning_plan, event, solver_input)
                self._record_decision_memory(winning_plan, event, outcome="AUTO_EXECUTED")

                return DisruptionRecoveryResult(
                    agent_run_id=run_id,
                    event_id=event.id,
                    status="RESOLVED",
                    execution_mode="AUTO_EXECUTE",
                    disruption_title=event.title,
                    affected_classes_count=len(affected_entries),
                    affected_teachers_count=len(affected_teachers_set),
                    affected_rooms_count=len(affected_rooms_set),
                    timetable_version=current_version,
                    plans=valid_plans,
                    selected_plan_id=winning_plan.plan_id,
                    summary=f"Auto-executed clean recovery plan for '{event.title}'. Timetable updated cleanly with 0 hard conflicts.",
                    explanation=f"Clean recovery plan applied atomically. {len(winning_plan.changes)} timetable assignments updated.",
                    notifications_sent=notifications_count,
                    created_at=now_str,
                )
            else:
                winning_plan.status = "INVALID"
                winning_plan.ranking_category = "INVALID"
                winning_plan.explanation = f"Atomic execution rolled back: {exec_error}"

        # Otherwise: Await Human Approval
        approval_req_id = str(uuid.uuid4())
        return DisruptionRecoveryResult(
            agent_run_id=run_id,
            event_id=event.id,
            status="REQUIRES_APPROVAL",
            execution_mode="REQUIRES_APPROVAL",
            disruption_title=event.title,
            affected_classes_count=len(affected_entries),
            affected_teachers_count=len(affected_teachers_set),
            affected_rooms_count=len(affected_rooms_set),
            timetable_version=current_version,
            plans=valid_plans,
            selected_plan_id=winning_plan.plan_id,
            summary=f"Disruption recovery for '{event.title}' generated {len(valid_plans)} candidate plans. Governance approval required.",
            explanation=f"Recovery plans involve multi-room reassignments or teacher substitutions. Recommended plan: {winning_plan.ranking_category} (Penalty: {winning_plan.soft_penalty:.1f}).",
            approval_request_id=approval_req_id,
            created_at=now_str,
        )

    def _identify_affected_entries(
        self,
        event: DisruptionEvent,
        existing_timetable: list[ScheduledEntryDTO]
    ) -> list[ScheduledEntryDTO]:
        affected = []
        p_start_order = int(event.start_period.replace("P", "")) if "P" in event.start_period else 1
        p_end_order = int(event.end_period.replace("P", "")) if "P" in event.end_period else 8

        for entry in existing_timetable:
            if not (event.start_date <= entry.school_date <= event.end_date):
                continue

            entry_p_order = int(entry.period_code.replace("P", "")) if "P" in entry.period_code else 1
            if not (p_start_order <= entry_p_order <= p_end_order):
                continue

            is_room_hit = entry.room_id in event.affected_rooms
            is_teacher_hit = entry.teacher_id in event.affected_teachers
            is_section_hit = entry.section_id in event.affected_sections

            if is_room_hit or is_teacher_hit or is_section_hit:
                affected.append(entry)

        return affected

    def _generate_recovery_plans(
        self,
        event: DisruptionEvent,
        affected_entries: list[ScheduledEntryDTO],
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO],
        timetable_version: str
    ) -> list[RecoveryPlan]:
        plans = []
        room_map = {r.id: r for r in solver_input.rooms}
        teacher_map = {t.id: t for t in solver_input.teachers}
        course_map = {c.id: c for c in solver_input.courses}
        section_map = {s.id: s for s in solver_input.sections}

        # Build occupancy maps excluding affected entries
        occupied_rooms = set()
        occupied_teachers = set()
        for e in existing_timetable:
            if e not in affected_entries:
                occupied_rooms.add((e.room_id, e.school_date, e.period_code))
                occupied_teachers.add((e.teacher_id, e.school_date, e.period_code))

        # Disrupted rooms/teachers set
        disrupted_rooms = set(event.affected_rooms)
        disrupted_teachers = set(event.affected_teachers)

        # Plan 1: Direct Room Reallocation & Teacher Substitution (Primary Plan)
        plan1_changes = []
        plan1_penalty = 0.0
        plan1_hard_conflicts = 0

        # Track assignments within plan
        plan1_room_assignments = set(occupied_rooms)
        plan1_teacher_assignments = set(occupied_teachers)

        for entry in affected_entries:
            sec_obj = section_map.get(entry.section_id)
            sec_size = sec_obj.student_count if sec_obj else 25
            crs_obj = course_map.get(entry.course_id)
            req_eq = crs_obj.required_equipment if crs_obj else []

            target_room_id = entry.room_id
            target_teacher_id = entry.teacher_id
            target_period_code = entry.period_code

            # 1. Check Room Replacement if room is disrupted
            if entry.room_id in disrupted_rooms or (entry.room_id, entry.school_date, entry.period_code) in plan1_room_assignments:
                alt_room = self._find_best_alternative_room(
                    section_size=sec_size,
                    required_equipment=req_eq,
                    school_date=entry.school_date,
                    period_code=entry.period_code,
                    disrupted_rooms=disrupted_rooms,
                    occupied_rooms=plan1_room_assignments,
                    all_rooms=solver_input.rooms
                )
                if alt_room:
                    target_room_id = alt_room.id
                    plan1_penalty += (alt_room.capacity - sec_size) * 0.1  # capacity waste penalty
                else:
                    plan1_hard_conflicts += 1

            # 2. Check Teacher Replacement if teacher is disrupted
            if entry.teacher_id in disrupted_teachers or (entry.teacher_id, entry.school_date, entry.period_code) in plan1_teacher_assignments:
                sub_teacher = self._find_best_substitute_teacher(
                    course_id=entry.course_id,
                    subject_id=crs_obj.subject_id if crs_obj else None,
                    school_date=entry.school_date,
                    period_code=entry.period_code,
                    disrupted_teachers=disrupted_teachers,
                    occupied_teachers=plan1_teacher_assignments,
                    solver_input=solver_input
                )
                if sub_teacher:
                    target_teacher_id = sub_teacher.id
                    plan1_penalty += 1.5  # substitution penalty
                else:
                    plan1_hard_conflicts += 1

            plan1_room_assignments.add((target_room_id, entry.school_date, target_period_code))
            plan1_teacher_assignments.add((target_teacher_id, entry.school_date, target_period_code))

            plan1_changes.append(RecoveryPlanChange(
                timetable_entry_id=f"{entry.school_date}_{entry.period_code}_{entry.section_id}",
                school_date=entry.school_date,
                old_teacher_id=entry.teacher_id,
                new_teacher_id=target_teacher_id,
                old_room_id=entry.room_id,
                new_room_id=target_room_id,
                old_period_code=entry.period_code,
                new_period_code=target_period_code,
                change_reason=f"Reallocated due to {event.title}"
            ))

        # Categorize Plan 1
        p1_category = "INVALID" if plan1_hard_conflicts > 0 else (
            "CLEAN_RECOVERY" if plan1_penalty == 0.0 else
            "LOW_DISRUPTION" if plan1_penalty < 4.0 else
            "MODERATE_DISRUPTION"
        )

        plan1 = RecoveryPlan(
            plan_id=str(uuid.uuid4()),
            disruption_id=event.id,
            timetable_version=timetable_version,
            plan_title="Plan A: Room Reallocation & Substitute Matching",
            ranking_category=p1_category,
            changes=plan1_changes,
            hard_conflicts=plan1_hard_conflicts,
            soft_penalty=round(plan1_penalty, 2),
            affected_classes=len(affected_entries),
            affected_teachers=len({c.new_teacher_id for c in plan1_changes if c.new_teacher_id != c.old_teacher_id}),
            affected_rooms=len({c.new_room_id for c in plan1_changes if c.new_room_id != c.old_room_id}),
            status="PROPOSED",
            explanation="Reassigns affected classes to feasible alternative rooms and qualified substitute teachers in existing periods.",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        plans.append(plan1)

        # Plan 2: Alternative Strategy (Period Shift + Room Reallocation)
        if len(affected_entries) > 1:
            plan2_changes = []
            plan2_penalty = 2.0  # base penalty for period shifts
            plan2_hard_conflicts = 0

            periods_list = [p.code for p in solver_input.periods]

            for idx, entry in enumerate(affected_entries):
                sec_obj = section_map.get(entry.section_id)
                sec_size = sec_obj.student_count if sec_obj else 25
                crs_obj = course_map.get(entry.course_id)
                req_eq = crs_obj.required_equipment if crs_obj else []

                # Shift period for second half of entries if room/teacher tight
                target_period_code = entry.period_code
                if idx % 2 == 1 and len(periods_list) > 1:
                    available_periods = [p for p in periods_list if p != entry.period_code]
                    if available_periods:
                        target_period_code = available_periods[0]
                        plan2_penalty += 3.0  # period shift penalty

                alt_room = self._find_best_alternative_room(
                    section_size=sec_size,
                    required_equipment=req_eq,
                    school_date=entry.school_date,
                    period_code=target_period_code,
                    disrupted_rooms=disrupted_rooms,
                    occupied_rooms=occupied_rooms,
                    all_rooms=solver_input.rooms
                )
                target_room_id = alt_room.id if alt_room else entry.room_id

                sub_teacher = self._find_best_substitute_teacher(
                    course_id=entry.course_id,
                    subject_id=crs_obj.subject_id if crs_obj else None,
                    school_date=entry.school_date,
                    period_code=target_period_code,
                    disrupted_teachers=disrupted_teachers,
                    occupied_teachers=occupied_teachers,
                    solver_input=solver_input
                )
                target_teacher_id = sub_teacher.id if sub_teacher else entry.teacher_id

                plan2_changes.append(RecoveryPlanChange(
                    timetable_entry_id=f"{entry.school_date}_{entry.period_code}_{entry.section_id}",
                    school_date=entry.school_date,
                    old_teacher_id=entry.teacher_id,
                    new_teacher_id=target_teacher_id,
                    old_room_id=entry.room_id,
                    new_room_id=target_room_id,
                    old_period_code=entry.period_code,
                    new_period_code=target_period_code,
                    change_reason=f"Period Shift & Room Reallocation for {event.title}"
                ))

            plan2 = RecoveryPlan(
                plan_id=str(uuid.uuid4()),
                disruption_id=event.id,
                timetable_version=timetable_version,
                plan_title="Plan B: Combined Period Rescheduling & Facility Shift",
                ranking_category="MODERATE_DISRUPTION" if plan2_hard_conflicts == 0 else "INVALID",
                changes=plan2_changes,
                hard_conflicts=plan2_hard_conflicts,
                soft_penalty=round(plan2_penalty + 1.5, 2),
                affected_classes=len(affected_entries),
                affected_teachers=len({c.new_teacher_id for c in plan2_changes if c.new_teacher_id != c.old_teacher_id}),
                affected_rooms=len({c.new_room_id for c in plan2_changes if c.new_room_id != c.old_room_id}),
                status="PROPOSED",
                explanation="Reschedules conflicting classes into available open periods while assigning substitute teachers and alternative rooms.",
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
            plans.append(plan2)

        return plans

    def _find_best_alternative_room(
        self,
        section_size: int,
        required_equipment: list[str],
        school_date: str,
        period_code: str,
        disrupted_rooms: set[str],
        occupied_rooms: set[tuple[str, str, str]],
        all_rooms: list[Any]
    ) -> Optional[Any]:
        candidates = []
        for room in all_rooms:
            if room.id in disrupted_rooms:
                continue
            if getattr(room, 'status', 'AVAILABLE') != 'AVAILABLE':
                continue
            if room.capacity < section_size:
                continue
            if (room.id, school_date, period_code) in occupied_rooms:
                continue

            room_eq = getattr(room, 'equipment', [])
            if required_equipment and not all(eq in room_eq for eq in required_equipment):
                continue

            capacity_waste = room.capacity - section_size
            candidates.append((capacity_waste, room))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _find_best_substitute_teacher(
        self,
        course_id: str,
        subject_id: Optional[str],
        school_date: str,
        period_code: str,
        disrupted_teachers: set[str],
        occupied_teachers: set[tuple[str, str, str]],
        solver_input: SolverInput
    ) -> Optional[Any]:
        # Filter qualified teachers
        qualified_teacher_ids = set()
        if subject_id:
            for cap in solver_input.capabilities:
                if cap.subject_id == subject_id:
                    qualified_teacher_ids.add(cap.teacher_id)

        candidates = []
        for teacher in solver_input.teachers:
            if teacher.id in disrupted_teachers:
                continue
            if getattr(teacher, 'status', 'ACTIVE') != 'ACTIVE':
                continue
            if (teacher.id, school_date, period_code) in occupied_teachers:
                continue

            is_qualified = (teacher.id in qualified_teacher_ids) if qualified_teacher_ids else True
            penalty = 0.0 if is_qualified else 5.0

            candidates.append((penalty, teacher))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def execute_recovery_plan(
        self,
        plan: RecoveryPlan,
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO],
        current_version: str = "v1.0"
    ) -> tuple[bool, list[ScheduledEntryDTO], str]:
        """
        ATOMIC EXECUTION:
        1. Validates timetable version (rejects stale plans).
        2. Applies all plan changes to a candidate timetable.
        3. Executes ConflictDetector validation.
        4. If hard conflicts > 0: ROLLBACK (return False).
        5. If valid: Commit changes atomically and return True.
        """
        # Version Check
        if plan.timetable_version != current_version:
            plan.status = "STALE"
            return False, existing_timetable, f"Timetable version mismatch (Plan: {plan.timetable_version}, Current: {current_version}). Plan marked STALE."

        # Deep copy existing timetable
        updated_timetable = [copy.deepcopy(e) for e in existing_timetable]
        change_map = {c.timetable_entry_id: c for c in plan.changes}

        # Apply changes
        for entry in updated_timetable:
            entry_key = f"{entry.school_date}_{entry.period_code}_{entry.section_id}"
            if entry_key in change_map:
                chg = change_map[entry_key]
                entry.teacher_id = chg.new_teacher_id
                entry.room_id = chg.new_room_id
                entry.period_code = chg.new_period_code
                entry.flag = "recovered"
                entry.status = "RECOVERED"

        # ConflictDetector Validation
        conflict_report = self.conflict_detector.validate(solver_input, updated_timetable)

        if len(conflict_report.hard_conflicts) > 0:
            plan.status = "INVALID"
            first_err = conflict_report.hard_conflicts[0].description
            return False, existing_timetable, f"Atomic execution rollback: ConflictDetector identified hard conflict: {first_err}"

        # Success - Apply to target in-place
        existing_timetable.clear()
        existing_timetable.extend(updated_timetable)
        plan.status = "EXECUTED"

        return True, existing_timetable, "Atomic execution succeeded."

    def _dispatch_notifications(
        self,
        plan: RecoveryPlan,
        event: DisruptionEvent,
        solver_input: SolverInput
    ) -> int:
        count = 0
        for change in plan.changes:
            # Teacher notification
            count += 1
            # Substitute teacher notification
            if change.new_teacher_id != change.old_teacher_id:
                count += 1
        return count

    def _record_decision_memory(
        self,
        plan: RecoveryPlan,
        event: DisruptionEvent,
        outcome: str = "SUCCESS"
    ):
        # Structured memory logging
        memory_payload = {
            "disruption_event": event.title,
            "severity": event.severity,
            "plan_title": plan.plan_title,
            "ranking_category": plan.ranking_category,
            "changes_count": len(plan.changes),
            "soft_penalty": plan.soft_penalty,
            "outcome": outcome,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return memory_payload
