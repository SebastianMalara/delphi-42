# Scope And Non-Goals

- Purpose: Lock the scope boundaries for Prototype v1 and prevent accidental product expansion.
- Audience: Engineering, operations, and project leadership.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: project_brief.md, non_functional_requirements.md, ../project/execution_plan.md
- Exit Criteria: Prototype v1 in-scope work, out-of-scope items, and deferred items are explicit enough to guide planning.

## In Scope For Prototype V1

- Single-node deployment on Raspberry Pi
- One Meshtastic-connected oracle process handling direct messages
- Commands: `?help`, `?where`, `?pos`, `?ask <question>`, and `?chat <message>`
- Allowlisted `.zim` archives as the grounded runtime corpus
- Hybrid archive design: Kiwix for browsing plus direct `.zim` retrieval for answers
- Retrieval-first answer generation through the AX8850-backed local `StackFlow` API or deterministic fallback
- Hotspot-based access to a larger local archive
- Repeatable runbooks for provision, deploy, recover, and validate
- Trackable project execution plan and risk register

## Explicit Non-Goals

- Multi-node coordination or federation
- Public-channel question answering
- Cloud-hosted LLMs or cloud retrieval
- Autonomous long-form reasoning agents
- Voice assistant UX, wake word flows, or Whisplay-style audio interaction
- Full moderation platform or user account system
- Continuous online updates from the public internet
- Native AXCL SDK integration instead of the local OpenAI-compatible API
- Production manufacturing documentation

## Deferred After Prototype V1

- Rich ranking and reranking across multiple corpora
- OTA updates between nodes
- Signed package distribution for field fleets
- Automated solar telemetry and battery analytics
- Full multilingual prompt and corpus support
- Web admin UI for operators
- Alternative accelerator backends beyond the AX8850 / StackFlow baseline

## Scope Guardrails

- Every feature must preserve offline operation.
- Every public broadcast must remain short and privacy-safe.
- Every dependency must justify its storage, power, and maintenance cost.
- Every new subsystem must map to a test plan and an operator runbook.
