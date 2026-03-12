# Service Operations

- Purpose: Define day-to-day operational procedures for Delphi-42 services.
- Audience: Operators and on-call maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: deployment_runbook.md, backup_recovery_and_upgrade.md, container_workflows.md, ../../systemd/oracle-bot.service
- Exit Criteria: Routine service starts, stops, validation, and health checks are documented.

## Core Services

- `oracle-app`: long-running question-answer container
- `oracle-indexer`: oneshot or scheduled index rebuild container
- `llm-openai-api.service`: AX8850-backed local model service
- `kiwix`: local archive container
- legacy `systemd` wrappers remain available for non-container Pi deployments

## Daily Operator Tasks

- confirm services are active after reboot
- confirm storage mount is present
- check index age and corpus freshness
- check available disk space
- check `llm-openai-api` health and visible model list
- check container health and restart state
- review privacy-safe logs for errors
- review low-power events from the battery or charge-controller telemetry path

## Standard Commands

```bash
docker compose -f compose.yaml -f compose.pi.yaml ps
docker compose -f compose.yaml -f compose.pi.yaml logs oracle-app --tail=100
docker compose -f compose.yaml -f compose.pi.yaml restart oracle-app
docker compose -f compose.yaml -f compose.pi.yaml run --rm oracle-indexer
systemctl status llm-openai-api
systemctl restart llm-openai-api
curl http://127.0.0.1:8000/v1/models
```

## Service Health Indicators

- app container starts without config or import errors
- radio path resolves correctly
- index file exists and matches configured location
- host-local model service responds and shows the configured model
- hotspot archive responds locally
- restart behavior is clean after container or host reboot
- battery or charge-controller telemetry is visible enough to drive reduced-service mode and graceful shutdown
