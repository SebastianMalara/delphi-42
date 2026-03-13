# Test Matrix

- Purpose: Provide a trackable coverage matrix for Prototype v1 features, risks, and test ownership.
- Audience: QA, engineering, and project leads.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-12
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
- prototype hardware kit with Raspberry Pi 5, M5 AX8850 kit, and Heltec T114

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
| TM-007 | answer bundle stays within deterministic packet limits | Unit | local dev | AI Lead | `pytest` output |
| TM-008 | hotspot archive reachable locally | System | Pi bench | Ops Lead | local access checklist |
| TM-009 | service restarts cleanly after reboot | System | Pi bench | Ops Lead | reboot drill log |
| TM-010 | node survives field power cycle | Field | controlled field site | Hardware Lead | field acceptance note |
| TM-011 | privacy-safe logging behavior | System | Pi bench | Ops Lead | log review |
| TM-012 | end-to-end ask flow over mesh | Field | controlled field site | QA Lead | field acceptance transcript |
| TM-013 | low-power event triggers graceful shutdown or reduced-service mode | System | Pi bench | Ops Lead | power management test note |
| TM-014 | Kiwix/ZIM refresh followed by index rebuild preserves answerability | System | Pi bench | Ops Lead | upgrade drill note |
| TM-015 | StackFlow `/v1/models` preflight passes before `oracle-bot` start | Integration | Pi bench | Ops Lead | provisioning validation log |
| TM-016 | missing local model service or model package degrades to deterministic answers | Unit | local dev | AI Lead | `pytest` output |
| TM-017 | runtime `.zim` fallback triggers only after SQLite misses and stays bounded to the allowlist | Unit | local dev | AI Lead | `pytest` output |
| TM-018 | `extract_zim` writes normalized plaintext from allowlisted archives | Unit | local dev | AI Lead | `pytest` output |
| TM-019 | `compose.dev` starts `oracle-app`, `oracle-indexer`, and `mock-openai` with a working sample corpus | Integration | local dev | Software Lead | compose smoke log |
| TM-020 | `oracle-app` in Pi Compose can reach host `llm-openai-api` through the configured host alias | System | Pi bench | Ops Lead | container networking note |
| TM-021 | simulated radio console can exercise `help`, `where`, and `ask` without hardware | Integration | local dev | Software Lead | console smoke note |
| TM-022 | Mac preflight succeeds against LM Studio, the configured model id, and a real completion probe | Integration | local dev | Software Lead | preflight output |
| TM-023 | Mac-native simulated lane answers with LM Studio over the OpenAI-compatible API | Integration | local dev | AI Lead | M1 quickstart smoke note |
| TM-024 | Mac-native runtime `.zim` fallback works on a real allowlisted archive after a forced SQLite miss | System | local dev | AI Lead | M1 `.zim` validation note |
| TM-025 | Mac-native supervised live T114 lane exchanges DMs over USB serial, ignores public traffic, and survives no-fix position requests | System | local dev | Software Lead | M1 live-mesh note |
