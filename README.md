# DELPHI-42

Delphi-42 is a prototype offline oracle node for Meshtastic: a Raspberry Pi system that receives private LoRa questions, retrieves grounded local knowledge from allowlisted `.zim` archives, and returns short answers without internet dependency.

The design baseline is now Kiwix-first: Kiwix serves the browseable archive over local hotspot WiFi, and Delphi-42 answers mesh questions directly from allowlisted `.zim` files through `llm-tools-kiwix` plus a local OpenAI-compatible model. The bot exposes explicit `?ask`, `?chat`, `?help`, `?where`, and `?pos` commands, prefixes each answer with `🤖 `, and uses a multi-pass answer pipeline so the first packet is a condensate of the fuller reply instead of a duplicated fragment.

Active development is now container-first for the portable parts of the stack. On macOS or any `arm64` Linux host, Delphi-42 runs through `docker compose` with simulated radio, a mock OpenAI-compatible API by default, and optional Ollama for manual demos. On Raspberry Pi 5, the same Delphi app image can run in Compose while the M5 `llm-openai-api` service stays host-managed.

For the fastest software validation loop on an Apple Silicon Mac, use the host-native M1 path in [`docs/operations/mac_m1_pro_quickstart.md`](docs/operations/mac_m1_pro_quickstart.md): Delphi-42 in a `uv`-managed environment, LM Studio on the host, optional Kiwix in Docker, staged `.zim` testing, and a supervised live T114 path over USB.

For an x86 Ubuntu prototype lane such as LattePanda Sigma, use [`docs/operations/ubuntu_sigma_ovms_quickstart.md`](docs/operations/ubuntu_sigma_ovms_quickstart.md): Delphi-42 in a `uv`-managed environment, OpenVINO Model Server on the host, a managed Kiwix container for archive browsing, staged `.zim` testing, and an optional live T114 path over USB.

This repository now treats [`docs/README.md`](docs/README.md) as the documentation entry point and the source of truth for how the system should be built, deployed, tested, and operated.

## Start Here

- Project brief: [`docs/overview/project_brief.md`](docs/overview/project_brief.md)
- System context: [`docs/architecture/system_context.md`](docs/architecture/system_context.md)
- Hardware pack: [`docs/hardware/node_topology.md`](docs/hardware/node_topology.md)
- AI and retrieval design: [`docs/ai/retrieval_and_response_policy.md`](docs/ai/retrieval_and_response_policy.md)
- M1 Pro software quickstart: [`docs/operations/mac_m1_pro_quickstart.md`](docs/operations/mac_m1_pro_quickstart.md)
- Ubuntu/OpenVINO quickstart: [`docs/operations/ubuntu_sigma_ovms_quickstart.md`](docs/operations/ubuntu_sigma_ovms_quickstart.md)
- Container workflows: [`docs/operations/container_workflows.md`](docs/operations/container_workflows.md)
- Deployment runbook: [`docs/operations/deployment_runbook.md`](docs/operations/deployment_runbook.md)
- Test strategy: [`docs/testing/test_strategy.md`](docs/testing/test_strategy.md)
- Execution plan: [`docs/project/execution_plan.md`](docs/project/execution_plan.md)
- Risk register: [`docs/project/risk_register.md`](docs/project/risk_register.md)

## Repository Layout

```text
delphi-42/
├── bot/          # Meshtastic-facing message handling
├── core/         # Intent, retrieval, prompt, and answer policy
├── config/       # Example runtime configuration
├── compose*.yaml # Container workflows for dev and Pi
├── Dockerfile    # Multi-arch app image definition
├── systemd/      # Starter unit files for Raspberry Pi deployment
├── docs/         # Source-of-truth documentation suite
├── scripts/      # Repo-local tooling, including doc checks
└── tests/        # Starter test suite
```

## Quick Start

Fastest software-testing path on an M1 Pro:

```bash
brew install libzim uv
uv venv
uv pip install -e .[bot,llm,zim]
uv run python -m scripts.mac_preflight --config config/oracle.mac.sim.yaml
DELPHI_CONFIG=config/oracle.mac.sim.yaml uv run python -m bot.dev_console
```

Full instructions for LM Studio, real `.zim` files, optional Kiwix, and the supervised live T114 lane are in [`docs/operations/mac_m1_pro_quickstart.md`](docs/operations/mac_m1_pro_quickstart.md).

For an Ubuntu/OpenVINO host lane using OVMS and the same `openai-compatible` runtime contract, use [`docs/operations/ubuntu_sigma_ovms_quickstart.md`](docs/operations/ubuntu_sigma_ovms_quickstart.md).

Containerized dev path:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
docker compose -f compose.yaml -f compose.dev.yaml run --rm oracle-app python -m bot.dev_console
pytest
```

To run the app natively instead of through Compose without the full Mac validation lane:

```bash
brew install uv
uv venv
uv pip install -e .[bot,llm,zim]
DELPHI_CONFIG=config/oracle.dev.yaml uv run python -m bot.dev_console
```

## Current Status

- Codebase status: Python 3.9+ bot with explicit mode commands, Kiwix-only retrieval through allowlisted `.zim` archives, short chat memory, multi-pass packet generation, provider-aware config and preflight support, container assets, config profiles, and tests.
- Documentation status: full in-repo suite for engineering and operations planning.
- Product status: Prototype v1 definition re-baselined around Raspberry Pi 5 + M5 AI-8850 kit, with container-first core development and host-managed accelerator services on Pi.
- Archive policy: self-managed Kiwix software and ZIM refreshes are operator-driven and do not require an annual Delphi-42 subscription model.

## License

TBD
