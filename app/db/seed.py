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

        print("[Seed] Seeding realistic school data idempotently...")

        # 1. School Days
        cursor.execute("""
            INSERT INTO school_days (academic_year, term, date, day_of_week, is_instructional_day, notes)
            VALUES 
                ('2026-2027', 'Fall Term', '2026-08-25', 'MON', TRUE, 'First day of Fall term'),
                ('2026-2027', 'Fall Term', '2026-08-26', 'TUE', TRUE, 'Instructional day'),
                ('2026-2027', 'Fall Term', '2026-08-27', 'WED', TRUE, 'Instructional day')
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

        # 3. Grades
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

        # 4. Subjects
        cursor.execute("""
            INSERT INTO subjects (code, name, department, description)
            VALUES 
                ('LIT100', 'Medieval Literature', 'English', 'Classic medieval prose and poetry'),
                ('MATH101', 'Algebra I', 'Mathematics', 'Fundamental algebraic structures'),
                ('PHYS200', 'Physical Science', 'Science', 'Introductory physics and chemistry principles'),
                ('HIST150', 'Ancient History', 'Social Studies', 'History of ancient civilizations'),
                ('PE100', 'Physical Education', 'Athletics', 'Physical fitness and team sports'),
                ('CHEM300', 'Chemistry', 'Science', 'General laboratory chemistry')
            ON CONFLICT (code) DO NOTHING;
        """)

        # 5. Rooms (Demonstrating capacities, maintenance, and equipment)
        cursor.execute("""
            INSERT INTO rooms (room_number, building, capacity, room_type, status)
            VALUES 
                ('Room 201', 'Humanities Wing', 30, 'STANDARD', 'AVAILABLE'),
                ('Room 202', 'Humanities Wing', 35, 'STANDARD', 'AVAILABLE'),
                ('Room 207', 'Humanities Wing', 25, 'STANDARD', 'AVAILABLE'), -- Small capacity edge case
                ('Room 208', 'Math Wing', 32, 'STANDARD', 'AVAILABLE'),
                ('Science Lab 1', 'Science Wing', 30, 'LAB', 'AVAILABLE'),
                ('Science Lab 2', 'Science Wing', 28, 'LAB', 'UNDER_MAINTENANCE'), -- Maintenance edge case
                ('Gymnasium', 'Athletic Complex', 150, 'GYM', 'AVAILABLE'),
                ('Main Auditorium', 'Arts Complex', 300, 'AUDITORIUM', 'AVAILABLE')
            ON CONFLICT (room_number) DO NOTHING;
        """)

        # 6. Room Equipment
        cursor.execute("""
            INSERT INTO room_equipment (room_id, equipment_name, quantity)
            SELECT id, 'Smart Board', 1 FROM rooms WHERE room_number = 'Room 201'
            ON CONFLICT DO NOTHING;
            INSERT INTO room_equipment (room_id, equipment_name, quantity)
            SELECT id, 'Chemistry Benches', 15 FROM rooms WHERE room_number = 'Science Lab 1'
            ON CONFLICT DO NOTHING;
            INSERT INTO room_equipment (room_id, equipment_name, quantity)
            SELECT id, 'Projector', 1 FROM rooms WHERE room_number = 'Science Lab 1'
            ON CONFLICT DO NOTHING;
        """)

        # 7. Users & Teachers (Demonstrating multi-capability & availability differences)
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name, role)
            VALUES 
                ('11111111-1111-1111-1111-111111111111', 'cooper@school.edu', 'Sarah', 'Cooper', 'TEACHER'),
                ('22222222-2222-2222-2222-222222222222', 'smith@school.edu', 'David', 'Smith', 'TEACHER'),
                ('33333333-3333-3333-3333-333333333333', 'ross@school.edu', 'Elena', 'Ross', 'TEACHER'),
                ('44444444-4444-4444-4444-444444444444', 'blake@school.edu', 'Marcus', 'Blake', 'TEACHER'),
                ('55555555-5555-5555-5555-555555555555', 'admin@school.edu', 'Arthur', 'Pendelton', 'ADMINISTRATOR')
            ON CONFLICT (email) DO NOTHING;
        """)

        cursor.execute("""
            INSERT INTO teachers (id, user_id, employee_code, max_weekly_hours, max_consecutive_periods, department)
            VALUES 
                ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'EMP-COOPER', 35, 3, 'English'),
                ('a2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'EMP-SMITH', 40, 4, 'Mathematics'),
                ('a3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'EMP-ROSS', 30, 3, 'Science'),
                ('a4444444-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 'EMP-BLAKE', 35, 3, 'Social Studies')
            ON CONFLICT (employee_code) DO NOTHING;
        """)

        # 8. Teacher Capabilities (Cooper can teach both Literature and History - Multi-qualification edge case)
        cursor.execute("""
            INSERT INTO teacher_capabilities (teacher_id, subject_id, qualification_level)
            SELECT t.id, s.id, 'PRIMARY'
            FROM teachers t, subjects s
            WHERE t.employee_code = 'EMP-COOPER' AND s.code IN ('LIT100', 'HIST150')
            ON CONFLICT (teacher_id, subject_id) DO NOTHING;

            INSERT INTO teacher_capabilities (teacher_id, subject_id, qualification_level)
            SELECT t.id, s.id, 'PRIMARY'
            FROM teachers t, subjects s
            WHERE t.employee_code = 'EMP-SMITH' AND s.code = 'MATH101'
            ON CONFLICT (teacher_id, subject_id) DO NOTHING;

            INSERT INTO teacher_capabilities (teacher_id, subject_id, qualification_level)
            SELECT t.id, s.id, 'PRIMARY'
            FROM teachers t, subjects s
            WHERE t.employee_code = 'EMP-ROSS' AND s.code IN ('PHYS200', 'CHEM300')
            ON CONFLICT (teacher_id, subject_id) DO NOTHING;
        """)

        # 9. Teacher Availability (Ross unavailable Monday P1 - Availability constraint edge case)
        cursor.execute("""
            INSERT INTO teacher_availability (teacher_id, day_of_week, period_code, is_available, preference_weight)
            SELECT id, 1, 'P1', FALSE, 0.0 FROM teachers WHERE employee_code = 'EMP-ROSS'
            ON CONFLICT (teacher_id, day_of_week, period_code) DO NOTHING;
        """)

        print("[Seed] Successfully seeded realistic development environment data!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Seed] Error seeding database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    seed_database()
