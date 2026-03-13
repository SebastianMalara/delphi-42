# Execution Plan

- Purpose: Provide the tracked delivery plan for Delphi-42 Prototype v1 using explicit milestones and evidence.
- Audience: Project leads, engineering, and operations.
- Owner: Project Lead
- Status: Active
- Last Updated: 2026-03-12
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
| Core | Generalize runtime contract to `openai-compatible` plus transport-aware radio config | Software Lead | In Progress | 2026-03-13 | ADR-0001 | canonical config uses `openai-compatible`, legacy alias is supported, and radio transport is selected from config | runtime config tests |
| Core | Package Delphi-42 into multi-arch container image and Compose overlays | Software Lead | In Progress | 2026-03-14 | runtime contract | app image, dev overlay, and Pi overlay exist and are documented | `Dockerfile`, `compose*.yaml` |
| Core | Add simulated radio developer console and sample corpus workflow | Software Lead | In Progress | 2026-03-14 | runtime contract, container packaging | developers can exercise `help`, `where`, and `ask` locally without hardware | `bot/dev_console.py`, sample corpus |
| Core | Harden local model preflight and deterministic degraded mode | AI Lead | In Progress | 2026-03-17 | runtime contract | OpenAI-compatible preflight validates both model visibility and a sample completion, and failures degrade cleanly | `tests/test_llm_runner.py`, `tests/test_oracle_service.py`, `tests/test_mac_preflight.py` |
| Core | Add Mac M1 Pro host-native quickstart and config profiles | Software Lead | In Progress | 2026-03-15 | runtime contract | Mac-native configs, preflight helper, and quickstart doc exist | `config/oracle.mac.*.yaml`, `scripts/mac_preflight.py`, `docs/operations/mac_m1_pro_quickstart.md` |
| Testing | Mac M1 Pro simulated software validation | QA Lead | Not Started | 2026-03-18 | Mac quickstart, LM Studio | simulated radio plus LM Studio lane passes smoke tests on an M1 Pro | M1 Stage A note |
| Testing | Mac M1 Pro real `.zim` validation | QA Lead | Not Started | 2026-03-19 | Mac simulated validation, real `.zim` archive | real allowlisted archive passes extract, index, and runtime fallback checks | M1 Stage B note |
| Testing | Mac live T114 USB validation | QA Lead | Not Started | 2026-03-20 | Mac simulated validation, T114, second Meshtastic client | direct messages flow over the live USB-attached node, public traffic is ignored, and no-fix position requests do not kill the bot | M1 Stage C note |
| Core | Validate Mac/OrbStack Compose acceptance path | QA Lead | Not Started | 2026-03-18 | container packaging, dev console | local Compose stack starts and core flows work with simulated radio | compose acceptance note |
| Core | Package Pi Compose deployment around host-managed `llm-openai-api` | Ops Lead | Not Started | 2026-03-19 | container packaging, Raspberry Pi provisioning | Pi overlay maps the radio device and reaches the host model service | Pi compose drill note |
| Hardware | Refreeze prototype hardware BOM around AX8850 PiHat PD path | Hardware Lead | In Progress | 2026-03-18 | ADR-0005 | Exact M5-based bench package and upstream-PD field package documented with reopened signoff note | revised BOM draft and reopened signoff note |
| Hardware | Assemble bench prototype node | Hardware Lead | Not Started | 2026-03-27 | hardware BOM | powered bench node with Pi, radio, SSD, and enclosure draft | assembly checklist |
| Platform | Provision Debian 12 arm64 base image and storage layout | Ops Lead | Not Started | 2026-03-27 | bench prototype | Pi boots with stable mounts, StackFlow apt source, and base packages | provisioning log |
| Platform | Install StackFlow service and validate model preflight | Ops Lead | Not Started | 2026-04-03 | provisioned Pi, ADR-0001 | `llm-openai-api` responds on loopback, expected model is visible, and sample completion succeeds | StackFlow preflight log |
| Platform | Implement low-power shutdown and reduced-service policy | Ops Lead | Not Started | 2026-04-03 | provisioned Pi, upstream battery telemetry path | Pi reacts predictably to low-input and low-battery events with either graceful shutdown or reduced-service mode | power management test note |
| Radio | Replace dry-run transport with real Meshtastic integration | Software Lead | Not Started | 2026-04-03 | ADR-0002, provisioned Pi | bot communicates with live radio over supported device path | integration test note |
| Core | Implement persistent SQLite-backed retriever | AI Lead | Done | 2026-03-12 | staged corpus | runtime retrieval uses generated index | `tests/test_retriever.py`, `tests/test_oracle_service.py` |
| Core | Implement deterministic reply packet formatter | Software Lead | Done | 2026-03-12 | runtime flow contract | `ask` returns one sub-120-char packet plus at most 3 bounded continuation packets | `tests/test_reply_formatter.py`, `tests/test_oracle_service.py` |
| AI | Integrate host-local OpenAI-compatible runtime with deterministic fallback | AI Lead | In Progress | 2026-04-10 | ADR-0001, runtime config rework | configured local API backend returns bounded answers and degrades safely when unavailable | `tests/test_llm_runner.py`, `tests/test_oracle_bot.py` |
| AI | Stage Prototype v1 curated corpus | AI Lead | Not Started | 2026-04-10 | ADR-0004 | approved corpus staged and indexed | corpus manifest |
| Archive | Stand up Kiwix-backed local archive | Ops Lead | Not Started | 2026-04-17 | ADR-0003, provisioned Pi | hotspot client can browse local archive | hotspot checklist |
| Operations | Install and validate systemd services on Pi | Ops Lead | Not Started | 2026-04-17 | radio integration, retriever, StackFlow preflight | services restart cleanly after reboot and order correctly around `llm-openai-api` | service drill log |
| Privacy | Validate DM-only routing and private position behavior | Software Lead | Not Started | 2026-04-24 | radio integration | no public answer or coordinate leakage in bench tests | privacy test log |
| Testing | Complete automated bench test coverage for critical flows | QA Lead | Not Started | 2026-04-24 | radio, retriever, model integration | critical matrix rows green on bench environment | `pytest` plus bench notes |
| Field | Execute controlled field acceptance test | QA Lead | Not Started | 2026-05-01 | operations, archive, privacy validation | field protocol completed with findings logged | field acceptance packet |
| Readiness | Close or accept open Prototype v1 risks | Project Lead | Not Started | 2026-05-06 | field acceptance | all critical risks closed or explicitly accepted | risk review |
| Release | Approve Prototype v1 field-trial release | Project Lead | Not Started | 2026-05-08 | readiness review | release checklist signed off | release readiness note |

## Tracking Rules

- Update `Status`, `Target Date`, and `Evidence` in this file as work changes.
- Do not mark a milestone `Done` without a concrete artifact or test result.
- If a milestone slips, update the dependent rows in the same edit.

## Deferred After V1

- Alternative accelerator backends beyond the AX8850 / StackFlow baseline.
- Full hardware-first field packaging and power validation remain outside the active core-development lane.
