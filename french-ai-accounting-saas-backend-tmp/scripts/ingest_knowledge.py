# -----------------------------------------------------------------------------
# ingest_knowledge.py – Ingest RAG knowledge from canonical URLs (5.2.5)
# Run offline: python scripts/ingest_knowledge.py
# Fetches URSSAF, VAT (Cyplom), GDPR (Vanta), Appvizer; stores in knowledge_documents.
# -----------------------------------------------------------------------------

"""
Ingest knowledge documents for RAG from canonical URLs.
Do NOT rely on live HTTP at inference; run this periodically and store in DB.
"""
import asyncio
import os
import re
from pathlib import Path
from uuid import UUID

# Add backend to path
sys_path = Path(__file__).resolve().parent.parent
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))

from dotenv import load_dotenv
load_dotenv(sys_path / ".env")

# Canonical sources (5.2.5)
SOURCES = [
    {
        "url": "https://mycompanyinfrance.urssaf.fr/documentation/salari%C3%A9/r%C3%A9mun%C3%A9ration/frais-professionnels",
        "title": "URSSAF – Frais professionnels (salarié)",
        "type": "URSSAF",
        "language": "fr",
    },
    {
        "url": "https://www.vanta.com/resources/gdpr-compliance-for-saas",
        "title": "GDPR Compliance for SaaS",
        "type": "GDPR",
        "language": "en",
    },
    {
        "url": "https://www.cyplom.com/en/le-coin-pratique/vat-on-expense-reports-a-deduction-guide-for-your-business",
        "title": "VAT on expense reports – deduction guide",
        "type": "VAT",
        "language": "en",
    },
    {
        "url": "https://www.appvizer.com/magazine/accounting-finance/expense-management/urssaf-note-de-frais",
        "title": "URSSAF note de frais – expense management",
        "type": "URSSAF",
        "language": "fr",
    },
]


def strip_html(html: str) -> str:
    """Simple tag stripping and whitespace normalization."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def fetch_url(url: str) -> str:
    """Fetch URL content (run in executor to avoid blocking)."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
    except Exception as e:
        return f"[Fetch error for {url}: {e}]"


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text
    from common.models import Base, KnowledgeDocument

    database_url = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Default tenant for global knowledge (use first tenant if multi-tenant)
    async with async_session() as session:
        r = await session.execute(text("SELECT id FROM tenants WHERE deleted_at IS NULL LIMIT 1"))
        row = r.fetchone()
        tenant_id = UUID(str(row[0])) if row else None
        if not tenant_id:
            print("No tenant found. Create a tenant first.")
            return

    for src in SOURCES:
        print(f"Fetching {src['url'][:60]}...")
        html = await fetch_url(src["url"])
        content = strip_html(html)
        if not content or len(content) < 100:
            content = f"Content from {src['url']}. (Parsed content too short or unavailable.)"
        print(f"  Length: {len(content)} chars")

        async with async_session() as session:
            doc = KnowledgeDocument(
                tenant_id=tenant_id,
                title=src["title"],
                source_url=src["url"],
                type=src["type"],
                language=src["language"],
                content=content,
            )
            session.add(doc)
            await session.commit()
            print(f"  Stored knowledge_documents id={doc.id}")

    print("Done. Next: run RAG embed from knowledge_documents (e.g. POST /api/v1/rag/embed-from-knowledge) or script.")


if __name__ == "__main__":
    asyncio.run(main())
