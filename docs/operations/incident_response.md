# Incident Response

- Purpose: Provide initial response playbooks for common operational failures.
- Audience: Operators and maintainers.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: service_operations.md, backup_recovery_and_upgrade.md, ../testing/field_acceptance_protocol.md
- Exit Criteria: Common incidents have a documented triage path, owner, and recovery approach.

## Incident Classes

| ID | Incident | Initial Action |
| --- | --- | --- |
| INC-001 | Bot service down | Restart service, inspect logs, verify config path |
| INC-002 | Radio unavailable | Check USB path, cable, power, and radio health |
| INC-003 | Empty or missing index | Verify corpus mount, rebuild index, re-run sample query |
| INC-004 | Hotspot unavailable | Verify hotspot services and network config |
| INC-005 | Thermal or power instability | Reduce load, inspect cooling and battery path |
| INC-006 | Privacy policy breach risk | Stop service, preserve logs, review broadcast and routing config |

## Triage Rules

- preserve operator safety first
- stabilize power before debugging software
- do not leave the node answering publicly while privacy is uncertain
- document time, symptoms, actions, and outcome after each incident

## Escalation

- privacy incidents escalate to project lead immediately
- repeated power failures escalate to hardware lead
- repeated retrieval failures escalate to AI lead
