# Bill Of Materials

- Purpose: Define the recommended Prototype v1 hardware bill of materials and procurement assumptions.
- Audience: Builders, operators, and project leads.
- Owner: Hardware Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: node_topology.md, power_thermal_and_enclosure.md, ../project/adrs/0005-power-and-storage-design.md
- Exit Criteria: The prototype can be procured from this BOM without additional hardware decisions.

## Recommended Prototype BOM

| Item | Qty | Recommended Spec | Notes |
| --- | --- | --- | --- |
| Raspberry Pi 5 | 1 | 16 GB RAM | Gives headroom for local inference and hotspot services |
| Power supply or DC regulator | 1 | Stable 5V at 5A | Bench supply for dev, regulated battery feed for field |
| Meshtastic radio | 1 | USB-accessible node with optional GNSS | Must support stable serial connection |
| External SSD | 1 | 1 TB USB 3 | Stores model, corpus, index, logs |
| MicroSD card | 1 | 64 GB high-endurance | OS and recovery image |
| Cooling kit | 1 | Active fan plus heatsink | Required for sustained Pi 5 load |
| Weather-resistant enclosure | 1 | IP65 or better | Must allow cable glands and ventilation strategy |
| LiFePO4 battery | 1 | 12V, 40Ah nominal | Prototype field-power target |
| Solar panel | 1 | 100W nominal | Planning baseline for sustained outdoor use |
| Charge controller | 1 | 10A MPPT | Matches solar and battery assumptions |
| Cabling and glands | set | USB, power, RF, strain relief | Sized for field enclosure |
| Antenna hardware | 1 | Outdoor-suitable for chosen radio | Keep matched to the radio frequency band |

## Optional Prototype Additions

- USB GNSS receiver if the radio does not provide position
- OLED or small service display for bench diagnostics
- Spare SSD cloned for fast field recovery
- Environmental sensors for later power and thermal telemetry

## Procurement Rules

- Prefer parts with stable Linux support and operator-replaceable connectors.
- Avoid storage media without endurance specifications.
- Keep a second radio and second SSD as bench spares.
- Lock frequency band and antenna selection before field assembly.
