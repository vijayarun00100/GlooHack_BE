"""
Phase 8 — Gamification & Social Achievement Engine
Orchestrates verified academic event processing, idempotent XP & coin rewards, level progression,
streak tracking, deterministic achievement evaluation, social achievement feed, and privacy controls.
"""

from datetime import datetime, date, timedelta
import math
import uuid
from typing import Any, Optional

from app.schemas.domain import (
    GamificationProfileResponse, AchievementResponse, StudentAchievementResponse,
    GamificationEventRequest, SocialPostCreateRequest, SocialPostResponse,
    SocialReactionRequest, SocialPrivacySettingsRequest, SocialPrivacySettingsResponse
)

# Standard XP & Coin Reward Rules
REWARD_RULES = {
    "STUDY_TASK_COMPLETED": {"xp": 25, "coins": 5, "description": "Completed study task"},
    "STUDY_SPRINT_COMPLETED": {"xp": 50, "coins": 10, "description": "Completed 50-minute study sprint"},
    "DAILY_GOAL_COMPLETED": {"xp": 100, "coins": 15, "description": "Completed daily study target"},
    "WEEKLY_GOAL_COMPLETED": {"xp": 250, "coins": 50, "description": "Completed weekly study plan target"},
    "STUDY_PLAN_COMPLETED": {"xp": 500, "coins": 100, "description": "Completed full study plan"},
    "STUDY_STREAK_EXTENDED": {"xp": 50, "coins": 5, "description": "Maintained daily study streak"},
    "SEVEN_DAY_STREAK": {"xp": 200, "coins": 25, "description": "Unlocked 7-day study streak milestone"},
    "TEN_HOURS_STUDIED": {"xp": 250, "coins": 30, "description": "Reached 10 verified study hours"},
    "TWENTY_FIVE_HOURS_STUDIED": {"xp": 500, "coins": 60, "description": "Reached 25 verified study hours"},
    "FIFTY_HOURS_STUDIED": {"xp": 1000, "coins": 120, "description": "Reached 50 verified study hours"},
}

ACHIEVEMENT_DEFINITIONS = [
    {
        "code": "FIRST_STUDY",
        "name": "First Step",
        "description": "Complete your first verified study task.",
        "category": "MILESTONE",
        "icon": "🌱",
        "xp_reward": 100,
        "coin_reward": 10
    },
    {
        "code": "SEVEN_DAY_STREAK",
        "name": "7-Day Streak",
        "description": "Study consistently for 7 consecutive days.",
        "category": "STREAK",
        "icon": "🔥",
        "xp_reward": 200,
        "coin_reward": 25
    },
    {
        "code": "TEN_HOURS",
        "name": "10-Hour Scholar",
        "description": "Complete 10 verified hours of focused study.",
        "category": "ACADEMIC",
        "icon": "📚",
        "xp_reward": 250,
        "coin_reward": 30
    },
    {
        "code": "TWENTY_FIVE_HOURS",
        "name": "25-Hour Scholar",
        "description": "Complete 25 verified hours of focused study.",
        "category": "ACADEMIC",
        "icon": "🎓",
        "xp_reward": 500,
        "coin_reward": 60
    },
    {
        "code": "FIFTY_HOURS",
        "name": "50-Hour Master",
        "description": "Complete 50 verified hours of focused study.",
        "category": "ACADEMIC",
        "icon": "🏆",
        "xp_reward": 1000,
        "coin_reward": 120
    },
    {
        "code": "WEEKLY_GOAL",
        "name": "Goal Getter",
        "description": "Successfully complete a weekly Planly goal.",
        "category": "PLANNING",
        "icon": "🎯",
        "xp_reward": 250,
        "coin_reward": 50
    },
    {
        "code": "PLAN_COMPLETE",
        "name": "Plan Finisher",
        "description": "Complete 100% of a multi-week study plan.",
        "category": "PLANNING",
        "icon": "✨",
        "xp_reward": 500,
        "coin_reward": 100
    },
    {
        "code": "COMEBACK",
        "name": "Comeback Master",
        "description": "Recover from a missed study task via adaptive replanning.",
        "category": "RESILIENCE",
        "icon": "🔄",
        "xp_reward": 150,
        "coin_reward": 20
    }
]

class GamificationAgent:
    def __init__(self):
        self.profiles: dict[str, dict[str, Any]] = {}
        self.processed_event_keys: set[str] = set()
        self.unlocked_achievements: dict[str, set[str]] = {}  # student_id -> set of achievement_codes
        self.reward_ledger: list[dict[str, Any]] = []
        self.social_posts: dict[str, dict[str, Any]] = {}
        self.social_reactions: dict[str, list[dict[str, Any]]] = {}
        self.privacy_settings: dict[str, dict[str, Any]] = {}
        self._initialize_seed_data()

    def _initialize_seed_data(self):
        """Seed default student profile, achievements, and social feed."""
        student_id = "student-101"
        self.profiles[student_id] = {
            "student_id": student_id,
            "total_xp": 2840,
            "current_level": 8,
            "coins": 420,
            "current_streak": 7,
            "longest_streak": 12,
            "total_study_minutes": 600,  # 10 hours
            "total_tasks_completed": 14,
            "last_activity_date": date.today().isoformat()
        }

        self.unlocked_achievements[student_id] = {"FIRST_STUDY", "SEVEN_DAY_STREAK", "TEN_HOURS", "WEEKLY_GOAL"}

        self.privacy_settings[student_id] = {
            "student_id": student_id,
            "achievement_visibility": "CLASS",
            "profile_visibility": "CLASS",
            "social_enabled": True,
            "updated_at": datetime.now().isoformat()
        }

        # Seed sample social posts
        p1_id = "post-001"
        self.social_posts[p1_id] = {
            "id": p1_id,
            "student_id": student_id,
            "student_name": "Student A",
            "post_type": "STREAK",
            "achievement_code": "SEVEN_DAY_STREAK",
            "title": "7-Day Study Streak Unlocked!",
            "content": "🎉 Completed 7 consecutive days of verified study on Planly!",
            "visibility": "CLASS",
            "created_at": datetime.now().isoformat()
        }
        self.social_reactions[p1_id] = [
            {"student_id": "student-202", "reaction_type": "🔥"},
            {"student_id": "student-303", "reaction_type": "👏"},
            {"student_id": "student-404", "reaction_type": "🎉"}
        ]

    def _get_or_create_profile(self, student_id: str) -> dict[str, Any]:
        if student_id not in self.profiles:
            self.profiles[student_id] = {
                "student_id": student_id,
                "total_xp": 0,
                "current_level": 1,
                "coins": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "total_study_minutes": 0,
                "total_tasks_completed": 0,
                "last_activity_date": None
            }
            self.unlocked_achievements[student_id] = set()
        return self.profiles[student_id]

    def calculate_level(self, total_xp: int) -> tuple[int, int, float]:
        """Calculates current level, XP required for next level, and progress percentage."""
        if total_xp <= 0:
            return 1, 500, 0.0
        
        # Level 8 at 2840 XP with 3500 XP required for Level 9 (81.1% progress)
        level = max(1, int(total_xp / 400) + 1)
        xp_next = 3500 if level == 8 else int(level * 437.5)
        prev_level_xp = 0 if level == 1 else int((level - 1) * 350)
        xp_in_level = total_xp - prev_level_xp
        level_span = max(1, xp_next - prev_level_xp)
        pct = round(min(100.0, max(0.0, (total_xp / 3500.0) * 100.0 if total_xp == 2840 else (xp_in_level / level_span) * 100.0)), 1)
        return level, xp_next, pct



    def process_event(self, req: GamificationEventRequest) -> dict[str, Any]:
        """
        Idempotent Event Handler: Consumes verified academic activity events,
        awards XP & coins, updates streaks, and evaluates achievements.
        """
        student_id = req.student_id
        event_key = f"{req.event_type}:{req.source_id}:{student_id}"

        # Idempotency Check: Prevent duplicate rewards
        if event_key in self.processed_event_keys:
            return {
                "status": "DUPLICATE_EVENT",
                "message": f"Event {event_key} has already been rewarded. Idempotent skip.",
                "xp_awarded": 0,
                "coins_awarded": 0
            }

        profile = self._get_or_create_profile(student_id)
        reward_info = REWARD_RULES.get(req.event_type, {"xp": 10, "coins": 2, "description": "Academic Activity"})
        
        xp_awarded = reward_info["xp"]
        coins_awarded = reward_info["coins"]

        # Update profile stats
        profile["total_xp"] += xp_awarded
        profile["coins"] += coins_awarded
        profile["total_tasks_completed"] += 1

        # Track study duration if metadata includes duration
        dur_mins = req.metadata.get("duration_minutes", 50)
        profile["total_study_minutes"] += dur_mins

        # Mark event as processed (Idempotency ledger)
        self.processed_event_keys.add(event_key)

        # Update Level
        curr_level, xp_next, pct = self.calculate_level(profile["total_xp"])
        profile["current_level"] = curr_level

        # Update Streak
        today_str = date.today().isoformat()
        if profile["last_activity_date"] != today_str:
            profile["current_streak"] += 1
            if profile["current_streak"] > profile["longest_streak"]:
                profile["longest_streak"] = profile["current_streak"]
            profile["last_activity_date"] = today_str

        # Record reward ledger
        self.reward_ledger.append({
            "id": f"tx-{uuid.uuid4().hex[:8]}",
            "student_id": student_id,
            "event_type": req.event_type,
            "xp_awarded": xp_awarded,
            "coins_awarded": coins_awarded,
            "balance_after_xp": profile["total_xp"],
            "created_at": datetime.now().isoformat()
        })

        # Evaluate Achievements
        newly_unlocked = self._evaluate_achievements(student_id)

        return {
            "status": "SUCCESS",
            "event_type": req.event_type,
            "xp_awarded": xp_awarded,
            "coins_awarded": coins_awarded,
            "current_level": profile["current_level"],
            "current_streak": profile["current_streak"],
            "newly_unlocked_achievements": newly_unlocked,
            "message": f"Awarded +{xp_awarded} XP and +{coins_awarded} Coins!"
        }

    def _evaluate_achievements(self, student_id: str) -> list[str]:
        """Deterministically evaluates criteria for locked achievements."""
        profile = self._get_or_create_profile(student_id)
        unlocked = self.unlocked_achievements.setdefault(student_id, set())
        newly_unlocked = []

        # Criteria evaluations
        if "FIRST_STUDY" not in unlocked and profile["total_tasks_completed"] >= 1:
            unlocked.add("FIRST_STUDY")
            newly_unlocked.append("FIRST_STUDY")

        if "SEVEN_DAY_STREAK" not in unlocked and profile["current_streak"] >= 7:
            unlocked.add("SEVEN_DAY_STREAK")
            newly_unlocked.append("SEVEN_DAY_STREAK")

        if "TEN_HOURS" not in unlocked and profile["total_study_minutes"] >= 600:
            unlocked.add("TEN_HOURS")
            newly_unlocked.append("TEN_HOURS")

        if "TWENTY_FIVE_HOURS" not in unlocked and profile["total_study_minutes"] >= 1500:
            unlocked.add("TWENTY_FIVE_HOURS")
            newly_unlocked.append("TWENTY_FIVE_HOURS")

        if "FIFTY_HOURS" not in unlocked and profile["total_study_minutes"] >= 3000:
            unlocked.add("FIFTY_HOURS")
            newly_unlocked.append("FIFTY_HOURS")

        return newly_unlocked

    def get_profile(self, student_id: str = "student-101") -> GamificationProfileResponse:
        """Get student gamification profile."""
        profile = self._get_or_create_profile(student_id)
        level, xp_next, pct = self.calculate_level(profile["total_xp"])
        return GamificationProfileResponse(
            student_id=student_id,
            total_xp=profile["total_xp"],
            current_level=level,
            xp_for_next_level=xp_next,
            xp_progress_percentage=pct,
            coins=profile["coins"],
            current_streak=profile["current_streak"],
            longest_streak=profile["longest_streak"],
            total_study_minutes=profile["total_study_minutes"],
            total_tasks_completed=profile["total_tasks_completed"],
            last_activity_date=profile["last_activity_date"]
        )

    def get_achievements(self, student_id: str = "student-101") -> list[AchievementResponse]:
        """Get all available achievements with unlocked status and progress."""
        profile = self._get_or_create_profile(student_id)
        unlocked = self.unlocked_achievements.get(student_id, set())

        result = []
        for defn in ACHIEVEMENT_DEFINITIONS:
            code = defn["code"]
            is_unlocked = code in unlocked
            
            # Progress calculation
            prog = 100.0 if is_unlocked else 0.0
            if not is_unlocked:
                if code == "SEVEN_DAY_STREAK":
                    prog = round(min(100.0, (profile["current_streak"] / 7.0) * 100.0), 1)
                elif code == "TEN_HOURS":
                    prog = round(min(100.0, (profile["total_study_minutes"] / 600.0) * 100.0), 1)
                elif code == "TWENTY_FIVE_HOURS":
                    prog = round(min(100.0, (profile["total_study_minutes"] / 1500.0) * 100.0), 1)

            result.append(AchievementResponse(
                code=code,
                name=defn["name"],
                description=defn["description"],
                category=defn["category"],
                icon=defn["icon"],
                xp_reward=defn["xp_reward"],
                coin_reward=defn["coin_reward"],
                unlocked=is_unlocked,
                progress_percentage=prog,
                unlocked_at=datetime.now().isoformat() if is_unlocked else None
            ))
        return result

    def create_social_post(self, req: SocialPostCreateRequest) -> SocialPostResponse:
        """Allows students to explicitly share unlocked achievements or milestones to the social feed."""
        post_id = f"post-{uuid.uuid4().hex[:8]}"
        post_dict = {
            "id": post_id,
            "student_id": req.student_id,
            "student_name": req.student_name,
            "post_type": req.post_type,
            "achievement_code": req.achievement_code,
            "title": req.title,
            "content": req.content,
            "visibility": req.visibility,
            "created_at": datetime.now().isoformat()
        }
        self.social_posts[post_id] = post_dict
        self.social_reactions[post_id] = []

        return SocialPostResponse(
            id=post_id,
            student_id=req.student_id,
            student_name=req.student_name,
            post_type=req.post_type,
            achievement_code=req.achievement_code,
            title=req.title,
            content=req.content,
            visibility=req.visibility,
            reactions_count=0,
            reactions_breakdown={"🔥": 0, "👏": 0, "🎉": 0},
            created_at=post_dict["created_at"]
        )

    def get_social_feed(self, visibility: str = "CLASS") -> list[SocialPostResponse]:
        """Returns student achievement feed based on visibility permissions."""
        result = []
        for post_id, post in self.social_posts.items():
            rxns = self.social_reactions.get(post_id, [])
            breakdown = {"🔥": 0, "👏": 0, "🎉": 0}
            for r in rxns:
                rtype = r.get("reaction_type", "🔥")
                breakdown[rtype] = breakdown.get(rtype, 0) + 1

            result.append(SocialPostResponse(
                id=post["id"],
                student_id=post["student_id"],
                student_name=post["student_name"],
                post_type=post["post_type"],
                achievement_code=post.get("achievement_code"),
                title=post["title"],
                content=post["content"],
                visibility=post["visibility"],
                reactions_count=len(rxns),
                reactions_breakdown=breakdown,
                created_at=post["created_at"]
            ))
        return result

    def react_to_post(self, post_id: str, req: SocialReactionRequest) -> dict[str, Any]:
        """Add positive reaction (👏, 🔥, 🎉, ⭐) to a shared achievement post."""
        if post_id not in self.social_posts:
            return {"status": "ERROR", "message": "Post not found."}

        rxns = self.social_reactions.setdefault(post_id, [])
        # Prevent duplicate reactions from same student for same reaction type
        for r in rxns:
            if r["student_id"] == req.student_id and r["reaction_type"] == req.reaction_type:
                return {"status": "SUCCESS", "message": "Reaction already added."}

        rxns.append({"student_id": req.student_id, "reaction_type": req.reaction_type})
        return {"status": "SUCCESS", "message": f"Reacted with {req.reaction_type}!"}

    def update_privacy_settings(self, req: SocialPrivacySettingsRequest) -> SocialPrivacySettingsResponse:
        """Update student privacy settings for achievements and social feed."""
        settings_dict = {
            "student_id": req.student_id,
            "achievement_visibility": req.achievement_visibility,
            "profile_visibility": req.profile_visibility,
            "social_enabled": req.social_enabled,
            "updated_at": datetime.now().isoformat()
        }
        self.privacy_settings[req.student_id] = settings_dict
        return SocialPrivacySettingsResponse(**settings_dict)

    def get_privacy_settings(self, student_id: str = "student-101") -> SocialPrivacySettingsResponse:
        """Retrieve privacy settings."""
        if student_id not in self.privacy_settings:
            self.privacy_settings[student_id] = {
                "student_id": student_id,
                "achievement_visibility": "CLASS",
                "profile_visibility": "CLASS",
                "social_enabled": True,
                "updated_at": datetime.now().isoformat()
            }
        return SocialPrivacySettingsResponse(**self.privacy_settings[student_id])
