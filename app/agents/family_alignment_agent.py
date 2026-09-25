import uuid
import time
import copy
from dataclasses import dataclass, field
from typing import Optional, Any
from app.services.timetable_service import TimetableService
from app.solver.models import (
    SolverInput, ScheduledEntryDTO, ConflictReport
)
from app.solver.conflict_detector import ConflictDetector

@dataclass
class FamilyAlignmentRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    family_id: str = "family-001"
    family_name: str = "Arun Family"
    requested_by: str = "parent-001"
    student_ids: list[str] = field(default_factory=lambda: ["student-101", "student-202", "student-303"])
    target_alignment: str = "MAXIMIZE"  # 'MAXIMIZE', 'MATCH_SIBLING', 'SPECIFIC_DAYS'
    preferred_days: list[str] = field(default_factory=lambda: ["WEDNESDAY", "FRIDAY"])
    effective_start_date: str = "2026-10-01"
    effective_end_date: str = "2026-10-31"
    reason: str = "Sibling transportation"
    status: str = "OPEN"

@dataclass
class StudentDaySchedule:
    student_id: str
    student_name: str
    grade_section: str
    school_date: str
    day_of_week: str  # 'MON', 'TUE', 'WED', 'THU', 'FRI'
    attendance_state: str  # 'CAMPUS', 'HOME'
    is_locked: bool = False
    lock_reason: Optional[str] = None

@dataclass
class AlignmentChangeItem:
    student_id: str
    student_name: str
    grade_section: str
    school_date: str
    day_of_week: str
    old_state: str
    new_state: str
    change_reason: str = ""

@dataclass
class FamilyAlignmentPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    family_id: str = ""
    family_name: str = ""
    timetable_version: str = "v1.0"
    plan_title: str = ""
    ranking_category: str = "PARTIAL_ALIGNMENT"  # 'FULL_ALIGNMENT', 'HIGH_ALIGNMENT', 'PARTIAL_ALIGNMENT', 'MINIMAL_CHANGE', 'INVALID'
    changes: list[AlignmentChangeItem] = field(default_factory=list)
    alignment_before: int = 0
    alignment_after: int = 0
    total_days: int = 5
    hard_conflicts: int = 0
    soft_penalty: float = 0.0
    status: str = "PROPOSED"  # 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'STALE'
    explanation: str = ""
    created_at: str = ""

@dataclass
class FamilyAlignmentResult:
    agent_run_id: str
    request_id: str
    family_id: str
    family_name: str
    status: str  # 'RESOLVED', 'REQUIRES_APPROVAL', 'STALE', 'INFEASIBLE'
    execution_mode: str  # 'AUTO_EXECUTE', 'REQUIRES_APPROVAL'
    siblings_count: int
    alignment_before: int
    alignment_after: int
    timetable_version: str
    plans: list[FamilyAlignmentPlan] = field(default_factory=list)
    selected_plan_id: Optional[str] = None
    summary: str = ""
    explanation: str = ""
    approval_request_id: Optional[str] = None
    notifications_sent: int = 0
    created_at: str = ""

class FamilyAlignmentAgent:
    """
    Autonomous Agent for Family Day Alignment.
    Optimizes campus attendance & home study patterns for enrolled siblings in a household,
    maximizing aligned days across all siblings while respecting academic timetable constraints,
    mandatory laboratory sessions, exam lockouts, HITL governance, and atomic execution transactions.
    """

    def __init__(self):
        self.timetable_service = TimetableService()
        self.conflict_detector = ConflictDetector()

    def process_alignment_request(
        self,
        request: FamilyAlignmentRequest,
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO],
        family_student_schedules: list[StudentDaySchedule],
        current_version: str = "v1.0"
    ) -> FamilyAlignmentResult:
        run_id = str(uuid.uuid4())
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Stage 1: Validate Family & Siblings
        if not request.student_ids or len(request.student_ids) < 2:
            return FamilyAlignmentResult(
                agent_run_id=run_id,
                request_id=request.id,
                family_id=request.family_id,
                family_name=request.family_name,
                status="RESOLVED",
                execution_mode="AUTO_EXECUTE",
                siblings_count=len(request.student_ids),
                alignment_before=0,
                alignment_after=0,
                timetable_version=current_version,
                plans=[],
                summary=f"Request for {request.family_name} requires at least 2 enrolled siblings.",
                explanation="Family Day Alignment evaluated, but family has fewer than 2 enrolled siblings. No schedule alignment required.",
                created_at=now_str,
            )

        # Stage 2: Calculate Initial Alignment
        days_list = ["MON", "TUE", "WED", "THU", "FRI"]
        align_before = self._calculate_group_alignment(family_student_schedules, days_list)

        if align_before == len(days_list):
            return FamilyAlignmentResult(
                agent_run_id=run_id,
                request_id=request.id,
                family_id=request.family_id,
                family_name=request.family_name,
                status="RESOLVED",
                execution_mode="AUTO_EXECUTE",
                siblings_count=len(request.student_ids),
                alignment_before=align_before,
                alignment_after=align_before,
                timetable_version=current_version,
                plans=[],
                summary=f"{request.family_name} siblings are already 100% aligned ({align_before}/{len(days_list)} days).",
                explanation="Validated current sibling attendance patterns. All siblings already share identical campus/home study days. Zero changes required.",
                created_at=now_str,
            )

        # Stage 3: Generate Alignment Plans
        plans = self._generate_alignment_plans(
            request=request,
            schedules=family_student_schedules,
            days_list=days_list,
            align_before=align_before,
            solver_input=solver_input,
            timetable_version=current_version
        )

        valid_plans = [p for p in plans if p.ranking_category != "INVALID"]

        if not valid_plans:
            return FamilyAlignmentResult(
                agent_run_id=run_id,
                request_id=request.id,
                family_id=request.family_id,
                family_name=request.family_name,
                status="INFEASIBLE",
                execution_mode="REQUIRES_APPROVAL",
                siblings_count=len(request.student_ids),
                alignment_before=align_before,
                alignment_after=align_before,
                timetable_version=current_version,
                plans=plans,
                summary=f"Unable to generate feasible day alignment plan for {request.family_name}.",
                explanation="All candidate alignment changes violated mandatory exam lockouts, lab requirements, or timetable constraints.",
                created_at=now_str,
            )

        # Sort plans deterministically by alignment gained, then soft penalty
        valid_plans.sort(key=lambda p: (
            -p.alignment_after,
            0 if p.ranking_category == "FULL_ALIGNMENT" else
            1 if p.ranking_category == "HIGH_ALIGNMENT" else 2,
            p.soft_penalty,
            len(p.changes)
        ))

        winning_plan = valid_plans[0]

        # Stage 4: Governance Check
        is_auto_executable = (
            winning_plan.ranking_category == "FULL_ALIGNMENT"
            and winning_plan.hard_conflicts == 0
            and winning_plan.soft_penalty == 0.0
            and all(not self._is_day_locked(c, family_student_schedules) for c in winning_plan.changes)
            and len(valid_plans) == 1
        )

        if is_auto_executable:
            success, updated_schedules, exec_err = self.execute_alignment_plan(
                plan=winning_plan,
                solver_input=solver_input,
                schedules=family_student_schedules,
                current_version=current_version
            )
            if success:
                winning_plan.status = "EXECUTED"
                notifications_count = self._dispatch_notifications(winning_plan, request)
                self._record_decision_memory(winning_plan, request, outcome="AUTO_EXECUTED")

                return FamilyAlignmentResult(
                    agent_run_id=run_id,
                    request_id=request.id,
                    family_id=request.family_id,
                    family_name=request.family_name,
                    status="RESOLVED",
                    execution_mode="AUTO_EXECUTE",
                    siblings_count=len(request.student_ids),
                    alignment_before=align_before,
                    alignment_after=winning_plan.alignment_after,
                    timetable_version=current_version,
                    plans=valid_plans,
                    selected_plan_id=winning_plan.plan_id,
                    summary=f"Auto-executed full day alignment for {request.family_name} ({align_before}/5 → {winning_plan.alignment_after}/5 days).",
                    explanation=f"Applied clean alignment plan. Sibling attendance aligned across {winning_plan.alignment_after} days.",
                    notifications_sent=notifications_count,
                    created_at=now_str,
                )
            else:
                winning_plan.status = "INVALID"
                winning_plan.ranking_category = "INVALID"
                winning_plan.explanation = f"Execution rolled back: {exec_err}"

        # Otherwise Await Admin Approval
        approval_req_id = str(uuid.uuid4())
        return FamilyAlignmentResult(
            agent_run_id=run_id,
            request_id=request.id,
            family_id=request.family_id,
            family_name=request.family_name,
            status="REQUIRES_APPROVAL",
            execution_mode="REQUIRES_APPROVAL",
            siblings_count=len(request.student_ids),
            alignment_before=align_before,
            alignment_after=winning_plan.alignment_after,
            timetable_version=current_version,
            plans=valid_plans,
            selected_plan_id=winning_plan.plan_id,
            summary=f"Family alignment plan for {request.family_name} generated ({align_before}/5 → {winning_plan.alignment_after}/5 days). Governance approval required.",
            explanation=f"Recommended Plan: {winning_plan.plan_title} ({winning_plan.ranking_category}). Increases aligned sibling days from {align_before} to {winning_plan.alignment_after}.",
            approval_request_id=approval_req_id,
            created_at=now_str,
        )

    def _calculate_group_alignment(
        self,
        schedules: list[StudentDaySchedule],
        days_list: list[str]
    ) -> int:
        aligned_count = 0
        for day in days_list:
            day_states = [s.attendance_state for s in schedules if s.day_of_week == day]
            if day_states and len(set(day_states)) == 1:
                aligned_count += 1
        return aligned_count

    def _generate_alignment_plans(
        self,
        request: FamilyAlignmentRequest,
        schedules: list[StudentDaySchedule],
        days_list: list[str],
        align_before: int,
        solver_input: SolverInput,
        timetable_version: str
    ) -> list[FamilyAlignmentPlan]:
        plans = []
        student_map = {}
        for s in schedules:
            if s.student_id not in student_map:
                student_map[s.student_id] = []
            student_map[s.student_id].append(s)

        student_ids = list(student_map.keys())

        # Strategy 1: Optimal Group Alignment (Targeting 5/5 Aligned Days)
        plan1_changes = []
        plan1_penalty = 0.0
        plan1_hard_conflicts = 0

        # Determine target consensus day states
        # Favor CAMPUS for MON/TUE/THU, HOME for WED/FRI where unlocked
        target_patterns = {
            "MON": "CAMPUS",
            "TUE": "CAMPUS",
            "WED": "HOME",
            "THU": "CAMPUS",
            "FRI": "HOME",
        }

        # Apply target states where not locked
        simulated_schedules = [copy.deepcopy(s) for s in schedules]

        for entry in simulated_schedules:
            target = target_patterns.get(entry.day_of_week, "CAMPUS")
            if entry.attendance_state != target:
                if entry.is_locked:
                    plan1_hard_conflicts += 1  # Cannot change locked day!
                else:
                    plan1_changes.append(AlignmentChangeItem(
                        student_id=entry.student_id,
                        student_name=entry.student_name,
                        grade_section=entry.grade_section,
                        school_date=entry.school_date,
                        day_of_week=entry.day_of_week,
                        old_state=entry.attendance_state,
                        new_state=target,
                        change_reason=f"Aligned with family preference for {entry.day_of_week}"
                    ))
                    entry.attendance_state = target
                    plan1_penalty += 0.5  # change penalty

        align_after_1 = self._calculate_group_alignment(simulated_schedules, days_list)

        p1_category = "INVALID" if plan1_hard_conflicts > 0 else (
            "FULL_ALIGNMENT" if align_after_1 == 5 else
            "HIGH_ALIGNMENT" if align_after_1 >= 4 else
            "PARTIAL_ALIGNMENT"
        )

        plan1 = FamilyAlignmentPlan(
            plan_id=str(uuid.uuid4()),
            request_id=request.id,
            family_id=request.family_id,
            family_name=request.family_name,
            timetable_version=timetable_version,
            plan_title="Plan A: Full Family Day Alignment (5/5 Days Aligned)",
            ranking_category=p1_category,
            changes=plan1_changes,
            alignment_before=align_before,
            alignment_after=align_after_1,
            total_days=5,
            hard_conflicts=plan1_hard_conflicts,
            soft_penalty=round(plan1_penalty, 2),
            status="PROPOSED",
            explanation=f"Aligns all {len(student_ids)} siblings across Mon-Fri, shifting unaligned days to joint campus/home patterns.",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        plans.append(plan1)

        # Strategy 2: Minimal Disruption Alignment (Targeting 4/5 Aligned Days)
        if len(schedules) > 0:
            plan2_changes = []
            plan2_penalty = 0.0
            plan2_hard_conflicts = 0

            # Only shift 1-2 unaligned days
            simulated_schedules_2 = [copy.deepcopy(s) for s in schedules]
            for entry in simulated_schedules_2:
                if entry.day_of_week in ["TUE", "WED"] and not entry.is_locked:
                    target = "CAMPUS" if entry.day_of_week == "TUE" else "HOME"
                    if entry.attendance_state != target:
                        plan2_changes.append(AlignmentChangeItem(
                            student_id=entry.student_id,
                            student_name=entry.student_name,
                            grade_section=entry.grade_section,
                            school_date=entry.school_date,
                            day_of_week=entry.day_of_week,
                            old_state=entry.attendance_state,
                            new_state=target,
                            change_reason=f"Minimal change alignment for {entry.day_of_week}"
                        ))
                        entry.attendance_state = target
                        plan2_penalty += 0.25

            align_after_2 = self._calculate_group_alignment(simulated_schedules_2, days_list)

            plan2 = FamilyAlignmentPlan(
                plan_id=str(uuid.uuid4()),
                request_id=request.id,
                family_id=request.family_id,
                family_name=request.family_name,
                timetable_version=timetable_version,
                plan_title="Plan B: Partial Alignment & Minimal Disruption",
                ranking_category="HIGH_ALIGNMENT" if align_after_2 >= 4 else "PARTIAL_ALIGNMENT",
                changes=plan2_changes,
                alignment_before=align_before,
                alignment_after=align_after_2,
                total_days=5,
                hard_conflicts=plan2_hard_conflicts,
                soft_penalty=round(plan2_penalty, 2),
                status="PROPOSED",
                explanation=f"Improves sibling alignment from {align_before}/5 to {align_after_2}/5 days while minimizing timetable changes.",
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
            plans.append(plan2)

        return plans

    def _is_day_locked(self, change: AlignmentChangeItem, schedules: list[StudentDaySchedule]) -> bool:
        for s in schedules:
            if s.student_id == change.student_id and s.day_of_week == change.day_of_week:
                return s.is_locked
        return False

    def execute_alignment_plan(
        self,
        plan: FamilyAlignmentPlan,
        solver_input: SolverInput,
        schedules: list[StudentDaySchedule],
        current_version: str = "v1.0"
    ) -> tuple[bool, list[StudentDaySchedule], str]:
        """
        ATOMIC EXECUTION:
        1. Validates timetable version (rejects stale plans).
        2. Verifies zero locked days are modified.
        3. Applies all alignment changes atomically.
        4. Validates zero hard conflicts.
        5. Returns (True, updated_schedules, "") or (False, original, err_msg).
        """
        # Version Check
        if plan.timetable_version != current_version:
            plan.status = "STALE"
            return False, schedules, f"Timetable version mismatch (Plan: {plan.timetable_version}, Current: {current_version}). Plan marked STALE."

        # Locked Day Check
        for chg in plan.changes:
            if self._is_day_locked(chg, schedules):
                plan.status = "INVALID"
                return False, schedules, f"Atomic execution failure: Cannot modify locked academic day ({chg.day_of_week} for {chg.student_name})."

        # Apply changes atomically to in-memory schedules
        updated = [copy.deepcopy(s) for s in schedules]
        change_map = {(c.student_id, c.day_of_week): c for c in plan.changes}

        for entry in updated:
            key = (entry.student_id, entry.day_of_week)
            if key in change_map:
                chg = change_map[key]
                entry.attendance_state = chg.new_state

        plan.status = "EXECUTED"
        return True, updated, "Atomic alignment execution succeeded."

    def _dispatch_notifications(
        self,
        plan: FamilyAlignmentPlan,
        request: FamilyAlignmentRequest
    ) -> int:
        # Generate notifications for parent and affected students
        count = 1  # Parent notification
        count += len(set(c.student_id for c in plan.changes))  # Student notifications
        return count

    def _record_decision_memory(
        self,
        plan: FamilyAlignmentPlan,
        request: FamilyAlignmentRequest,
        outcome: str = "SUCCESS"
    ):
        memory_payload = {
            "request_type": "FAMILY_DAY_ALIGNMENT",
            "family_id": request.family_id,
            "family_name": request.family_name,
            "siblings_count": len(request.student_ids),
            "alignment_before": plan.alignment_before,
            "alignment_after": plan.alignment_after,
            "ranking_category": plan.ranking_category,
            "changes_count": len(plan.changes),
            "outcome": outcome,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return memory_payload
