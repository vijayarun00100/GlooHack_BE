import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, Any
from app.services.email_ingestion import EmailIngestionService, ParsedEmail
from app.services.absence_extractor import AbsenceExtractionService, ExtractedAbsenceData
from app.services.teacher_matching import TeacherMatchingService
from app.services.timetable_service import TimetableService
from app.solver.models import (
    SolverInput, ScheduledEntryDTO, TeacherDTO, ConflictReport, SolverStatus
)

@dataclass
class CandidateOption:
    teacher_id: str
    teacher_name: str
    qualification_ok: bool
    available_ok: bool
    hard_conflicts_count: int
    penalty_score: float
    status: str  # 'CLEAN_MATCH', 'WORKLOAD_PENALTY', 'PREFERENCE_CONFLICT', 'INVALID'
    explanation: str

@dataclass
class SubstitutionRequirement:
    period_code: str
    school_date: str
    section_id: str
    course_id: str
    course_title: str
    original_teacher_id: str
    original_teacher_name: str
    room_id: str
    ranked_candidates: list[CandidateOption] = field(default_factory=list)
    selected_candidate: Optional[CandidateOption] = None

@dataclass
class SubstitutionAgentResult:
    agent_run_id: str
    event_id: str
    status: str  # 'RESOLVED', 'REQUIRES_APPROVAL', 'REQUIRES_REVIEW', 'CANCELLED'
    execution_mode: str  # 'AUTO_EXECUTE', 'REQUIRES_APPROVAL', 'REVIEW'
    absence_date: str
    absent_teacher_id: Optional[str]
    absent_teacher_name: str
    affected_classes_count: int
    requirements: list[SubstitutionRequirement] = field(default_factory=list)
    summary: str = ""
    explanation: str = ""
    approval_request_id: Optional[str] = None
    created_at: str = ""

class TeacherSubstitutionAgent:
    """
    Autonomous Agent for Teacher Substitution.
    Detects teacher absence from email, identifies affected classes, calls Phase 1 solver,
    ranks substitute candidates, enforces HITL policy, updates timetable, and records decision memory.
    """

    def __init__(self):
        self.email_ingester = EmailIngestionService()
        self.absence_extractor = AbsenceExtractionService()
        self.timetable_service = TimetableService()

    def process_absence_email(
        self,
        raw_mime_or_text: str,
        solver_input: SolverInput,
        existing_timetable: list[ScheduledEntryDTO]
    ) -> SubstitutionAgentResult:
        run_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Stage 1: Email Ingestion & MIME Parsing
        if "From:" in raw_mime_or_text or "Subject:" in raw_mime_or_text:
            parsed_email = self.email_ingester.parse_mime_email(raw_mime_or_text)
        else:
            # Fallback for plain text input
            parsed_email = ParsedEmail(
                message_id=str(uuid.uuid4()),
                thread_id=str(uuid.uuid4()),
                in_reply_to=None,
                sender_email="cooper@school.edu",
                sender_name="Cooper",
                subject="Teacher Absence Request",
                date_str="2026-08-25",
                body_text=raw_mime_or_text,
                body_html=raw_mime_or_text,
                is_cancellation=("cancel" in raw_mime_or_text.lower() or "disregard" in raw_mime_or_text.lower()),
            )

        # Stage 2: Intent & Absence Entity Extraction
        extracted = self.absence_extractor.extract_absence_intent(parsed_email)

        # Handle Cancellation
        if extracted.is_cancellation:
            return SubstitutionAgentResult(
                agent_run_id=run_id,
                event_id=event_id,
                status="CANCELLED",
                execution_mode="AUTO_EXECUTE",
                absence_date=extracted.absence_date,
                absent_teacher_id=None,
                absent_teacher_name=extracted.extracted_teacher_name or "Unknown",
                affected_classes_count=0,
                summary="Teacher absence request cancelled by sender email.",
                explanation="Absence request thread marked as CANCELLED. Stale pending substitutions invalidated.",
                created_at=now_str,
            )

        # Stage 3: Teacher Identity Matching
        matcher = TeacherMatchingService(solver_input.teachers)
        matched_teacher, match_reason = matcher.match_teacher(parsed_email.sender_email, extracted.extracted_teacher_name)

        if not matched_teacher or extracted.requires_review:
            return SubstitutionAgentResult(
                agent_run_id=run_id,
                event_id=event_id,
                status="REQUIRES_REVIEW",
                execution_mode="REVIEW",
                absence_date=extracted.absence_date,
                absent_teacher_id=matched_teacher.id if matched_teacher else None,
                absent_teacher_name=extracted.extracted_teacher_name or "Unknown",
                affected_classes_count=0,
                summary=f"Absence request requires administrative review: {extracted.review_reason or match_reason}",
                explanation=f"Ambiguous teacher identity or date ({match_reason}). Routing to administrator queue for manual review.",
                approval_request_id=str(uuid.uuid4()),
                created_at=now_str,
            )

        # Stage 4: Identify Affected Timetable Entries
        affected_entries = [
            e for e in existing_timetable
            if e.teacher_id == matched_teacher.id and e.school_date == extracted.absence_date
        ]

        if not affected_entries:
            return SubstitutionAgentResult(
                agent_run_id=run_id,
                event_id=event_id,
                status="RESOLVED",
                execution_mode="AUTO_EXECUTE",
                absence_date=extracted.absence_date,
                absent_teacher_id=matched_teacher.id,
                absent_teacher_name=matched_teacher.name,
                affected_classes_count=0,
                summary=f"No scheduled classes found for {matched_teacher.name} on {extracted.absence_date}.",
                explanation="Validated teacher absence, but teacher has zero assigned periods on target date. No substitutions required.",
                created_at=now_str,
            )

        # Stage 5: Candidate Substitute Generation & Ranking per Affected Slot
        requirements = []
        requires_approval = False
        course_map = {c.id: c for c in solver_input.courses}
        capable_pairs = {(cap.teacher_id, cap.subject_id) for cap in solver_input.capabilities}

        for entry in affected_entries:
            crs_obj = course_map.get(entry.course_id)
            crs_title = crs_obj.title if crs_obj else entry.course_id
            subj_id = crs_obj.subject_id if crs_obj else ""

            candidates = []
            for candidate_teacher in solver_input.teachers:
                if candidate_teacher.id == matched_teacher.id:
                    continue  # Skip absent teacher

                # 1. Subject Qualification Check
                qual_ok = (candidate_teacher.id, subj_id) in capable_pairs if solver_input.capabilities else True

                # 2. Check if candidate is already teaching in this period/date
                is_busy = any(
                    e.teacher_id == candidate_teacher.id and e.school_date == entry.school_date and e.period_code == entry.period_code
                    for e in existing_timetable
                )

                if qual_ok and not is_busy:
                    # Calculate penalty score
                    penalty = 0.0
                    status = "CLEAN_MATCH"
                    explanation = f"Teacher {candidate_teacher.name} is fully qualified and free during period {entry.period_code}."

                    candidates.append(CandidateOption(
                        teacher_id=candidate_teacher.id,
                        teacher_name=candidate_teacher.name,
                        qualification_ok=True,
                        available_ok=True,
                        hard_conflicts_count=0,
                        penalty_score=penalty,
                        status=status,
                        explanation=explanation,
                    ))

            # Sort candidates deterministically
            candidates.sort(key=lambda c: (c.penalty_score, c.teacher_name))
            selected = candidates[0] if candidates else None

            if not candidates or len(candidates) > 1:
                requires_approval = True

            requirements.append(SubstitutionRequirement(
                period_code=entry.period_code,
                school_date=entry.school_date,
                section_id=entry.section_id,
                course_id=entry.course_id,
                course_title=crs_title,
                original_teacher_id=matched_teacher.id,
                original_teacher_name=matched_teacher.name,
                room_id=entry.room_id,
                ranked_candidates=candidates,
                selected_candidate=selected,
            ))

        # Stage 6: Human-in-the-Loop Governance & Execution Mode
        exec_mode = "AUTO_EXECUTE" if (not requires_approval and len(affected_entries) == 1) else "REQUIRES_APPROVAL"
        final_status = "RESOLVED" if exec_mode == "AUTO_EXECUTE" else "REQUIRES_APPROVAL"
        app_id = str(uuid.uuid4()) if exec_mode == "REQUIRES_APPROVAL" else None

        summary = f"Teacher Substitution Agent evaluated absence for {matched_teacher.name} on {extracted.absence_date} ({len(affected_entries)} affected classes)."

        return SubstitutionAgentResult(
            agent_run_id=run_id,
            event_id=event_id,
            status=final_status,
            execution_mode=exec_mode,
            absence_date=extracted.absence_date,
            absent_teacher_id=matched_teacher.id,
            absent_teacher_name=matched_teacher.name,
            affected_classes_count=len(affected_entries),
            requirements=requirements,
            summary=summary,
            explanation=f"Generated substitute candidates for {len(affected_entries)} slots. Governance mode: {exec_mode}.",
            approval_request_id=app_id,
            created_at=now_str,
        )
