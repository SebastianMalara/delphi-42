# Interfaces And Config

- Purpose: Define external commands, runtime configuration, service interfaces, and persistent data expectations.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: software_architecture.md, ../../config/oracle.example.yaml, ../../systemd/oracle-bot.service, ../../systemd/oracle-core.service
- Exit Criteria: Operators and implementers can understand the supported commands, config shape, services, and file interfaces without reading code first.

## Context

Prototype v1 exposes a deliberately small interface surface: a few DM commands, one YAML config file, one index-build entrypoint, and two starter `systemd` units.

## Components

- Meshtastic DM interface
- YAML configuration
- local service entrypoints
- persistent data directories for corpora, indexes, and models

## Interfaces

### User-Facing Commands

| Command | Meaning | Expected Result |
| --- | --- | --- |
| `help` | List supported actions | Text help response |
| `where` | Ask for private node location | Text confirmation plus private position packet |
| `pos` | Alias for location request | Same as `where` |
| `ask <question>` | Ask the oracle a question | Short grounded answer or grounded-failure response |

### Local Entry Points

| Entry Point | Purpose |
| --- | --- |
| `python -m bot.oracle_bot` | Start the bot loop |
| `python -m ingest.build_index --input-dir ... --db ...` | Build or rebuild the SQLite FTS index |

### Config Schema

Current config keys from `config/oracle.example.yaml`:

| Section | Key | Meaning |
| --- | --- | --- |
| top level | `node_name` | Human-readable node name |
| `radio` | `device`, `channel` | Radio device path and channel |
| `privacy` | `answer_public_messages`, `share_position_publicly` | Safety flags that should stay `false` in Prototype v1 |
| `broadcasts` | `interval_minutes`, `messages` | Public discovery behavior |
| `knowledge` | `plaintext_dir`, `index_path`, `kiwix_url` | Corpus, index, and archive locations |
| `llm` | `backend`, `model_path`, `max_words` | Local model runtime and output budget |
| `wifi` | `ssid` | Local hotspot name |

### Service Interfaces

| Service | Trigger | Responsibility |
| --- | --- | --- |
| `oracle-bot.service` | long-running | Run the Meshtastic-facing bot process |
| `oracle-core.service` | oneshot/manual or scheduled | Rebuild the local index from plaintext |

### File And Directory Interfaces

| Path Class | Expected Use |
| --- | --- |
| `config/oracle.yaml` | site-local runtime configuration, copied from example |
| `data/library/plaintext` | staged plaintext corpus |
| `data/index/oracle.db` | generated SQLite FTS database |
| `models/` | local model files such as `.gguf` |

## Data/Control Flow

- Operators modify config and stage data directories.
- Services read config and data paths at runtime.
- `ingest` writes the index that `core` later reads.
- `bot` exposes the user-facing command interface through Meshtastic.

## Failure Modes

- Config paths diverge from actual mount points
- Operators enable unsafe privacy flags
- Service units point to paths that do not exist on the target Pi
- Corpus rebuild path and bot runtime path drift apart

## Security/Privacy Constraints

- `answer_public_messages` and `share_position_publicly` remain disabled for Prototype v1.
- Model and corpus paths should not be stored in world-writable locations.
- Config files may contain deployment-sensitive paths and should stay local to the node.
