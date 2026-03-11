# Hardware BOM Signoff

- Purpose: Record the review and signoff evidence for the frozen Prototype v1 hardware BOM.
- Audience: Project leads, builders, and purchasers.
- Owner: Hardware Lead
- Status: Approved baseline
- Last Updated: 2026-03-11
- Dependencies: ../../hardware/bill_of_materials.md, ../../project/execution_plan.md
- Exit Criteria: The BOM has a named reviewer, review date, approval status, and bounded follow-up notes.

## Review Record

| Field | Value |
| --- | --- |
| Reviewer | Codex technical procurement review |
| Review Date | 2026-03-11 |
| Approval Status | Approved as the Prototype v1 procurement baseline |
| Reviewed Scope | Main-node BOM, bench-to-field rollups, EU 868 radio choice, and field power chain |
| Governing ADR | ADR-0005 |

## Review Outcome

- Preferred Pi-attached radio is frozen to the Heltec T114 Rev 2 GPS variant for EU 868.
- SenseCAP Solar Node P1 remains optional and is explicitly not the primary oracle radio.
- The first field power path is frozen around the official Pi PSU plus a small inverter, avoiding unresolved USB-C PD converter choices in Prototype v1.
- Remaining uncertainty is limited to validation outcomes, not component selection.

## Follow-Up Required

- Confirm measured bench draw against the power assumptions in `docs/hardware/power_thermal_and_enclosure.md`.
- Confirm T114 USB reconnect behavior during Step 2 bench assembly.
- Confirm field antenna placement and enclosure routing before outdoor deployment.
