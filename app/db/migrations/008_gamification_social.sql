-- Phase 8 Database Migration: Gamification & Social Achievement Engine
-- Tracking student gamification profiles, verified events, achievements, streaks, rewards, social posts, reactions, and privacy settings.

CREATE TABLE IF NOT EXISTS student_gamification_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL UNIQUE DEFAULT 'student-101',
    total_xp INT NOT NULL DEFAULT 0,
    current_level INT NOT NULL DEFAULT 1,
    coins INT NOT NULL DEFAULT 0,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    total_study_minutes INT NOT NULL DEFAULT 0,
    total_tasks_completed INT NOT NULL DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gamification_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- 'STUDY_TASK_COMPLETED', 'STUDY_SPRINT_COMPLETED', 'DAILY_GOAL_COMPLETED', 'WEEKLY_GOAL_COMPLETED', 'STUDY_PLAN_COMPLETED', 'STUDY_STREAK_EXTENDED', 'TEN_HOURS_STUDIED'
    source VARCHAR(50) NOT NULL DEFAULT 'PLANLY',
    source_id VARCHAR(255) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    xp_awarded INT NOT NULL DEFAULT 0,
    coins_awarded INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT idx_unique_event_source UNIQUE (event_type, source_id, student_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) NOT NULL UNIQUE, -- 'FIRST_STUDY', 'SEVEN_DAY_STREAK', 'TEN_HOURS', 'TWENTY_FIVE_HOURS', 'FIFTY_HOURS', 'WEEKLY_GOAL', 'PLAN_COMPLETE', 'COMEBACK', 'CONSISTENCY', 'EXAM_READY'
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
    icon VARCHAR(50) NOT NULL DEFAULT '🏆',
    xp_reward INT NOT NULL DEFAULT 100,
    coin_reward INT NOT NULL DEFAULT 10,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    achievement_code VARCHAR(100) NOT NULL REFERENCES achievements(code) ON DELETE CASCADE,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    progress NUMERIC(5,2) NOT NULL DEFAULT 100.00,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT idx_unique_student_achievement UNIQUE (student_id, achievement_code)
);

CREATE TABLE IF NOT EXISTS student_streaks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    streak_type VARCHAR(50) NOT NULL DEFAULT 'STUDY_DAILY',
    current_count INT NOT NULL DEFAULT 0,
    longest_count INT NOT NULL DEFAULT 0,
    last_activity_date DATE,
    shields_available INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reward_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'EARN_XP', 'EARN_COINS', 'SPEND_COINS'
    xp_amount INT NOT NULL DEFAULT 0,
    coin_amount INT NOT NULL DEFAULT 0,
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    balance_after INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    student_name VARCHAR(255) NOT NULL DEFAULT 'Student A',
    post_type VARCHAR(50) NOT NULL, -- 'ACHIEVEMENT', 'STREAK', 'MILESTONE', 'GOAL_COMPLETION'
    achievement_code VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    visibility VARCHAR(30) NOT NULL DEFAULT 'CLASS', -- 'PRIVATE', 'FRIENDS', 'CLASS', 'PUBLIC'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS social_reactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES social_posts(id) ON DELETE CASCADE,
    student_id VARCHAR(255) NOT NULL,
    reaction_type VARCHAR(20) NOT NULL DEFAULT '🔥', -- '👏', '🔥', '🎉', '⭐'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT idx_unique_post_reaction UNIQUE (post_id, student_id, reaction_type)
);

CREATE TABLE IF NOT EXISTS social_privacy_settings (
    student_id VARCHAR(255) PRIMARY KEY DEFAULT 'student-101',
    achievement_visibility VARCHAR(30) NOT NULL DEFAULT 'CLASS',
    profile_visibility VARCHAR(30) NOT NULL DEFAULT 'CLASS',
    social_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gamification_events_student ON gamification_events (student_id);
CREATE INDEX IF NOT EXISTS idx_student_achievements_student ON student_achievements (student_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_student ON social_posts (student_id);
CREATE INDEX IF NOT EXISTS idx_social_reactions_post ON social_reactions (post_id);
