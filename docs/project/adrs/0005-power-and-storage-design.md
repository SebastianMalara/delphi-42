# ADR-0005: Power And Storage Design

- Purpose: Record the Prototype v1 baseline for power and storage architecture.
- Audience: Hardware, operations, and project leadership.
- Owner: Hardware Lead
- Status: Accepted with reopened validation
- Last Updated: 2026-03-12
- Dependencies: ../../hardware/bill_of_materials.md, ../../hardware/power_thermal_and_enclosure.md
- Exit Criteria: Prototype v1 has one current power and storage baseline, and any re-opened validation scope is explicit.

## Context

The node must balance compute, storage, and field endurance without overcomplicating the prototype. Earlier iterations experimented with an inverter and then a Pi-side UPS layer, but the v1 accelerator choice changes the constraint set: the M5 PiHat is now the intended power entry point for the Pi plus AX8850 stack. The field design therefore needs a clean upstream PD-fed architecture rather than a Pi-side UPS workaround.

## Decision

Prototype v1 uses:

- Raspberry Pi 5 with active cooling
- M5 AI-8850 kit with the included PiHat as the only supported v1 system power entry
- 1 TB external SSD for model, corpus, and index
- high-endurance SD card for the OS
- 120W solar panel as the baseline field recharge source
- external 12V primary battery for field runtime
- solar charge controller sized for the 120W panel and 12V battery
- upstream 12V to USB-C PD source stage feeding the PiHat directly instead of an inverter or Pi-side UPS
- graceful shutdown and reduced-service behavior driven from upstream battery or charge-controller telemetry

## Consequences

- removes inverter losses and Pi-side UPS complexity from the field path
- allows storage-heavy offline content without relying on SD durability
- forces USB SSD storage because the AX8850 kit occupies the Pi PCIe path
- keeps the primary battery external and serviceable during Prototype v1
- makes graceful shutdown and low-power automation part of the platform design without relying on a Pi-mounted UPS battery
- requires explicit validation of PD source compatibility, enclosure clearance, thermal behavior, and low-voltage cutoff behavior before field release
