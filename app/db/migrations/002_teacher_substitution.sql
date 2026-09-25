-- Phase 2 Database Migration: Teacher Substitution Agent Extensions
-- Extends teacher_absences and substitution tables for email ingestion and thread tracking

CREATE TABLE IF NOT EXISTS teacher_absence_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_email_id VARCHAR(255),
    thread_id VARCHAR(255),
    raw_email_subject VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    teacher_id UUID REFERENCES teachers(id) ON DELETE SET NULL,
    extracted_teacher_name VARCHAR(100),
    absence_date DATE NOT NULL,
    start_period VARCHAR(20) DEFAULT 'P1',
    end_period VARCHAR(20) DEFAULT 'P5',
    duration VARCHAR(30) DEFAULT 'FULL_DAY', -- 'FULL_DAY', 'PARTIAL_DAY'
    reason TEXT,
    extraction_confidence NUMERIC(4,3) DEFAULT 0.95,
    status VARCHAR(30) NOT NULL DEFAULT 'DETECTED', -- 'DETECTED', 'VALIDATED', 'PROCESSING', 'RESOLVED', 'REQUIRES_REVIEW', 'CANCELLED'
    admin_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_absence_events_teacher ON teacher_absence_events (teacher_id, absence_date);
CREATE INDEX IF NOT EXISTS idx_absence_events_thread ON teacher_absence_events (thread_id);
CREATE INDEX IF NOT EXISTS idx_absence_events_status ON teacher_absence_events (status);
