# Scope And Non-Goals

- Purpose: Lock the scope boundaries for Prototype v1 and prevent accidental product expansion.
- Audience: Engineering, operations, and project leadership.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: project_brief.md, non_functional_requirements.md, ../project/execution_plan.md
- Exit Criteria: Prototype v1 in-scope work, out-of-scope items, and deferred items are explicit enough to guide planning.

## In Scope For Prototype V1

- Single-node deployment on Raspberry Pi
- One Meshtastic-connected oracle process handling direct messages
- Commands: `help`, `where`, `pos`, and `ask <question>`
- Offline corpus preparation into a local SQLite FTS index
- Retrieval-first answer generation with a small local LLM or deterministic fallback
- Hotspot-based access to a larger local archive
- Repeatable runbooks for provision, deploy, recover, and validate
- Trackable project execution plan and risk register

## Explicit Non-Goals

- Multi-node coordination or federation
- Public-channel question answering
- Cloud-hosted LLMs or cloud retrieval
- Autonomous long-form reasoning agents
- Full moderation platform or user account system
- Continuous online updates from the public internet
- Production manufacturing documentation

## Deferred After Prototype V1

- Rich ranking and reranking across multiple corpora
- OTA updates between nodes
- Signed package distribution for field fleets
- Automated solar telemetry and battery analytics
- Full multilingual prompt and corpus support
- Web admin UI for operators

## Scope Guardrails

- Every feature must preserve offline operation.
- Every public broadcast must remain short and privacy-safe.
- Every dependency must justify its storage, power, and maintenance cost.
- Every new subsystem must map to a test plan and an operator runbook.
