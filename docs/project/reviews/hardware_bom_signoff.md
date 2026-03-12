# Hardware BOM Signoff

- Purpose: Record the current review and signoff state for the Prototype v1 hardware BOM.
- Audience: Project leads, builders, and purchasers.
- Owner: Hardware Lead
- Status: Superseded by field power revision
- Last Updated: 2026-03-12
- Dependencies: ../../hardware/bill_of_materials.md, ../../project/execution_plan.md
- Exit Criteria: The BOM has a named reviewer, review date, approval status, and explicit notes for any reopened scope.

## Review Record

| Field | Value |
| --- | --- |
| Reviewer | Codex technical procurement review |
| Review Date | 2026-03-12 |
| Approval Status | Bench package approved; field power package reopened for revision |
| Reviewed Scope | Main-node BOM, bench package, EU 868 radio choice, and revised field power chain |
| Governing ADR | ADR-0005 |

## Review Outcome

- Preferred Pi-attached radio remains the Heltec T114 Rev 2 GPS variant for EU 868.
- SenseCAP Solar Node P1 remains optional and is explicitly not the primary oracle radio.
- The bench package remains approved and orderable as documented in the current BOM.
- The field power chain is no longer the earlier inverter design; it is under re-review around a 12V primary storage battery, 12V to 5V regulation, and a Pi-side UPS architecture.

## Follow-Up Required

- Confirm measured bench draw against the revised power assumptions in `docs/hardware/power_thermal_and_enclosure.md`.
- Confirm the selected charge controller matches the final 120W panel and 12V battery pairing.
- Confirm regulator temperature, Pi-side UPS current headroom, and low-voltage cutoff behavior under sustained Pi load.
- Confirm graceful shutdown or reduced-service behavior when the Pi-side UPS signals low battery.
- Confirm T114 USB reconnect behavior during Step 2 bench assembly.
- Confirm field antenna placement and enclosure routing before outdoor deployment.
