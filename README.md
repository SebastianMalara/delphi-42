# DELPHI-42

Delphi-42 is a prototype offline oracle node for Meshtastic: a Raspberry Pi system that receives private LoRa questions, retrieves grounded local knowledge, and returns short answers without internet dependency.

The design baseline is a hybrid offline knowledge stack: Kiwix serves the larger browseable archive over local hotspot WiFi, while Delphi-42 answers mesh questions from a curated local index derived from plaintext and selected archive extracts. Prototype v1 is now baselined on the `M5Stack AI-8850 LLM Accelerator M.2 Kit 8GB` running a local `StackFlow` OpenAI-compatible API on `Debian 12 arm64`, with deterministic retrieval summaries as the fallback path and a bounded allowlisted `.zim` lookup as the secondary retrieval source when the SQLite index misses.

This repository now treats [`docs/README.md`](docs/README.md) as the documentation entry point and the source of truth for how the system should be built, deployed, tested, and operated.

## Start Here

- Project brief: [`docs/overview/project_brief.md`](docs/overview/project_brief.md)
- System context: [`docs/architecture/system_context.md`](docs/architecture/system_context.md)
- Hardware pack: [`docs/hardware/node_topology.md`](docs/hardware/node_topology.md)
- AI and retrieval design: [`docs/ai/retrieval_and_response_policy.md`](docs/ai/retrieval_and_response_policy.md)
- Deployment runbook: [`docs/operations/deployment_runbook.md`](docs/operations/deployment_runbook.md)
- Test strategy: [`docs/testing/test_strategy.md`](docs/testing/test_strategy.md)
- Execution plan: [`docs/project/execution_plan.md`](docs/project/execution_plan.md)
- Risk register: [`docs/project/risk_register.md`](docs/project/risk_register.md)

## Repository Layout

```text
delphi-42/
├── bot/          # Meshtastic-facing message handling
├── core/         # Intent, retrieval, prompt, and answer policy
├── ingest/       # Offline corpus preparation and indexing
├── config/       # Example runtime configuration
├── systemd/      # Starter unit files for Raspberry Pi deployment
├── docs/         # Source-of-truth documentation suite
├── scripts/      # Repo-local tooling, including doc checks
└── tests/        # Starter test suite
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[bot,llm,zim]
pytest
python -m bot.oracle_bot
```

To extract allowlisted `.zim` archives and build a local text index:

```bash
python -m ingest.extract_zim --zim-dir data/library/zim --output-dir data/library/plaintext --allowlist wikipedia_en_medicine_maxi_2023-12.zim
python -m ingest.build_index --input-dir data/library/plaintext --db data/index/oracle.db
```

## Current Status

- Codebase status: Python 3.9+ scaffold with starter bot, retrieval, allowlisted `.zim` fallback, ingest/extraction tools, AX8850-backed local API adapter, deterministic packet formatting, config, and tests.
- Documentation status: full in-repo suite for engineering and operations planning.
- Product status: Prototype v1 definition re-baselined around Raspberry Pi 5 + M5 AI-8850 kit, not a field-hardened deployment.
- Archive policy: self-managed Kiwix software and ZIM refreshes are operator-driven and do not require an annual Delphi-42 subscription model.

## License

TBD
