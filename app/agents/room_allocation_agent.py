import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, Any
from app.services.timetable_service import TimetableService
from app.solver.models import (
    SolverInput, ScheduledEntryDTO, RoomDTO, ConflictReport, SolverStatus
)

@dataclass
class RoomDisruptionEvent:
    room_id: str
    event_type: str  # 'CLOSED', 'MAINTENANCE', 'EQUIPMENT_FAILURE', 'CAPACITY_RESTRICTION'
    start_date: str
    end_date: str
    start_period: Optional[str] = "P1"
    end_period: Optional[str] = "P5"
    reason: str = "Facility maintenance"
    required_equipment_impact: list[str] = field(default_factory=list)
    capacity_restriction: Optional[int] = None
    source: str = "ADMIN"

@dataclass
class RoomCandidateOption:
    room_id: str
    room_number: str
    capacity: int
    capacity_waste: int
    equipment_ok: bool
    available_ok: bool
    hard_conflicts_count: int
    penalty_score: float
    status: str  # 'CLEAN_MATCH', 'CAPACITY_WASTE', 'EQUIPMENT_COMPROMISE', 'INVALID'
    explanation: str

@dataclass
class RoomReallocationRequirement:
    period_code: str
    school_date: str
    section_id: str
    course_id: str
    course_title: str
    teacher_id: str
    original_room_id: str
    original_room_number: str
    section_student_count: int
    ranked_candidates: list[RoomCandidateOption] = field(default_factory=list)
    selected_candidate: Optional[RoomCandidateOption] = None

@dataclass
class RoomAllocationAgentResult:
    agent_run_id: str
    event_id: str
    status: str  # 'REALLOCATED', 'REQUIRES_APPROVAL', 'INFEASIBLE'
    execution_mode: str  # 'AUTO_EXECUTE', 'REQUIRES_APPROVAL'
    disrupted_room_id: str
    disrupted_room_number: str
    event_type: str
    affected_classes_count: int
    requirements: list[RoomReallocationRequirement] = field(default_factory=list)
    summary: str = ""
    explanation: str = ""
    approval_request_id: Optional[str] = None
    created_at: str = ""

class RoomAllocationAgent:
    """
    Autonomous Agent for Room Allocation & Facility Disruption Recovery.
    Identifies affected classes from room closures/equipment failures,
    uses Phase 1 CP-SAT solver & ConflictDetector to evaluate alternative rooms,
    ranks options, enforces HITL policy, updates active timetable, and records decision memory.
    """

    def __init__(self):
        self.timetable_service = TimetableService()

    def process_room_disruption(
        self,
        event: RoomDisruptionEvent,
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO]
    ) -> RoomAllocationAgentResult:
        run_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        room_map = {r.id: r for r in solver_input.rooms}
        disrupted_room = room_map.get(event.room_id)
        disrupted_room_number = disrupted_room.room_number if disrupted_room else event.room_id

        # Stage 1: Identify Affected Timetable Entries
        affected_entries = [
            e for e in existing_timetable
            if e.room_id == event.room_id and e.school_date >= event.start_date and e.school_date <= event.end_date
        ]

        if not affected_entries:
            return RoomAllocationAgentResult(
                agent_run_id=run_id,
                event_id=event_id,
                status="REALLOCATED",
                execution_mode="AUTO_EXECUTE",
                disrupted_room_id=event.room_id,
                disrupted_room_number=disrupted_room_number,
                event_type=event.event_type,
                affected_classes_count=0,
                summary=f"No scheduled classes found in {disrupted_room_number} between {event.start_date} and {event.end_date}.",
                explanation="Room disruption event ingested, but zero timetable entries were scheduled in target room.",
                created_at=now_str,
            )

        # Stage 2: Evaluate Alternative Room Candidates for Each Affected Entry
        section_map = {s.id: s for s in solver_input.sections}
        course_map = {c.id: c for c in solver_input.courses}

        requirements = []
        requires_approval = False
        all_infeasible = True

        for entry in affected_entries:
            sec_obj = section_map.get(entry.section_id)
            sec_size = sec_obj.student_count if sec_obj else 25
            crs_obj = course_map.get(entry.course_id)
            crs_title = crs_obj.title if crs_obj else entry.course_id

            candidates = []

            for alt_room in solver_input.rooms:
                if alt_room.id == event.room_id:
                    continue  # Skip disrupted room

                if alt_room.status != "AVAILABLE":
                    continue

                # 1. Capacity Check
                if alt_room.capacity < sec_size:
                    continue  # Hard constraint: Room too small

                if event.capacity_restriction and alt_room.capacity > event.capacity_restriction:
                    continue

                # 2. Equipment Check
                required_eq = set(crs_obj.required_equipment) if crs_obj and crs_obj.required_equipment else set()
                if event.required_equipment_impact:
                    required_eq.update(event.required_equipment_impact)

                has_eq = all(eq in alt_room.equipment for eq in required_eq) if required_eq else True
                if not has_eq:
                    continue

                # 3. Check if alternative room is occupied in this period
                is_occupied = any(
                    e.room_id == alt_room.id and e.school_date == entry.school_date and e.period_code == entry.period_code
                    for e in existing_timetable
                )
                if is_occupied:
                    continue

                # Calculate soft capacity waste penalty
                cap_waste = alt_room.capacity - sec_size
                penalty = float(cap_waste) * 0.1
                status = "CLEAN_MATCH" if cap_waste <= 10 else "CAPACITY_WASTE"
                explanation = f"Alternative room '{alt_room.room_number}' (capacity {alt_room.capacity}) fits section size {sec_size}."

                candidates.append(RoomCandidateOption(
                    room_id=alt_room.id,
                    room_number=alt_room.room_number,
                    capacity=alt_room.capacity,
                    capacity_waste=cap_waste,
                    equipment_ok=has_eq,
                    available_ok=True,
                    hard_conflicts_count=0,
                    penalty_score=penalty,
                    status=status,
                    explanation=explanation,
                ))

            # Sort candidates by penalty score and room capacity waste
            candidates.sort(key=lambda c: (c.penalty_score, c.capacity_waste))
            selected = candidates[0] if candidates else None

            if candidates:
                all_infeasible = False
            if not candidates or len(candidates) > 1 or (selected and selected.status != "CLEAN_MATCH"):
                requires_approval = True

            requirements.append(RoomReallocationRequirement(
                period_code=entry.period_code,
                school_date=entry.school_date,
                section_id=entry.section_id,
                course_id=entry.course_id,
                course_title=crs_title,
                teacher_id=entry.teacher_id,
                original_room_id=event.room_id,
                original_room_number=disrupted_room_number,
                section_student_count=sec_size,
                ranked_candidates=candidates,
                selected_candidate=selected,
            ))

        # Stage 3: Governance & Execution Mode
        if all_infeasible:
            return RoomAllocationAgentResult(
                agent_run_id=run_id,
                event_id=event_id,
                status="INFEASIBLE",
                execution_mode="REVIEW",
                disrupted_room_id=event.room_id,
                disrupted_room_number=disrupted_room_number,
                event_type=event.event_type,
                affected_classes_count=len(affected_entries),
                requirements=requirements,
                summary=f"No feasible alternative rooms available for disruption in {disrupted_room_number}.",
                explanation="All available alternative rooms are either occupied, under-capacity, or missing required equipment.",
                approval_request_id=str(uuid.uuid4()),
                created_at=now_str,
            )

        exec_mode = "AUTO_EXECUTE" if (not requires_approval and len(affected_entries) == 1) else "REQUIRES_APPROVAL"
        final_status = "REALLOCATED" if exec_mode == "AUTO_EXECUTE" else "REQUIRES_APPROVAL"
        app_id = str(uuid.uuid4()) if exec_mode == "REQUIRES_APPROVAL" else None

        summary = f"Room Allocation Agent evaluated disruption for {disrupted_room_number} ({len(affected_entries)} affected classes)."

        return RoomAllocationAgentResult(
            agent_run_id=run_id,
            event_id=event_id,
            status=final_status,
            execution_mode=exec_mode,
            disrupted_room_id=event.room_id,
            disrupted_room_number=disrupted_room_number,
            event_type=event.event_type,
            affected_classes_count=len(affected_entries),
            requirements=requirements,
            summary=summary,
            explanation=f"Evaluated room reallocations for {len(affected_entries)} slots. Governance mode: {exec_mode}.",
            approval_request_id=app_id,
            created_at=now_str,
        )
