# Project Brief

- Purpose: Define the mission, problem statement, stakeholders, and Prototype v1 success definition for Delphi-42.
- Audience: Engineering, operations, and project sponsors.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: ../README.md, ../architecture/system_context.md, ../project/execution_plan.md
- Exit Criteria: Readers understand what Delphi-42 is, why it exists, who it serves, and what Prototype v1 must prove.

## Mission

Delphi-42 is an offline oracle node for low-connectivity environments. It exists to make practical local knowledge discoverable over Meshtastic direct messages and through a nearby WiFi archive without depending on the internet.

## Problem Statement

When conventional connectivity is absent or intermittent, people lose access to reference material, field guides, repair instructions, and basic knowledge services. Existing offline archives are useful, but they are often not easy to discover or query over low-bandwidth mesh networks.

Delphi-42 addresses that gap by combining:

- Meshtastic for discovery and private low-bandwidth interaction
- Raspberry Pi for local compute and storage
- offline archives for trustworthy local content
- a constrained local model for short, grounded answers

## Prototype V1 Objective

Prototype v1 must prove that a single node can:

- receive private Meshtastic questions
- retrieve relevant local passages from an offline corpus
- return short grounded answers
- keep location disclosure private
- expose a larger local archive over hotspot WiFi
- operate on repeatable hardware and software instructions

## Primary Stakeholders

- Field users: people who need concise answers over the mesh
- Operators: people who deploy, power, and maintain a node
- Builders: engineers who assemble hardware and implement software
- Project leads: people who decide scope, risk, and readiness

## Value Proposition

- Knowledge access without internet dependence
- A privacy-preserving public presence: the node advertises itself without leaking operator or user intent
- A bridge between very low-bandwidth interaction and richer local archives
- Repeatable deployment on commodity hardware

## Success Criteria

Prototype v1 is successful when:

- a field user can send `ask <question>` and receive a useful short answer
- `where` returns private position only
- an operator can deploy and recover the node from the runbooks
- a builder can reproduce the hardware and software stack from this repo
- the node can support a curated offline corpus and local hotspot archive

## Related Documents

- [`user_journeys.md`](user_journeys.md)
- [`scope_and_non_goals.md`](scope_and_non_goals.md)
- [`non_functional_requirements.md`](non_functional_requirements.md)
