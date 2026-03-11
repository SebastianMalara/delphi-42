# Execution Plan

- Purpose: Provide the tracked delivery plan for Delphi-42 Prototype v1 using explicit milestones and evidence.
- Audience: Project leads, engineering, and operations.
- Owner: Project Lead
- Status: Active
- Last Updated: 2026-03-11
- Dependencies: risk_register.md, ../testing/test_matrix.md, ../overview/scope_and_non_goals.md
- Exit Criteria: The project can be managed directly from this plan without requiring an external tracker for milestone status.

## Status Legend

- `Done`: completed and evidenced
- `In Progress`: active work with identified owner
- `Not Started`: planned but not yet active
- `Blocked`: cannot proceed until dependencies clear

## Milestones

| Workstream | Milestone | Owner | Status | Target Date | Dependencies | Exit Criteria | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation | Publish repo-native documentation suite | Project Lead | Done | 2026-03-11 | none | docs taxonomy, README front door, and governance docs merged | `docs/README.md` |
| Documentation | Publish tracked execution plan and risk register | Project Lead | Done | 2026-03-11 | none | tracked project docs merged | `docs/project/execution_plan.md`, `docs/project/risk_register.md` |
| Hardware | Freeze prototype hardware BOM | Hardware Lead | Done | 2026-03-11 | ADR-0005 | BOM approved and procurement-ready | `docs/hardware/bill_of_materials.md`, `docs/project/reviews/hardware_bom_signoff.md` |
| Hardware | Assemble bench prototype node | Hardware Lead | Not Started | 2026-03-27 | hardware BOM | powered bench node with Pi, radio, SSD, and enclosure draft | assembly checklist |
| Platform | Provision Raspberry Pi base image and storage layout | Ops Lead | Not Started | 2026-03-27 | bench prototype | Pi boots with stable mounts and base packages | provisioning log |
| Radio | Replace dry-run transport with real Meshtastic integration | Software Lead | Not Started | 2026-04-03 | ADR-0002, provisioned Pi | bot communicates with live radio over supported device path | integration test note |
| Core | Implement persistent SQLite-backed retriever | AI Lead | Not Started | 2026-04-03 | staged corpus, platform provisioned | runtime retrieval uses generated index | retrieval test evidence |
| AI | Wire local `llama.cpp` runtime with fallback path | AI Lead | Not Started | 2026-04-10 | ADR-0001, provisioned Pi | configured model backend returns bounded answers | model smoke test |
| AI | Stage Prototype v1 curated corpus | AI Lead | Not Started | 2026-04-10 | ADR-0004 | approved corpus staged and indexed | corpus manifest |
| Archive | Stand up Kiwix-backed local archive | Ops Lead | Not Started | 2026-04-17 | ADR-0003, provisioned Pi | hotspot client can browse local archive | hotspot checklist |
| Operations | Install and validate systemd services on Pi | Ops Lead | Not Started | 2026-04-17 | radio integration, retriever, model | services restart cleanly after reboot | service drill log |
| Privacy | Validate DM-only routing and private position behavior | Software Lead | Not Started | 2026-04-24 | radio integration | no public answer or coordinate leakage in bench tests | privacy test log |
| Testing | Complete automated bench test coverage for critical flows | QA Lead | Not Started | 2026-04-24 | radio, retriever, model integration | critical matrix rows green on bench environment | `pytest` plus bench notes |
| Field | Execute controlled field acceptance test | QA Lead | Not Started | 2026-05-01 | operations, archive, privacy validation | field protocol completed with findings logged | field acceptance packet |
| Readiness | Close or accept open Prototype v1 risks | Project Lead | Not Started | 2026-05-06 | field acceptance | all critical risks closed or explicitly accepted | risk review |
| Release | Approve Prototype v1 field-trial release | Project Lead | Not Started | 2026-05-08 | readiness review | release checklist signed off | release readiness note |

## Tracking Rules

- Update `Status`, `Target Date`, and `Evidence` in this file as work changes.
- Do not mark a milestone `Done` without a concrete artifact or test result.
- If a milestone slips, update the dependent rows in the same edit.
