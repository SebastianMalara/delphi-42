# Container Workflows

- Purpose: Define the container-first development workflow on macOS/OrbStack and the hybrid Compose deployment model on Raspberry Pi.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: deployment_runbook.md, raspberry_pi_provisioning.md, ../../compose.yaml, ../../compose.dev.yaml, ../../compose.pi.yaml
- Exit Criteria: A developer can run Delphi-42 locally without hardware, and an operator can understand which services belong in containers versus on the Pi host.

## Development Workflow

The default development path is:

1. start the portable services with Compose
2. build the local SQLite index from the repo-tracked sample corpus
3. run the app against simulated radio
4. inspect outbound packets through the dev console

Use these commands on macOS/OrbStack or any compatible `arm64` Docker host:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
docker compose -f compose.yaml -f compose.dev.yaml run --rm oracle-app python -m bot.dev_console
```

The dev profile uses:

- `config/oracle.dev.yaml`
- simulated radio transport
- repo-tracked plaintext fixtures under `sample_data/plaintext`
- mock OpenAI-compatible service on `mock-openai:8000`
- optional `ollama` profile for manual model demos

## Pi Hybrid Workflow

On Raspberry Pi 5, use the same Delphi app image and Compose packaging for the portable runtime, but keep the M5 model service on the host.

Use these commands on the Pi:

```bash
docker compose -f compose.yaml -f compose.pi.yaml up --build -d
docker compose -f compose.yaml -f compose.pi.yaml run --rm oracle-indexer
```

The Pi profile uses:

- `config/oracle.pi.yaml`
- Meshtastic device mapping for `/dev/ttyUSB0`
- `host.docker.internal:8000` as the host-local StackFlow API endpoint
- mounted `data/library/plaintext`, `data/library/zim`, and `data/index`

## Service Boundaries

Containerized services:

- `oracle-app`
- `oracle-indexer`
- `kiwix`
- `mock-openai` in development only

Host-managed Pi services:

- `llm-openai-api`
- StackFlow model packages
- power management and shutdown hooks
- hardware monitoring and telemetry collection

## Validation Checks

- `oracle-indexer` completes successfully and writes the configured SQLite DB
- `oracle-app` starts with the expected config profile
- `mock-openai` responds on `/v1/models` in development
- `oracle-app` degrades to deterministic summaries if the model API is unavailable
- `kiwix` serves mounted `.zim` files when available, or stays idle if no local archive is mounted
