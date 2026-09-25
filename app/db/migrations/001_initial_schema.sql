-- Phase 0 Initial Database Migration Schema
-- Domain: Agentic School Scheduling & Student Support Platform
-- Database: PostgreSQL + pgvector

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ==========================================
-- 1. IDENTITY & HOUSEHOLD DOMAIN
-- ==========================================

CREATE TYPE user_role AS ENUM ('STUDENT', 'TEACHER', 'ADMINISTRATOR', 'PARENT');
CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED');

CREATE TABLE IF NOT EXISTS households (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_name VARCHAR(100) NOT NULL,
    address TEXT,
    primary_contact_phone VARCHAR(30),
    primary_contact_email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    status user_status NOT NULL DEFAULT 'ACTIVE',
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS parents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    household_id UUID REFERENCES households(id) ON DELETE SET NULL,
    relationship_to_student VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS administrators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(100),
    title VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    employee_code VARCHAR(50) UNIQUE NOT NULL,
    max_weekly_hours INT NOT NULL DEFAULT 40,
    max_consecutive_periods INT NOT NULL DEFAULT 3,
    department VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    household_id UUID REFERENCES households(id) ON DELETE SET NULL,
    student_code VARCHAR(50) UNIQUE NOT NULL,
    grade_level INT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sibling_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student1_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student2_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'SIBLING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_sibling_pair UNIQUE(student1_id, student2_id),
    CONSTRAINT chk_no_self_sibling CHECK (student1_id <> student2_id)
);

-- ==========================================
-- 2. ACADEMIC DOMAIN
-- ==========================================

CREATE TABLE IF NOT EXISTS grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level INT UNIQUE NOT NULL, -- e.g., 7, 8, 9, 10, 11, 12
    name VARCHAR(50) NOT NULL, -- e.g., "Grade 8"
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- e.g., "8A", "8B"
    academic_year VARCHAR(20) NOT NULL, -- e.g., "2026-2027"
    target_capacity INT NOT NULL DEFAULT 30,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_section_grade_year UNIQUE (grade_id, name, academic_year)
);

CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(30) UNIQUE NOT NULL, -- e.g., "MATH101", "LIT201"
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    periods_per_week INT NOT NULL DEFAULT 5,
    requires_lab BOOLEAN DEFAULT FALSE,
    required_equipment VARCHAR(100)[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'ACTIVE',
    CONSTRAINT unique_student_section UNIQUE (student_id, section_id)
);

-- ==========================================
-- 3. ROOMS & RESOURCES DOMAIN
-- ==========================================

CREATE TYPE room_status AS ENUM ('AVAILABLE', 'UNAVAILABLE', 'UNDER_MAINTENANCE', 'RESERVED');

CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_number VARCHAR(50) UNIQUE NOT NULL, -- e.g., "Room 201", "Science Lab 1"
    building VARCHAR(100) NOT NULL,
    capacity INT NOT NULL,
    room_type VARCHAR(50) NOT NULL DEFAULT 'STANDARD', -- 'LAB', 'GYM', 'AUDITORIUM', 'CLASSROOM'
    status room_status NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS room_equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    equipment_name VARCHAR(100) NOT NULL, -- e.g., "Smart Board", "Projector", "Chemistry Benches"
    quantity INT NOT NULL DEFAULT 1,
    status VARCHAR(30) DEFAULT 'OPERATIONAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS room_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    period_code VARCHAR(20) NOT NULL, -- e.g., "P1", "P2"
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_room_slot UNIQUE (room_id, date, period_code)
);

CREATE TABLE IF NOT EXISTS room_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    period_code VARCHAR(20) NOT NULL,
    status VARCHAR(30) DEFAULT 'ASSIGNED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 4. TEACHER CAPABILITIES & CONSTRAINTS DOMAIN
-- ==========================================

CREATE TABLE IF NOT EXISTS teacher_capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    qualification_level VARCHAR(50) DEFAULT 'QUALIFIED', -- 'PRIMARY', 'SECONDARY', 'SUBSTITUTE_ONLY'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_teacher_subject UNIQUE (teacher_id, subject_id)
);

CREATE TABLE IF NOT EXISTS teacher_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 1=Monday
    period_code VARCHAR(20) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    preference_weight NUMERIC(3,2) DEFAULT 1.0, -- 1.0 = standard, 0.0 = avoid
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_teacher_avail UNIQUE (teacher_id, day_of_week, period_code)
);

CREATE TABLE IF NOT EXISTS teacher_constraints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL, -- 'MAX_DAILY_PERIODS', 'NO_FIRST_PERIOD', 'PREFER_ROOM'
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_hard_constraint BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teacher_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    academic_year VARCHAR(20) NOT NULL,
    term VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_teacher_course_section UNIQUE (teacher_id, course_id, section_id, academic_year, term)
);

-- ==========================================
-- 5. SCHEDULING & TIMETABLE DOMAIN
-- ==========================================

CREATE TYPE timetable_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED', 'SUPERSEDED');

CREATE TABLE IF NOT EXISTS school_days (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    academic_year VARCHAR(20) NOT NULL,
    term VARCHAR(50) NOT NULL,
    date DATE NOT NULL UNIQUE,
    day_of_week VARCHAR(20) NOT NULL,
    is_instructional_day BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL, -- e.g., 'P1', 'P2', 'P3'
    name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    period_order INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS timetable_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(150) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    term VARCHAR(50) NOT NULL,
    version_number INT NOT NULL DEFAULT 1,
    status timetable_status NOT NULL DEFAULT 'DRAFT',
    created_by UUID REFERENCES users(id),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS timetable_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES timetable_versions(id) ON DELETE CASCADE,
    school_date DATE NOT NULL,
    period_id UUID NOT NULL REFERENCES periods(id),
    section_id UUID NOT NULL REFERENCES sections(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    room_id UUID NOT NULL REFERENCES rooms(id),
    color_code VARCHAR(30) DEFAULT 'blue',
    flag VARCHAR(30), -- 'updated', 'warning', 'conflict'
    status VARCHAR(30) DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_section_period_date UNIQUE (version_id, section_id, school_date, period_id)
);

-- ==========================================
-- 6. ABSENCE & SUBSTITUTION DOMAIN
-- ==========================================

CREATE TYPE absence_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');
CREATE TYPE substitution_status AS ENUM ('UNASSIGNED', 'PROPOSED', 'CONFIRMED', 'REJECTED', 'COMPLETED');

CREATE TABLE IF NOT EXISTS teacher_absences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status absence_status NOT NULL DEFAULT 'PENDING',
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS substitution_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    absence_id UUID NOT NULL REFERENCES teacher_absences(id) ON DELETE CASCADE,
    timetable_entry_id UUID NOT NULL REFERENCES timetable_entries(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    period_id UUID NOT NULL REFERENCES periods(id),
    original_teacher_id UUID NOT NULL REFERENCES teachers(id),
    status substitution_status NOT NULL DEFAULT 'UNASSIGNED',
    urgency_level VARCHAR(20) DEFAULT 'MEDIUM',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS substitution_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID UNIQUE NOT NULL REFERENCES substitution_requests(id) ON DELETE CASCADE,
    substitute_teacher_id UUID NOT NULL REFERENCES teachers(id),
    assigned_by_agent VARCHAR(100), -- Agent name or Administrator UUID
    confidence_score NUMERIC(4,3),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'CONFIRMED',
    notes TEXT
);

-- ==========================================
-- 7. DISRUPTIONS & RECOVERY PLAN DOMAIN
-- ==========================================

CREATE TYPE disruption_type AS ENUM ('TEACHER_ABSENCE', 'ROOM_CLOSURE', 'EQUIPMENT_FAILURE', 'WEATHER_EVENT', 'SCHOOL_EVENT', 'FIRE_DRILL');
CREATE TYPE disruption_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE disruption_status AS ENUM ('OPEN', 'ANALYZING', 'RECOVERY_PROPOSED', 'RESOLVED', 'DISMISSED');

CREATE TABLE IF NOT EXISTS disruptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    type disruption_type NOT NULL,
    severity disruption_severity NOT NULL DEFAULT 'MEDIUM',
    status disruption_status NOT NULL DEFAULT 'OPEN',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES users(id),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS affected_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disruption_id UUID NOT NULL REFERENCES disruptions(id) ON DELETE CASCADE,
    timetable_entry_id UUID NOT NULL REFERENCES timetable_entries(id) ON DELETE CASCADE,
    impact_type VARCHAR(50) NOT NULL, -- 'CANCELLED', 'RELOCATED', 'TEACHER_MISSING'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disruption_id UUID NOT NULL REFERENCES disruptions(id) ON DELETE CASCADE,
    plan_title VARCHAR(200) NOT NULL,
    score NUMERIC(5,2),
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED', -- 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED'
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_plan_options (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recovery_plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    affected_period_id UUID NOT NULL REFERENCES affected_periods(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- 'SWAP_ROOM', 'ASSIGN_SUBSTITUTE', 'RESCHEDULE', 'CANCEL'
    new_teacher_id UUID REFERENCES teachers(id),
    new_room_id UUID REFERENCES rooms(id),
    new_date DATE,
    new_period_id UUID REFERENCES periods(id),
    reasoning TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 8. FAMILY ALIGNMENT & PATTERNS
-- ==========================================

CREATE TABLE IF NOT EXISTS family_day_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    academic_year VARCHAR(20) NOT NULL,
    campus_days VARCHAR(20)[], -- e.g., ARRAY['MON', 'TUE', 'THU']
    home_study_days VARCHAR(20)[],
    alignment_score NUMERIC(4,2), -- 0.00 to 100.00
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 9. POLICIES & CONSTRAINTS DOMAIN
-- ==========================================

CREATE TABLE IF NOT EXISTS scheduling_constraints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) UNIQUE NOT NULL, -- e.g., "NO_TEACHER_OVERLAP", "ROOM_CAPACITY"
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'TEACHER', 'ROOM', 'SECTION', 'PEDAGOGICAL'
    is_hard_constraint BOOLEAN NOT NULL DEFAULT TRUE,
    penalty_weight NUMERIC(5,2) DEFAULT 1.0,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS school_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 10. AGENT SYSTEM & HUMAN-IN-THE-LOOP DOMAIN
-- ==========================================

CREATE TYPE agent_execution_status AS ENUM ('IDLE', 'RUNNING', 'COMPLETED', 'FAILED', 'AWAITING_APPROVAL');
CREATE TYPE approval_decision AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'MODIFIED');

CREATE TABLE IF NOT EXISTS agent_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- 'TEACHER_ABSENCE_REPORTED', 'ROOM_PROJECTOR_BROKEN'
    source VARCHAR(100) NOT NULL, -- 'SYSTEM_TRIGGER', 'USER_INPUT', 'SCHEDULE_CHECK'
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES agent_events(id) ON DELETE SET NULL,
    agent_name VARCHAR(100) NOT NULL, -- 'Teacher Substitution Agent', 'Room Allocation Agent'
    status agent_execution_status NOT NULL DEFAULT 'IDLE',
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL, -- 'PROPOSE_SUBSTITUTE', 'REASSIGN_ROOM'
    target_entity VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    payload JSONB NOT NULL,
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    explanation TEXT NOT NULL,
    confidence NUMERIC(4,3) NOT NULL,
    chosen_option JSONB NOT NULL,
    rejected_options JSONB DEFAULT '[]'::jsonb,
    is_executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    agent_decision_id UUID NOT NULL REFERENCES agent_decisions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    impact_assessment JSONB NOT NULL DEFAULT '{}'::jsonb,
    status approval_decision NOT NULL DEFAULT 'PENDING',
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    admin_feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 11. AGENT MEMORY (PGVECTOR + STRUCTURED)
-- ==========================================

CREATE TABLE IF NOT EXISTS decision_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    agent_decision_id UUID REFERENCES agent_decisions(id) ON DELETE SET NULL,
    event_context TEXT NOT NULL,
    decision_summary TEXT NOT NULL,
    outcome VARCHAR(50) NOT NULL, -- 'SUCCESS', 'REJECTED_BY_ADMIN', 'OVERRIDDEN'
    admin_feedback TEXT,
    tags VARCHAR(50)[],
    embedding vector(1536), -- Vector representation for semantic memory lookup
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policy_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES school_policies(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    content_chunk TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    embedding vector(1536), -- Vector representation for RAG retrieval
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 12. NOTIFICATIONS DOMAIN
-- ==========================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'SCHEDULE_CHANGE', 'SUBSTITUTION_ASSIGNED', 'APPROVAL_REQUIRED'
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- INDEXES FOR PERFORMANCE & CONSTRAINTS
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_timetable_entries_lookup ON timetable_entries (school_date, period_id, room_id, teacher_id);
CREATE INDEX IF NOT EXISTS idx_timetable_entries_version ON timetable_entries (version_id);
CREATE INDEX IF NOT EXISTS idx_teacher_availability_teacher ON teacher_availability (teacher_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_room_availability_room ON room_availability (room_id, date);
CREATE INDEX IF NOT EXISTS idx_substitution_requests_status ON substitution_requests (status, date);
CREATE INDEX IF NOT EXISTS idx_disruptions_status ON disruptions (status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs (agent_name, status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests (status);
CREATE INDEX IF NOT EXISTS idx_decision_memory_agent ON decision_memory (agent_name);

CREATE INDEX IF NOT EXISTS idx_decision_memory_embedding ON decision_memory USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_policy_memory_embedding ON policy_memory USING hnsw (embedding vector_cosine_ops);
