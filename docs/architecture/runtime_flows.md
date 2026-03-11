# Runtime Flows

- Purpose: Describe the main runtime sequences for answering questions, sharing position, and rebuilding the knowledge index.
- Audience: Engineering, QA, and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: system_context.md, software_architecture.md, ../operations/service_operations.md
- Exit Criteria: Core runtime sequences are defined well enough to drive implementation, runbooks, and tests.

## Context

Runtime flows center on three repeatable behaviors: direct-message answering, private location sharing, and offline corpus ingest.

## Components

- User device
- Meshtastic radio
- `bot` service
- `core` service logic
- SQLite FTS index
- local model runtime
- operator-triggered ingest command

## Interfaces

- DM commands and private reply channel
- `python -m bot.oracle_bot`
- `python -m ingest.build_index --input-dir ... --db ...`
- `systemd` service boundaries

## Data/Control Flow

### Ask Flow

```mermaid
sequenceDiagram
  participant User
  participant Mesh as Meshtastic Mesh
  participant Bot as bot
  participant Core as oracle_service
  participant Index as SQLite FTS
  participant LLM as Local LLM

  User->>Mesh: DM "ask how to purify water"
  Mesh->>Bot: inbound private packet
  Bot->>Core: ParsedCommand(name="ask", argument=...)
  Core->>Index: search(question)
  Index-->>Core: top context chunks
  Core->>LLM: grounded prompt
  LLM-->>Core: short answer
  Core-->>Bot: OracleReply(text)
  Bot-->>Mesh: private answer
```

### Where Flow

```mermaid
sequenceDiagram
  participant User
  participant Mesh as Meshtastic Mesh
  participant Bot as bot
  participant Core as oracle_service

  User->>Mesh: DM "where"
  Mesh->>Bot: inbound private packet
  Bot->>Core: ParsedCommand(name="where")
  Core-->>Bot: OracleReply(text, share_position=true)
  Bot-->>Mesh: private confirmation message
  Bot-->>Mesh: private position packet
```

### Ingest Flow

```mermaid
sequenceDiagram
  participant Operator
  participant Ingest as build_index
  participant Corpus as Plaintext/ZIM Source
  participant DB as SQLite FTS

  Operator->>Ingest: run build_index
  Ingest->>Corpus: load or extract text
  Ingest->>Ingest: chunk content
  Ingest->>DB: rebuild chunks index
  DB-->>Ingest: success/failure
  Ingest-->>Operator: index build result
```

## Failure Modes

- Ask flow returns no answer because index is empty or model runtime is unavailable
- Where flow leaks publicly if routing ignores DM-only policy
- Ingest rebuild erases useful data without replacement if source directory is incomplete

## Security/Privacy Constraints

- Every flow handling user content assumes DM-only routing.
- Position sharing is a separate private packet, not embedded in public text.
- Ingest and logs must not expose sensitive local file paths more broadly than needed.
