-- Phase 6 Database Migration: Schedule Quality Review & Teacher Work-Life Balance Extensions
-- Tracking quality review sessions, metrics, identified issues, recommendations, and optimization plans.

CREATE TABLE IF NOT EXISTS schedule_quality_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timetable_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    scope VARCHAR(50) NOT NULL DEFAULT 'FULL_SCHOOL', -- 'FULL_SCHOOL', 'TEACHER', 'SECTION', 'ROOM', 'DATE_RANGE'
    start_date DATE,
    end_date DATE,
    overall_quality_score NUMERIC(5,2) NOT NULL DEFAULT 85.00,
    teacher_balance_score NUMERIC(5,2) NOT NULL DEFAULT 82.00,
    section_balance_score NUMERIC(5,2) NOT NULL DEFAULT 90.00,
    room_utilization_score NUMERIC(5,2) NOT NULL DEFAULT 88.00,
    preference_alignment_score NUMERIC(5,2) NOT NULL DEFAULT 84.00,
    hard_conflicts_count INT NOT NULL DEFAULT 0,
    issues_count INT NOT NULL DEFAULT 0,
    recommendations_count INT NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'COMPLETED', -- 'PROCESSING', 'COMPLETED', 'OPTIMIZATION_PROPOSED', 'RESOLVED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedule_quality_issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID NOT NULL REFERENCES schedule_quality_reviews(id) ON DELETE CASCADE,
    issue_type VARCHAR(50) NOT NULL, -- 'TEACHER_CONSECUTIVE_LOAD', 'TEACHER_IDLE_GAP', 'TEACHER_PREFERENCE_VIOLATION', 'WORKLOAD_IMBALANCE', 'ROOM_UNDERUTILIZATION', 'ROOM_OVERUTILIZATION', 'ROOM_HOPPING', 'SUBJECT_CONCENTRATION'
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM', -- 'INFO', 'LOW', 'MEDIUM', 'HIGH'
    entity_type VARCHAR(50) NOT NULL, -- 'TEACHER', 'SECTION', 'ROOM', 'SUBJECT'
    entity_id VARCHAR(255) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    observed_value NUMERIC(8,2) NOT NULL,
    threshold_value NUMERIC(8,2) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedule_quality_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID NOT NULL REFERENCES schedule_quality_reviews(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES schedule_quality_issues(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL, -- 'TEACHER_WORKLOAD', 'ROOM_UTILIZATION', 'SUBJECT_DISTRIBUTION'
    recommendation_text TEXT NOT NULL,
    expected_improvement TEXT,
    feasibility_status VARCHAR(30) DEFAULT 'FEASIBLE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedule_optimization_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID NOT NULL REFERENCES schedule_quality_reviews(id) ON DELETE CASCADE,
    timetable_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    plan_title VARCHAR(255) NOT NULL,
    ranking_category VARCHAR(50) NOT NULL, -- 'SIGNIFICANT_IMPROVEMENT', 'MODERATE_IMPROVEMENT', 'MINOR_IMPROVEMENT', 'MINIMAL_CHANGE', 'INVALID'
    changes_count INT NOT NULL DEFAULT 0,
    affected_teachers INT NOT NULL DEFAULT 0,
    affected_sections INT NOT NULL DEFAULT 0,
    affected_rooms INT NOT NULL DEFAULT 0,
    quality_before NUMERIC(5,2) NOT NULL,
    quality_after NUMERIC(5,2) NOT NULL,
    hard_conflicts INT NOT NULL DEFAULT 0,
    soft_penalty NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED', -- 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'STALE'
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedule_optimization_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES schedule_optimization_plans(id) ON DELETE CASCADE,
    timetable_entry_id VARCHAR(255) NOT NULL,
    school_date DATE NOT NULL,
    period_code VARCHAR(20) NOT NULL,
    old_teacher_id VARCHAR(255),
    new_teacher_id VARCHAR(255),
    old_room_id VARCHAR(255),
    new_room_id VARCHAR(255),
    old_period_code VARCHAR(20),
    new_period_code VARCHAR(20),
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_reviews_version ON schedule_quality_reviews (timetable_version);
CREATE INDEX IF NOT EXISTS idx_quality_issues_review ON schedule_quality_issues (review_id);
CREATE INDEX IF NOT EXISTS idx_quality_opt_plans_review ON schedule_optimization_plans (review_id);
