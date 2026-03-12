# Requirements Traceability

- Purpose: Map project requirements and non-functional targets to implementing docs, tests, and evidence.
- Audience: QA, engineering, and project leads.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: ../overview/non_functional_requirements.md, test_matrix.md, ../project/execution_plan.md
- Exit Criteria: Every critical requirement and NFR is traceable to planned verification and ownership.

## Scope

This traceability map covers Prototype v1 requirements that must be implemented and verified before field deployment.

## Test Levels

- unit
- integration
- system
- field

## Environments

- local dev
- Pi bench
- field site

## Fixtures

- representative DM prompts
- curated corpus
- prototype hardware node
- current config snapshot

## Acceptance Criteria

- every NFR row has one or more matrix references
- critical functional requirements map to both implementation docs and test evidence

## Evidence

Evidence should be linked through the test matrix, release checklist, or field acceptance packet.

## Traceability Matrix

| Requirement | Source | Implementation Docs | Test Coverage |
| --- | --- | --- | --- |
| FR-001 Private DM question answering | Project brief | `architecture/runtime_flows.md`, `ai/retrieval_and_response_policy.md` | TM-001, TM-004, TM-012 |
| FR-002 Private location sharing | Project brief | `architecture/interfaces_and_config.md`, `operations/agentic_oracle_sop.md` | TM-003, TM-012 |
| FR-003 Offline hotspot archive | Project brief | `hardware/node_topology.md`, `operations/deployment_runbook.md` | TM-008, TM-012 |
| NFR-001 Offline operation | NFR doc | `operations/deployment_runbook.md`, `project/adrs/0003-hotspot-and-local-archive-stack.md` | TM-005, TM-008, TM-012 |
| NFR-002 Privacy | NFR doc | `ai/retrieval_and_response_policy.md`, `operations/incident_response.md` | TM-003, TM-004, TM-011, TM-012 |
| NFR-003 Answer latency | NFR doc | `ai/evaluation_plan.md` | TM-006, TM-012 |
| NFR-004 Response size | NFR doc | `ai/retrieval_and_response_policy.md`, `architecture/runtime_flows.md` | TM-007 |
| NFR-005 Recoverability | NFR doc | `operations/backup_recovery_and_upgrade.md`, `operations/service_operations.md` | TM-009, TM-010, TM-014, TM-015 |
| NFR-008 Power awareness | NFR doc | `hardware/power_thermal_and_enclosure.md` | TM-010, TM-013 |
| NFR-010 Documentation completeness | NFR doc | `project/documentation_governance.md`, `docs/README.md` | completeness review, docs check script |
