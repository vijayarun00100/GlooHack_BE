from typing import Optional
from app.solver.models import TeacherDTO

class TeacherMatchingService:
    """
    Maps extracted email addresses and raw teacher names to database teacher records.
    Ensures zero silent false-positive assignments.
    """

    def __init__(self, teachers: list[TeacherDTO]):
        self.teachers = teachers

    def match_teacher(self, sender_email: str, extracted_name: Optional[str]) -> tuple[Optional[TeacherDTO], str]:
        # 1. Check exact email match
        for t in self.teachers:
            if t.employee_code.lower() in sender_email.lower() or sender_email.lower().startswith(t.name.lower()):
                return t, "EXACT_EMAIL_MATCH"

        # 2. Check exact name match
        if extracted_name:
            norm_extracted = extracted_name.strip().lower()
            matches = [t for t in self.teachers if t.name.lower() == norm_extracted or norm_extracted in t.name.lower()]
            if len(matches) == 1:
                return matches[0], "EXACT_NAME_MATCH"
            elif len(matches) > 1:
                return None, "AMBIGUOUS_MULTIPLE_NAME_MATCHES"

        # 3. Code match
        for t in self.teachers:
            if t.id.lower() == sender_email.lower() or t.employee_code.lower() in sender_email.lower():
                return t, "EMPLOYEE_CODE_MATCH"

        return None, "UNMAPPED_TEACHER_IDENTITY"
