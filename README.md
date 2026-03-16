# DELPHI-42

Delphi-42 is a prototype offline oracle node for Meshtastic: a Raspberry Pi system that receives private LoRa questions, retrieves grounded local knowledge from allowlisted `.zim` archives, and returns short answers without internet dependency.

The design baseline is now Kiwix-first: Kiwix serves the browseable archive over local hotspot WiFi, and Delphi-42 answers mesh questions directly from allowlisted `.zim` files through `llm-tools-kiwix` plus a local OpenAI-compatible model. The bot exposes explicit `?ask`, `?chat`, `?help`, `?where`, and `?pos` commands, prefixes each answer with `🤖 `, and uses a multi-pass answer pipeline so the first packet is a condensate of the fuller reply instead of a duplicated fragment.

Active development is now container-first for the portable parts of the stack. On macOS or any `arm64` Linux host, Delphi-42 runs through `docker compose` with simulated radio, a mock OpenAI-compatible API by default, and optional Ollama for manual demos. On Raspberry Pi 5, the same Delphi app image can run in Compose while the M5 `llm-openai-api` service stays host-managed.

For the fastest software validation loop on an Apple Silicon Mac, use the host-native M1 path in [`docs/operations/mac_m1_pro_quickstart.md`](docs/operations/mac_m1_pro_quickstart.md): Delphi-42 in a `uv`-managed environment, LM Studio on the host, optional Kiwix in Docker, staged `.zim` testing, and a supervised live T114 path over USB.

For an x86 Ubuntu prototype lane such as LattePanda Sigma, use [`docs/operations/ubuntu_sigma_ovms_quickstart.md`](docs/operations/ubuntu_sigma_ovms_quickstart.md): Delphi-42 in a `uv`-managed environment, OpenVINO Model Server on the host, a managed Kiwix container for archive browsing, staged `.zim` testing, and an optional live T114 path over USB.

## Development Status (2026-03)

- **Runtime behavior:** explicit command modes only (`?help`, `?where`, `?pos`, `?ask`, `?chat`, `?mesh`); bare text intentionally falls back to help so intent is never guessed silently.
- **Retrieval behavior:** Kiwix-first, allowlist-bounded `.zim` retrieval at runtime (no separate index build required for the normal ask flow).
- **Model API contract:** OpenAI-compatible endpoint with provider profile selection (`generic`, `stackflow`, `lm-studio`, `ovms`) and deterministic fallback behavior when provider/model health checks fail.
- **Platform lanes under active development:**
  - Apple Silicon host-native lane (LM Studio + optional Kiwix container)
  - Ubuntu x86 lane (e.g., LattePanda Sigma + OVMS + optional live T114)
  - Raspberry Pi Compose lane (containerized app + host-managed accelerator service)
- **Observed validation runs:** documented Ubuntu OVMS preflight and simulated-lane smoke checks on LattePanda Sigma-class x86 hosts, plus Mac host-native validation notes in the test matrix.
- **Validation status:** unit/integration tests run in CI/local dev; lane-specific host preflight and smoke procedures are documented for Mac and Ubuntu Sigma workflows.

## Compatibility Layers and Libraries

Delphi-42 intentionally uses compatibility layers so the bot can target different local inference runtimes while keeping one bot-level contract:

- **Inference compatibility layer:** `openai-compatible` backend abstraction in app config.
- **Provider compatibility profiles:** `llm.provider` profiles tune expectations/docs for `generic`, `stackflow`, `lm-studio`, and `ovms` without changing core command/retrieval logic.
- **Legacy backend alias:** `axcl-openai` is accepted as a compatibility alias and normalized to `openai-compatible`.
- **Retrieval compatibility layer:** `llm-tools-kiwix` bridges LLM tool calls to local allowlisted `.zim` archives.

Primary Python dependencies and optional extras are declared in `pyproject.toml`:

- Base: `PyYAML`, `beautifulsoup4`, `strip-tags`
- Bot integration: `meshtastic`
- LLM/runtime integration: `openai`, `llm`, `llm-tools-kiwix`
- Archive access: `libzim`

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

### 1) Host-native bootstrap (M1 Pro / Apple Silicon)

Fastest software validation path on Apple Silicon with simulated radio:

```bash
brew install libzim uv
uv venv
uv pip install -e .[bot,llm,zim]
uv run python -m scripts.mac_preflight --config config/oracle.mac.sim.yaml
DELPHI_CONFIG=config/oracle.mac.sim.yaml uv run python -m bot.dev_console
```

Full instructions for LM Studio, real `.zim` files, optional Kiwix, and the supervised live T114 lane are in [`docs/operations/mac_m1_pro_quickstart.md`](docs/operations/mac_m1_pro_quickstart.md).

### 2) Host-native bootstrap (Ubuntu x86 / LattePanda Sigma + OVMS)

Preferred one-command bootstrap for the Ubuntu Sigma lane:

```bash
./scripts/bootstrap_ubuntu_ovms.sh
```

Then start the generated simulated runtime wrapper:

```bash
artifacts/ubuntu-ovms/bin/run-sim
```

For full manual flow and live-radio staging details, use [`docs/operations/ubuntu_sigma_ovms_quickstart.md`](docs/operations/ubuntu_sigma_ovms_quickstart.md).

### 3) Containerized dev bootstrap

Container-first software path (mock OpenAI provider by default):

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
docker compose -f compose.yaml -f compose.dev.yaml run --rm oracle-app python -m bot.dev_console
pytest
```

### 4) Minimal native run (generic local dev)

To run the app natively without full lane-specific setup:

```bash
brew install uv
uv venv
uv pip install -e .[bot,llm,zim]
DELPHI_CONFIG=config/oracle.dev.yaml uv run python -m bot.dev_console
```

## `?<keyword>` Command Modes

Delphi-42 uses explicit mode commands over Meshtastic DMs. Each command starts with `?`.

- `?help` — show supported commands and examples.
- `?ask <question>` — retrieval-grounded Q&A against allowlisted `.zim` archives.
- `?chat <message>` — lightweight conversational mode without retrieval.
- `?where` — private location request flow (text confirmation + private position packet).
- `?pos` — alias of `?where`.
- `?mesh` — mesh status/diagnostic mode intended for quick radio-path checks.

Notes:

- Missing required arguments (for `?ask`/`?chat`) return help.
- Bare text (no leading `?`) returns help by design.
- Unsupported keywords (for example `?foo`) return help.

## Current Status

- Codebase status: Python 3.9+ bot with explicit mode commands, Kiwix-only retrieval through allowlisted `.zim` archives, short chat memory, multi-pass packet generation, provider-aware config and preflight support, container assets, config profiles, and tests.
- Documentation status: full in-repo suite for engineering and operations planning.
- Product status: Prototype v1 definition re-baselined around Raspberry Pi 5 + M5 AI-8850 kit, with container-first core development and host-managed accelerator services on Pi.
- Archive policy: self-managed Kiwix software and ZIM refreshes are operator-driven and do not require an annual Delphi-42 subscription model.

## License

MIT — see [LICENSE](LICENSE).
