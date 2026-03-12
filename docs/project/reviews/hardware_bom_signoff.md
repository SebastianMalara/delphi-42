# Hardware BOM Signoff

- Purpose: Record the current review and signoff state for the Prototype v1 hardware BOM.
- Audience: Project leads, builders, and purchasers.
- Owner: Hardware Lead
- Status: Reopened for AX8850 re-baseline
- Last Updated: 2026-03-12
- Dependencies: ../../hardware/bill_of_materials.md, ../../project/execution_plan.md
- Exit Criteria: The BOM has a named reviewer, review date, approval status, and explicit notes for any reopened scope.

## Review Record

| Field | Value |
| --- | --- |
| Reviewer | Codex technical procurement review |
| Review Date | 2026-03-12 |
| Approval Status | Reopened; AX8850-based bench and field packages require refreshed signoff |
| Reviewed Scope | Main-node BOM, AX8850 accelerator choice, EU 868 radio choice, and revised PiHat-fed field power chain |
| Governing ADR | ADR-0005 |

## Review Outcome

- Preferred Pi-attached radio remains the Heltec T114 Rev 2 GPS variant for EU 868.
- SenseCAP Solar Node P1 remains optional and is explicitly not the primary oracle radio.
- Prototype v1 now assumes the M5 AI-8850 kit as the only supported local-generation hardware path.
- The field power chain is no longer the earlier inverter or Pi-side UPS design; it is under re-review around a 12V primary storage battery and an upstream USB-C PD source stage feeding the M5 PiHat.

## Follow-Up Required

- Confirm measured bench draw against the revised power assumptions in `docs/hardware/power_thermal_and_enclosure.md`.
- Confirm the selected charge controller matches the final 120W panel and 12V battery pairing.
- Confirm PD source stability, PiHat temperature, and low-voltage cutoff behavior under sustained Pi plus AX8850 load.
- Confirm graceful shutdown or reduced-service behavior when upstream battery or charge-controller telemetry indicates low power.
- Confirm T114 USB reconnect behavior during Step 2 bench assembly.
- Confirm field antenna placement and enclosure routing before outdoor deployment.
