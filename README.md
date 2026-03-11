# DELPHI-42

Delphi-42 is a prototype offline oracle node for Meshtastic: a Raspberry Pi system that receives private LoRa questions, retrieves grounded local knowledge, and returns short answers without internet dependency.

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
pip install -e .
pytest
python -m bot.oracle_bot
```

To build a local text index:

```bash
python -m ingest.build_index --input-dir data/library/plaintext --db data/index/oracle.db
```

## Current Status

- Codebase status: Python 3.9+ scaffold with starter bot, retrieval, ingest, config, and tests.
- Documentation status: full in-repo suite for engineering and operations planning.
- Product status: Prototype v1 definition, not a field-hardened deployment.

## License

TBD
