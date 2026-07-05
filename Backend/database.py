"""
Production database layer — PostgreSQL via SQLModel.
Falls back to SQLite when DATABASE_URL is not set (local dev).

Tables:
  - users:     Basic user registry for future auth/multi-tenancy.
  - sessions:  One row per chat session, optionally linked to a user.
  - messages:  Full turn-by-turn conversation history with cited sources.
  - resources: Registry of every indexed video or PDF.
"""

import os
from datetime import datetime, timezone
from typing import Optional, List
from dotenv import load_dotenv
from sqlmodel import SQLModel, Field, create_engine, Session, select, col

# Load .env first so DATABASE_URL is available before engine creation
load_dotenv()

# ── Engine ────────────────────────────────────────────────────────────────────
_raw_url = os.getenv("DATABASE_URL", "sqlite:///./edubot.db")

# Heroku / Railway emit 'postgres://' — SQLAlchemy 1.4+ requires 'postgresql://'
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = _raw_url.startswith("sqlite")

engine = create_engine(
    _raw_url,
    echo=False,
    # SQLite needs check_same_thread=False; PostgreSQL does not accept it
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Connection pool tuning for PostgreSQL
    **({} if _is_sqlite else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,   # detect stale connections
    })
)


# ── Models ────────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    """Basic user table — ready for future auth integration."""
    __tablename__: str = "users"  # type: ignore[assignment]
    id: str = Field(primary_key=True)
    email: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatSession(SQLModel, table=True):
    __tablename__: str = "sessions"  # type: ignore[assignment]
    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_resource_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)


class Message(SQLModel, table=True):
    __tablename__: str = "messages"  # type: ignore[assignment]
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    role: str
    content: str
    sources_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Resource(SQLModel, table=True):
    __tablename__: str = "resources"  # type: ignore[assignment]
    id: str = Field(primary_key=True)
    title: str
    resource_type: str
    chunk_count: int = Field(default=0)
    file_size_bytes: Optional[int] = Field(default=None)
    video_url: Optional[str] = Field(default=None)
    video_id: Optional[str] = Field(default=None)
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist (used for SQLite dev / first run)."""
    SQLModel.metadata.create_all(engine)


# ── Session helpers ───────────────────────────────────────────────────────────

def get_or_create_session(
    session_id: str,
    active_resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ChatSession:
    with Session(engine) as db:
        existing = db.get(ChatSession, session_id)
        if existing:
            return existing
        new_session = ChatSession(
            id=session_id,
            active_resource_id=active_resource_id,
            user_id=user_id,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session


def clear_session_messages(session_id: str):
    with Session(engine) as db:
        msgs = db.exec(select(Message).where(Message.session_id == session_id)).all()
        for m in msgs:
            db.delete(m)
        db.commit()


# ── Message helpers ───────────────────────────────────────────────────────────

def save_message(
    session_id: str,
    role: str,
    content: str,
    sources_json: Optional[str] = None,
):
    with Session(engine) as db:
        db.add(Message(
            session_id=session_id,
            role=role,
            content=content,
            sources_json=sources_json,
        ))
        db.commit()


def get_recent_messages(session_id: str, limit: int = 6) -> List[Message]:
    """Return the last `limit` messages for a session (oldest first)."""
    with Session(engine) as db:
        all_msgs = db.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(col(Message.created_at))
        ).all()
        return list(all_msgs[-limit:])


# ── Resource helpers ──────────────────────────────────────────────────────────

def register_resource(
    resource_id: str,
    title: str,
    resource_type: str,
    chunk_count: int,
    file_size_bytes: Optional[int] = None,
    video_url: Optional[str] = None,
    video_id: Optional[str] = None,
):
    with Session(engine) as db:
        if db.get(Resource, resource_id):
            return
        db.add(Resource(
            id=resource_id,
            title=title,
            resource_type=resource_type,
            chunk_count=chunk_count,
            file_size_bytes=file_size_bytes,
            video_url=video_url,
            video_id=video_id,
        ))
        db.commit()


def get_all_resources(resource_type: Optional[str] = None) -> List[Resource]:
    with Session(engine) as db:
        query = select(Resource)
        if resource_type:
            query = query.where(Resource.resource_type == resource_type)
        return list(db.exec(query.order_by(col(Resource.indexed_at).desc())).all())


def delete_resource(resource_id: str) -> bool:
    with Session(engine) as db:
        resource = db.get(Resource, resource_id)
        if not resource:
            return False
        db.delete(resource)
        db.commit()
        return True
