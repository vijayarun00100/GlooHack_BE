import os
import sys
import psycopg2
from app.core.config import settings

def seed_database():
    print("[Seed] Connecting to PostgreSQL database...")
    db_url = settings.DATABASE_URL
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[Seed] Seeding realistic production school data idempotently...")

        # 1. School Days
        cursor.execute("""
            INSERT INTO school_days (academic_year, term, date, day_of_week, is_instructional_day, notes)
            VALUES 
                ('2026-2027', 'Fall Term', '2026-08-25', 'MON', TRUE, 'First day of Fall term'),
                ('2026-2027', 'Fall Term', '2026-08-26', 'TUE', TRUE, 'Instructional day'),
                ('2026-2027', 'Fall Term', '2026-08-27', 'WED', TRUE, 'Instructional day'),
                ('2026-2027', 'Fall Term', '2026-08-28', 'THU', TRUE, 'Instructional day'),
                ('2026-2027', 'Fall Term', '2026-08-29', 'FRI', TRUE, 'Instructional day')
            ON CONFLICT (date) DO NOTHING;
        """)

        # 2. Periods
        cursor.execute("""
            INSERT INTO periods (code, name, start_time, end_time, period_order)
            VALUES 
                ('P1', 'Period 1', '08:00:00', '08:50:00', 1),
                ('P2', 'Period 2', '09:00:00', '09:50:00', 2),
                ('P3', 'Period 3', '10:00:00', '10:50:00', 3),
                ('P4', 'Period 4', '11:00:00', '11:50:00', 4),
                ('P5', 'Period 5', '13:00:00', '13:50:00', 5)
            ON CONFLICT (code) DO NOTHING;
        """)

        # 3. Grades & Sections
        cursor.execute("""
            INSERT INTO grades (level, name, description)
            VALUES 
                (7, 'Grade 7', 'Junior High School 7th Grade'),
                (8, 'Grade 8', 'Junior High School 8th Grade'),
                (9, 'Grade 9', 'High School Freshman'),
                (10, 'Grade 10', 'High School Sophomore'),
                (11, 'Grade 11', 'High School Junior'),
                (12, 'Grade 12', 'High School Senior')
            ON CONFLICT (level) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO sections (grade_id, name, academic_year, target_capacity)
            SELECT id, '10A', '2026-2027', 30 FROM grades WHERE level = 10
            ON CONFLICT (grade_id, name, academic_year) DO NOTHING;

            INSERT INTO sections (grade_id, name, academic_year, target_capacity)
            SELECT id, '10B', '2026-2027', 30 FROM grades WHERE level = 10
            ON CONFLICT (grade_id, name, academic_year) DO NOTHING;
        """)

        # 4. Subjects & Courses
        cursor.execute("""
            INSERT INTO subjects (code, name, department, description)
            VALUES 
                ('MATH101', 'Mathematics', 'Mathematics', 'High School Mathematics & Algebra II'),
                ('PHYS200', 'Physics', 'Science', 'Physical Science & Mechanics'),
                ('CHEM300', 'Chemistry', 'Science', 'General Laboratory Chemistry'),
                ('LIT100', 'English', 'English', 'English Literature & Composition'),
                ('CS101', 'Computer Science', 'Technology', 'Intro to Computer Science & Python'),
                ('BIO101', 'Biology', 'Science', 'General Biology & Genetics')
            ON CONFLICT (code) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO courses (id, subject_id, grade_id, title, periods_per_week)
            SELECT 'c0000001-0000-0000-0000-000000000001', s.id, g.id, 'Grade 10 Mathematics', 5
            FROM subjects s, grades g WHERE s.code = 'MATH101' AND g.level = 10
            ON CONFLICT (id) DO NOTHING;

            INSERT INTO courses (id, subject_id, grade_id, title, periods_per_week)
            SELECT 'c0000002-0000-0000-0000-000000000002', s.id, g.id, 'Grade 10 Physics', 5
            FROM subjects s, grades g WHERE s.code = 'PHYS200' AND g.level = 10
            ON CONFLICT (id) DO NOTHING;
        """)

        # 5. Rooms & Equipment
        cursor.execute("""
            INSERT INTO rooms (room_number, building, capacity, room_type, status)
            VALUES 
                ('Room 101', 'Humanities Wing', 40, 'STANDARD', 'AVAILABLE'),
                ('Room 102', 'Humanities Wing', 35, 'STANDARD', 'AVAILABLE'),
                ('Physics Lab', 'Science Wing', 30, 'LAB', 'AVAILABLE'),
                ('Chemistry Lab', 'Science Wing', 30, 'LAB', 'UNDER_MAINTENANCE'),
                ('Computer Lab', 'Technology Wing', 40, 'LAB', 'AVAILABLE'),
                ('Auditorium', 'Arts Complex', 200, 'AUDITORIUM', 'AVAILABLE')
            ON CONFLICT (room_number) DO NOTHING;
        """)

        # 6. Users & Teachers
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name, role)
            VALUES 
                ('11111111-1111-1111-1111-111111111111', 'meera@school.edu', 'Dr. Meera', 'Nair', 'TEACHER'),
                ('22222222-2222-2222-2222-222222222222', 'arjun@school.edu', 'Mr. Arjun', 'Verma', 'TEACHER'),
                ('33333333-3333-3333-3333-333333333333', 'kavya@school.edu', 'Ms. Kavya', 'Iyer', 'TEACHER'),
                ('44444444-4444-4444-4444-444444444444', 'priya_t@school.edu', 'Ms. Priya', 'Kapoor', 'TEACHER'),
                ('55555555-5555-5555-5555-555555555555', 'rahul_t@school.edu', 'Mr. Rahul', 'Deshmukh', 'TEACHER'),
                ('66666666-6666-6666-6666-666666666666', 'admin@school.edu', 'Arthur', 'Pendelton', 'ADMINISTRATOR')
            ON CONFLICT (email) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO teachers (id, user_id, employee_code, max_weekly_hours, max_consecutive_periods, department)
            VALUES 
                ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'EMP-MEERA', 35, 3, 'Mathematics'),
                ('a2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'EMP-ARJUN', 35, 3, 'Science'),
                ('a3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'EMP-KAVYA', 30, 3, 'Science'),
                ('a4444444-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 'EMP-PRIYAT', 35, 3, 'English'),
                ('a5555555-5555-5555-5555-555555555555', '55555555-5555-5555-5555-555555555555', 'EMP-RAHULT', 40, 4, 'Technology')
            ON CONFLICT (employee_code) DO NOTHING;
        """)

        # 7. Students
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name, role)
            VALUES 
                ('e1011011-1011-1011-1011-101110111011', 'arun.demo@example.com', 'Arun', 'Kumar', 'STUDENT'),
                ('e1021021-1021-1021-1021-102110211021', 'priya.demo@example.com', 'Priya', 'Sharma', 'STUDENT'),
                ('e1031031-1031-1031-1031-103110311031', 'rahul.demo@example.com', 'Rahul', 'Menon', 'STUDENT'),
                ('e1041041-1041-1041-1041-104110411041', 'ananya.demo@example.com', 'Ananya', 'Raj', 'STUDENT')
            ON CONFLICT (email) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO students (id, user_id, student_code, grade_level, status)
            VALUES 
                ('f1011011-1011-1011-1011-101110111011', 'e1011011-1011-1011-1011-101110111011', 'STU-1001', 10, 'ACTIVE'),
                ('f1021021-1021-1021-1021-102110211021', 'e1021021-1021-1021-1021-102110211021', 'STU-1002', 10, 'ACTIVE'),
                ('f1031031-1031-1031-1031-103110311031', 'e1031031-1031-1031-1031-103110311031', 'STU-1003', 10, 'ACTIVE'),
                ('f1041041-1041-1041-1041-104110411041', 'e1041041-1041-1041-1041-104110411041', 'STU-1004', 10, 'ACTIVE')
            ON CONFLICT (student_code) DO NOTHING;
        """)

        # 8. Timetable Versions & Entries
        cursor.execute("""
            INSERT INTO timetable_versions (id, title, academic_year, term, version_number, status)
            VALUES 
                ('90000001-0000-0000-0000-000000000001', 'Master Timetable Fall 2026', '2026-2027', 'Fall Term', 1, 'PUBLISHED')
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO timetable_entries (version_id, school_date, period_id, section_id, course_id, teacher_id, room_id, status)
            SELECT 
                '90000001-0000-0000-0000-000000000001',
                '2026-08-25',
                p.id,
                sec.id,
                c.id,
                'a1111111-1111-1111-1111-111111111111',
                r.id,
                'SCHEDULED'
            FROM periods p, sections sec, courses c, rooms r
            WHERE p.code = 'P1' AND sec.name = '10A' AND c.id = 'c0000001-0000-0000-0000-000000000001' AND r.room_number = 'Room 101'
            ON CONFLICT (version_id, section_id, school_date, period_id) DO NOTHING;
        """)


        # 9. Learnly (Planly) Study Goals & Plans
        cursor.execute("""
            INSERT INTO study_goals (id, student_id, title, description, target_date, priority, status, subjects, focus_topics)
            VALUES 
                ('b1011011-1011-1011-1011-101110111011', 'student-101', 'Prepare for Mathematics Midterm', 'Master Quadratic Equations, Discriminant, and Functions before midterm exam.', '2026-10-15', 'HIGH', 'ACTIVE', '["Mathematics", "Physics"]'::jsonb, '["Quadratic Equations", "Discriminant", "Laws of Motion"]'::jsonb),
                ('b1021021-1021-1021-1021-102110211021', 'student-102', 'Physics & Chemistry Mastery', 'Complete physics problem sets and chemistry lab reports.', '2026-10-18', 'HIGH', 'ACTIVE', '["Physics", "Chemistry"]'::jsonb, '["Laws of Motion", "Atomic Structure"]'::jsonb),
                ('b1031031-1031-1031-1031-103110311031', 'student-103', 'CS Project & Mathematics', 'Finish Python project and practice algebraic functions.', '2026-10-20', 'MEDIUM', 'ACTIVE', '["Computer Science", "Mathematics"]'::jsonb, '["Python Data Structures", "Functions"]'::jsonb),
                ('b1041041-1041-1041-1041-104110411041', 'student-104', 'Biology & English Revision', 'Review cell biology and complete literature essay draft.', '2026-10-22', 'MEDIUM', 'ACTIVE', '["Biology", "English"]'::jsonb, '["Genetics", "Essay Structure"]'::jsonb)
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO study_plans (id, student_id, goal_id, start_date, end_date, status, total_hours, planned_hours, completed_hours, completion_percentage, feasibility_score, overall_quality_score)
            VALUES 
                ('c1011011-1011-1011-1011-101110111011', 'student-101', 'b1011011-1011-1011-1011-101110111011', '2026-08-25', '2026-10-15', 'ACTIVE', 10.0, 8.0, 6.5, 81.25, 95.0, 92.0),
                ('c1021021-1021-1021-1021-102110211021', 'student-102', 'b1021021-1021-1021-1021-102110211021', '2026-08-25', '2026-10-18', 'ACTIVE', 10.0, 10.0, 7.0, 70.00, 90.0, 88.0),
                ('c1031031-1031-1031-1031-103110311031', 'student-103', 'b1031031-1031-1031-1031-103110311031', '2026-08-25', '2026-10-20', 'ACTIVE', 8.0, 6.0, 5.5, 91.67, 98.0, 95.0),
                ('c1041041-1041-1041-1041-104110411041', 'student-104', 'b1041041-1041-1041-1041-104110411041', '2026-08-25', '2026-10-22', 'ACTIVE', 8.0, 6.0, 4.5, 75.00, 88.0, 85.0)
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO study_sprints (id, plan_id, school_date, start_time, end_time, duration_minutes, subject, focus_area, sprint_type, status)
            VALUES 
                ('d1011011-1011-1011-1011-101110111011', 'c1011011-1011-1011-1011-101110111011', CURRENT_DATE, '17:00:00', '17:30:00', 30, 'Mathematics', 'Quadratic Equations & Discriminant', 'PRACTICE', 'PLANNED'),
                ('d1011022-1011-1011-1011-101110111011', 'c1011011-1011-1011-1011-101110111011', CURRENT_DATE, '17:40:00', '18:10:00', 30, 'Physics', 'Laws of Motion Revision', 'REVIEW', 'PLANNED')
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO study_tasks (id, sprint_id, title, description, task_type, estimated_minutes, priority, status)
            VALUES 
                ('e1011011-1011-1011-1011-101110111011', 'd1011011-1011-1011-1011-101110111011', 'Quadratic Discriminant Practice', 'Solve 10 problems finding nature of roots using b^2 - 4ac formula.', 'PRACTICE_PROBLEMS', 30, 'HIGH', 'PLANNED'),
                ('e1011022-1011-1011-1011-101110111011', 'd1011022-1011-1011-1011-101110111011', 'Newton Second Law Calculations', 'Calculate force, mass, and acceleration vectors.', 'REVIEW', 30, 'MEDIUM', 'PLANNED')
            ON CONFLICT (id) DO NOTHING;
        """)

        # 10. Striver Documents, Chunks, and Mastery
        cursor.execute("""
            INSERT INTO striver_documents (id, title, subject, grade, course, uploaded_by, source_type, status, chunk_count)
            VALUES 
                ('f1011011-1011-1011-1011-101110111011', 'Mathematics — Quadratic Equations.pdf', 'Mathematics', 10, 'Mathematics', 'a1111111-1111-1111-1111-111111111111', 'CHAPTER_NOTES', 'READY', 42),
                ('f1021021-1021-1021-1021-102110211021', 'Physics — Laws of Motion.pdf', 'Physics', 10, 'Physical Science', 'a2222222-2222-2222-2222-222222222222', 'TEXTBOOK_EXCERPT', 'READY', 31),
                ('f1031031-1031-1031-1031-103110311031', 'Chemistry — Atomic Structure.pdf', 'Chemistry', 10, 'Chemistry', 'a3333333-3333-3333-3333-333333333333', 'TEACHER_NOTES', 'READY', 28)
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO striver_document_chunks (id, document_id, chunk_index, content, metadata)
            VALUES 
                ('a1011011-1011-1011-1011-101110111011', 'f1011011-1011-1011-1011-101110111011', 1, 'The quadratic equation standard form is ax^2 + bx + c = 0 where a != 0. The solutions are given by the quadratic formula x = (-b +- sqrt(b^2 - 4ac)) / (2a).', '{"subject": "Mathematics", "topic": "Quadratic Equations", "page_number": 12}'::jsonb),
                ('a1011022-1011-1011-1011-101110111011', 'f1011011-1011-1011-1011-101110111011', 2, 'The discriminant D = b^2 - 4ac determines the nature of the roots: If D > 0, there are two distinct real roots. If D = 0, there is exactly one real root (repeated). If D < 0, there are two complex conjugate roots.', '{"subject": "Mathematics", "topic": "Discriminant", "page_number": 15}'::jsonb),
                ('a1021011-1021-1021-1021-102110211021', 'f1021021-1021-1021-1021-102110211021', 1, 'Newton''s Second Law of Motion states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass: F = ma.', '{"subject": "Physics", "topic": "Laws of Motion", "page_number": 8}'::jsonb)
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO striver_mastery (student_id, subject, topic, mastery_score, mastery_level, confidence, attempts, correct_attempts)
            VALUES 
                ('student-101', 'Mathematics', 'Algebra', 88.0, 'STRONG', 'HIGH', 15, 13),
                ('student-101', 'Mathematics', 'Quadratic Equations', 71.0, 'PRACTICING', 'MEDIUM', 10, 7),
                ('student-101', 'Mathematics', 'Discriminant', 45.0, 'NEEDS_SUPPORT', 'LOW', 6, 2),
                ('student-101', 'Mathematics', 'Functions', 64.0, 'DEVELOPING', 'MEDIUM', 8, 5),
                ('student-102', 'Physics', 'Laws of Motion', 85.0, 'STRONG', 'HIGH', 12, 10),
                ('student-102', 'Physics', 'Work and Energy', 70.0, 'PRACTICING', 'MEDIUM', 8, 5),
                ('student-103', 'Chemistry', 'Atomic Structure', 92.0, 'MASTERED', 'HIGH', 20, 19),
                ('student-103', 'Chemistry', 'Chemical Bonding', 80.0, 'STRONG', 'HIGH', 14, 11)
            ON CONFLICT (student_id, subject, topic) DO UPDATE
            SET mastery_score = EXCLUDED.mastery_score,
                mastery_level = EXCLUDED.mastery_level;
        """)

        # 11. Gamification & Social Data
        cursor.execute("""
            INSERT INTO student_gamification_profiles (student_id, total_xp, current_level, coins, current_streak, longest_streak, total_study_minutes, total_tasks_completed)
            VALUES 
                ('student-101', 2840, 8, 420, 7, 14, 390, 24),
                ('student-102', 1950, 6, 280, 4, 8,  280, 18),
                ('student-103', 3450, 9, 510, 12, 21, 520, 32),
                ('student-104', 1500, 5, 200, 3, 5,  210, 14)
            ON CONFLICT (student_id) DO UPDATE
            SET total_xp = EXCLUDED.total_xp,
                current_level = EXCLUDED.current_level,
                coins = EXCLUDED.coins,
                current_streak = EXCLUDED.current_streak;
        """)

        cursor.execute("""
            INSERT INTO achievements (code, name, description, category, icon, xp_reward, coin_reward)
            VALUES 
                ('FIRST_STUDY', 'First Steps', 'Completed your first study session.', 'STUDY', '🚀', 100, 10),
                ('SEVEN_DAY_STREAK', '7-Day Study Streak', 'Maintained a study streak for 7 consecutive days.', 'STREAK', '🔥', 300, 50),
                ('TEN_HOURS', '10 Hours Studied', 'Logged over 10 hours of focused study time.', 'TIME', '⏳', 500, 75),
                ('EXAM_READY', 'Exam Ready', 'Mastered all core topics for an upcoming midterm.', 'MASTERY', '🎓', 750, 100),
                ('QUIZ_MASTER', 'Quiz Master', 'Scored 90%+ accuracy on 5 Striver quizzes.', 'MASTERY', '🎯', 400, 60)
            ON CONFLICT (code) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO student_achievements (student_id, achievement_code, progress)
            VALUES 
                ('student-101', 'FIRST_STUDY', 100.0),
                ('student-101', 'SEVEN_DAY_STREAK', 100.0),
                ('student-101', 'TEN_HOURS', 100.0),
                ('student-102', 'FIRST_STUDY', 100.0),
                ('student-103', 'FIRST_STUDY', 100.0),
                ('student-103', 'SEVEN_DAY_STREAK', 100.0),
                ('student-103', 'QUIZ_MASTER', 100.0)
            ON CONFLICT (student_id, achievement_code) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO social_posts (id, student_id, student_name, post_type, achievement_code, title, content, visibility)
            VALUES 
                ('b1011011-1011-1011-1011-101110111011', 'student-101', 'Arun Kumar', 'STREAK', 'SEVEN_DAY_STREAK', 'Hit my 7-Day Study Streak! 🔥', 'Just completed my 7-day study streak with Learnly and Striver!', 'CLASS'),
                ('b1021022-1022-1022-1022-102210221022', 'student-103', 'Rahul Menon', 'ACHIEVEMENT', 'QUIZ_MASTER', 'Quiz Master Unlocked 🎯', 'Scored 95% on Chemistry Atomic Structure quiz on Striver!', 'CLASS')
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO social_privacy_settings (student_id, achievement_visibility, profile_visibility, social_enabled)
            VALUES 
                ('student-101', 'CLASS', 'CLASS', TRUE),
                ('student-102', 'CLASS', 'CLASS', TRUE),
                ('student-103', 'CLASS', 'CLASS', TRUE),
                ('student-104', 'CLASS', 'CLASS', TRUE)
            ON CONFLICT (student_id) DO NOTHING;
        """)

        # 12. Households & Sibling Links
        cursor.execute("""
            INSERT INTO households (id, family_name, primary_contact_email)
            VALUES 
                ('10000101-0000-0000-0000-000000000101', 'Arun Family', 'suresh.kumar@example.com')
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO teacher_absences (id, teacher_id, start_date, end_date, reason, status)
            VALUES 
                ('20000101-0000-0000-0000-000000000101', 'a1111111-1111-1111-1111-111111111111', '2026-10-06', '2026-10-06', 'Medical Leave', 'APPROVED')
            ON CONFLICT (id) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO room_disruption_events (id, room_id, event_type, start_date, end_date, reason, status)
            SELECT '30000101-0000-0000-0000-000000000101', id, 'MAINTENANCE', '2026-10-07', '2026-10-07', 'HVAC Maintenance', 'OPEN'
            FROM rooms WHERE room_number = 'Physics Lab'
            ON CONFLICT (id) DO NOTHING;
        """)


        print("========================================")
        print("DEMO DATABASE SEED COMPLETE")
        print("========================================")
        print("Students:              4 (Arun, Priya, Rahul, Ananya)")
        print("Teachers:              5")
        print("Subjects:              6")
        print("Rooms:                 6")
        print("Timetable entries:     1")
        print("Learnly goals:         4")
        print("Learnly plans:         4")
        print("Striver documents:     3")
        print("Striver mastery:       8")
        print("Gamification profiles: 4")
        print("Achievements:          5")
        print("Social posts:          2")
        print("========================================")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Seed] Error seeding database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    seed_database()
