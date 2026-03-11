# Assembly And Field Packaging

- Purpose: Provide the prototype assembly sequence and field packaging checklist.
- Audience: Builders and operators.
- Owner: Hardware Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: node_topology.md, bill_of_materials.md, ../operations/deployment_runbook.md
- Exit Criteria: A builder can assemble the hardware stack and prepare it for field deployment without undocumented steps.

## Assembly Sequence

1. Bench-test the Raspberry Pi, SSD, and radio before enclosure mounting.
2. Install cooling kit and verify thermal contact.
3. Flash the Pi OS image and confirm first boot.
4. Mount Pi, SSD, and radio with strain relief.
5. Route power, USB, and antenna lines cleanly.
6. Connect battery and regulated supply only after polarity verification.
7. Validate radio detection, storage mounts, and hotspot startup before sealing the enclosure.

## Field Packaging Checklist

- spare power cable
- spare USB cable for radio
- recovery SD card
- printed quick-start sheet with service commands
- antenna and mounting accessories
- weather sealing consumables
- basic tools for storage and cable replacement

## Assembly Sign-Off

Before deployment, capture:

- hardware serials and radio identity
- storage size and mount path
- enclosure configuration
- battery and solar sizing actually installed
- operator contact and deployment date
