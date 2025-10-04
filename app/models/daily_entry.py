"""Daily entry database model."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DailyEntry(Base):
    """
    Daily entry model for tracking daily habit completion.

    Attributes:
        id: Unique entry identifier (UUID)
        habit_id: Foreign key to habit being tracked
        date: Date of this entry (normalized to start of day)
        completed: Whether habit was completed (for binary habits)
        count: Count value (for counted habits)
        created_at: Timestamp when entry was created
        updated_at: Timestamp when entry was last updated
        habit: Relationship to parent habit
    """
    __tablename__ = "daily_entries"

    id = Column(String, primary_key=True)
    habit_id = Column(String, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # Normalized to start of day
    completed = Column(Boolean, default=False, nullable=False)
    count = Column(Integer, nullable=True)  # For counted habits
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    habit = relationship("Habit", back_populates="entries")

    # Ensure one entry per habit per day
    __table_args__ = (
        UniqueConstraint('habit_id', 'date', name='uix_habit_date'),
    )

    def __repr__(self):
        return f"<DailyEntry(id={self.id}, habit_id={self.habit_id}, date={self.date}, completed={self.completed})>"
