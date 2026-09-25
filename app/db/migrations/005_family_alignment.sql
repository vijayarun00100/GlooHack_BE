-- Phase 5 Database Migration: Family Day Alignment Agent Extensions
-- Tracking family alignment requests, candidate alignment plans, and sibling attendance changes.

CREATE TABLE IF NOT EXISTS family_alignment_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id VARCHAR(255) NOT NULL,
    family_name VARCHAR(255) NOT NULL,
    requested_by VARCHAR(255) NOT NULL,
    student_ids TEXT[] NOT NULL DEFAULT '{}',
    target_alignment VARCHAR(50) DEFAULT 'MAXIMIZE', -- 'MAXIMIZE', 'MATCH_SIBLING', 'SPECIFIC_DAYS'
    preferred_days TEXT[] DEFAULT '{}',
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'PROCESSING', 'PROPOSED', 'RESOLVED', 'REQUIRES_APPROVAL', 'CANCELLED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS family_alignment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES family_alignment_requests(id) ON DELETE CASCADE,
    family_id VARCHAR(255) NOT NULL,
    timetable_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    plan_title VARCHAR(255) NOT NULL,
    ranking_category VARCHAR(50) NOT NULL, -- 'FULL_ALIGNMENT', 'HIGH_ALIGNMENT', 'PARTIAL_ALIGNMENT', 'MINIMAL_CHANGE', 'INVALID'
    alignment_before INT NOT NULL DEFAULT 0,
    alignment_after INT NOT NULL DEFAULT 0,
    total_days INT NOT NULL DEFAULT 5,
    hard_conflicts INT NOT NULL DEFAULT 0,
    soft_penalty NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED', -- 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'STALE'
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS family_alignment_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES family_alignment_plans(id) ON DELETE CASCADE,
    student_id VARCHAR(255) NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    grade_section VARCHAR(50) NOT NULL,
    school_date DATE NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    old_state VARCHAR(20) NOT NULL, -- 'CAMPUS', 'HOME'
    new_state VARCHAR(20) NOT NULL, -- 'CAMPUS', 'HOME'
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_family_req_family ON family_alignment_requests (family_id);
CREATE INDEX IF NOT EXISTS idx_family_plans_req ON family_alignment_plans (request_id);
CREATE INDEX IF NOT EXISTS idx_family_plans_status ON family_alignment_plans (status);
