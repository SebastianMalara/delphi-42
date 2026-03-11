# SOP: Agentic AI for Delphi-42

## Purpose

This SOP defines how Delphi-42 should behave as an offline agentic oracle running on:

- Raspberry Pi
- Meshtastic radio link
- offline knowledge archives served locally with Kiwix
- local text extraction and SQLite FTS retrieval
- a small local LLM used only after retrieval

The operating goal is simple: accept private low-bandwidth questions, ground answers in local material, and preserve privacy and radio discipline.

## Operating Principles

1. Retrieval first. The model is never the source of truth.
2. Direct-message only for user questions and answers.
3. No public location disclosure under any circumstance.
4. Keep responses short enough for reliable mesh delivery.
5. Prefer deterministic fallback behavior over speculative generation.
6. Fail closed: if retrieval is weak, say so.

## Agent Roles

Delphi-42 does not need a cloud-style swarm of agents. It needs a small, explicit pipeline with bounded responsibilities.

### 1. Radio Agent

Mapped to `bot/`.

Responsibilities:

- listen for Meshtastic packets
- accept direct messages only
- reject or ignore public questions
- normalize inbound text into commands
- emit private replies and position packets

Rules:

- ignore non-DM traffic except scheduled public broadcast messages
- never echo user prompts onto public channels
- rate-limit responses if the mesh is congested

### 2. Intent Agent

Mapped to `core/intent.py`.

Responsibilities:

- classify `help`
- classify `where` and `pos`
- classify `ask <question>`
- reject malformed or ambiguous input into a safe fallback

Rules:

- unknown or empty messages fall back to help text
- plain text without a verb may be treated as an implicit `ask`

### 3. Retrieval Agent

Mapped to `core/retriever.py` and `ingest/`.

Responsibilities:

- search the local index only
- return a small set of best-fit chunks
- avoid broad dumps of irrelevant context

Rules:

- target top 3 chunks unless testing suggests otherwise
- prefer concise passages over whole-document blobs
- attach source identifiers in the internal pipeline

### 4. Synthesis Agent

Mapped to `core/prompt_builder.py` and `core/llm_runner.py`.

Responsibilities:

- transform retrieved evidence into a compact prompt
- generate a short answer only from the provided context
- respect a strict word budget

Rules:

- never answer from model priors if retrieval is empty
- default answer budget: 40 words
- prefer a one-message response rather than multi-message monologues

### 5. Safety and Privacy Agent

Enforced across `bot/` and `core/`.

Responsibilities:

- suppress public location sharing
- suppress unsafe speculation
- prevent accidental leakage of private requests

Rules:

- `where` and `pos` return private position only
- public broadcasts contain no coordinates and no user data
- if content looks sensitive or ungrounded, return a short refusal or fallback

### 6. Broadcast Agent

Operationally part of `bot/oracle_bot.py`.

Responsibilities:

- send sparse, cryptic, public discovery messages

Rules:

- do not broadcast more often than operationally justified
- do not include support chatter, logs, or debugging output
- treat channel 0 as scarce shared space

## Standard Request Lifecycle

### `help`

1. Receive DM.
2. Parse command.
3. Return command list immediately.
4. Do not invoke retrieval or LLM.

### `where` or `pos`

1. Receive DM.
2. Verify request is private.
3. Return a short confirmation message.
4. Send private position packet.
5. Never mirror this response in public.

### `ask <question>`

1. Receive DM.
2. Normalize the question.
3. Retrieve top local passages from SQLite FTS.
4. Build a grounding prompt from those passages.
5. Generate a compact answer with the local model.
6. Return one short response.
7. If retrieval is empty, say the archive has no grounded answer.

## Knowledge Ingestion SOP

Mapped to `ingest/`.

1. Acquire offline source material such as ZIM archives, manuals, or curated plaintext.
2. Extract text from the source corpus.
3. Normalize document metadata and source IDs.
4. Chunk text into retrieval-sized units.
5. Build or rebuild the SQLite FTS index.
6. Spot-check top retrieval results before deploying.

Minimum acceptance checks:

- chunk size remains small enough for prompt construction
- duplicate boilerplate is minimized
- source identifiers remain stable across rebuilds
- index build completes without SQLite errors

## Deployment SOP on Raspberry Pi

1. Provision Python 3.9+ and a virtual environment.
2. Attach the Meshtastic device and confirm the serial path.
3. Copy `config/oracle.example.yaml` to `config/oracle.yaml`.
4. Set storage paths for plaintext corpus, SQLite index, and local model.
5. Install the `systemd/` unit files.
6. Run an index build before enabling the bot service.
7. Validate a local dry-run request before field deployment.

## Runtime Guardrails

- If the index is missing, the bot should stay online but answer with a clear local-archive-unavailable message.
- If the model is unavailable, the bot should degrade to deterministic retrieval summaries rather than go silent.
- If the radio device is unavailable, fail loudly in logs and avoid pretending the node is healthy.
- If storage is low, pause ingest jobs before corrupting the index.

## Logging and Observability

Keep logs local and small.

Log:

- service startup and shutdown
- radio connection success or failure
- command type counts
- retrieval hit or miss counts
- index build completion

Do not log:

- exact user questions in plaintext unless explicitly needed for debugging
- private coordinates in normal operation logs
- long model prompts or archive excerpts

## Operational Security

- Keep the node fully functional without internet access.
- Treat all public broadcasts as potentially hostilely observed.
- Store large archives and models outside git.
- Rebuild indexes from source material rather than hand-editing SQLite files.

## Implementation Mapping

- `bot/command_parser.py`: normalize wire input
- `bot/message_router.py`: DM-only routing
- `bot/oracle_bot.py`: startup loop and broadcasts
- `core/intent.py`: safe command classification
- `core/retriever.py`: local search interface
- `core/prompt_builder.py`: bounded context packaging
- `core/llm_runner.py`: deterministic fallback or local model wrapper
- `core/oracle_service.py`: final response policy
- `ingest/chunker.py`: chunk sizing
- `ingest/build_index.py`: SQLite FTS build path

## Exit Criteria for “Ready for Field Test”

The node is ready for a field test when:

- DM parsing works reliably
- public messages are ignored
- `where` sends a private position packet only
- at least one local corpus can be indexed
- retrieval returns relevant passages on sample survival questions
- answers stay within the configured budget
- services restart cleanly after reboot
