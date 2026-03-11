# Service Operations

- Purpose: Define day-to-day operational procedures for Delphi-42 services.
- Audience: Operators and on-call maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: deployment_runbook.md, backup_recovery_and_upgrade.md, ../../systemd/oracle-bot.service
- Exit Criteria: Routine service starts, stops, validation, and health checks are documented.

## Core Services

- `oracle-bot.service`: long-running question-answer service
- `oracle-core.service`: oneshot or scheduled index rebuild
- hotspot and archive services managed by the host

## Daily Operator Tasks

- confirm services are active after reboot
- confirm storage mount is present
- check index age and corpus freshness
- check available disk space
- review privacy-safe logs for errors

## Standard Commands

```bash
systemctl status oracle-bot
systemctl start oracle-bot
systemctl restart oracle-bot
systemctl start oracle-core
journalctl -u oracle-bot -n 100
```

## Service Health Indicators

- bot process starts without config or import errors
- radio path resolves correctly
- index file exists and matches configured location
- hotspot archive responds locally
- restart behavior is clean after service or host reboot
