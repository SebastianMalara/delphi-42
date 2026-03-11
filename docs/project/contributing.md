# Contributing

- Purpose: Define the expected workflow for contributing code, documentation, and architectural changes to Delphi-42.
- Audience: Contributors and maintainers.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: documentation_governance.md, execution_plan.md, ../../README.md
- Exit Criteria: Contributors can make changes while preserving documentation quality, test coverage, and decision traceability.

## Workflow Expectations

1. Read the relevant docs before changing the subsystem.
2. Update implementation and documentation in the same change when behavior changes.
3. Add or update tests for behavior changes.
4. Capture major design decisions as ADRs before or alongside implementation.

## Pull Request Expectations

- explain the subsystem changed
- reference the relevant execution-plan milestone or risk
- include test evidence
- include doc updates when interfaces, runbooks, or scope change

## When To Write An ADR

- new runtime backend
- new operator-visible workflow
- new storage or deployment pattern
- any change that affects privacy, power, or field behavior

## Minimum Completion Checks

- `pytest`
- `python scripts/check_docs.py`
- manual review of any new Mermaid diagrams
