# Power, Thermal, And Enclosure

- Purpose: Capture Prototype v1 power sizing, thermal assumptions, and enclosure requirements.
- Audience: Hardware builders and operators.
- Owner: Hardware Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: node_topology.md, bill_of_materials.md, ../testing/field_acceptance_protocol.md
- Exit Criteria: Power and enclosure decisions are explicit enough to build and validate the node in bench and field environments.

## Power Budget Assumptions

| Subsystem | Typical Load | Peak Load | Notes |
| --- | --- | --- | --- |
| Raspberry Pi 5 | 6W | 12W | Higher under inference or indexing |
| External SSD | 1W | 3W | Higher during index rebuild |
| Meshtastic radio | 1W | 3W | Depends on radio and transmit duty cycle |
| Cooling | 1W | 2W | Active cooling assumed |
| Hotspot / WiFi | 1W | 2W | Included in Pi networking load planning |
| Total node estimate | 10W | 22W | Use 15W planning average for field sizing |

## Field Sizing Guidance

- Daily energy assumption at 15W average: roughly 360Wh/day
- Battery reserve at 12V/40Ah nominal: roughly 480Wh raw, lower after usable-depth planning
- Solar planning target: 100W panel sized for recovery and cloudy-day margin in Prototype v1

## Thermal Guidance

- Use active cooling on the Pi 5.
- Avoid sealing the enclosure without a heat path.
- Separate battery heat and compute heat where possible.
- Validate thermal stability during index rebuild and model inference, not only idle operation.

## Enclosure Requirements

- Weather-resistant shell with accessible cable glands
- Mounting strategy for Pi, SSD, battery, and radio
- External antenna routing compatible with the chosen band
- Service access for storage swap, SD recovery, and power disconnect
- Clear labeling for operator-safe maintenance

## Failure Conditions To Test

- thermal throttling during a long `ask` session
- brownout during model load
- connector strain causing radio disconnect
- condensation or inadequate venting after overnight field operation
