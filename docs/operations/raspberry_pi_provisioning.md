# Raspberry Pi Provisioning

- Purpose: Define the base operating system and host setup steps for a Delphi-42 node.
- Audience: Operators and builders.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: deployment_runbook.md, ../../config/oracle.example.yaml, ../../systemd/
- Exit Criteria: An operator can provision a clean Raspberry Pi host ready for Delphi-42 deployment.

## Host Baseline

- Debian 12 arm64
- Python 3.9 or newer
- working USB support for radio and SSD
- persistent mount point for corpus and index data
- M5 StackFlow packages installed from the official `bookworm llm8850` apt repository
- local `llm-openai-api` service running on `127.0.0.1:8000`

## Provisioning Steps

1. Flash a clean Debian 12 arm64 image and boot the Pi.
2. Configure hostname, time zone, locale, and SSH access.
3. Update base packages and install Python, `git`, `curl`, `jq`, and service dependencies.
4. Add the M5 StackFlow apt key and repository:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo wget -qO /etc/apt/keyrings/StackFlow.gpg https://repo.llm.m5stack.com/m5stack-apt-repo/key/StackFlow.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/StackFlow.gpg] https://repo.llm.m5stack.com/m5stack-apt-repo bookworm llm8850" | sudo tee /etc/apt/sources.list.d/StackFlow.list > /dev/null
sudo apt update
sudo apt install -y lib-llm llm-sys llm-llm llm-openai-api llm-model-qwen3-1.7b-int8-ctx-axcl
sudo systemctl restart llm-openai-api
```

5. Attach and mount the SSD at a stable path.
6. Create the deployment directory, recommended as `/opt/delphi-42`.
7. Copy repo contents or deploy a packaged checkout.
8. Create and activate a virtual environment.
9. Install the project in editable or packaged mode with required extras, including `zim` support.
10. Validate the local model service before bot deployment:

```bash
curl http://127.0.0.1:8000/v1/models
```

11. Confirm the expected model ID `qwen3-1.7B-Int8-ctx-axcl` is visible, then run a sample `chat/completions` call.

## Required Local Services

- `hostapd` and `dnsmasq` or equivalent for hotspot mode
- Kiwix or equivalent archive server
- `systemd` for service supervision
- `llm-openai-api` for local AX8850-backed generation

## Provisioning Validation

- Pi boots cleanly
- radio is visible at the expected device path
- SSD mount is persistent after reboot
- Python environment can run `pytest` and local entry points
- the Python environment can import `libzim` before runtime `.zim` fallback is enabled
- `curl http://127.0.0.1:8000/v1/models` succeeds locally
- the expected model is visible to the local API
- a sample local `chat/completions` call succeeds before `oracle-bot` is started
