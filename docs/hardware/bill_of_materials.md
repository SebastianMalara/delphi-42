# Bill Of Materials

- Purpose: Define the controlled Prototype v1 hardware bill of materials for the Delphi-42 main node.
- Audience: Builders, operators, purchasers, and project leads.
- Owner: Hardware Lead
- Status: Revised direct-DC draft
- Last Updated: 2026-03-12
- Dependencies: node_topology.md, power_thermal_and_enclosure.md, ../project/adrs/0005-power-and-storage-design.md, ../project/reviews/hardware_bom_signoff.md
- Exit Criteria: The bench node can be ordered immediately, and the revised field power stack is documented tightly enough for final validation and re-review.

## Freeze Rules

- Region is locked to EU 868 for the Pi-attached radio path.
- Prices below were captured on 2026-03-12 and should be treated as procurement-time estimates.
- The bench package remains the approved baseline. The field power package below reflects the revised primary-battery plus Pi-side UPS architecture requested on 2026-03-12.
- Bench-to-field means the bench package is sufficient for Step 2 assembly, and the field package adds power, enclosure, and outdoor RF parts.

## Procurement Schema

| Subsystem | Line Item | Preferred Part | Vendor / SKU | Alternate Part | Qty | Unit Price (EUR) | Lead Time | Bench / Field | Compatibility Notes | Procurement Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Compute | SBC | Raspberry Pi 5 16GB | [BerryBase / RPI5-16GB](https://www.berrybase.de/en/raspberry-pi-5-16gb-ram) | Raspberry Pi 5 16GB via [JACOB / SC1113](https://www.jacob.de/produkte/raspberry-pi-5-16gb-sc1113-artnr-100130460.html) | 1 | 209.90 | 1-3 days | Required for bench | Baseline compute node for bot, retrieval, hotspot, and local services | Frozen - buy |
| Compute | AC bench PSU | Raspberry Pi 27W USB-C Power Supply, EU plug, black | [RaspberryPi.dk / 9711](https://raspberrypi.dk/en/product/raspberry-pi-27w-usb-c-power-supply-black/) | Raspberry Pi 27W USB-C PSU via [RATO Education / SC1408](https://www.ratoeducation.com/en/raspberry-pi/3355-raspberry-pi-27w-usb-c-power-supply-black.html) | 1 | 15.93 | In stock | Required for bench | Chosen for Pi 5 USB-C PD compatibility without custom power work | Frozen - buy |
| Thermal | Active cooling | Raspberry Pi Active Cooler | [Welectron / SC1148](https://www.welectron.com/Raspberry-Pi-Active-Cooler-for-Raspberry-Pi-5_1) | Raspberry Pi Active Cooler via [Melopero / RP5-ACT-COOL](https://www.melopero.com/en/shop/components-and-accessories/cooling/raspberry-pi-active-cooler/) | 1 | 4.90 | 1-3 business days | Required for bench | Required to avoid Pi 5 throttling during indexing and model load | Frozen - buy |
| Boot media | microSD | Samsung PRO Endurance 64GB microSDXC | [Bechtle / MB-MJ64KA-EU](https://www.bechtle.com/it/shop/samsung-pro-endurance-microsd-64gb-memory-card--4606099--p) | SanDisk High Endurance 64GB via [Rovision / SDSQQNR-064G-GN6IA](https://www.rovision.ro/cartela-micro-sdhc-sandisk-high-endurance-64-gb-clasa-10-adaptor-p-102025.html) | 1 | 16.79 | Stock-sensitive | Required for bench | OS and recovery image only; runtime data stays on external SSD | Frozen - buy |
| Storage | External SSD | Crucial X9 1TB Portable SSD | [Bechtle / CT1000X9SSD9](https://www.bechtle.com/at/shop/crucial-x9-1tb-portable-ssd--4848516--p) | Samsung T7 Shield 1TB via [Bechtle / MU-PE1T0S-EU](https://www.bechtle.com/be-en/shop/samsung-portable-ssd-t7-shield-1tb-black--4748954--p) | 1 | 125.99 | Few days | Required for bench | Stores corpus, index, model, and logs; preferred over SD-only storage for endurance | Frozen - buy |
| Radio | Pi-attached Meshtastic node | Heltec Mesh Node T114 Rev 2 with GPS, 868 MHz | [Nettigo / MOD-2382](https://nettigo.eu/products/mesh-node-t114-nrf52840-sx1262-bluetooth-5-0-lora-gps-tft-ultra-low-power) | Heltec Mesh Node T114 Rev 2 without GPS via [Nettigo / MOD-2411](https://nettigo.eu/products/mesh-node-t114-nrf52840-sx1262-868-mhz-bluetooth-5-0-lora-ultra-low-power-heltec-mesh-node-t114) | 1 | 51.77 | Fast shipping from stock | Required for bench | Preferred because it is USB-attachable to the Pi, supports EU 868, and includes GPS for private position replies | Frozen - buy |
| RF | Bench antenna | 868 MHz swivel SMA antenna | [SOS electronic / SECTRON AO-A868-G410S](https://www.soselectronic.com/en-si/products/sectron/g410s-149157) | Use included antenna from alternate T114 bundle if procured as a kit | 1 | 3.03 | In stock | Required for bench | Direct-fit bench antenna for T114 validation | Frozen - buy |
| Cabling | Radio USB cable | UGREEN USB-A to USB-C cable, 0.5 m, 2-pack | [UGREEN EU / US176](https://eu.ugreen.com/products/2pack-usb-to-usb-c-fast-charging-cable) | Equivalent short USB-A to USB-C data cable from a local reseller | 1 | 8.24 | In stock | Required for bench | One cable for the live radio, one spare; short length minimizes enclosure clutter | Frozen - buy |
| Field enclosure | Electronics enclosure | IP68 polycarbonate enclosure with clear lid | [RS / Hammond 1554X2GYCL](https://ie.rs-online.com/web/p/general-purpose-enclosures/2291110) | Solid-lid variant via [RS / Hammond 1554X2GYSL](https://ie.rs-online.com/web/p/general-purpose-enclosures/2215857) | 1 | 101.47 | In stock | Required for field | Sized for Pi, SSD, T114, glands, and service access; battery stays external in Prototype v1 | Frozen - buy |
| Field enclosure | Cable glands | M20 IP68 cable gland, grey | [Mouser / Molex 936000352](https://eu.mouser.com/ProductDetail/Molex/936000352) | Equivalent IP68 M20 gland from local stock | 4 | 1.12 | In stock | Required for field | Four glands cover DC in, antenna, service USB, and auxiliary cable pass-through | Frozen - buy |
| RF | Field antenna | 868 MHz IP67 screw-mount antenna, 3 dBi, 1.5 m cable | [SOS electronic / SECTRON AO-A868-R36S15](https://www.soselectronic.com/en-lt/products/sectron/r36s15-115783) | Magnetic base antenna via [RS / Panorama MAR-868-2SP](https://ie.rs-online.com/web/p/antennas/7665382) | 1 | 19.55 | In stock | Required for field | Externalized antenna improves enclosure placement and reduces attenuation | Frozen - buy |
| Field power | Primary battery | 12V 42Ah LiFePO4 deep-cycle battery | [autobatterienbilliger.de / Accurat VBL-LFP-12V-T42 (TN3662)](https://www.autobatterienbilliger.de/Accurat-Traction-T42-VBL-LFP-12V-T42-Lithium-Versorgungsbatterie-LiFePO4-12V-42Ah) | 12V 20Ah LiFePO4 only if runtime expectations are explicitly reduced | 1 | 118.85 | Available from stock | Required for field | Main solar energy store; external battery keeps the Pi-side UPS scoped to graceful shutdown and short hold-up events instead of full node runtime | Revised - validate before buy |
| Field power | Solar panel | 120W ShadowFlux anti-shading N-Type solar panel | [Renogy EU / RSP120DC-ASR-EU](https://eu.renogy.com/products/120w-shadowflux-anti-shading-n-type-solar-panel) | Renogy 115W bifacial panel via [Renogy EU / RSP115DT-EU](https://eu.renogy.com/products/bifacial-115-watt-12-volt-monocrystalline-solar-panel) if the 120W panel is unavailable | 1 | 144.99 | In stock | Required for field | Updated to the 120W planning baseline for faster recharge and cloudy-day recovery | Revised - validate before buy |
| Field power | Solar charge controller | Victron SmartSolar MPPT 75/15 | [Victron / SCC075015060R](https://www.victronenergy.com/media/pg/Manual_SmartSolar_MPPT_75-10_up_to_100-20/en/technical-specifications.html) | Victron SmartSolar MPPT 100/15 only if the final panel Voc or cable run requires it | 1 | 59.00 | Stock-listed | Required for field | 75/15 supports a 12V battery system and up to 220W nominal PV on 12V, which covers the 120W field panel | Revised - validate before buy |
| Field power | Pi DC regulator | Pololu 5V, 6A step-down voltage regulator D42V55F5 | [Pololu / 3783](https://www.pololu.com/product/3783) | Higher-current 5V regulator only if sustained bench load exceeds thermal margin | 1 | 33.00 | Active / stock-sensitive | Required for field | Converts the 12V battery bus to a stable 5V rail ahead of the Pi-side UPS; keep cable runs short and validate undervoltage margin under peak Pi load | Revised - validate before buy |
| Field power | Inline fuse holder | Littelfuse MINI waterproof in-line fuse holder 0FHM0200Z | [Mouser / 0FHM0200Z](https://www.mouser.com/new/littelfuse/littelfuse-fhm-in-line-fuse-holders/) | Equivalent IP67 10A to 15A DC fuse holder from local stock | 1 | 7.50 | In stock | Required for field | Place between battery pack output and regulator input; size final fuse after measured peak current | Revised - validate before buy |
| Field power | Pi-side UPS and RTC | PiSugar 3 Plus UPS for Raspberry Pi | [PiSugar / PISUGAR3P1001](https://docs.pisugar.com/docs/product-wiki/battery/pisugar3/pisugar-3-series) | DFRobot UPS HAT only if PiSugar current headroom proves insufficient and a separate shutdown path is accepted | 1 | 46.00 | Active / distributor stock | Required for field | Adds hold-up battery, RTC, and software-triggered shutdown, but the documented 5V and 3A limit means it remains a validated candidate rather than a fully frozen power stage for Pi 5 loads | Revised - validate before buy |
| Optional | T114 enclosure shell | Printed shell for Heltec T114 Rev 2 | [Nettigo / AKC-2412](https://nettigo.eu/products/mesh-node-t114-rev-2-0-shell) | None | 1 | 5.95 | In stock | Optional | Useful for bench protection; not required if the radio lives inside the main enclosure | Optional |
| Optional | Alternate Pi UPS HAT | Raspberry Pi 5 18650 Battery UPS HAT (5.1V 5A) | [DFRobot / FIT0992](https://www.dfrobot.com/product-2840.html) | None | 1 | 49.00 | In stock | Optional | Kept as the higher-current fallback if the PiSugar 3 Plus 3A ceiling proves too tight for the Pi 5 field load | Optional |
| Optional | Solar companion node | SenseCAP Solar Node P1 for Meshtastic | [OpenELAB EU / Seeed-114993643](https://openelab.io/fi/products/seeed-studio-sensecap-node-p1) | SenseCAP Solar Node P1-Pro via [Seeed / 114993633](https://www.seeedstudio.com/SenseCAP-Solar-Node-P1-Pro-for-Meshtastic-LoRa-p-6412.html) | 1 | 89.95 | Pre-order / 10 business days | Optional | Treated as a standalone solar relay or remote companion node, not the primary Pi-attached radio for Delphi-42 | Optional |

## Package Rollups

### Bench Package

Required line items:

- Raspberry Pi 5 16GB
- Raspberry Pi 27W USB-C PSU
- Raspberry Pi Active Cooler
- Samsung PRO Endurance 64GB
- Crucial X9 1TB SSD
- Heltec T114 Rev 2 with GPS, 868 MHz
- SECTRON AO-A868-G410S bench antenna
- UGREEN short USB cable pack

Bench package estimated total: `EUR 436.55`

### Field Add-On Package

Additional line items beyond the bench package:

- Hammond 1554X2GYCL enclosure
- 4x Molex M20 cable glands
- SECTRON AO-A868-R36S15 external antenna
- Accurat T42 LiFePO4 battery
- Renogy RSP120DC-ASR-EU solar panel
- Victron SmartSolar MPPT 75/15
- Pololu D42V55F5 5V regulator
- Littelfuse 0FHM0200Z fuse holder
- PiSugar 3 Plus UPS

Field add-on estimated total: `EUR 534.84`

Bench-to-field total estimated baseline: `EUR 971.39`

## Expected Physical Dependencies

- The bench package is sufficient to build and validate the main oracle node indoors.
- The field package assumes the battery remains external to the Hammond electronics enclosure.
- The revised field package uses a 12V primary storage battery, a 12V to 5V regulator, and a Pi-side UPS layer for hold-up power, RTC, and scripted shutdown behavior.
- The optional SenseCAP Solar Node P1 is a network extension, not a substitution for the main Pi-attached oracle radio.

## Procurement Notes

- Buy one additional SSD and one additional T114 as spares if budget allows.
- If the GPS-capable T114 is unavailable, the non-GPS T114 can unblock bench work, but private position testing must then be deferred or emulated.
- If a larger custom PiSugar battery is pursued later, PiSugar documentation limits that path to a single 3.7V lithium cell and explicitly warns against parallel battery configurations.
- The revised field power path removes the inverter, but it reopens validation of regulator thermals, Pi-side UPS current headroom, and scripted low-power behavior.
- Review country-specific VAT handling at checkout; the table normalizes prices to EUR consumer-facing values available on 2026-03-12.
