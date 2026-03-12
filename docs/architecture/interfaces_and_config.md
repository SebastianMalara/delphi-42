# Interfaces And Config

- Purpose: Define external commands, runtime configuration, service interfaces, and persistent data expectations.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: software_architecture.md, ../../config/oracle.example.yaml, ../../systemd/oracle-bot.service, ../../systemd/oracle-core.service
- Exit Criteria: Operators and implementers can understand the supported commands, config shape, services, and file interfaces without reading code first.

## Context

Prototype v1 exposes a deliberately small interface surface: a few DM commands, one YAML config file, one index-build entrypoint, two starter `systemd` units, and one host-local OpenAI-compatible model service.

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
| `ask <question>` | Ask the oracle a question | Ultra-short grounded answer plus optional bounded continuation or grounded-failure response |

### Local Entry Points

| Entry Point | Purpose |
| --- | --- |
| `python -m bot.oracle_bot` | Start the bot loop |
| `python -m ingest.extract_zim --zim-dir ... --output-dir ... --allowlist ...` | Export curated `.zim` content into staged plaintext |
| `python -m ingest.build_index --input-dir ... --db ...` | Build or rebuild the SQLite FTS index |

### Config Schema

Current config keys from `config/oracle.example.yaml`:

| Section | Key | Meaning |
| --- | --- | --- |
| top level | `node_name` | Human-readable node name |
| `radio` | `device`, `channel` | Radio device path and channel |
| `privacy` | `answer_public_messages`, `share_position_publicly` | Safety flags that should stay `false` in Prototype v1 |
| `broadcasts` | `interval_minutes`, `messages` | Public discovery behavior |
| `knowledge` | `plaintext_dir`, `index_path`, `kiwix_url`, `zim_dir`, `runtime_zim_fallback_enabled`, `runtime_zim_allowlist`, `runtime_zim_search_limit` | Corpus, index, browse-archive locations, and bounded runtime `.zim` fallback policy |
| `llm` | `backend`, `base_url`, `model`, `api_key`, `timeout_seconds` | Local AX8850-backed model runtime over the StackFlow OpenAI-compatible API |
| `reply` | `short_max_chars`, `continuation_max_chars`, `max_continuation_packets` | Deterministic packet contract enforced in application logic |
| `wifi` | `ssid` | Local hotspot name |

Current implementation note:

- Prototype v1 accepts only `axcl-openai` and `deterministic` as runtime backends.
- The configured API key is a local placeholder contract for the OpenAI client and may remain `sk-` unless the local service is hardened differently.

### Service Interfaces

| Service | Trigger | Responsibility |
| --- | --- | --- |
| `oracle-bot.service` | long-running | Run the Meshtastic-facing bot process |
| `oracle-core.service` | oneshot/manual or scheduled | Rebuild the local index from plaintext |
| `llm-openai-api.service` | host service | Expose the AX8850-backed local chat and model endpoints on loopback |

### File And Directory Interfaces

| Path Class | Expected Use |
| --- | --- |
| `config/oracle.yaml` | site-local runtime configuration, copied from example |
| `data/library/plaintext` | staged plaintext corpus |
| `data/library/zim` | optional staged ZIM files or archive source mount |
| `data/index/oracle.db` | generated SQLite FTS database |
| host package state | StackFlow packages and installed model packages managed by `apt` on Debian 12 |

## Data/Control Flow

- Operators modify config and stage data directories.
- Services read config and data paths at runtime.
- `ingest` writes the index that `core` later reads.
- Kiwix serves the larger archive independently from the answer-time index.
- Allowlisted `.zim` files can be searched directly as a secondary retrieval source when the indexed corpus misses.
- `bot` exposes the user-facing command interface through Meshtastic.

## Failure Modes

- Config paths diverge from actual mount points
- Operators enable unsafe privacy flags
- Service units point to paths that do not exist on the target Pi
- Corpus rebuild path and bot runtime path drift apart
- Operators refresh Kiwix content without rebuilding the derived answer index
- runtime `.zim` fallback is enabled but the allowlisted `.zim` files are missing
- StackFlow service is installed but the configured model package is missing
- A legacy config still uses `llm.model_path` or `llm.max_words` instead of the current v1 contract

## Security/Privacy Constraints

- `answer_public_messages` and `share_position_publicly` remain disabled for Prototype v1.
- Model and corpus paths should not be stored in world-writable locations.
- Config files may contain deployment-sensitive paths and should stay local to the node.
