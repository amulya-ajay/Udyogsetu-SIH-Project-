# AI Features

UDYOGSETU's AI layer combines a **no-vector-library RAG pipeline**, a
deterministic **LLM abstraction**, **controlled tool-calling**, **document
intelligence**, and **AI query resolution**.

> Note: `numpy` / `sentence-transformers` are intentionally **not** installed.
> All vector math is pure Python.

## 1. RAG Pipeline (`app/rag/pipeline.py`)

- **Ingest**: `ingest_document` reads regulation text, chunks it, and writes
  `KnowledgeDocument` + `KnowledgeChunk` rows (pure-Python embeddings).
- **Versioning**: documents carry `effective_date`, `effective_to`, `version`,
  `is_latest`, `supersedes_document_id`, `superseded_by_document_id`.
  `retrieve_context` excludes superseded/expired versions
  (`effective_to < now`).
- **Retrieval**: `retrieve_context(query, top_k)` returns relevant chunks.
- **Evaluation**: `scripts/evaluate_rag.py` + `data/rag_evaluation/questions.json`
  compute retrieval recall and answer-coverage metrics.

## 2. LLM abstraction (`app/ai/`)

- `LLMProviderFactory.create()` returns a deterministic mock provider.
- `generate_with_fallback` / `structured_output` never block and always return
  a usable result, so the system works offline.

## 3. Controlled tool-calling (`app/ai/tools.py`, `app/services/copilot_tools.py`)

An **allow-listed** set of read-only tools lets the copilot answer grounded,
project-scoped questions:

| Tool | Purpose |
|------|---------|
| `get_project_profile` | Project metadata |
| `get_approval_status` | Current approval statuses |
| `search_documents` | Find business documents |
| `check_compliance` | Compliance items |
| `find_incentives` | Matching incentive schemes |

- `ToolCallingService.execute` validates arguments against each tool's JSON
  schema and returns `{ok, result|error}`.
- Endpoints: `GET /tools`, `POST /tools/execute` (ownership enforced).
- The copilot's `_general_flow` asks the LLM to pick tools, executes them, and
  synthesises a grounded answer (see `app/workflows/copilot_workflow.py`).

## 4. Document intelligence

- `DocumentIntelligenceService` + `document_processor.py`: upload → OCR/extract
  → `extracted_fields`; `cross_validate` compares multiple certificates.
- **Explanation** (`app/services/document_explanation.py`):
  `explain_findings` turns insertion/expiry/name mismatches into
  human-readable narratives with a per-field action.
- Endpoint: `GET /documents/project/{project_id}/cross-validate/explain`.

## 5. AI query resolution (`app/services/query_resolution.py`)

`QueryResolutionService.resolve_for_approval`:
1. Reads the stored government query (or polls the gateway).
2. Gathers relevant project documents by token match.
3. Pulls regulatory context from the RAG service.
4. Produces an LLM explanation of what the query means and what to provide.

Endpoint: `GET /synchronization/{approval_id}/query-resolution`.

## Usage

- Copilot chat: `POST /chat/query` (intent routing to rules / RAG / schemes /
  general tools; see `docs/REGULATORY_COPILOT.md`).
