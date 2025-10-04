"""Challenge database model."""

import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChallengeStatus(str, enum.Enum):
    """Challenge status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Challenge(Base):
    """
    Challenge model for storing 30-day challenge information.

    Attributes:
        id: Unique challenge identifier (UUID)
        user_id: Foreign key to user who owns this challenge
        start_date: Challenge start date
        end_date: Challenge end date (30 days from start)
        status: Current challenge status (active, completed, abandoned)
        created_at: Timestamp when challenge was created
        updated_at: Timestamp when challenge was last updated
        user: Relationship to user who owns this challenge
        habits: Relationship to habits in this challenge
    """
    __tablename__ = "challenges"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="challenges")
    habits = relationship("Habit", back_populates="challenge", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Challenge(id={self.id}, user_id={self.user_id}, status={self.status})>"
