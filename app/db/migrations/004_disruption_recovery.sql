-- Phase 4 Database Migration: Disruption Recovery Agent Extensions
-- Tracking major campus disruptions (building closures, emergencies, multi-room failures)
-- and candidate multi-change recovery plans.

CREATE TABLE IF NOT EXISTS campus_disruption_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL, -- 'CAMPUS_DISRUPTION', 'BUILDING_CLOSURE', 'FIRE_DRILL', 'WEATHER_EMERGENCY', 'INFRASTRUCTURE_OUTAGE'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_period VARCHAR(20) DEFAULT 'P1',
    end_period VARCHAR(20) DEFAULT 'P5',
    affected_rooms TEXT[] DEFAULT '{}',
    affected_teachers TEXT[] DEFAULT '{}',
    affected_sections TEXT[] DEFAULT '{}',
    severity VARCHAR(30) DEFAULT 'HIGH', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    source VARCHAR(50) DEFAULT 'ADMIN', -- 'ADMIN', 'SYSTEM', 'IOT_SENSOR'
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'PROCESSING', 'RECOVERY_PROPOSED', 'RESOLVED', 'REQUIRES_APPROVAL', 'CANCELLED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disruption_id UUID NOT NULL REFERENCES campus_disruption_events(id) ON DELETE CASCADE,
    timetable_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    plan_title VARCHAR(255) NOT NULL,
    ranking_category VARCHAR(50) NOT NULL, -- 'CLEAN_RECOVERY', 'LOW_DISRUPTION', 'MODERATE_DISRUPTION', 'HIGH_DISRUPTION', 'INVALID'
    hard_conflicts INT NOT NULL DEFAULT 0,
    soft_penalty NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    affected_classes INT NOT NULL DEFAULT 0,
    affected_teachers INT NOT NULL DEFAULT 0,
    affected_rooms INT NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED', -- 'PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'STALE'
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_plan_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recovery_plan_id UUID NOT NULL REFERENCES recovery_plans(id) ON DELETE CASCADE,
    timetable_entry_id VARCHAR(255) NOT NULL,
    school_date DATE NOT NULL,
    old_teacher_id VARCHAR(255),
    new_teacher_id VARCHAR(255),
    old_room_id VARCHAR(255),
    new_room_id VARCHAR(255),
    old_period_code VARCHAR(20) NOT NULL,
    new_period_code VARCHAR(20) NOT NULL,
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campus_disruption_dates ON campus_disruption_events (start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_campus_disruption_status ON campus_disruption_events (status);
CREATE INDEX IF NOT EXISTS idx_recovery_plans_disruption ON recovery_plans (disruption_id);
CREATE INDEX IF NOT EXISTS idx_recovery_plans_status ON recovery_plans (status);
