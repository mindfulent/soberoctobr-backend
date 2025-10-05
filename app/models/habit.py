"""Habit database model."""

import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class HabitType(str, enum.Enum):
    """Habit type enumeration."""
    BINARY = "binary"
    COUNTED = "counted"


class Habit(Base):
    """
    Habit model for storing habit configuration within a challenge.

    Attributes:
        id: Unique habit identifier (UUID)
        challenge_id: Foreign key to parent challenge
        name: Habit name/description
        type: Habit type (binary or counted)
        target_count: Target count for counted habits
        preferred_time: Preferred time of day (morning, afternoon, evening)
        icon: Emoji icon for visual representation
        order: Display order within the challenge
        is_active: Whether habit is currently active (for archival)
        template_id: Optional reference to template used to create this habit
        created_at: Timestamp when habit was created
        updated_at: Timestamp when habit was last updated
        challenge: Relationship to parent challenge
        entries: Relationship to daily entries for this habit
    """
    __tablename__ = "habits"

    id = Column(String, primary_key=True)
    challenge_id = Column(String, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(HabitType), nullable=False)
    target_count = Column(Integer, nullable=True)  # For counted habits
    preferred_time = Column(String, nullable=True)  # "morning", "afternoon", "evening"
    icon = Column(String, nullable=True)  # Emoji icon for visual representation
    order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    template_id = Column(String, nullable=True)  # Reference to template if created from one
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    challenge = relationship("Challenge", back_populates="habits")
    entries = relationship("DailyEntry", back_populates="habit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Habit(id={self.id}, name={self.name}, type={self.type})>"
