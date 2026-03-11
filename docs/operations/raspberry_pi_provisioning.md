# Raspberry Pi Provisioning

- Purpose: Define the base operating system and host setup steps for a Delphi-42 node.
- Audience: Operators and builders.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: deployment_runbook.md, ../../config/oracle.example.yaml, ../../systemd/
- Exit Criteria: An operator can provision a clean Raspberry Pi host ready for Delphi-42 deployment.

## Host Baseline

- Raspberry Pi OS 64-bit or equivalent Debian-based image
- Python 3.9 or newer
- working USB support for radio and SSD
- persistent mount point for corpus, model, and index data

## Provisioning Steps

1. Flash the base image and boot the Pi.
2. Configure hostname, time zone, locale, and SSH access.
3. Update base packages and install Python, `git`, and service dependencies.
4. Attach and mount the SSD at a stable path.
5. Create the deployment directory, recommended as `/opt/delphi-42`.
6. Copy repo contents or deploy a packaged checkout.
7. Create and activate a virtual environment.
8. Install the project in editable or packaged mode.

## Required Local Services

- `hostapd` and `dnsmasq` or equivalent for hotspot mode
- Kiwix or equivalent archive server
- `systemd` for service supervision

## Provisioning Validation

- Pi boots cleanly
- radio is visible at the expected device path
- SSD mount is persistent after reboot
- Python environment can run `pytest` and local entry points
