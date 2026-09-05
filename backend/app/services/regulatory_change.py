"""Regulatory change detection (spec §30).

Detects and describes changes introduced by a new version of a regulation.
Uses the versioning columns on KnowledgeDocument (supersedes_document_id)
to compare successive versions and produce a human-readable change summary
plus the list of departments whose approvals may be impacted.

This is advisory analysis; statutory interpretation remains with the user.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Approval, KnowledgeDocument


def _short(version: str | None) -> str:
    return version or "current"


class RegulatoryChangeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def diff(self, document_id: UUID) -> dict:
        """Compare a regulation with the version it supersedes."""
        doc = (await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )).scalar_one_or_none()
        if not doc:
            return {"error": "Regulation not found"}

        previous = None
        if doc.supersedes_document_id:
            previous = (await self.db.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == doc.supersedes_document_id
                )
            )).scalar_one_or_none()

        changed_fields = self._field_changes(previous, doc)
        text_diff = self._text_diff(previous, doc)

        impacted_departments = await self._impacted_departments(doc.department)

        return {
            "document_id": str(doc.id),
            "title": doc.title,
            "version": _short(doc.version),
            "supersedes_version": _short(previous.version) if previous else None,
            "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
            "changed_fields": changed_fields,
            "text_changed": text_diff["changed"],
            "text_change_summary": text_diff["summary"],
            "similarity": text_diff["similarity"],
            "impacted_departments": impacted_departments,
            "note": "Advisory analysis: not a statutory determination.",
        }

    async def recent_changes(self, limit: int = 20) -> list[dict]:
        """List recently published regulation versions with change summaries."""
        docs = (await self.db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.supersedes_document_id.isnot(None))
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        )).scalars().all()

        result = []
        for doc in docs:
            prev = (await self.db.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == doc.supersedes_document_id
                )
            )).scalar_one_or_none()
            text_diff = self._text_diff(prev, doc)
            result.append({
                "document_id": str(doc.id),
                "title": doc.title,
                "department": doc.department,
                "version": _short(doc.version),
                "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
                "text_changed": text_diff["changed"],
                "text_change_summary": text_diff["summary"],
                "similarity": text_diff["similarity"],
            })
        return result

    async def _impacted_departments(self, department: str | None) -> list[dict]:
        if not department:
            return []
        rows = (await self.db.execute(
            select(Approval.department)
            .where(Approval.department == department, Approval.is_active.is_(True))
            .distinct()
        )).all()
        return [{"department": r[0]} for r in rows]

    @staticmethod
    def _field_changes(previous: KnowledgeDocument | None, doc: KnowledgeDocument) -> list[dict]:
        changes = []
        for field in ("title", "department", "document_type", "version", "jurisdiction", "sector"):
            old = getattr(previous, field, None) if previous else None
            new = getattr(doc, field, None)
            if old != new:
                changes.append({"field": field, "from": old, "to": new})
        return changes

    @staticmethod
    def _text_diff(previous: KnowledgeDocument | None, doc: KnowledgeDocument) -> dict:
        if not previous:
            return {"changed": True, "summary": "No previous version to compare.", "similarity": 0.0}
        old_text = (previous.text or "").strip()
        new_text = (doc.text or "").strip()
        similarity = round(SequenceMatcher(None, old_text, new_text).ratio(), 3)
        changed = old_text != new_text
        if not changed:
            summary = "Text unchanged."
        elif len(new_text) > len(old_text):
            summary = f"Text expanded (+{len(new_text) - len(old_text)} chars)."
        else:
            summary = f"Text shortened ({len(old_text) - len(new_text)} chars removed)."
        return {"changed": changed, "summary": summary, "similarity": similarity, "old_chars": len(old_text), "new_chars": len(new_text)}
