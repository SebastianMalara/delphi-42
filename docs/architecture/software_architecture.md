# Software Architecture

- Purpose: Define the software subsystems, responsibilities, runtime composition, and implementation boundaries for Delphi-42.
- Audience: Engineering and architecture reviewers.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: system_context.md, runtime_flows.md, ../../bot/, ../../core/, ../../ingest/
- Exit Criteria: The intended code structure and subsystem responsibilities are concrete enough for implementation without additional product decisions.

## Context

The current repository is a Python-first scaffold and the architecture follows that shape. Prototype v1 uses a small number of explicit subsystems rather than a dynamic multi-agent orchestration model.

## Components

- `bot/`
  - radio interface abstraction
  - command parsing
  - message routing
  - bot loop and broadcast scheduling
- `core/`
  - intent classification
  - retrieval abstraction
  - prompt construction
  - local model runner or deterministic fallback
  - answer policy and privacy rules
- `ingest/`
  - text extraction
  - chunking
  - SQLite FTS index construction
- `config/`
  - YAML runtime configuration
- `systemd/`
  - service wrappers for deployment on Raspberry Pi

## Interfaces

- `bot` calls `core.oracle_service` with canonical parsed commands.
- `core` depends on retriever and model interfaces, not on radio details.
- `ingest` produces the persistent index consumed by `core`.
- `config/oracle.yaml` configures radio path, privacy rules, knowledge paths, hotspot data, and model runtime.

## Data/Control Flow

1. `bot` receives or simulates inbound messages.
2. `command_parser` converts text to a canonical command.
3. `oracle_service` classifies intent and chooses help, position, or ask handling.
4. On `ask`, retrieval runs before prompt construction.
5. The model runner generates a constrained answer or the deterministic fallback handles missing context.
6. `bot` translates the resulting reply into outbound messages or a private position packet.

## Failure Modes

- Tight coupling between radio and core logic causing hard-to-test behavior
- Ingest and retrieval drift causing queries to miss intended content
- LLM backend failure causing silent answer loss unless fallback is enforced
- Misconfiguration of index or model paths causing runtime degradation

## Security/Privacy Constraints

- Privacy enforcement belongs in the answer policy, not only in UI or operator discipline.
- The bot must reject public question-answer flows even if the radio library exposes them.
- Model output must remain grounded to retrieved text or declared unavailable.

## Implementation Notes

- Keep the retriever and model runner behind narrow interfaces so alternative backends can be swapped without rewriting the radio flow.
- Avoid introducing asynchronous complexity unless the real radio integration requires it.
- Treat the deterministic fallback as a first-class operational safety path, not just a test helper.
