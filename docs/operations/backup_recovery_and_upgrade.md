# Backup, Recovery, And Upgrade

- Purpose: Define what state must be backed up, how to recover a failed node, and how to upgrade safely.
- Audience: Operators and maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: deployment_runbook.md, service_operations.md, ../project/risk_register.md
- Exit Criteria: Operators can preserve essential state and restore service with bounded guesswork.

## What To Back Up

- site-local config derived from `config/oracle.pi.yaml`
- `/etc/apt/sources.list.d/StackFlow.list`
- installed StackFlow package manifest
- operator notes and deployment metadata
- curated plaintext corpus or a reproducible manifest of it
- Kiwix ZIM manifest and local archive inventory
- Compose overrides or environment files used on the Pi
- benchmark and field-evaluation artifacts

Generated artifacts such as the SQLite index can be rebuilt and do not need to be the primary backup target if source corpus, config, and StackFlow package state are preserved.

## Recovery Priorities

1. restore power and host boot
2. verify SSD mount and radio connectivity
3. restore StackFlow apt source and reinstall `lib-llm`, `llm-sys`, `llm-llm`, `llm-openai-api`, and the default model package
4. verify `curl http://127.0.0.1:8000/v1/models` and the configured model ID
5. restore config
6. restore or restage Kiwix ZIM content if needed
7. restage curated corpus or derived extracts if needed
8. rebuild index
9. start containers and host services
10. validate `help`, `ask`, `where`, and hotspot archive access

## Upgrade Policy

- upgrade software in a bench environment first
- snapshot config before changing runtime dependencies
- keep one known-good SD image and one known-good SSD copy
- do not combine corpus refresh, StackFlow model change, and service refactor in one field upgrade
- Kiwix software and ZIM content can be refreshed after initial install; the safe path is replace content, validate Kiwix locally, rebuild derived plaintext and index, then validate representative `ask` queries
- Delphi-42 assumes self-managed Kiwix software and content refresh, not a recurring payment model for standard software or ZIM updates
