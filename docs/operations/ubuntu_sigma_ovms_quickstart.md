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

- run Delphi-42 natively on the host
- run OVMS on the host as the OpenAI-compatible model API
- keep `llm.backend: openai-compatible` and `llm.provider: ovms`
- use Kiwix in Docker only if you want archive browsing
- start with simulated radio, then switch to a supervised live T114 over USB

## Preferred Bootstrap

For this lane, the preferred path is now the one-line bootstrap script from the repo root:

```bash
./scripts/bootstrap_ubuntu_ovms.sh
```

It installs the Ubuntu host prerequisites, creates the gitignored runtime root under `artifacts/ubuntu-ovms/`, downloads the selected medicine archive into `artifacts/ubuntu-ovms/library/zim/releases/`, aliases it locally as `medicine.zim`, builds the runtime index, starts OVMS with `OpenVINO/Phi-3.5-mini-instruct-int4-ov`, detects the attached Heltec T114 by `/dev/serial/by-id/...`, generates local sim/live configs, and runs both preflight checks.

Assumptions and caveats:

- this bootstrap is aimed at the full Ubuntu + OVMS + live-T114 lane, not a simulated-only host
- the T114 should already be attached before you run it
- if the script has to add your user to `plugdev`, it will finish the host/sim setup, generate the live config, and skip live preflight for that run; log out and back in, then rerun the bootstrap or `artifacts/ubuntu-ovms/bin/preflight-live`
- if you want a staged or simulated-only setup without the live radio attached yet, use the manual fallback flow below

Useful overrides:

```bash
./scripts/bootstrap_ubuntu_ovms.sh --zim-profile maxi
./scripts/bootstrap_ubuntu_ovms.sh --radio-device /dev/serial/by-id/usb-Heltec_...
./scripts/bootstrap_ubuntu_ovms.sh --refresh-zim
./scripts/bootstrap_ubuntu_ovms.sh --reuse-index
```

Use `--reuse-index` on reruns when `artifacts/ubuntu-ovms/library/plaintext/` and `artifacts/ubuntu-ovms/index/oracle-ubuntu-ovms.db` are already populated and you only want to restart OVMS, regenerate local wrappers, or rerun preflight without extracting/indexing again.

The generated helper commands are:

- `artifacts/ubuntu-ovms/bin/preflight-sim`
- `artifacts/ubuntu-ovms/bin/preflight-live`
- `artifacts/ubuntu-ovms/bin/run-sim`
- `artifacts/ubuntu-ovms/bin/run-live`

If you need to control each step manually instead of using the bootstrap, use the fallback flow below.

## Manual Fallback Prerequisites

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

## Stage A: Simulated Radio + OVMS + Allowlisted ZIM

```bash
mkdir -p data/library/zim
cp /path/to/<actual-download>.zim data/library/zim/medicine.zim
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

- `?ask how do i purify water`
- `/public how do i purify water`
- `?where`

Expected results:

- direct `?ask` produces a bounded reply
- public traffic is ignored
- `where` produces a text confirmation plus a simulated private position packet
- if OVMS is down or the model id is wrong, Delphi-42 degrades to deterministic grounded summaries

## Stage B: Real `.zim` Validation

Copy one real archive into the local ZIM directory and stage it under the stable local alias:

```bash
cp /path/to/<actual-download>.zim data/library/zim/medicine.zim
```

Validate direct runtime `.zim` retrieval by rerunning preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.sim.yaml
```

Expected results:

- direct Kiwix-backed `.zim` lookup works from the allowlisted archive
- the first packet is a condensate of the continuation packets
- runtime `.zim` retrieval no longer depends on a separate index build

## Stage C: Supervised Live T114 Over USB

1. Attach the T114 to the Ubuntu host over USB.
2. Run live preflight:

```bash
uv run python -m scripts.host_preflight --config config/oracle.ubuntu.ovms.live.yaml
```

The first live preflight run will usually fail until you replace the placeholder device path. Prefer the listed `/dev/serial/by-id/...` entry for the attached T114. Use `/dev/ttyACM*` or `/dev/ttyUSB*` only if a stable by-id path is unavailable.

3. Edit [`config/oracle.ubuntu.ovms.live.yaml`](../../config/oracle.ubuntu.ovms.live.yaml):
   - replace `radio.device` with the actual `/dev/serial/by-id/...` path when available, or the correct `/dev/ttyACM...` or `/dev/ttyUSB...` fallback
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
