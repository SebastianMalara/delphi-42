# Test Strategy

- Purpose: Define the overall verification approach for Delphi-42 across unit, integration, system, and field levels.
- Audience: Engineering, QA, and operations.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: test_matrix.md, field_acceptance_protocol.md, requirements_traceability.md
- Exit Criteria: The team can choose appropriate test levels, environments, and evidence for every planned subsystem change.

## Scope

The strategy covers:

- command parsing and privacy behavior
- retrieval and answer policy
- ingest and indexing
- service startup and recovery
- hotspot/archive availability
- field validation on prototype hardware

## Test Levels

- Unit: parser, chunker, service policy, config loading, fallback logic
- Integration: bot-to-core flow, ingest-to-index flow, config-to-service flow
- System: full node on Raspberry Pi with radio, index, model, and hotspot services
- Field: over-the-air mesh interaction and on-site hotspot access

## Environments

- developer laptop for unit and fast integration tests
- Raspberry Pi bench node for system validation
- field deployment environment for radio, power, and hotspot behavior

## Fixtures

- representative direct-message commands
- curated plaintext corpus for deterministic retrieval tests
- example runtime config
- prototype hardware kit with radio, SSD, battery, and hotspot stack

## Acceptance Criteria

- every critical user flow has at least one automated test or field protocol
- every NFR maps to a verification path
- privacy and public-channel guardrails are tested before field deployment

## Evidence

- `pytest` output
- documented benchmark prompts and expected outcomes
- service logs with sensitive data redacted
- signed-off field protocol results
