-- Phase 3 Database Migration: Room Allocation Agent Extensions
-- Tracking room disruptions, equipment failures, capacity restrictions, and maintenance closures

CREATE TABLE IF NOT EXISTS room_disruption_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'CLOSED', 'MAINTENANCE', 'EQUIPMENT_FAILURE', 'CAPACITY_RESTRICTION'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_period VARCHAR(20) DEFAULT 'P1',
    end_period VARCHAR(20) DEFAULT 'P5',
    reason TEXT NOT NULL,
    required_equipment_impact VARCHAR(100)[],
    capacity_restriction INT,
    source VARCHAR(50) DEFAULT 'ADMIN', -- 'ADMIN', 'SYSTEM', 'EMAIL'
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'PROCESSING', 'REALLOCATED', 'REQUIRES_APPROVAL', 'CANCELLED'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_room_disruption_room ON room_disruption_events (room_id, start_date);
CREATE INDEX IF NOT EXISTS idx_room_disruption_status ON room_disruption_events (status);
