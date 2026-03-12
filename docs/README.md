# Delphi-42 Documentation

- Purpose: Provide the source-of-truth documentation set for building, testing, and operating Delphi-42.
- Audience: Engineering, operations, and project leads.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: README.md, config/oracle.example.yaml, systemd/, bot/, core/, ingest/
- Exit Criteria: A new engineer or operator can navigate from this index to all required build, run, and validation documents.

## How To Use This Suite

Read the docs in this order if you are new to the project:

1. [`overview/project_brief.md`](overview/project_brief.md)
2. [`overview/scope_and_non_goals.md`](overview/scope_and_non_goals.md)
3. [`architecture/system_context.md`](architecture/system_context.md)
4. [`hardware/node_topology.md`](hardware/node_topology.md)
5. [`ai/retrieval_and_response_policy.md`](ai/retrieval_and_response_policy.md)
6. [`operations/deployment_runbook.md`](operations/deployment_runbook.md)
7. [`testing/test_strategy.md`](testing/test_strategy.md)
8. [`project/execution_plan.md`](project/execution_plan.md)

## Documentation Taxonomy

### Overview

- [`overview/project_brief.md`](overview/project_brief.md): mission, stakeholders, and prototype objective.
- [`overview/user_journeys.md`](overview/user_journeys.md): builder, operator, and field-user journeys.
- [`overview/scope_and_non_goals.md`](overview/scope_and_non_goals.md): scope boundaries for Prototype v1.
- [`overview/non_functional_requirements.md`](overview/non_functional_requirements.md): target reliability, privacy, latency, power, and maintainability.
- [`overview/glossary.md`](overview/glossary.md): shared vocabulary.

### Architecture

- [`architecture/system_context.md`](architecture/system_context.md): external actors, deployment context, and trust boundaries.
- [`architecture/software_architecture.md`](architecture/software_architecture.md): module boundaries and runtime composition.
- [`architecture/runtime_flows.md`](architecture/runtime_flows.md): message, retrieval, and ingest sequence flows.
- [`architecture/interfaces_and_config.md`](architecture/interfaces_and_config.md): command, config, service, and file interfaces.

### Hardware

- [`hardware/node_topology.md`](hardware/node_topology.md): physical architecture.
- [`hardware/bill_of_materials.md`](hardware/bill_of_materials.md): prototype bill of materials.
- [`hardware/power_thermal_and_enclosure.md`](hardware/power_thermal_and_enclosure.md): power, cooling, and field packaging.
- [`hardware/assembly_and_field_packaging.md`](hardware/assembly_and_field_packaging.md): assembly and deployment preparation.

### AI

- [`ai/corpus_strategy.md`](ai/corpus_strategy.md): source strategy and content priorities.
- [`ai/ingestion_and_indexing.md`](ai/ingestion_and_indexing.md): extract, chunk, and index pipeline.
- [`ai/retrieval_and_response_policy.md`](ai/retrieval_and_response_policy.md): retrieval-first answer policy.
- [`ai/evaluation_plan.md`](ai/evaluation_plan.md): qualitative and quantitative validation.

### Operations

- [`operations/raspberry_pi_provisioning.md`](operations/raspberry_pi_provisioning.md): base Pi setup.
- [`operations/deployment_runbook.md`](operations/deployment_runbook.md): deploy the full node.
- [`operations/service_operations.md`](operations/service_operations.md): operating the services day to day.
- [`operations/backup_recovery_and_upgrade.md`](operations/backup_recovery_and_upgrade.md): persistence and update procedures.
- [`operations/incident_response.md`](operations/incident_response.md): operational fault handling.
- [`operations/agentic_oracle_sop.md`](operations/agentic_oracle_sop.md): runtime SOP for the oracle behavior.

### Testing

- [`testing/test_strategy.md`](testing/test_strategy.md): test levels and acceptance model.
- [`testing/test_matrix.md`](testing/test_matrix.md): trackable test coverage matrix.
- [`testing/field_acceptance_protocol.md`](testing/field_acceptance_protocol.md): field validation procedure.
- [`testing/release_readiness.md`](testing/release_readiness.md): go/no-go checklist.
- [`testing/requirements_traceability.md`](testing/requirements_traceability.md): requirement-to-test mapping.

### Project

- [`project/execution_plan.md`](project/execution_plan.md): tracked delivery plan.
- [`project/risk_register.md`](project/risk_register.md): risks, mitigations, and owners.
- [`project/contributing.md`](project/contributing.md): expected workflow for contributors.
- [`project/documentation_governance.md`](project/documentation_governance.md): document structure, review, and quality checks.
- [`project/reviews/hardware_bom_signoff.md`](project/reviews/hardware_bom_signoff.md): milestone review and current signoff state for the hardware BOM.
- [`project/adrs/README.md`](project/adrs/README.md): architectural decision records.

## Document Standards

Every controlled Markdown document in `docs/` must include:

- purpose
- audience
- owner
- status
- last updated
- dependencies
- exit criteria

Every architecture document must also include:

- context
- components
- interfaces
- data/control flow
- failure modes
- security/privacy constraints

Every testing document must also include:

- scope
- test levels
- environments
- fixtures
- acceptance criteria
- evidence

## Validation

Run the repo-local documentation checks before marking doc work complete:

```bash
python scripts/check_docs.py
```

Use [`project/documentation_governance.md`](project/documentation_governance.md) for policy and review cadence.
