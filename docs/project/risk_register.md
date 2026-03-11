# Risk Register

- Purpose: Track the major delivery, safety, privacy, and operational risks for Prototype v1.
- Audience: Project leads, engineering, operations, and QA.
- Owner: Project Lead
- Status: Active
- Last Updated: 2026-03-11
- Dependencies: execution_plan.md, ../testing/release_readiness.md, adrs/README.md
- Exit Criteria: Critical project risks have owners, mitigation plans, and explicit review status.

## Risks

| ID | Risk | Impact | Likelihood | Owner | Mitigation | Trigger | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Local model too slow on target Pi hardware | High | Medium | AI Lead | benchmark smaller models, keep deterministic fallback | median answer latency exceeds target | Open |
| R-002 | Radio integration is unstable across device reconnects | High | Medium | Software Lead | freeze around Heltec T114 Rev 2 USB radio, then add reconnect handling and reboot tests on bench | radio path disappears or bot stops receiving | Open |
| R-003 | Corpus quality is too weak for useful answers | High | Medium | AI Lead | curate higher-value sources, run retrieval benchmarks early | repeated irrelevant or missing answers | Open |
| R-004 | Hotspot and archive stack becomes operationally fragile | Medium | Medium | Ops Lead | keep hotspot stack simple, rehearse restart and recovery | users cannot reach local archive on-site | Open |
| R-005 | Power budget underestimates field load | High | Medium | Hardware Lead | frozen BOM now fixes the field power stack to 100W panel, Victron 75/10, 12V/42Ah battery, and Victron Phoenix 12/250 inverter; bench-test draw and inverter losses before field release | repeated brownouts or short endurance | Open |
| R-006 | Public privacy leak through routing or broadcast logic | Critical | Low | Software Lead | test DM-only behavior, review logs and broadcast code paths | public answer or coordinate exposure | Open |
| R-007 | Documentation drifts from implementation | Medium | Medium | Project Lead | require docs update in related changes, run docs check script | broken links or stale procedures found | Open |
| R-008 | Storage corruption or failed mounts break the node | High | Medium | Ops Lead | frozen BOM uses a dedicated 1TB Crucial X9 SSD plus endurance microSD; add mount checks, spare SSD, and rebuild runbook before field release | missing index, missing corpus, or mount failure | Open |

## Milestone Review Note

The hardware BOM freeze removes component-selection ambiguity for the main node, but it does not close validation risks for radio stability, inverter losses, or overnight field endurance. Those risks remain open until the bench prototype is assembled and tested.

## Review Rules

- Review risks at least once per milestone boundary.
- Escalate any `Critical` risk immediately if it becomes active.
- Closed risks must cite the milestone or evidence that resolved them.
