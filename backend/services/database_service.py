# Database service
# SQLite + SQLAlchemy for storing generation history

import os
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── setup ──────────────────────────────────────────────────

# database file will be created at project root
DATABASE_URL = "sqlite:///history.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# ─── model ──────────────────────────────────────────────────

class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    output_type = Column(String(50), nullable=False)
    topic = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    audio_path = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)

# create table if it doesn't exist — runs once on import
Base.metadata.create_all(bind=engine)

# ─── session helper ─────────────────────────────────────────

@contextmanager
def get_db():
    """Context manager that provides a database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ─── functions ──────────────────────────────────────────────

def save_generation(
    output_type: str,
    content: str,
    topic: str = None,
    sources: list = None,
    audio_path: str = None,
    duration: int = None
) -> int:
    """
    Save a generation record to the database.

    Args:
        output_type: one of 'summary', 'topic_summary', 'podcast', 'audiobook', 'qa'
        content: the generated text (summary/script/answer)
        topic: the topic requested, if any
        sources: list of source names
        audio_path: path to MP3 file, if audio was generated
        duration: duration in minutes, for podcast/audiobook

    Returns:
        id of the saved record
    """
    sources_str = ", ".join(sources) if sources else None

    with get_db() as db:
        record = Generation(
            output_type=output_type,
            topic=topic,
            sources=sources_str,
            content=content,
            audio_path=audio_path,
            duration=duration
        )
        db.add(record)
        db.flush()  # assigns the id before commit
        return record.id


def get_all_generations() -> list:
    """
    Fetch all generation records, newest first.

    Returns:
        list of dictionaries, one per record
    """
    with get_db() as db:
        records = db.query(Generation).order_by(Generation.created_at.desc()).all()
        return [_to_dict(r) for r in records]


def get_generation_by_id(record_id: int) -> dict:
    """
    Fetch one specific generation record by id.

    Args:
        record_id: the id of the record to fetch

    Returns:
        dictionary of the record, or None if not found
    """
    with get_db() as db:
        record = db.query(Generation).filter(Generation.id == record_id).first()
        if record is None:
            return None
        return _to_dict(record)


def delete_generation(record_id: int) -> bool:
    """
    Delete a generation record by id.

    Args:
        record_id: the id of the record to delete

    Returns:
        True if deleted, False if not found
    """
    with get_db() as db:
        record = db.query(Generation).filter(Generation.id == record_id).first()
        if record is None:
            return False
        db.delete(record)
        return True


def _to_dict(record: Generation) -> dict:
    """Convert a Generation object to a plain dictionary."""
    return {
        "id": record.id,
        "created_at": record.created_at.strftime("%d %b %Y, %I:%M %p"),
        "output_type": record.output_type,
        "topic": record.topic,
        "sources": record.sources,
        "content": record.content,
        "audio_path": record.audio_path,
        "duration": record.duration
    }