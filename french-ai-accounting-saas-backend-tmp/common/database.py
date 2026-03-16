# -----------------------------------------------------------------------------
# File: database.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Database connection manager and session management for async SQLAlchemy
# -----------------------------------------------------------------------------

"""
Database connection manager
Phase 1 - Placeholder
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from common.models import Base
import os
from pathlib import Path

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        # Use override=False so Docker/Compose env vars (e.g. DATABASE_URL) are not overwritten
        load_dotenv(env_path, override=False)
    except ImportError:
        # python-dotenv not installed, manually parse .env file
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

# TODO: Implement proper database connection management
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create engine with settings that allow it to work across different event loops
# pool_pre_ping=True to validate connections before use (fixes connection closed errors)
# Increased pool size to handle concurrent requests better
# Increased timeouts to prevent premature timeout errors during login
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Enable ping to validate connections before use
    pool_size=10,  # Increased pool size for better concurrency
    max_overflow=20,  # Allow more overflow connections
    pool_recycle=1800,  # Recycle connections after 30 minutes (more frequent)
    pool_reset_on_return='commit',  # Reset connections on return to pool
    pool_timeout=60,  # Increased timeout for getting connection from pool (60s)
    connect_args={
        "server_settings": {
            "application_name": "dou_expense_audit",
            # Removed statement_timeout to avoid query cancellation issues
            # Let PostgreSQL use default timeout or no timeout
        },
        "command_timeout": 60,  # Increased command timeout to 60 seconds
        "timeout": 30,  # Increased connection timeout to 30 seconds
    }
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        yield session

# Export Base for backward compatibility
__all__ = ['engine', 'AsyncSessionLocal', 'get_db', 'Base']


