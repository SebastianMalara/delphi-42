# Power, Thermal, And Enclosure

- Purpose: Capture Prototype v1 power sizing, thermal assumptions, and enclosure requirements.
- Audience: Hardware builders and operators.
- Owner: Hardware Lead
- Status: Revised v1
- Last Updated: 2026-03-12
- Dependencies: node_topology.md, bill_of_materials.md, ../testing/field_acceptance_protocol.md
- Exit Criteria: Power and enclosure decisions are explicit enough to build and validate the node in bench and field environments.

## Power Budget Assumptions

| Subsystem | Typical Load | Peak Load | Notes |
| --- | --- | --- | --- |
| Raspberry Pi 5 16GB | 6W | 12W | Higher under inference or indexing |
| M5 AI-8850 kit | 8W | 11W | Includes AX8850 card and PiHat overhead during local inference |
| Crucial X9 SSD | 1W | 3W | Higher during index rebuild |
| Heltec T114 | 1W | 3W | Depends on transmit duty cycle and GPS use |
| Pi Active Cooler | 1W | 2W | Active cooling assumed |
| Hotspot / WiFi | 1W | 2W | Included in Pi networking load planning |
| PD source and conversion losses | 2W | 4W | Includes field-side PD conversion and cable loss budget |
| Total node estimate | 19W | 37W | Use 20W planning average for the revised field power budget |

## Revised Power Chain

- Bench path: USB-C PD wall charger with at least `9V@3A` into the M5 PiHat.
- Field path: Renogy 120W panel -> Victron SmartSolar MPPT 75/15 -> external 12V primary battery -> inline fuse -> 12V accessory socket / harness -> USB-C PD source stage -> M5 PiHat PD input.
- This revised field path removes inverter losses and Pi-side UPS complexity, while keeping all node power entry at the PiHat as required by the AX8850 kit baseline.

## Field Sizing Guidance

- Daily energy assumption at 20W average: roughly 480Wh/day
- Battery reserve at 12V/42Ah nominal: roughly 504Wh raw, lower after discharge limits and regulator losses
- Solar planning target: 120W panel sized for faster daytime recovery and better weather margin than the earlier 100W baseline
- Resulting Prototype v1 assumption: one-day autonomy is still tight on paper and must be protected by reduced-service mode plus graceful shutdown based on upstream battery or charge-controller telemetry

## Bench vs Field Rollup

- Bench hardware total from the reopened AX8850 BOM: `EUR 779.10`
- Field add-on total from the revised BOM: `EUR 495.08`
- Combined bench-to-field total: `EUR 1,274.18`

## Thermal Guidance

- Use active cooling on the Pi 5.
- Respect the AX8850 card blower intake and outlet clearance.
- Avoid sealing the enclosure without a heat path.
- Keep the 12V primary battery external to the Hammond electronics enclosure.
- Validate thermal stability during index rebuild and model inference, not only idle operation.
- Validate PiHat temperature, AX8850 blower effectiveness, PD charger temperature, and enclosure cable temperature under sustained load before field closure.

## Enclosure Requirements

- Weather-resistant Hammond 1554X2GYCL shell with accessible M20 cable glands
- Internal mounting for Pi, PiHat, AX8850 card, SSD, T114, and PD wiring only; primary battery remains external
- External antenna routing fixed to EU 868 with the SECTRON R36S15 assembly
- Service access for storage swap, SD recovery, power disconnect, and fuse replacement
- Clear labeling for operator-safe maintenance

## Failure Conditions To Test

- thermal throttling during a long `ask` session
- PD negotiation dropping below the PiHat requirement during model load
- connector strain causing radio disconnect
- USB-C PD source stage instability or undervoltage reset during peak Pi plus AX8850 load
- low-power event fails to trigger graceful shutdown or reduced-service mode from upstream battery telemetry
- condensation or inadequate venting after overnight field operation
