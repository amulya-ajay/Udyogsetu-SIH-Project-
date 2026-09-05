# Regulatory Copilot

The copilot answers free-text questions and routes each query to the right
engine via `CopilotWorkflow` (`app/workflows/copilot_workflow.py`).

## Intent routing

`detect_intent(question)` scores the query against keyword sets and returns the
best intent:

| Intent | Keywords | Engine used |
|--------|----------|-------------|
| `regulation` | regulation, law, rule, act, consent, NOC, clearance, required… | RAG over the regulation KB (`RAGService`) |
| `document` | document, upload, PAN, GSTIN, validation, cross, mismatch, expired… | Doc-AI cross-validate summary |
| `status` | status, track, SLA, where is my application… | live mock gateway status poll |
| `scheme` | scheme, subsidy, incentive, grant, PMEGP, eligibility… | incentive matcher |
| `general` | (fallback) | LLM + project-scoped tool calls |

## Response shape

Every answer returns:

```json
{
  "intent": "status",
  "engine": "status",
  "answer": "Your MPCB consent is QUERY_RAISED: 'ETP capacity details required'.",
  "sources": [],
  "confidence": 0.9
}
```

## General flow with tool-calling

For `general` intents (with a `project_id`) the copilot:
1. Asks the LLM to emit a JSON tool-use plan (`get_project_profile`,
   `get_approval_status`, `search_documents`, `check_compliance`,
   `find_incentives`).
2. Executes each tool via `ToolCallingService`.
3. Synthesises a deterministic, grounded answer grounded only in tool results.

See `docs/AI_FEATURES.md` for the tool catalog.

## HTTP

```
POST /chat/query          { "question": "...", "project_id": "uuid" }
GET  /chat/history/{project_id}
POST /regulatory/query    (regulatory-only variant)
POST /regulatory/chat
```

## Design notes

- Intent detection is deterministic (keyword scoring) so the copilot is
  predictable and testable without an external model.
- The mock LLM never blocks, so latency is low and the copilot works offline.
