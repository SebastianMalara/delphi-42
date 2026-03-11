# Field Acceptance Protocol

- Purpose: Define the step-by-step field validation procedure for a Prototype v1 node.
- Audience: QA, operators, and project leadership.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: test_strategy.md, ../operations/deployment_runbook.md, ../hardware/power_thermal_and_enclosure.md
- Exit Criteria: The team can execute a repeatable field trial and capture enough evidence to decide readiness.

## Scope

This protocol validates the complete user and operator experience on actual prototype hardware outside the development desk environment.

## Test Levels

- System
- Field

## Environments

- outdoor or radio-representative test site
- bench fallback station for recovery

## Fixtures

- one fully provisioned node
- one or more Meshtastic client devices
- representative question list
- power kit matching the target deployment
- hotspot client device

## Acceptance Criteria

- DM `help`, `ask`, and `where` succeed
- public channel receives only expected oracle broadcasts
- hotspot archive is reachable on-site
- node remains stable through a power-cycle drill
- operator can recover service using repo runbooks

## Evidence

- timestamped operator checklist
- redacted radio transcript
- power and thermal observations
- incident notes if failures occur

## Procedure

1. Confirm battery and enclosure state before power-on.
2. Start the node and wait for services to stabilize.
3. Send `help`, `ask`, and `where` from a test device.
4. Verify the answer path, response time, and private position behavior.
5. Join the hotspot and verify archive access.
6. Perform one controlled service restart and one power-cycle recovery.
7. Record anomalies, operator interventions, and final status.
