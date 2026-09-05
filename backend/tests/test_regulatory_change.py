"""Tests for regulatory change detection (spec §30)."""

from app.models import KnowledgeDocument
from app.services.regulatory_change import RegulatoryChangeService


async def _make(db, **kwargs):
    doc = KnowledgeDocument(
        title=kwargs.get("title", "Boiler Regulations"),
        department=kwargs.get("department", "boiler"),
        version=kwargs.get("version", "1.0"),
        is_latest=kwargs.get("is_latest", True),
        text=kwargs.get("text", "Rule text."),
        document_type="regulation",
        supersedes_document_id=kwargs.get("supersedes_document_id"),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def test_diff_detects_changed_fields_and_text(db_session):
    old = await _make(db_session, title="Boiler Regulations 2024", version="2024", text="Old boiler safety provision.")
    new = await _make(
        db_session,
        title="Boiler Regulations 2026",
        version="2026",
        supersedes_document_id=old.id,
        text="New boiler safety provision, substantially expanded and adding inspection rules.",
    )

    result = await RegulatoryChangeService(db_session).diff(new.id)
    assert result["title"] == "Boiler Regulations 2026"
    assert result["supersedes_version"] == "2024"
    assert any(c["field"] == "title" for c in result["changed_fields"])
    assert result["text_changed"] is True
    assert "impacted_departments" in result
    assert result["note"]


async def test_recent_changes_lists_versioned_docs(db_session):
    old = await _make(db_session, version="v1")
    await _make(db_session, version="v2", supersedes_document_id=old.id)

    changes = await RegulatoryChangeService(db_session).recent_changes()
    assert len(changes) >= 1
    assert all(isinstance(c["similarity"], float) for c in changes)
