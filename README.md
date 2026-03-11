# DELPHI-42

### A post-apocalyptic oracle node for Meshtastic

Delphi-42 is an experimental offline oracle node built for:

- Meshtastic LoRa mesh communication
- Raspberry Pi deployment
- Offline knowledge bases such as Kiwix and ZIM archives
- A small local LLM for short grounded answers

The node accepts Meshtastic direct messages, retrieves context from a local archive, and returns compact answers without relying on the internet.

## Concept

In a world without reliable connectivity, knowledge becomes scarce.

Delphi-42 is meant to behave like a digital shrine of knowledge:

- discoverable through the Meshtastic mesh
- powered by offline libraries
- queryable via LoRa messages
- accessible locally through a WiFi hotspot for full archive browsing

Typical user flow:

1. Ask a question via Meshtastic direct message.
2. Receive a short oracle answer.
3. Request the oracle's location privately.
4. Travel to the node.
5. Join the hotspot and browse the larger archive.

## Features

### Meshtastic Oracle Bot

The bot:

- listens for direct messages
- ignores public questions
- answers compact `ask <question>` requests
- broadcasts occasional public oracle messages
- can share a private position packet to the requesting node

Supported direct-message commands:

```text
help
where
pos
ask <question>
```

Examples:

```text
ask how to purify water
ask hypothermia symptoms
where
```

### Oracle Broadcasts

Example public broadcasts:

```text
THE ORACLE LISTENS. SEND DM FOR COUNSEL.
ASH NODE AWAKE.
SEEK WISDOM IN PRIVATE.
```

Broadcasts should invite discovery without flooding the mesh.

### Privacy Model

- The oracle never shares its position publicly.
- Public channel traffic is limited to short cryptic broadcasts.
- Knowledge answers are delivered only in private.

### Offline Knowledge

The retrieval layer is designed for offline datasets such as:

- Wikipedia snapshots
- survival manuals
- first aid material
- repair guides

Recommended format:

```text
ZIM archive
  -> text extraction
  -> chunking
  -> SQLite FTS index
```

### Local WiFi Archive

When a user reaches the node physically, they can join the hotspot and browse the full archive through Kiwix or another local web interface.

## System Architecture

```text
Meshtastic Network
        |
        v
   Meshtastic Node
        | USB
        v
Raspberry Pi Oracle Node
 |- bot
 |- core
 |- local LLM
 |- knowledge index
 `- Kiwix server
        |
        v
   WiFi hotspot
        |
        v
 users / explorers
```

## Repository Layout

The repository is now organized as a Python-first project skeleton that matches the architecture above:

```text
delphi-42/
├── bot/
│   ├── __init__.py
│   ├── command_parser.py
│   ├── message_router.py
│   ├── oracle_bot.py
│   └── radio_interface.py
├── config/
│   └── oracle.example.yaml
├── core/
│   ├── __init__.py
│   ├── intent.py
│   ├── llm_runner.py
│   ├── oracle_service.py
│   ├── prompt_builder.py
│   └── retriever.py
├── docs/
│   └── sops/
│       └── agentic_ai.md
├── ingest/
│   ├── __init__.py
│   ├── build_index.py
│   ├── chunker.py
│   └── zim_extract.py
├── systemd/
│   ├── oracle-bot.service
│   └── oracle-core.service
├── tests/
│   ├── test_chunker.py
│   ├── test_command_parser.py
│   └── test_oracle_service.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Software Components

### `bot/`

Meshtastic-facing logic:

- parse incoming commands
- filter for direct-message traffic
- route requests to `core/`
- emit replies and private position packets

### `core/`

Reasoning and response layer:

- classify intent
- retrieve relevant local context
- build constrained prompts
- run a local answer generator
- enforce short response limits suitable for mesh delivery

### `ingest/`

Knowledge-preparation pipeline:

- extract text from offline sources
- chunk long documents
- build a local SQLite FTS index

### `docs/sops/agentic_ai.md`

Operational SOP for running an offline agentic oracle on Raspberry Pi + Meshtastic + Kiwix + local LLM.

## Bootstrap

Create a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run tests:

```bash
pytest
```

Start the starter bot locally:

```bash
python -m bot.oracle_bot
```

Build an index from plaintext files:

```bash
python -m ingest.build_index --input-dir data/library/plaintext --db data/index/oracle.db
```

## Deployment Notes

- Copy `config/oracle.example.yaml` to `config/oracle.yaml` and adjust device paths, model paths, and storage locations.
- Install the starter systemd units from `systemd/` on the Raspberry Pi.
- Treat the current code as a scaffold: it establishes repo shape, interfaces, and operational boundaries, not a finished radio daemon.

## Roadmap

### Phase 1

- Meshtastic direct-message listener
- command parser
- oracle broadcasts

### Phase 2

- knowledge index
- deterministic answers

### Phase 3

- local LLM integration

### Phase 4

- WiFi archive
- pilgrimage mode

## Project Status

Early experimental prototype with a now-initialized repository structure and Python 3.9+ starter scaffold.

## Inspiration

- Meshtastic mesh networks
- offline internet projects
- knowledge shrines
- post-collapse communication systems

## License

TBD
