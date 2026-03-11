# ADR-0003: Hotspot And Local Archive Stack

- Purpose: Record the default local archive and hotspot stack for Prototype v1.
- Audience: Engineering and operations.
- Owner: Ops Lead
- Status: Accepted
- Last Updated: 2026-03-11
- Dependencies: ../../operations/raspberry_pi_provisioning.md, ../../hardware/node_topology.md
- Exit Criteria: The project has one documented baseline for on-site archive access.

## Context

Users who physically reach the node need a straightforward local browsing experience with minimal moving parts.

## Decision

Prototype v1 uses a Pi-hosted WiFi hotspot backed by `hostapd` and `dnsmasq`, with Kiwix serving the local browseable archive.

## Consequences

- uses common Linux primitives and a well-known offline archive server
- separates browseable archive access from low-bandwidth DM answering
- adds operational surface area that must be covered by runbooks and drills
