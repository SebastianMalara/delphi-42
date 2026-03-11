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
| Raspberry Pi 5 16GB | 6W | 12W | Higher under inference or indexing |
| Crucial X9 SSD | 1W | 3W | Higher during index rebuild |
| Heltec T114 | 1W | 3W | Depends on transmit duty cycle and GPS use |
| Pi Active Cooler | 1W | 2W | Active cooling assumed |
| Hotspot / WiFi | 1W | 2W | Included in Pi networking load planning |
| Inverter overhead | 2W | 5W | Prototype simplification cost for retaining the official Pi PSU |
| Total node estimate | 12W | 27W | Use 17W planning average for the first field power budget |

## Frozen Power Chain

- Bench path: official 27W Raspberry Pi USB-C PSU from mains AC.
- Field path: Renogy 100W panel -> Victron SmartSolar 75/10 -> Accurat T42 12V LiFePO4 -> Victron Phoenix 12/250 pure sine inverter -> official Pi USB-C PSU.
- This field path is intentionally conservative: it preserves known-good Pi power behavior at the cost of inverter losses.

## Field Sizing Guidance

- Daily energy assumption at 17W average: roughly 408Wh/day
- Battery reserve at 12V/40Ah nominal: roughly 480Wh raw, lower after usable-depth planning
- Solar planning target: 100W panel sized for recovery and cloudy-day margin in Prototype v1
- Resulting Prototype v1 assumption: one-day autonomy is plausible on paper, but bench validation of inverter loss and overnight draw is still required

## Bench vs Field Rollup

- Bench hardware total from the frozen BOM: `EUR 436.55`
- Field add-on total from the frozen BOM: `EUR 459.70`
- Combined bench-to-field total: `EUR 896.25`

## Thermal Guidance

- Use active cooling on the Pi 5.
- Avoid sealing the enclosure without a heat path.
- Keep the LiFePO4 battery external to the Hammond electronics enclosure.
- Validate thermal stability during index rebuild and model inference, not only idle operation.
- Validate inverter temperature under continuous load before field closure.

## Enclosure Requirements

- Weather-resistant Hammond 1554X2GYCL shell with accessible M20 cable glands
- Internal mounting for Pi, SSD, and T114 only; battery remains external
- External antenna routing fixed to EU 868 with the SECTRON R36S15 assembly
- Service access for storage swap, SD recovery, and power disconnect
- Clear labeling for operator-safe maintenance

## Failure Conditions To Test

- thermal throttling during a long `ask` session
- brownout during model load
- connector strain causing radio disconnect
- inverter noise affecting radio stability
- condensation or inadequate venting after overnight field operation
