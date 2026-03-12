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
| Crucial X9 SSD | 1W | 3W | Higher during index rebuild |
| Heltec T114 | 1W | 3W | Depends on transmit duty cycle and GPS use |
| Pi Active Cooler | 1W | 2W | Active cooling assumed |
| Hotspot / WiFi | 1W | 2W | Included in Pi networking load planning |
| Regulator losses | 1W | 3W | Direct-DC conversion cost for the 5V field path |
| Pi-side UPS overhead | 1W | 3W | Depends on UPS battery charge state and event signaling |
| Total node estimate | 11W | 28W | Use 16W planning average for the revised field power budget |

## Revised Power Chain

- Bench path: official 27W Raspberry Pi USB-C PSU from mains AC.
- Field path: Renogy 120W panel -> Victron SmartSolar MPPT 75/15 -> external 12V primary battery -> inline fuse -> Pololu D42V55F5 -> Pi-side UPS -> Pi power rail.
- This revised field path removes inverter losses and extra AC conversion, while adding a Pi-side hold-up layer for graceful shutdown and low-power automation.

## Field Sizing Guidance

- Daily energy assumption at 16W average: roughly 384Wh/day
- Battery reserve at 12V/42Ah nominal: roughly 504Wh raw, lower after discharge limits and regulator losses
- Solar planning target: 120W panel sized for faster daytime recovery and better weather margin than the earlier 100W baseline
- Resulting Prototype v1 assumption: one-day autonomy can be approached on paper only with controlled duty cycle and low-power policy; graceful shutdown remains the protection mechanism, not a substitute for primary storage sizing

## Bench vs Field Rollup

- Bench hardware total from the frozen BOM: `EUR 436.55`
- Field add-on total from the revised BOM: `EUR 534.84`
- Combined bench-to-field total: `EUR 971.39`

## Thermal Guidance

- Use active cooling on the Pi 5.
- Avoid sealing the enclosure without a heat path.
- Keep the 12V primary battery external to the Hammond electronics enclosure.
- Validate thermal stability during index rebuild and model inference, not only idle operation.
- Validate regulator temperature, Pi-side UPS temperature, and enclosure cable temperature under sustained load before field closure.

## Enclosure Requirements

- Weather-resistant Hammond 1554X2GYCL shell with accessible M20 cable glands
- Internal mounting for Pi, SSD, T114, regulator, and Pi-side UPS only; primary battery remains external
- External antenna routing fixed to EU 868 with the SECTRON R36S15 assembly
- Service access for storage swap, SD recovery, power disconnect, and fuse replacement
- Clear labeling for operator-safe maintenance

## Failure Conditions To Test

- thermal throttling during a long `ask` session
- brownout during model load
- connector strain causing radio disconnect
- regulator instability or undervoltage reset during peak Pi load
- Pi-side UPS current ceiling causing instability under combined Pi, SSD, and radio load
- low-power event fails to trigger graceful shutdown or reduced-service mode
- condensation or inadequate venting after overnight field operation
