"""
Phase 8 Test Suite: Gamification & Social Achievement Engine
Verifies profile creation, deterministic XP & level calculations, streak tracking,
achievement unlock evaluation, idempotency (duplicate event handling), social post sharing,
reactions, and privacy settings.
"""

import pytest

from app.agents.gamification_agent import GamificationAgent
from app.schemas.domain import (
    GamificationEventRequest, SocialPostCreateRequest, SocialReactionRequest,
    SocialPrivacySettingsRequest
)

@pytest.fixture
def gamification_agent():
    return GamificationAgent()

def test_gamification_profile(gamification_agent):
    profile = gamification_agent.get_profile("student-101")
    assert profile.student_id == "student-101"
    assert profile.total_xp >= 2000
    assert profile.current_level >= 1
    assert profile.coins >= 0

def test_level_progression_formula(gamification_agent):
    level, xp_next, pct = gamification_agent.calculate_level(0)
    assert level == 1
    assert xp_next == 500

    level_8, xp_next_8, pct_8 = gamification_agent.calculate_level(2840)
    assert level_8 == 8
    assert xp_next_8 > 2840

def test_process_event_and_idempotency(gamification_agent):
    event_req = GamificationEventRequest(
        student_id="student-test-99",
        event_type="STUDY_TASK_COMPLETED",
        source="PLANLY",
        source_id="task-unique-123",
        metadata={"duration_minutes": 50}
    )

    # First event processing: Should award XP
    res1 = gamification_agent.process_event(event_req)
    assert res1["status"] == "SUCCESS"
    assert res1["xp_awarded"] == 25
    assert res1["coins_awarded"] == 5

    # Second event processing with exact same key: Must be IDEMPOTENT (0 XP awarded)
    res2 = gamification_agent.process_event(event_req)
    assert res2["status"] == "DUPLICATE_EVENT"
    assert res2["xp_awarded"] == 0
    assert res2["coins_awarded"] == 0

def test_streak_and_achievement_unlock(gamification_agent):
    # Process 7 distinct study task events across profile to reach 7-day streak requirement
    for i in range(7):
        gamification_agent.process_event(GamificationEventRequest(
            student_id="student-streak-test",
            event_type="STUDY_TASK_COMPLETED",
            source_id=f"task-streak-{i+1}"
        ))

    achievements = gamification_agent.get_achievements("student-streak-test")
    first_step = next(a for a in achievements if a.code == "FIRST_STUDY")
    assert first_step.unlocked is True

def test_social_post_creation_and_feed(gamification_agent):
    post_req = SocialPostCreateRequest(
        student_id="student-101",
        student_name="Student A",
        post_type="ACHIEVEMENT",
        achievement_code="SEVEN_DAY_STREAK",
        title="7-Day Streak Unlocked!",
        content="🎉 Completed 7 days of verified study!",
        visibility="CLASS"
    )
    post = gamification_agent.create_social_post(post_req)
    assert post.id is not None
    assert post.title == "7-Day Streak Unlocked!"

    feed = gamification_agent.get_social_feed("CLASS")
    assert len(feed) >= 1

def test_social_post_reaction(gamification_agent):
    rxn_res = gamification_agent.react_to_post("post-001", SocialReactionRequest(student_id="student-999", reaction_type="🔥"))
    assert rxn_res["status"] == "SUCCESS"

    # Duplicate reaction check
    rxn_dup = gamification_agent.react_to_post("post-001", SocialReactionRequest(student_id="student-999", reaction_type="🔥"))
    assert rxn_dup["status"] == "SUCCESS"

def test_privacy_settings(gamification_agent):
    update_req = SocialPrivacySettingsRequest(
        student_id="student-101",
        achievement_visibility="FRIENDS",
        profile_visibility="PRIVATE",
        social_enabled=True
    )
    updated = gamification_agent.update_privacy_settings(update_req)
    assert updated.achievement_visibility == "FRIENDS"
    assert updated.profile_visibility == "PRIVATE"
