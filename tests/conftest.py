"""Pytest configuration and shared fixtures."""

import os
import uuid
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Set test environment before importing app modules
# Use file::memory:?cache=shared to ensure all connections share the same in-memory database
os.environ["DATABASE_URL"] = "sqlite:///file::memory:?cache=shared&uri=true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Import Base first, then all models to register them with Base.metadata
from app.core.database import Base, get_db
from app.models.user import User
from app.models.challenge import Challenge, ChallengeStatus
from app.models.habit import Habit, HabitType
from app.models.daily_entry import DailyEntry
from app.core.security import create_access_token
from app.main import app

# Test database URL (use in-memory SQLite for speed)
# Use file::memory:?cache=shared to ensure all connections share the same in-memory database
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False, "uri": True},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine, db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        picture="https://example.com/picture.jpg",
        google_id="google_test_123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Create another test user for authorization tests."""
    user = User(
        id=str(uuid.uuid4()),
        email="other@example.com",
        name="Other User",
        picture="https://example.com/other.jpg",
        google_id="google_other_456",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a JWT token for the test user."""
    return create_access_token(data={"sub": test_user.id})


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_challenge(db_session: Session, test_user: User) -> Challenge:
    """Create a test challenge."""
    # Use dynamic dates relative to today to avoid test failures
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    challenge = Challenge(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        start_date=today - timedelta(days=15),  # Started 15 days ago
        end_date=today + timedelta(days=15),    # Ends 15 days from now
        status=ChallengeStatus.ACTIVE,
    )
    db_session.add(challenge)
    db_session.commit()
    db_session.refresh(challenge)
    return challenge


@pytest.fixture
def test_binary_habit(db_session: Session, test_challenge: Challenge) -> Habit:
    """Create a test binary habit."""
    habit = Habit(
        id=str(uuid.uuid4()),
        challenge_id=test_challenge.id,
        name="Meditate",
        type=HabitType.BINARY,
        preferred_time="morning",
        order=0,
        is_active=True,
    )
    db_session.add(habit)
    db_session.commit()
    db_session.refresh(habit)
    return habit


@pytest.fixture
def test_counted_habit(db_session: Session, test_challenge: Challenge) -> Habit:
    """Create a test counted habit."""
    habit = Habit(
        id=str(uuid.uuid4()),
        challenge_id=test_challenge.id,
        name="Drink water",
        type=HabitType.COUNTED,
        target_count=8,
        preferred_time="afternoon",
        order=1,
        is_active=True,
    )
    db_session.add(habit)
    db_session.commit()
    db_session.refresh(habit)
    return habit


@pytest.fixture
def test_entry(db_session: Session, test_binary_habit: Habit) -> DailyEntry:
    """Create a test daily entry."""
    entry = DailyEntry(
        id=str(uuid.uuid4()),
        habit_id=test_binary_habit.id,
        date=datetime(2024, 10, 1),
        completed=True,
        count=None,
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry
