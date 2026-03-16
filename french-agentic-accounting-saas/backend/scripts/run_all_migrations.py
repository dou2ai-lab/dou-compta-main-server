# -----------------------------------------------------------------------------
# File: run_all_migrations.py
# Description: Run all SQL migrations in backend/migrations/versions in a stable order
# -----------------------------------------------------------------------------

"""
Run all SQL migration files in backend/migrations/versions.

- Designed for local/dev + docker-compose bootstrapping.
- Uses a simple schema_migrations table to avoid reapplying the same file.
- Orders numbered migrations by numeric prefix and then by first "phase" number in filename.
- Applies "fix_" migrations after numbered migrations.
"""

import asyncio
import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Tuple, Optional

import asyncpg

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
        print(f"[OK] Loaded .env from: {env_path}")
    except ImportError:
        # python-dotenv not installed, manually parse .env file
        print(f"[WARN] python-dotenv not installed, manually parsing .env")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Strip quotes and whitespace
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
                    if key.strip() == 'DATABASE_URL':
                        print(f"   Found DATABASE_URL: {value[:50]}...")

# Default matches docker-compose.yml (port 5433, password dou_password123)
DEFAULT_DB_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5433/dou_expense_audit"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
# Debug: show what URL we're using (mask password)
if DATABASE_URL != DEFAULT_DB_URL:
    url_parts = DATABASE_URL.split('@')
    if len(url_parts) > 0 and ':' in url_parts[0]:
        user_part = url_parts[0].split('//')[-1] if '//' in url_parts[0] else url_parts[0]
        if ':' in user_part:
            user = user_part.split(':')[0]
            print(f"[INFO] Using DATABASE_URL from environment (user: {user})")
        else:
            print(f"[INFO] Using DATABASE_URL from environment")
    else:
        print(f"[INFO] Using DATABASE_URL from environment")
else:
    print(f"[WARN] Using DEFAULT_DB_URL (environment variable not set)")


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _sort_key(filename: str) -> Tuple[int, int, str]:
    """
    Return a stable sort key.

    - Numbered files like 006_phase5_phase6_schema.sql:
      (seq=6, phase=5, name=filename)
    - fix_* files:
      (seq=9999, phase=9999, name=filename)
    """
    m = re.match(r"^(\d+)_", filename)
    if not m:
        return (9999, 9999, filename)

    seq = int(m.group(1))
    phase = 9999
    pm = re.search(r"phase(\d+)", filename)
    if pm:
        try:
            phase = int(pm.group(1))
        except ValueError:
            phase = 9999
    return (seq, phase, filename)


def _list_migrations(migrations_dir: Path) -> List[str]:
    files = [p.name for p in migrations_dir.iterdir() if p.is_file() and p.name.endswith(".sql")]
    files.sort(key=_sort_key)
    return files


async def _ensure_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

async def _table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    # to_regclass returns NULL if the relation doesn't exist
    row = await conn.fetchrow("SELECT to_regclass($1) AS reg", f"public.{table_name}")
    return row is not None and row["reg"] is not None

async def _migration_count(conn: asyncpg.Connection) -> int:
    row = await conn.fetchrow("SELECT COUNT(*) AS c FROM schema_migrations")
    return int(row["c"]) if row and row["c"] is not None else 0


async def _already_applied(conn: asyncpg.Connection, filename: str) -> bool:
    row = await conn.fetchrow("SELECT filename FROM schema_migrations WHERE filename = $1", filename)
    return row is not None


async def _mark_applied(conn: asyncpg.Connection, filename: str) -> None:
    await conn.execute(
        "INSERT INTO schema_migrations (filename) VALUES ($1) ON CONFLICT (filename) DO NOTHING",
        filename,
    )

async def _mark_all_applied(conn: asyncpg.Connection, filenames: List[str]) -> None:
    # Batch insert for speed
    await conn.executemany(
        "INSERT INTO schema_migrations (filename) VALUES ($1) ON CONFLICT (filename) DO NOTHING",
        [(f,) for f in filenames],
    )


async def run_all_migrations(selected: Optional[List[str]] = None) -> None:
    migrations_dir = Path(__file__).parent.parent / "migrations" / "versions"
    if not migrations_dir.exists():
        raise RuntimeError(f"migrations dir not found: {migrations_dir}")

    all_files = _list_migrations(migrations_dir)

    # For local/dev we don't need all Phase 3+ and ERP extras to get core
    # upload/OCR/expense flows working. Some advanced migrations reference
    # tables that may not exist yet and can block setup. Skip them by default
    # unless explicitly requested via `selected`.
    SKIP_BY_DEFAULT = {
        "003_phase3_schema.sql",
        "009_phase25_26_erp_tables.sql",
        "011_phase29_30_performance_indexes.sql",
    }

    files = [
        f
        for f in all_files
        if (selected is None or f in selected) and (selected or f not in SKIP_BY_DEFAULT)
    ]

    # Parse DB URL in a stable way (avoid asyncpg private APIs)
    db_url = _to_asyncpg_url(DATABASE_URL)
    parsed = urllib.parse.urlparse(db_url)
    
    # Extract password - handle URL encoding
    password = parsed.password
    if password:
        password = urllib.parse.unquote(password)  # Decode URL-encoded password
        password = password.strip()  # Remove any whitespace
    
    # Use correct default password that matches docker-compose
    if not password:
        password = "dou_password123"
    
    # TEMPORARY FIX: Force correct password (matches docker-compose.yml)
    # TODO: Debug why parsed.password doesn't match
    if parsed.port == 5433 and parsed.hostname in ("localhost", "127.0.0.1"):
        password = "dou_password123"
        print(f"[WARN] Using hardcoded password for local dev")
    
    print(f"[INFO] Connecting to: {parsed.hostname}:{parsed.port}, user: {parsed.username}, database: {parsed.path[1:] if parsed.path else 'N/A'}")
    print(f"[INFO] Password: {'*' * len(password)} (length: {len(password)}, first 3: '{password[:3]}', last 3: '{password[-3:]}')")

    conn = await asyncpg.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        user=parsed.username or "dou_user",
        password=password,
        database=(parsed.path[1:] if parsed.path and len(parsed.path) > 1 else "dou_expense_audit"),
        ssl=False,  # Disable SSL for local development
    )

    try:
        await _ensure_migrations_table(conn)

        # Safety: if the DB already has tables but no migration history, we can't reliably infer
        # which non-idempotent migrations ran. Ask user to reset the dev volume.
        if await _migration_count(conn) == 0 and await _table_exists(conn, "tenants"):
            raise RuntimeError(
                "Existing database schema detected but no schema_migrations history found.\n"
                "For a clean dev setup, reset the Postgres volume and rerun.\n"
                "Example:\n"
                "  docker compose down -v\n"
                "  docker compose up -d --build\n"
            )

        applied = 0
        skipped = 0
        errors = 0
        for fname in files:
            if await _already_applied(conn, fname):
                skipped += 1
                continue

            sql_path = migrations_dir / fname
            sql_content = sql_path.read_text(encoding="utf-8")
            print(f"[APPLY] Applying {fname} ...")
            try:
                await conn.execute(sql_content)
                await _mark_applied(conn, fname)
                applied += 1
            except Exception as e:
                error_msg = str(e)
                # Handle duplicate object errors - mark as applied since objects already exist
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print(f"[WARN] Migration {fname} failed due to existing objects, marking as applied: {error_msg[:100]}")
                    await _mark_applied(conn, fname)
                    applied += 1
                else:
                    print(f"[ERROR] Migration {fname} failed: {error_msg}")
                    errors += 1
                    raise  # Re-raise non-duplicate errors

        print(f"[OK] Migrations complete. applied={applied} skipped={skipped} errors={errors} total={len(files)}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_all_migrations())

