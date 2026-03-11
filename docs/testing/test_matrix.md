# Test Matrix

- Purpose: Provide a trackable coverage matrix for Prototype v1 features, risks, and test ownership.
- Audience: QA, engineering, and project leads.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: test_strategy.md, requirements_traceability.md, ../project/execution_plan.md
- Exit Criteria: Each critical capability is mapped to a planned test level, environment, and evidence artifact.

## Scope

This matrix covers the critical functional, operational, and privacy behaviors required for Prototype v1 readiness.

## Test Levels

- Unit
- Integration
- System
- Field

## Environments

- local dev
- Pi bench
- controlled field site

## Fixtures

- demo questions
- curated sample corpus
- example config
- prototype hardware kit

## Acceptance Criteria

- critical rows have an owner and a planned evidence artifact
- no critical row is left without a test level

## Evidence

Evidence references should point to test logs, checklists, or field notes recorded during execution.

## Matrix

| ID | Capability | Level | Environment | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| TM-001 | `help` returns command list | Unit | local dev | Software Lead | `pytest` output |
| TM-002 | plain text is treated as implicit `ask` | Unit | local dev | Software Lead | `pytest` output |
| TM-003 | `where` triggers private position flow only | Integration | local dev | Software Lead | router/service test log |
| TM-004 | public questions are ignored | Integration | local dev | Software Lead | bot integration test |
| TM-005 | index rebuild succeeds from staged corpus | System | Pi bench | AI Lead | index build log |
| TM-006 | retrieval returns relevant top-3 passage | System | Pi bench | AI Lead | evaluation notes |
| TM-007 | answer stays within word budget | Unit | local dev | AI Lead | `pytest` output |
| TM-008 | hotspot archive reachable locally | System | Pi bench | Ops Lead | local access checklist |
| TM-009 | service restarts cleanly after reboot | System | Pi bench | Ops Lead | reboot drill log |
| TM-010 | node survives field power cycle | Field | controlled field site | Hardware Lead | field acceptance note |
| TM-011 | privacy-safe logging behavior | System | Pi bench | Ops Lead | log review |
| TM-012 | end-to-end ask flow over mesh | Field | controlled field site | QA Lead | field acceptance transcript |
