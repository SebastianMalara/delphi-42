# Mac M1 Pro Quickstart

- Purpose: Provide the fastest host-native software validation path for Delphi-42 on an Apple Silicon Mac using LM Studio, optional Kiwix, real `.zim` archives, and an optional live T114.
- Audience: Engineering and advanced operators.
- Owner: Software Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: ../../config/oracle.mac.sim.yaml, ../../config/oracle.mac.live.yaml, ../../scripts/mac_preflight.py, container_workflows.md
- Exit Criteria: A new M1 Pro user can reach simulated validation, real `.zim` validation, and live T114 validation without relying on tribal knowledge.

## Overview

This is the preferred fast-feedback software lane for Delphi-42:

- run Delphi-42 natively in a `uv`-managed Python environment
- run LM Studio on the host as the OpenAI-compatible model API
- use Kiwix in Docker only if you want archive browsing
- keep real `.zim` archives under `data/library/zim`
- start with simulated radio, then switch to a supervised live T114 over USB

## Prerequisites

1. Install Homebrew if it is not already present.
2. Install `libzim` and `uv`:

```bash
brew install libzim uv
```

3. Confirm you have:
   - Python 3.9 or newer
   - LM Studio installed
   - Docker or OrbStack only if you want optional Kiwix browsing
4. From the repo root, create the local data directories:

```bash
mkdir -p data/index data/library/plaintext data/library/zim
```

5. Create the Python environment and install the project:

```bash
uv venv
uv pip install -e .[bot,llm,zim]
```

## LM Studio Setup

1. Open LM Studio.
2. Load the model you want to use for local testing.
3. Start the OpenAI-compatible local server.
4. Confirm the model id:

```bash
curl http://127.0.0.1:1234/v1/models
```

5. Edit both [`config/oracle.mac.sim.yaml`](../../config/oracle.mac.sim.yaml) and [`config/oracle.mac.live.yaml`](../../config/oracle.mac.live.yaml):
   - replace `llm.model` with the exact model id returned by `/v1/models`

## Stage A: Simulated Radio + LM Studio + Sample Corpus

Build the sample index:

```bash
uv run python -m ingest.build_index --input-dir sample_data/plaintext --db data/index/oracle-mac.db
```

Run preflight:

```bash
uv run python -m scripts.mac_preflight --config config/oracle.mac.sim.yaml
```

Start the simulated console:

```bash
DELPHI_CONFIG=config/oracle.mac.sim.yaml uv run python -m bot.dev_console
```

Smoke tests:

- `how do i purify water`
- `/public how do i purify water`
- `where`

Expected results:

- direct `ask` produces a bounded reply
- public traffic is ignored
- `where` produces a text confirmation plus a simulated private position packet
- if LM Studio is down or the model id is wrong, Delphi-42 degrades to deterministic summaries

## Stage B: Real `.zim` Validation

Copy one real archive into the local ZIM directory:

```bash
cp /path/to/wikipedia_en_medicine_maxi_2023-12.zim data/library/zim/
```

Enable runtime fallback in [`config/oracle.mac.sim.yaml`](../../config/oracle.mac.sim.yaml):

- set `knowledge.runtime_zim_fallback_enabled: true`

Validate direct runtime `.zim` fallback first by keeping the sample-only SQLite index and rerunning preflight:

```bash
uv run python -m scripts.mac_preflight --config config/oracle.mac.sim.yaml
```

Run the simulated console again and ask a question that is not answered by `sample_data/plaintext` but is likely covered by the allowlisted archive. That should force:

- SQLite miss
- bounded runtime `.zim` lookup
- LM Studio or deterministic answer formatting over `.zim`-derived chunks

Then validate the ingest path explicitly:

```bash
uv run python -m ingest.extract_zim --zim-dir data/library/zim --output-dir data/library/plaintext --allowlist wikipedia_en_medicine_maxi_2023-12.zim
uv run python -m ingest.build_index --input-dir data/library/plaintext --db data/index/oracle-mac-zim.db
```

Expected results:

- `extract_zim` writes normalized plaintext under `data/library/plaintext`
- the extracted archive can be indexed into a second SQLite database
- runtime `.zim` fallback works even before you switch the main runtime to the extracted index

## Stage C: Supervised Live T114 Over USB

1. Attach the T114 to the Mac over USB.
2. List visible serial devices:

```bash
uv run python -m scripts.mac_preflight --config config/oracle.mac.live.yaml
```

The first live preflight run will usually fail until you replace the placeholder device path. Use the listed `/dev/cu.usb*` or `/dev/tty.usb*` values to choose the correct device.

3. Edit [`config/oracle.mac.live.yaml`](../../config/oracle.mac.live.yaml):
   - replace `radio.device` with the actual `/dev/cu.usbmodem...` or `/dev/tty.usb...` path
   - if you already enabled `.zim` fallback in the simulated config, mirror that change here if you want the same retrieval behavior live

4. Re-run preflight:

```bash
uv run python -m scripts.mac_preflight --config config/oracle.mac.live.yaml
```

5. Only continue if preflight exits successfully, then start the live bot:

```bash
DELPHI_CONFIG=config/oracle.mac.live.yaml uv run python -m bot.oracle_bot
```

6. Use a second Meshtastic client, such as another node or the phone app, to send DMs to the Mac-attached T114.

Expected results:

- Delphi-42 opens the configured serial device successfully
- public messages are ignored
- direct messages receive replies over the live mesh path
- `where`/`pos` sends a private position packet when the local node has a valid fix
- `where`/`pos` returns `Position fix unavailable right now.` and stays alive when the local node has no valid fix
- temporary transport faults trigger reconnect attempts on the configured serial path; if macOS re-enumerates the T114 under a different path, rerun preflight, update the config if needed, and restart the bot

## Optional Kiwix

If you want browse testing on the same Mac, run Kiwix separately:

```bash
docker compose -f compose.yaml up kiwix
```

Kiwix is browse-only for this lane. It is not required for answer generation.
