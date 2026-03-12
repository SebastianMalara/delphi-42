# Interfaces And Config

- Purpose: Define external commands, runtime configuration, service interfaces, and persistent data expectations.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: software_architecture.md, ../../config/oracle.example.yaml, ../../systemd/oracle-bot.service, ../../systemd/oracle-core.service
- Exit Criteria: Operators and implementers can understand the supported commands, config shape, services, and file interfaces without reading code first.

## Context

Prototype v1 exposes a deliberately small interface surface: a few DM commands, YAML config profiles, local entrypoints, container services, and one host-local OpenAI-compatible model service on Pi.

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
| `python -m bot.dev_console` | Start the simulated-radio development console |
| `python -m scripts.mac_preflight --config ...` | Validate the Mac-native LM Studio plus `.zim` plus Meshtastic environment |
| `python -m ingest.extract_zim --zim-dir ... --output-dir ... --allowlist ...` | Export curated `.zim` content into staged plaintext |
| `python -m ingest.build_index --input-dir ... --db ...` | Build or rebuild the SQLite FTS index |

### Config Schema

Current config keys from `config/oracle.example.yaml`:

| Section | Key | Meaning |
| --- | --- | --- |
| top level | `node_name` | Human-readable node name |
| `radio` | `transport`, `device`, `channel` | Radio transport, device path, and channel |
| `privacy` | `answer_public_messages`, `share_position_publicly` | Safety flags that should stay `false` in Prototype v1 |
| `broadcasts` | `interval_minutes`, `messages` | Public discovery behavior |
| `knowledge` | `plaintext_dir`, `index_path`, `kiwix_url`, `zim_dir`, `runtime_zim_fallback_enabled`, `runtime_zim_allowlist`, `runtime_zim_search_limit` | Corpus, index, browse-archive locations, and bounded runtime `.zim` fallback policy |
| `llm` | `backend`, `base_url`, `model`, `api_key`, `timeout_seconds` | OpenAI-compatible local model runtime settings |
| `reply` | `short_max_chars`, `continuation_max_chars`, `max_continuation_packets` | Deterministic packet contract enforced in application logic |
| `wifi` | `ssid` | Local hotspot name |

Current implementation note:

- Prototype v1 accepts `openai-compatible` and `deterministic` as runtime backends.
- The legacy backend name `axcl-openai` is accepted as a compatibility alias and normalized to `openai-compatible`.
- The configured API key is a local placeholder contract for the OpenAI client and may remain `sk-` unless the local service is hardened differently.
- `config/oracle.dev.yaml` is the default simulated-radio dev profile.
- `config/oracle.pi.yaml` is the default Pi Compose profile.
- `config/oracle.mac.sim.yaml` is the host-native Apple Silicon simulated-radio profile for LM Studio.
- `config/oracle.mac.live.yaml` is the host-native Apple Silicon live-Meshtastic profile for a USB-attached T114.

### Service Interfaces

| Service | Trigger | Responsibility |
| --- | --- | --- |
| `oracle-app` | long-running container | Run the bot process in Compose |
| `oracle-indexer` | oneshot container | Rebuild the local index from plaintext |
| `oracle-bot.service` | long-running host service | Legacy host-managed bot wrapper for non-container Pi deployments |
| `oracle-core.service` | oneshot/manual or scheduled | Legacy host-managed index rebuild wrapper |
| `kiwix` | container or host service | Expose mounted `.zim` files over local HTTP |
| `llm-openai-api.service` | host service | Expose the AX8850-backed local chat and model endpoints on loopback |

### File And Directory Interfaces

| Path Class | Expected Use |
| --- | --- |
| `config/oracle.example.yaml` | generic reference configuration |
| `config/oracle.dev.yaml` | simulated-radio development config |
| `config/oracle.pi.yaml` | Pi Compose runtime config |
| `config/oracle.mac.sim.yaml` | host-native Mac simulated-radio config |
| `config/oracle.mac.live.yaml` | host-native Mac live-radio config |
| `compose.yaml`, `compose.dev.yaml`, `compose.pi.yaml` | portable runtime packaging and environment overlays |
| `sample_data/plaintext` | repo-tracked sample corpus for local development |
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
- `radio.transport` does not match the intended environment
- Operators enable unsafe privacy flags
- Service units point to paths that do not exist on the target Pi
- Corpus rebuild path and bot runtime path drift apart
- Operators refresh Kiwix content without rebuilding the derived answer index
- runtime `.zim` fallback is enabled but the allowlisted `.zim` files are missing
- StackFlow service is installed but the configured model package is missing
- the Pi app container cannot reach `host.docker.internal:8000`
- A legacy config still uses `llm.model_path` or `llm.max_words` instead of the current v1 contract

## Security/Privacy Constraints

- `answer_public_messages` and `share_position_publicly` remain disabled for Prototype v1.
- Model and corpus paths should not be stored in world-writable locations.
- Config files may contain deployment-sensitive paths and should stay local to the node.
