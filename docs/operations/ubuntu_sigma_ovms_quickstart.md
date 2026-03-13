# Ubuntu Sigma OVMS Quickstart

- Purpose: Provide the fastest host-native software validation path for Delphi-42 on an Ubuntu x86 host such as LattePanda Sigma using OpenVINO Model Server, optional Kiwix, real `.zim` archives, and an optional live T114.
- Audience: Engineering and advanced operators.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-13
- Dependencies: ../../config/oracle.ubuntu.ovms.sim.yaml, ../../config/oracle.ubuntu.ovms.live.yaml, ../../scripts/host_preflight.py, container_workflows.md
- Exit Criteria: A new Ubuntu x86 user can reach simulated validation, real `.zim` validation, and live T114 validation without relying on tribal knowledge.

## Overview

This is the preferred x86 Ubuntu prototype lane for Delphi-42:

- run Delphi-42 natively in a `uv`-managed Python environment
- run OVMS on the host as the OpenAI-compatible model API
- keep `llm.backend: openai-compatible` and `llm.provider: ovms`
- use Kiwix in Docker only if you want archive browsing
- start with simulated radio, then switch to a supervised live T114 over USB

## Prerequisites

1. Install Ubuntu 22.04 or another supported Ubuntu release for your OVMS setup.
2. Install `libzim`, Python 3.9 or newer, and `uv`.
3. Confirm OVMS is already installed and serving a text-generation model through its OpenAI-compatible `/v3` endpoints.
4. Install Docker only if you want optional Kiwix browsing.
5. From the repo root, create the local data directories:

```bash
mkdir -p data/index data/library/plaintext data/library/zim
```

6. Create the Python environment and install the project:

```bash
uv venv
uv pip install -e .[bot,llm,zim]
```

## OVMS Setup

1. Confirm OVMS is reachable on the host:

```bash
curl http://127.0.0.1:8000/v3/models
```

2. Edit both [`config/oracle.ubuntu.ovms.sim.yaml`](../../config/oracle.ubuntu.ovms.sim.yaml) and [`config/oracle.ubuntu.ovms.live.yaml`](../../config/oracle.ubuntu.ovms.live.yaml):
   - keep `llm.provider: ovms`
   - keep `llm.base_url` pointed at the OVMS `/v3` base URL
   - replace `llm.model` with the exact model id returned by `/v3/models`

## Stage A: Simulated Radio + OVMS + Sample Corpus

Build the sample index:

```bash
uv run python -m ingest.build_index --input-dir sample_data/plaintext --db data/index/oracle-ubuntu-ovms.db
```

Run preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.sim.yaml
```

Start the simulated console:

```bash
DELPHI_CONFIG=config/oracle.ubuntu.ovms.sim.yaml uv run python -m bot.dev_console
```

Smoke tests:

- `how do i purify water`
- `/public how do i purify water`
- `where`

Expected results:

- direct `ask` produces a bounded reply
- public traffic is ignored
- `where` produces a text confirmation plus a simulated private position packet
- if OVMS is down or the model id is wrong, Delphi-42 degrades to deterministic summaries

## Stage B: Real `.zim` Validation

Copy one real archive into the local ZIM directory:

```bash
cp /path/to/wikipedia_en_medicine_maxi_2023-12.zim data/library/zim/
```

Enable runtime fallback in [`config/oracle.ubuntu.ovms.sim.yaml`](../../config/oracle.ubuntu.ovms.sim.yaml):

- set `knowledge.runtime_zim_fallback_enabled: true`

Validate direct runtime `.zim` fallback first by keeping the sample-only SQLite index and rerunning preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.sim.yaml
```

Then validate the ingest path explicitly:

```bash
uv run python -m ingest.extract_zim --zim-dir data/library/zim --output-dir data/library/plaintext --allowlist wikipedia_en_medicine_maxi_2023-12.zim
uv run python -m ingest.build_index --input-dir data/library/plaintext --db data/index/oracle-ubuntu-ovms-zim.db
```

Expected results:

- `extract_zim` writes normalized plaintext under `data/library/plaintext`
- the extracted archive can be indexed into a second SQLite database
- runtime `.zim` fallback works even before you switch the main runtime to the extracted index

## Stage C: Supervised Live T114 Over USB

1. Attach the T114 to the Ubuntu host over USB.
2. Run live preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.live.yaml
```

The first live preflight run will usually fail until you replace the placeholder device path. Use the listed `/dev/ttyACM*` or `/dev/ttyUSB*` values to choose the correct device.

3. Edit [`config/oracle.ubuntu.ovms.live.yaml`](../../config/oracle.ubuntu.ovms.live.yaml):
   - replace `radio.device` with the actual `/dev/ttyACM...` or `/dev/ttyUSB...` path
   - if you already enabled `.zim` fallback in the simulated config, mirror that change here if you want the same retrieval behavior live

4. Re-run preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.live.yaml
```

5. Only continue if preflight exits successfully, then start the live bot:

```bash
DELPHI_CONFIG=config/oracle.ubuntu.ovms.live.yaml uv run python -m bot.oracle_bot
```

6. Use a second Meshtastic client, such as another node or the phone app, to send DMs to the Ubuntu-attached T114.

## Optional Kiwix

If you want browse testing on the same host, run Kiwix separately:

```bash
docker compose -f compose.yaml up kiwix
```

Kiwix is browse-only for this lane. It is not required for answer generation.
