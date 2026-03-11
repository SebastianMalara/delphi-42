# ADR-0005: Power And Storage Design

- Purpose: Record the Prototype v1 baseline for power and storage architecture.
- Audience: Hardware, operations, and project leadership.
- Owner: Hardware Lead
- Status: Accepted
- Last Updated: 2026-03-11
- Dependencies: ../../hardware/bill_of_materials.md, ../../hardware/power_thermal_and_enclosure.md
- Exit Criteria: Prototype v1 has one baseline power and storage design suitable for procurement and bench validation.

## Context

The node must balance compute, storage, and field endurance without overcomplicating the prototype.

## Decision

Prototype v1 uses:

- Raspberry Pi 5 with active cooling
- 1 TB external SSD for model, corpus, and index
- high-endurance SD card for the OS
- 12V 40Ah LiFePO4 battery with 100W solar planning baseline

## Consequences

- creates a realistic field-oriented prototype baseline
- allows storage-heavy offline content without relying on SD durability
- requires explicit power and thermal validation before field release
