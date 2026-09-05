"""AI query resolution — spec §20.

When the government integration layer returns a ``QUERY_RAISED`` status with
an open query (for example "Please provide ETP capacity details and water
meter reading"), the platform helps the entrepreneur respond by:

  1. Retrieving the relevant uploaded documents (Doc-AI) for the project,
  2. Pulling the applicable regulation context (RAG),
  3. Composing an AI-assisted explanation and answer suggestion.

This keeps the copilot grounded: suggestion text is derived only from the
query, the project's own documents, and the regulatory KB.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select

from app.models import Approval, Document, GovernmentApplication
from app.services.gateway_service import GatewayService
from app.ai.llm_provider import generate_with_fallback

logger = logging.getLogger(__name__)


class QueryResolutionService:
    """Explain a government query and suggest how to respond."""

    def __init__(self, db, gateway: GatewayService | None = None):
        self.db = db
        self.gateway = gateway or GatewayService()

    async def resolve_for_approval(self, approval: Approval) -> dict:
        gov = None
        query_text = None
        result = await self.db.execute(
            select(GovernmentApplication).where(GovernmentApplication.approval_id == approval.id)
        )
        gov = result.scalar_one_or_none()
        if gov:
            raw = gov.raw_response or {}
            query_text = (raw.get("data") or {}).get("query")

        # If there is no stored query, poll the gateway once.
        if not query_text and gov:
            env = await self.gateway.get_status(gov.system, gov.government_application_id)
            query_text = ((env or {}).get("data") or {}).get("query")

        if gov and query_text:
            gov.raw_response = {**gov.raw_response, "query": query_text}
            await self.db.commit()

        return await self._compose(gov, query_text)

    async def _compose(self, gov: GovernmentApplication | None, query_text: str | None) -> dict:
        if not query_text:
            return {
                "query_present": False,
                "explanation": "No open query for this application.",
                "relevant_documents": [],
                "regulatory_context": [],
                "suggestion": None,
            }

        relevant_docs = []
        regulatory_context = []
        if gov:
            docs_result = await self.db.execute(
                select(Document).where(Document.project_id == gov.project_id)
            )
            docs = docs_result.scalars().all()
            query_tokens = set(_tokens(query_text))
            for d in docs:
                haystack = _tokens(" ".join([
                    d.file_name or "",
                    (d.custom_metadata or {}).get("document_type") or "",
                    (d.extracted_text or "")[:300],
                ]))
                if query_tokens & haystack:
                    relevant_docs.append({
                        "document_id": str(d.id),
                        "file_name": d.file_name,
                        "document_type": (d.custom_metadata or {}).get("document_type"),
                    })

            # Pull matching regulation context via RAG for grounding.
            from app.services.rag_service import RAGService
            rag = await RAGService(self.db).answer_regulatory_question(query_text)
            regulatory_context = rag.get("sources", [])[:3]

        from app.services.ai_observability import AIObservability
        import time as _time
        obs = AIObservability(self.db)
        start = _time.perf_counter()
        try:
            explanation = await generate_with_fallback(
                "You are UdyogSetu. Explain a government query to an entrepreneur in plain language.",
                (
                    f"Here is a query raised by a government department: \"{query_text}\"\n"
                    "Explain clearly what the department is asking for and what kind of "
                    "evidence/document would satisfy it. Keep it to three sentences. "
                    "Do not invent legal requirements."
                ),
                temperature=0.3,
            )
        except Exception:
            try:
                await obs.log_event(request_type="query_resolution", latency_ms=int((_time.perf_counter() - start) * 1000), success=False, error_kind="generation_failed")
            except Exception:
                pass
            raise
        try:
            await obs.log_event(request_type="query_resolution", latency_ms=int((_time.perf_counter() - start) * 1000), success=True)
        except Exception:
            pass

        return {
            "query_present": True,
            "query": query_text,
            "explanation": explanation,
            "relevant_documents": relevant_docs,
            "regulatory_context": regulatory_context,
        }


def _tokens(text: str) -> set[str]:
    import re
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))
