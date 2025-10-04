"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLAlchemy engine
# Use different args for SQLite vs PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    # Use smaller pool for production (especially on small instances)
    # Keep it minimal to avoid connection overhead on startup
    pool_size = 1 if settings.ENVIRONMENT == "production" else 5
    max_overflow = 2 if settings.ENVIRONMENT == "production" else 10
    
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=300,  # Recycle connections every 5 minutes
        connect_args={
            "connect_timeout": 5,  # Faster timeout for production
            "options": "-c statement_timeout=30000"  # 30 second statement timeout
        }
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        ```python
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    Creates all tables defined in models if they don't exist.
    This is useful for development. In production, use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
