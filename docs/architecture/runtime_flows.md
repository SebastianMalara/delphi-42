# Runtime Flows

- Purpose: Describe the main runtime sequences for answering questions, sharing position, and rebuilding the knowledge index.
- Audience: Engineering, QA, and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: system_context.md, software_architecture.md, ../operations/service_operations.md
- Exit Criteria: Core runtime sequences are defined well enough to drive implementation, runbooks, and tests.

## Context

Runtime flows center on three repeatable behaviors: direct-message answering, private location sharing, and offline corpus ingest.

## Components

- User device
- Meshtastic radio
- `bot` service
- `core` service logic
- allowlisted `.zim` archives
- StackFlow OpenAI-compatible API
- deterministic packet formatter
- operator-triggered ingest command

## Interfaces

- DM commands and private reply channel
- `python -m bot.oracle_bot`
- `python -m scripts.inspect_retrieval --config ... --question ...`
- `systemd` service boundaries

## Data/Control Flow

### Ask Flow

```mermaid
sequenceDiagram
  participant User
  participant Mesh as Meshtastic Mesh
  participant Bot as bot
  participant Core as oracle_service
  participant Index as Allowlisted .zim
  participant LLM as StackFlow API

  User->>Mesh: DM "?ask how to purify water"
  Mesh->>Bot: inbound private packet
  Bot->>Core: ParsedCommand(name="ask", argument=...)
  Core->>Index: search allowlisted .zim archives
  Index-->>Core: top grounded context chunks
  Core->>LLM: grounded full-answer prompt
  LLM-->>Core: grounded full answer
  Core->>LLM: condensed continuation prompt
  LLM-->>Core: condensed continuation answer
  Core->>LLM: ultra-short first-packet prompt
  LLM-->>Core: ultra-short first packet
  Core->>Core: prefix-aware packet formatting and shrink validation
  Core-->>Bot: OracleReply(bundle)
  Bot-->>Mesh: private short answer
  Bot-->>Mesh: optional continuation packets
```

### Where Flow

```mermaid
sequenceDiagram
  participant User
  participant Mesh as Meshtastic Mesh
  participant Bot as bot
  participant Core as oracle_service

	  User->>Mesh: DM "?where"
  Mesh->>Bot: inbound private packet
  Bot->>Core: ParsedCommand(name="where")
  Core-->>Bot: OracleReply(text, share_position=true)
  Bot-->>Mesh: private confirmation message
  Bot-->>Mesh: private position packet
```

### Chat Flow

```mermaid
sequenceDiagram
  participant Operator
  participant Memory as Chat Memory
  participant LLM as StackFlow API

  User->>Mesh: DM "?chat keep me company"
  Mesh->>Bot: inbound private packet
  Bot->>Core: ParsedCommand(name="chat", argument=...)
  Core->>Memory: load short sender history
  Core->>LLM: chat prompt with bounded history
  LLM-->>Core: chat reply
  Core->>Memory: store user turn + condensed reply
  Core-->>Bot: OracleReply(bundle)
  Bot-->>Mesh: private chat answer
```

## Failure Modes

- Ask flow returns no answer because the allowlisted archives are missing or retrieval is weak
- Ask flow overruns radio limits unless packet formatting is deterministic
- Ask flow never reaches usable grounded context because the allowlisted `.zim` files are missing or misconfigured
- Where flow leaks publicly if routing ignores DM-only policy
- Chat flow loses continuity if per-sender memory is reset

## Security/Privacy Constraints

- Every flow handling user content assumes DM-only routing.
- Position sharing is a separate private packet, not embedded in public text.
- Ingest and logs must not expose sensitive local file paths more broadly than needed.
- Packet splitting must never introduce content that was not present in the grounded answer draft.
