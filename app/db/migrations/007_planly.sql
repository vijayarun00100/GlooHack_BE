-- Phase 7 Database Migration: Planly Personalized Study Planning Agent
-- Tracking study goals, study plans, study sprints, study tasks, and progress tracking.

CREATE TABLE IF NOT EXISTS study_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL DEFAULT 'student-101',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_date DATE NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'HIGH', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'COMPLETED', 'ARCHIVED', 'PAUSED'
    subjects JSONB NOT NULL DEFAULT '["Mathematics"]'::jsonb,
    focus_topics JSONB NOT NULL DEFAULT '["Algebra", "Quadratic Equations", "Functions"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL DEFAULT 'student-101',
    goal_id UUID REFERENCES study_goals(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'COMPLETED', 'REPLANNED', 'ARCHIVED'
    total_hours NUMERIC(5,2) NOT NULL DEFAULT 10.00,
    planned_hours NUMERIC(5,2) NOT NULL DEFAULT 8.00,
    completed_hours NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    completion_percentage NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    feasibility_score NUMERIC(5,2) NOT NULL DEFAULT 100.00,
    goal_coverage_score NUMERIC(5,2) NOT NULL DEFAULT 92.00,
    time_utilization_score NUMERIC(5,2) NOT NULL DEFAULT 88.00,
    deadline_safety_score NUMERIC(5,2) NOT NULL DEFAULT 95.00,
    workload_balance_score NUMERIC(5,2) NOT NULL DEFAULT 90.00,
    overall_quality_score NUMERIC(5,2) NOT NULL DEFAULT 92.00,
    energy_preference VARCHAR(20) NOT NULL DEFAULT 'NORMAL', -- 'LOW', 'NORMAL', 'HIGH'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_sprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    school_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 50,
    subject VARCHAR(100) NOT NULL,
    focus_area VARCHAR(255) NOT NULL,
    sprint_type VARCHAR(50) NOT NULL DEFAULT 'PRACTICE', -- 'REVIEW', 'MAIN_STUDY', 'PRACTICE', 'SUMMARY', 'MOCK_TEST'
    status VARCHAR(30) NOT NULL DEFAULT 'PLANNED', -- 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'MISSED', 'SKIPPED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sprint_id UUID NOT NULL REFERENCES study_sprints(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL DEFAULT 'PRACTICE_PROBLEMS',
    estimated_minutes INT NOT NULL DEFAULT 30,
    actual_minutes INT DEFAULT 0,
    priority VARCHAR(20) NOT NULL DEFAULT 'HIGH',
    status VARCHAR(30) NOT NULL DEFAULT 'PLANNED', -- 'PLANNED', 'COMPLETED', 'MISSED', 'REPLANNED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL DEFAULT 'student-101',
    plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    task_id UUID REFERENCES study_tasks(id) ON DELETE CASCADE,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    actual_minutes INT NOT NULL DEFAULT 0,
    self_reported_difficulty VARCHAR(30) DEFAULT 'MEDIUM', -- 'EASY', 'MEDIUM', 'HARD'
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_goals_student ON study_goals (student_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_student ON study_plans (student_id);
CREATE INDEX IF NOT EXISTS idx_study_sprints_plan ON study_sprints (plan_id);
CREATE INDEX IF NOT EXISTS idx_study_sprints_date ON study_sprints (school_date);
CREATE INDEX IF NOT EXISTS idx_study_tasks_sprint ON study_tasks (sprint_id);
