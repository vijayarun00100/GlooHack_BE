from app.solver.models import (
    SolverInput, ScheduledEntryDTO, ConflictReport, ConflictItem, ConflictSeverity
)

class ConflictDetector:
    """
    Deterministic inspector that validates timetables against domain constraints
    without invoking the full CP-SAT solver.
    """

    def validate(self, input_data: SolverInput, entries: list[ScheduledEntryDTO]) -> ConflictReport:
        hard_conflicts = []
        soft_conflicts = []

        # Maps for domain lookups
        teacher_map = {t.id: t for t in input_data.teachers}
        room_map = {r.id: r for r in input_data.rooms}
        course_map = {c.id: c for c in input_data.courses}
        section_map = {s.id: s for s in input_data.sections}
        period_map = {p.code: p for p in input_data.periods}

        # Capability map
        capable_pairs = {(cap.teacher_id, cap.subject_id) for cap in input_data.capabilities}

        # Teacher unavail map
        unavail_teacher = {
            (ta.teacher_id, ta.day_of_week, ta.period_code)
            for ta in input_data.teacher_availability
            if not ta.is_available
        }

        # Room unavail map
        unavail_room = {
            (ra.room_id, ra.date_str, ra.period_code)
            for ra in input_data.room_availability
            if not ra.is_available
        }

        # Index entries by slot keys
        teacher_slots = {}
        room_slots = {}
        section_slots = {}
        assignment_counts = {}

        for entry in entries:
            # Day of week calculation
            day_obj = next((d for d in input_data.school_days if d.date_str == entry.school_date), None)
            day_of_week = day_obj.day_of_week if day_obj else 1

            # 1. Teacher Overlap Check
            t_key = (entry.teacher_id, entry.school_date, entry.period_code)
            if t_key in teacher_slots:
                prev = teacher_slots[t_key]
                t_name = teacher_map.get(entry.teacher_id, entry.teacher_id)
                t_name = getattr(t_name, 'name', entry.teacher_id)
                hard_conflicts.append(ConflictItem(
                    conflict_type="TEACHER_OVERLAP",
                    severity=ConflictSeverity.HARD,
                    description=f"Teacher '{t_name}' assigned to multiple classes during period {entry.period_code} on {entry.school_date}.",
                    entity_ids=[entry.teacher_id, prev.section_id, entry.section_id],
                    period_code=entry.period_code,
                    school_date=entry.school_date,
                ))
            else:
                teacher_slots[t_key] = entry

            # 2. Room Overlap Check
            r_key = (entry.room_id, entry.school_date, entry.period_code)
            if r_key in room_slots:
                prev = room_slots[r_key]
                r_num = room_map.get(entry.room_id, entry.room_id)
                r_num = getattr(r_num, 'room_number', entry.room_id)
                hard_conflicts.append(ConflictItem(
                    conflict_type="ROOM_OVERLAP",
                    severity=ConflictSeverity.HARD,
                    description=f"Room '{r_num}' assigned to multiple sections during period {entry.period_code} on {entry.school_date}.",
                    entity_ids=[entry.room_id, prev.section_id, entry.section_id],
                    period_code=entry.period_code,
                    school_date=entry.school_date,
                ))
            else:
                room_slots[r_key] = entry

            # 3. Section Overlap Check
            s_key = (entry.section_id, entry.school_date, entry.period_code)
            if s_key in section_slots:
                prev = section_slots[s_key]
                sec_obj = section_map.get(entry.section_id, entry.section_id)
                sec_name = getattr(sec_obj, 'name', entry.section_id)
                hard_conflicts.append(ConflictItem(
                    conflict_type="SECTION_OVERLAP",
                    severity=ConflictSeverity.HARD,
                    description=f"Section '{sec_name}' scheduled for multiple classes during period {entry.period_code} on {entry.school_date}.",
                    entity_ids=[entry.section_id, prev.course_id, entry.course_id],
                    period_code=entry.period_code,
                    school_date=entry.school_date,
                ))
            else:
                section_slots[s_key] = entry

            # 4. Room Capacity Check
            sec_obj = section_map.get(entry.section_id)
            room_obj = room_map.get(entry.room_id)
            if sec_obj and room_obj:
                if room_obj.capacity < sec_obj.student_count:
                    hard_conflicts.append(ConflictItem(
                        conflict_type="ROOM_CAPACITY",
                        severity=ConflictSeverity.HARD,
                        description=f"Room '{room_obj.room_number}' (capacity {room_obj.capacity}) is too small for Section '{sec_obj.name}' ({sec_obj.student_count} students).",
                        entity_ids=[entry.room_id, entry.section_id],
                        period_code=entry.period_code,
                        school_date=entry.school_date,
                    ))

            # 5. Required Equipment Check
            course_obj = course_map.get(entry.course_id)
            if course_obj and course_obj.required_equipment and room_obj:
                missing = [eq for eq in course_obj.required_equipment if eq not in room_obj.equipment]
                if missing:
                    hard_conflicts.append(ConflictItem(
                        conflict_type="ROOM_EQUIPMENT_MISMATCH",
                        severity=ConflictSeverity.HARD,
                        description=f"Room '{room_obj.room_number}' lacks required equipment {missing} for course '{course_obj.title}'.",
                        entity_ids=[entry.room_id, entry.course_id],
                        period_code=entry.period_code,
                        school_date=entry.school_date,
                    ))

            # 6. Teacher Availability Check
            if (entry.teacher_id, day_of_week, entry.period_code) in unavail_teacher:
                t_obj = teacher_map.get(entry.teacher_id)
                t_name = t_obj.name if t_obj else entry.teacher_id
                hard_conflicts.append(ConflictItem(
                    conflict_type="TEACHER_AVAILABILITY",
                    severity=ConflictSeverity.HARD,
                    description=f"Teacher '{t_name}' is unavailable during period {entry.period_code} on {entry.school_date}.",
                    entity_ids=[entry.teacher_id],
                    period_code=entry.period_code,
                    school_date=entry.school_date,
                ))

            # 7. Room Availability Check
            if (entry.room_id, entry.school_date, entry.period_code) in unavail_room or (room_obj and room_obj.status != "AVAILABLE"):
                r_name = room_obj.room_number if room_obj else entry.room_id
                hard_conflicts.append(ConflictItem(
                    conflict_type="ROOM_AVAILABILITY",
                    severity=ConflictSeverity.HARD,
                    description=f"Room '{r_name}' is unavailable or under maintenance during period {entry.period_code} on {entry.school_date}.",
                    entity_ids=[entry.room_id],
                    period_code=entry.period_code,
                    school_date=entry.school_date,
                ))

            # 8. Teacher Qualification Check
            if course_obj and input_data.capabilities:
                if (entry.teacher_id, course_obj.subject_id) not in capable_pairs:
                    t_obj = teacher_map.get(entry.teacher_id)
                    t_name = t_obj.name if t_obj else entry.teacher_id
                    hard_conflicts.append(ConflictItem(
                        conflict_type="TEACHER_QUALIFICATION",
                        severity=ConflictSeverity.HARD,
                        description=f"Teacher '{t_name}' is not qualified to teach course '{course_obj.title}'.",
                        entity_ids=[entry.teacher_id, entry.course_id],
                    ))

            # Track counts for weekly period requirements
            assignment_counts[(entry.section_id, entry.course_id)] = assignment_counts.get((entry.section_id, entry.course_id), 0) + 1

        # 9. Required Weekly Course Periods Check
        for req in input_data.assignments:
            actual = assignment_counts.get((req.section_id, req.course_id), 0)
            if actual < req.periods_required:
                sec_obj = section_map.get(req.section_id)
                crs_obj = course_map.get(req.course_id)
                sec_name = sec_obj.name if sec_obj else req.section_id
                crs_name = crs_obj.title if crs_obj else req.course_id
                hard_conflicts.append(ConflictItem(
                    conflict_type="MISSING_COURSE_PERIODS",
                    severity=ConflictSeverity.HARD,
                    description=f"Section '{sec_name}' for course '{crs_name}' requires {req.periods_required} periods, but only {actual} were scheduled.",
                    entity_ids=[req.section_id, req.course_id],
                ))

        total_conflicts = len(hard_conflicts) + len(soft_conflicts)
        return ConflictReport(
            is_valid=(len(hard_conflicts) == 0),
            total_conflicts=total_conflicts,
            hard_conflicts=hard_conflicts,
            soft_conflicts=soft_conflicts,
        )
