# Interfaces And Config

- Purpose: Define external commands, runtime configuration, service interfaces, and persistent data expectations.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-13
- Dependencies: software_architecture.md, ../../config/oracle.example.yaml, ../../systemd/oracle-bot.service, ../../systemd/oracle-core.service
- Exit Criteria: Operators and implementers can understand the supported commands, config shape, services, and file interfaces without reading code first.

## Context

Prototype v1 exposes a deliberately small interface surface: a few DM commands, YAML config profiles, local entrypoints, container services, and one provider-selected host-local OpenAI-compatible model service per node.

## Components

- Meshtastic DM interface
- YAML configuration
- local service entrypoints
- persistent data directories for archives and models

## Interfaces

### User-Facing Commands

| Command | Meaning | Expected Result |
| --- | --- | --- |
| `?help` | List supported actions | Text help response |
| `?where` | Ask for private node location | Text confirmation plus private position packet |
| `?pos` | Alias for location request | Same as `?where` |
| `?ask <question>` | Ask the oracle a question | Ultra-short grounded answer plus bounded continuation or grounded-failure response |
| `?chat <message>` | Talk to the bot without retrieval | Short conversational reply plus optional continuation |

### Local Entry Points

| Entry Point | Purpose |
| --- | --- |
| `python -m bot.oracle_bot` | Start the bot loop |
| `python -m bot.dev_console` | Start the simulated-radio development console |
| `python -m scripts.host_preflight --config ...` | Validate host-native OpenAI-compatible runtime, `.zim`, and Meshtastic environment |
| `python -m scripts.mac_preflight --config ...` | Compatibility wrapper for the Mac-native LM Studio lane |
| `python -m scripts.inspect_retrieval --config ... --question ...` | Inspect anchor terms, retrieval confidence, selected source, and answer policy for one question |

### Config Schema

Current config keys from `config/oracle.example.yaml`:

| Section | Key | Meaning |
| --- | --- | --- |
| top level | `node_name` | Human-readable node name |
| `radio` | `transport`, `device`, `channel`, `text_packet_spacing_seconds`, `text_packet_retry_attempts`, `text_packet_retry_delay_seconds`, `max_text_payload_bytes` | Radio transport, device path, pacing, retry policy, and safe text payload ceiling |
| `privacy` | `answer_public_messages`, `share_position_publicly` | Safety flags that should stay `false` in Prototype v1 |
| `broadcasts` | `interval_minutes`, `messages` | Public discovery behavior |
| `knowledge` | `kiwix_url`, `zim_dir`, `zim_allowlist`, `zim_search_limit` | Browse-archive location and allowlisted runtime `.zim` retrieval inputs |
| `llm` | `backend`, `provider`, `base_url`, `model`, `api_key`, `timeout_seconds` | OpenAI-compatible local model runtime settings |
| `reply` | `short_max_chars`, `condensed_max_chars`, `max_total_packets` | Multi-pass reply targets enforced in application logic |
| `wifi` | `ssid` | Local hotspot name |

Current implementation note:

- Prototype v1 accepts `openai-compatible` and `deterministic` as runtime backends.
- `llm.provider` selects provider-specific docs and preflight expectations while keeping `llm.base_url` authoritative.
- Supported `llm.provider` values are `generic`, `stackflow`, `lm-studio`, and `ovms`.
- The legacy backend name `axcl-openai` is accepted as a compatibility alias and normalized to `openai-compatible`.
- The configured API key is a local placeholder contract for the OpenAI client and may remain `sk-` unless the local service is hardened differently.
- `config/oracle.dev.yaml` is the default simulated-radio dev profile.
- `config/oracle.pi.yaml` is the default Pi Compose profile.
- `config/oracle.mac.sim.yaml` is the host-native Apple Silicon simulated-radio profile for LM Studio.
- `config/oracle.mac.live.yaml` is the host-native Apple Silicon live-Meshtastic profile for a USB-attached T114.
- `config/oracle.ubuntu.ovms.sim.yaml` is the host-native Ubuntu x86 simulated-radio profile for OVMS.
- `config/oracle.ubuntu.ovms.live.yaml` is the host-native Ubuntu x86 live-Meshtastic profile for OVMS.

### Service Interfaces

| Service | Trigger | Responsibility |
| --- | --- | --- |
| `oracle-app` | long-running container | Run the bot process in Compose |
| `oracle-bot.service` | long-running host service | Legacy host-managed bot wrapper for non-container Pi deployments |
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
| `config/oracle.ubuntu.ovms.sim.yaml` | host-native Ubuntu OVMS simulated-radio config |
| `config/oracle.ubuntu.ovms.live.yaml` | host-native Ubuntu OVMS live-radio config |
| `compose.yaml`, `compose.dev.yaml`, `compose.pi.yaml` | portable runtime packaging and environment overlays |
| `data/library/zim` | optional staged ZIM files or archive source mount |
| host package state | provider-specific runtime packages and installed model packages managed outside the app |

## Data/Control Flow

- Operators modify config and stage data directories.
- Services read config and data paths at runtime.
- Kiwix serves the larger archive independently from the answer-time retrieval calls.
- Allowlisted `.zim` files are the only grounded retrieval source at runtime.
- Meshtastic text answers are paced and retried in application logic, and live profiles enforce a radio-safe payload envelope.
- `bot` exposes the user-facing command interface through Meshtastic.

## Failure Modes

- Config paths diverge from actual mount points
- `radio.transport` does not match the intended environment
- Operators enable unsafe privacy flags
- Service units point to paths that do not exist on the target Pi
- Operators refresh Kiwix content but forget to update the allowlisted runtime archives
- configured `.zim` allowlist files are missing
- provider-specific model service is installed but the configured model package or endpoint path is wrong
- the Pi app container cannot reach `host.docker.internal:8000`
- A legacy config still uses `llm.model_path` or `llm.max_words` instead of the current v1 contract

## Security/Privacy Constraints

- `answer_public_messages` and `share_position_publicly` remain disabled for Prototype v1.
- Model and corpus paths should not be stored in world-writable locations.
- Config files may contain deployment-sensitive paths and should stay local to the node.
