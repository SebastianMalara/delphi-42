# Container Workflows

- Purpose: Define the container-first development workflow on macOS/OrbStack and the hybrid Compose deployment model on Raspberry Pi.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-13
- Dependencies: deployment_runbook.md, raspberry_pi_provisioning.md, ../../compose.yaml, ../../compose.dev.yaml, ../../compose.pi.yaml
- Exit Criteria: A developer can run Delphi-42 locally without hardware, and an operator can understand which services belong in containers versus on the Pi host.

## Development Workflow

The default development path is:

1. start the portable services with Compose
2. stage allowlisted `.zim` files under `data/library/zim`
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
- mock OpenAI-compatible service on `mock-openai:8000` with the default `/v1` API prefix
- optional `ollama` profile for manual model demos

If you want to validate LM Studio, real `.zim` archives, or a live T114 on an Apple Silicon Mac, use the host-native path in [`mac_m1_pro_quickstart.md`](mac_m1_pro_quickstart.md) instead of this containerized dev profile.

If you want to validate OVMS on an Ubuntu x86 host such as LattePanda Sigma, use [`ubuntu_sigma_ovms_quickstart.md`](ubuntu_sigma_ovms_quickstart.md) instead of this containerized dev profile.

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

## mock-openai Environment Variables

The `mock-openai` service (`scripts/mock_openai_api.py`) is configurable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `MOCK_OPENAI_MODEL` | `qwen3-1.7B-Int8-ctx-axcl` | Model name returned by the `/v1/models` endpoint |
| `MOCK_OPENAI_PORT` | `8000` | TCP port the mock server listens on |
| `MOCK_OPENAI_API_PREFIX` | `/v1` | URL prefix for all API routes |

Set these in `compose.dev.yaml` under the `mock-openai` service `environment` block if you need to override the defaults.

## Validation Checks

- `oracle-indexer` completes successfully and writes the configured SQLite DB
- `oracle-app` starts with the expected config profile
- `mock-openai` responds on its configured API prefix, `/v1` by default, in development
- `oracle-app` degrades to deterministic summaries if the model API is unavailable
- `kiwix` serves mounted `.zim` files when available, or stays idle if no local archive is mounted
