"""
Alembic env.py — reads DATABASE_URL from .env and uses SQLModel metadata
so all table definitions are auto-detected from database.py models.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Make sure 'Backend/' is on the path so we can import database.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv()

# Import all models so SQLModel metadata is populated
from database import SQLModel  # noqa: F401
import database  # noqa: F401

# Alembic config object
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object Alembic uses for autogenerate
target_metadata = SQLModel.metadata

# Read DB URL directly from env — bypasses configparser % interpolation issues
_db_url = os.getenv("DATABASE_URL", "sqlite:///./edubot.db")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL scripts)."""
    context.configure(
        url=_db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = create_engine(
        _db_url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
