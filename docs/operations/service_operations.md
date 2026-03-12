# Service Operations

- Purpose: Define day-to-day operational procedures for Delphi-42 services.
- Audience: Operators and on-call maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: deployment_runbook.md, backup_recovery_and_upgrade.md, ../../systemd/oracle-bot.service
- Exit Criteria: Routine service starts, stops, validation, and health checks are documented.

## Core Services

- `oracle-bot.service`: long-running question-answer service
- `oracle-core.service`: oneshot or scheduled index rebuild
- `llm-openai-api.service`: AX8850-backed local model service
- hotspot and archive services managed by the host

## Daily Operator Tasks

- confirm services are active after reboot
- confirm storage mount is present
- check index age and corpus freshness
- check available disk space
- check `llm-openai-api` health and visible model list
- review privacy-safe logs for errors
- review low-power events from the battery or charge-controller telemetry path

## Standard Commands

```bash
systemctl status oracle-bot
systemctl status llm-openai-api
systemctl start oracle-bot
systemctl restart oracle-bot
systemctl restart llm-openai-api
systemctl start oracle-core
journalctl -u oracle-bot -n 100
curl http://127.0.0.1:8000/v1/models
```

## Service Health Indicators

- bot process starts without config or import errors
- radio path resolves correctly
- index file exists and matches configured location
- local model service responds and shows the configured model
- hotspot archive responds locally
- restart behavior is clean after service or host reboot
- battery or charge-controller telemetry is visible enough to drive reduced-service mode and graceful shutdown
