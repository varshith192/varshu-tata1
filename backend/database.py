"""
SQLAlchemy database setup.
Primary: PostgreSQL (DATABASE_URL env var).
Fallback: SQLite (Stelos.db) for local dev without Postgres.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger("StelosAPI")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(__file__), 'stelos.db')}"
)

# psycopg2 uses postgres://, SQLAlchemy 2.x needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Create all tables. Safe to call on every startup (no-op if tables exist)."""
    import models  # noqa: F401 — registers ORM models against Base
    Base.metadata.create_all(bind=engine)
    backend = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    logger.info(f"Database initialised ({backend}): {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
