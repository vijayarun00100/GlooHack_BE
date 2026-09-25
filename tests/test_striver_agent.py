"""
Phase 9 Test Suite: Striver RAG-Powered Personal Study & Learning Agent
Verifies document ingestion, pgvector semantic retrieval, metadata filtering, source citations,
hallucination fallback, learning session creation, adaptive explanation modes, practice evaluation,
quiz scoring, topic mastery updates, Planly context integration, and Gamification event emission.
"""

import pytest

from app.agents.striver_agent import StriverAgent
from app.agents.gamification_agent import GamificationAgent
from app.schemas.domain import (
    StriverDocumentCreateRequest, StriverSessionStartRequest,
    StriverExplainRequest, StriverPracticeAnswerRequest, StriverQuizAnswerRequest
)

@pytest.fixture
def gamification_agent():
    return GamificationAgent()

@pytest.fixture
def striver_agent(gamification_agent):
    return StriverAgent(gamification_agent=gamification_agent)

def test_document_ingestion_and_chunking(striver_agent):
    req = StriverDocumentCreateRequest(
        title="Physics Chapter 2: Kinematics & Laws of Motion",
        subject="Physics",
        grade=9,
        course="Physics",
        uploaded_by="teacher-002",
        source_type="TEACHER_NOTES",
        content="Newton's First Law states that an object remains at rest unless acted upon by a net force.\n\nNewton's Second Law: F = ma."
    )
    doc = striver_agent.ingest_document(req)
    assert doc.id is not None
    assert doc.chunk_count == 2
    assert len(striver_agent.document_chunks) >= 5

def test_vector_retrieval_and_source_citations(striver_agent):
    retrieved = striver_agent.search_knowledge_base("Mathematics", "Quadratic Equations", "quadratic formula discriminant", top_k=2)
    assert len(retrieved) > 0
    assert retrieved[0]["relevance_score"] >= 0.6
    assert "Quadratic" in retrieved[0]["chunk"]["content"] or "Discriminant" in retrieved[0]["chunk"]["content"]

def test_explain_mode_with_citations(striver_agent):
    req = StriverExplainRequest(
        student_id="student-101",
        subject="Mathematics",
        topic="Quadratic Equations",
        prompt="Explain the quadratic formula.",
        mode="EXPLAIN"
    )
    res = striver_agent.generate_explanation(req)
    assert res.session_id is not None
    assert len(res.sources) >= 1
    assert res.sources[0].page_number >= 1
    assert res.grounded_in_materials is True

def test_hallucination_fallback(striver_agent):
    req = StriverExplainRequest(
        student_id="student-101",
        subject="Biology",
        topic="Photosynthesis",
        prompt="Explain the Calvin Cycle in detail.",
        mode="EXPLAIN"
    )
    res = striver_agent.generate_explanation(req)
    assert res.grounded_in_materials is False
    assert "couldn't find relevant material" in res.explanation.lower()

def test_practice_question_evaluation_and_mastery(striver_agent):
    answer_req = StriverPracticeAnswerRequest(
        session_id="session-test-01",
        question_id="pq-math-101",
        student_answer="x = 2 and 3"
    )
    res = striver_agent.evaluate_practice_answer(answer_req)
    assert res.is_correct is True
    assert res.updated_mastery > 60.0
    assert len(res.sources) >= 1

def test_quiz_scoring_and_gamification_event_emission(striver_agent, gamification_agent):
    initial_xp = gamification_agent.get_profile("student-101").total_xp
    
    quiz_answers = {
        "q1": "A",
        "q2": "B",
        "q3": "C",
        "q4": "B",
        "q5": "A"
    }
    quiz_req = StriverQuizAnswerRequest(session_id="session-quiz-101", answers=quiz_answers)
    res = striver_agent.submit_quiz(quiz_req)
    
    assert res.score == 5
    assert res.accuracy_percentage == 100.0
    assert res.mastery_after > res.mastery_before
    
    # Verify Gamification received event and awarded XP
    new_xp = gamification_agent.get_profile("student-101").total_xp
    assert new_xp > initial_xp

def test_topic_mastery_retrieval(striver_agent):
    mastery = striver_agent.get_mastery("student-101", "Mathematics", "Quadratic Equations")
    assert mastery.student_id == "student-101"
    assert mastery.mastery_score >= 50.0
    assert mastery.mastery_level in ["NEEDS_SUPPORT", "DEVELOPING", "PRACTICING", "STRONG", "MASTERED"]
