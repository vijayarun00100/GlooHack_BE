-- Phase 9 Database Migration: Striver RAG-Powered Personal Study & Learning Agent
-- Tracking study documents, semantic vector chunks, striver learning sessions, interactions, practice attempts, mastery scores, and learning events.

CREATE TABLE IF NOT EXISTS striver_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    grade INT NOT NULL DEFAULT 9,
    course VARCHAR(100) NOT NULL DEFAULT 'Mathematics',
    uploaded_by VARCHAR(255) NOT NULL DEFAULT 'teacher-001',
    source_type VARCHAR(50) NOT NULL DEFAULT 'CHAPTER_NOTES', -- 'TEACHER_NOTES', 'TEXTBOOK_EXCERPT', 'STUDENT_NOTES', 'ASSIGNMENT'
    status VARCHAR(30) NOT NULL DEFAULT 'READY', -- 'UPLOADING', 'PROCESSING', 'INDEXING', 'READY', 'FAILED'
    chunk_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS striver_document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES striver_documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb, -- { subject, grade, chapter, topic, page_number }
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS striver_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL DEFAULT 'student-101',
    planly_task_id VARCHAR(255),
    subject VARCHAR(100) NOT NULL DEFAULT 'Mathematics',
    topic VARCHAR(255) NOT NULL DEFAULT 'Quadratic Equations',
    mode VARCHAR(50) NOT NULL DEFAULT 'EXPLAIN', -- 'EXPLAIN', 'SIMPLE', 'PRACTICE', 'QUIZ', 'REVISION', 'HINT', 'SOCRATIC'
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    questions_asked INT NOT NULL DEFAULT 0,
    practice_attempts INT NOT NULL DEFAULT 0,
    correct_attempts INT NOT NULL DEFAULT 0,
    mastery_before NUMERIC(5,2) NOT NULL DEFAULT 60.00,
    mastery_after NUMERIC(5,2) NOT NULL DEFAULT 71.00
);

CREATE TABLE IF NOT EXISTS striver_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES striver_sessions(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL DEFAULT 'EXPLAIN',
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS striver_practice_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES striver_sessions(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    student_answer TEXT,
    expected_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    hint_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS striver_mastery (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL DEFAULT 'student-101',
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    mastery_score NUMERIC(5,2) NOT NULL DEFAULT 60.00,
    mastery_level VARCHAR(30) NOT NULL DEFAULT 'PRACTICING', -- 'NEEDS_SUPPORT', 'DEVELOPING', 'PRACTICING', 'STRONG', 'MASTERED'
    confidence VARCHAR(30) NOT NULL DEFAULT 'MEDIUM',
    attempts INT NOT NULL DEFAULT 0,
    correct_attempts INT NOT NULL DEFAULT 0,
    last_practiced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT idx_unique_student_subject_topic UNIQUE (student_id, subject, topic)
);

CREATE TABLE IF NOT EXISTS striver_learning_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(255) NOT NULL,
    session_id UUID REFERENCES striver_sessions(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL, -- 'STRIVER_SESSION_COMPLETED', 'STRIVER_QUIZ_COMPLETED', 'STRIVER_TOPIC_PRACTICED', 'STRIVER_MASTERY_MILESTONE'
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_striver_chunks_document ON striver_document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_striver_sessions_student ON striver_sessions (student_id);
CREATE INDEX IF NOT EXISTS idx_striver_mastery_student ON striver_mastery (student_id, subject, topic);
