# ADR-0005: Power And Storage Design

- Purpose: Record the Prototype v1 baseline for power and storage architecture.
- Audience: Hardware, operations, and project leadership.
- Owner: Hardware Lead
- Status: Accepted with revision
- Last Updated: 2026-03-12
- Dependencies: ../../hardware/bill_of_materials.md, ../../hardware/power_thermal_and_enclosure.md
- Exit Criteria: Prototype v1 has one current power and storage baseline, and any re-opened validation scope is explicit.

## Context

The node must balance compute, storage, and field endurance without overcomplicating the prototype. The first field-power pass used an inverter to preserve the official Pi PSU path, and the second pass moved the 18650 pack into the main field battery role. The project instead wants a split architecture: a normal 12V solar storage system for runtime and a smaller Pi-side UPS layer for hold-up power, RTC, and controlled shutdown behavior.

## Decision

Prototype v1 uses:

- Raspberry Pi 5 with active cooling
- 1 TB external SSD for model, corpus, and index
- high-endurance SD card for the OS
- 120W solar panel as the baseline field recharge source
- external 12V primary battery for field runtime
- solar charge controller sized for the 120W panel and 12V battery
- direct 12V to 5V regulation into the Pi field power path instead of an inverter
- Pi-side UPS layer for RTC, hold-up power, and graceful shutdown behavior

## Consequences

- removes inverter losses and AC conversion from the field path
- allows storage-heavy offline content without relying on SD durability
- keeps the primary battery external and serviceable during Prototype v1
- makes graceful shutdown and low-power automation part of the platform design
- requires explicit validation of charger compatibility, regulator thermals, Pi-side UPS current headroom, and low-voltage cutoff behavior before field release
- does not allow the Pi-side UPS battery to be treated as the main field energy store
