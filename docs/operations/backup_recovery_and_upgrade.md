# Backup, Recovery, And Upgrade

- Purpose: Define what state must be backed up, how to recover a failed node, and how to upgrade safely.
- Audience: Operators and maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: deployment_runbook.md, service_operations.md, ../project/risk_register.md
- Exit Criteria: Operators can preserve essential state and restore service with bounded guesswork.

## What To Back Up

- `config/oracle.yaml`
- operator notes and deployment metadata
- curated plaintext corpus or a reproducible manifest of it
- benchmark and field-evaluation artifacts

Generated artifacts such as the SQLite index can be rebuilt and do not need to be the primary backup target if source corpus and config are preserved.

## Recovery Priorities

1. restore power and host boot
2. verify SSD mount and radio connectivity
3. restore config
4. restage corpus if needed
5. rebuild index
6. start services
7. validate `help`, `ask`, and `where`

## Upgrade Policy

- upgrade software in a bench environment first
- snapshot config before changing runtime dependencies
- keep one known-good SD image and one known-good SSD copy
- do not combine corpus refresh, model change, and service refactor in one field upgrade
