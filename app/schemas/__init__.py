"""Pydantic schemas package."""

from app.schemas.base import base_response_config
from app.schemas.user import UserResponse, UserCreate
from app.schemas.challenge import ChallengeCreate, ChallengeResponse, ChallengeUpdate
from app.schemas.habit import HabitCreate, HabitResponse, HabitUpdate
from app.schemas.daily_entry import DailyEntryCreate, DailyEntryResponse, DailyEntryUpdate
from app.schemas.auth import Token, GoogleAuthRequest
from app.schemas.habit_template import HabitTemplateResponse

__all__ = [
    "UserResponse",
    "UserCreate",
    "ChallengeCreate",
    "ChallengeResponse",
    "ChallengeUpdate",
    "HabitCreate",
    "HabitResponse",
    "HabitUpdate",
    "DailyEntryCreate",
    "DailyEntryResponse",
    "DailyEntryUpdate",
    "Token",
    "GoogleAuthRequest",
    "HabitTemplateResponse",
]
