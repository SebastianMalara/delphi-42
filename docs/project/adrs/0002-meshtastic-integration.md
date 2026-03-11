# ADR-0002: Meshtastic Integration Approach

- Purpose: Record the Prototype v1 decision for connecting Delphi-42 to the mesh.
- Audience: Engineering and operations.
- Owner: Software Lead
- Status: Accepted
- Last Updated: 2026-03-11
- Dependencies: ../../architecture/software_architecture.md, ../../operations/deployment_runbook.md
- Exit Criteria: The project has one supported baseline radio integration approach for Prototype v1.

## Context

The node needs stable private-message handling with minimal operational complexity and straightforward Python integration.

## Decision

Prototype v1 integrates with Meshtastic through the Python client over a locally attached USB-accessible radio device. One bot process owns the radio connection.

## Consequences

- matches the Python-first repository structure
- keeps deployment simple on Raspberry Pi
- constrains Prototype v1 to one radio session owner
- requires reconnect handling and device-path validation
