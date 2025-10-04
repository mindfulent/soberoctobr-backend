"""User database model."""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    User model for storing user account information.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address from Google OAuth
        name: User's full name
        picture: URL to user's profile picture
        google_id: Google account identifier
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        challenges: Relationship to user's challenges
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    challenges = relationship("Challenge", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
