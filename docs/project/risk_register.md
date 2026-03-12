# Risk Register

- Purpose: Track the major delivery, safety, privacy, and operational risks for Prototype v1.
- Audience: Project leads, engineering, operations, and QA.
- Owner: Project Lead
- Status: Active
- Last Updated: 2026-03-12
- Dependencies: execution_plan.md, ../testing/release_readiness.md, adrs/README.md
- Exit Criteria: Critical project risks have owners, mitigation plans, and explicit review status.

## Risks

| ID | Risk | Impact | Likelihood | Owner | Mitigation | Trigger | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | AX8850 local service or model package is unavailable on target hardware | High | Medium | AI Lead | bench Debian 12 plus StackFlow install early, preflight `/v1/models`, and keep deterministic fallback | `llm-openai-api` is down or the configured model is missing | Open |
| R-002 | Radio integration is unstable across device reconnects | High | Medium | Software Lead | freeze around Heltec T114 Rev 2 USB radio, then add reconnect handling and reboot tests on bench | radio path disappears or bot stops receiving | Open |
| R-003 | Corpus quality is too weak for useful answers | High | Medium | AI Lead | curate higher-value sources, run retrieval benchmarks early | repeated irrelevant or missing answers | Open |
| R-004 | Hotspot and archive stack becomes operationally fragile | Medium | Medium | Ops Lead | keep hotspot stack simple, rehearse restart and recovery | users cannot reach local archive on-site | Open |
| R-005 | PD source stage or field power budget underestimates combined Pi plus AX8850 load | High | Medium | Hardware Lead | revised field stack uses a 120W panel, 12V primary battery, inline fuse, accessory socket, and USB-C PD source stage; bench-test draw, recharge profile, PD negotiation, shutdown behavior, and thermals before field release | repeated brownouts, short endurance, or PiHat power negotiation failure | Open |
| R-006 | Public privacy leak through routing or broadcast logic | Critical | Low | Software Lead | test DM-only behavior, review logs and broadcast code paths | public answer or coordinate exposure | Open |
| R-007 | Documentation drifts from implementation | Medium | Medium | Project Lead | require docs update in related changes, run docs check script | broken links or stale procedures found | Open |
| R-008 | Storage corruption or failed mounts break the node | High | Medium | Ops Lead | baseline uses a dedicated 1TB Crucial X9 SSD plus endurance microSD because the AX8850 consumes the PCIe path; add mount checks, spare SSD, and rebuild runbook before field release | missing index, missing corpus, or mount failure | Open |
| R-009 | Third-party StackFlow apt repo or model packaging changes break reproducibility | Medium | Medium | Ops Lead | record apt source, installed package manifest, and known-good image; bench upgrades before field rollout | package install fails or model IDs drift unexpectedly | Open |
| R-010 | Containerized Pi app cannot reach the host-local model API reliably | Medium | Medium | Ops Lead | standardize on `host.docker.internal:host-gateway`, test preflight from the container, and keep deterministic fallback active | `oracle-app` logs model API connection failures on Pi | Open |
| R-011 | Containerized radio path behaves differently from native Meshtastic on reconnect or permission changes | High | Medium | Software Lead | add Pi Compose drills for `/dev/ttyUSB0`, test reconnect behavior, and keep simulated radio confined to development only | container loses access to the serial device or stops receiving after reconnect | Open |
| R-012 | LM Studio model id or local server settings drift from the Mac config profiles | Medium | Medium | Software Lead | add Mac preflight, require `/v1/models` check before runtime, and document model-id replacement explicitly in the quickstart | Mac preflight fails or the bot degrades to deterministic unexpectedly | Open |

## Milestone Review Note

The v1 hardware and AI baseline was reopened when the project switched from a generic Pi-only model path to the M5 AX8850 kit. The current open validation scope is the PiHat-fed PD power chain, enclosure clearance and thermals, Debian 12 plus StackFlow reproducibility, and real local API behavior on the bench node.

## Review Rules

- Review risks at least once per milestone boundary.
- Escalate any `Critical` risk immediately if it becomes active.
- Closed risks must cite the milestone or evidence that resolved them.
