import pytest
import uuid
import psycopg2
from app.core.config import settings
from app.db.seed import seed_database
import app.db.repository as repo

def test_db_seed_execution():
    """Verify that seed_database executes cleanly and seeds tables in PostgreSQL."""
    seed_database()
    students = repo.get_all_students()
    assert len(students) >= 4
    student_numbers = [s["student_number"] for s in students]
    assert "STU-1001" in student_numbers

def test_directory_repository_queries():
    """Verify directory queries return valid DB objects."""
    teachers = repo.get_all_teachers()
    assert len(teachers) >= 5
    
    subjects = repo.get_all_subjects()
    assert len(subjects) >= 6
    subject_codes = [s["code"] for s in subjects]
    assert "MATH101" in subject_codes
    assert "PHYS200" in subject_codes

    rooms = repo.get_all_rooms()
    assert len(rooms) >= 6

def test_striver_documents_and_mastery_persistence():
    """Verify Striver documents and student mastery records from PostgreSQL."""
    docs = repo.get_striver_documents_db()
    assert len(docs) >= 3

    mastery = repo.get_striver_mastery_db("student-101", "Mathematics", "Quadratic Equations")
    assert mastery["mastery_score"] == 71.0

    # Test updating mastery in DB
    updated = repo.update_striver_mastery_db("student-101", "Mathematics", "Quadratic Equations", 75.0, "STRONG")
    assert updated is True

    mastery_after = repo.get_striver_mastery_db("student-101", "Mathematics", "Quadratic Equations")
    assert mastery_after["mastery_score"] == 75.0

def test_gamification_profile_persistence():
    """Verify gamification profile retrieval from PostgreSQL."""
    profile = repo.get_gamification_profile_db("student-101")
    assert profile["total_xp"] == 2840
    assert profile["current_level"] == 8
    assert profile["current_streak"] == 7
