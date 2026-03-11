# User Journeys

- Purpose: Describe the end-to-end journeys for field users, operators, and builders.
- Audience: Engineering, operations, UX, and project planning.
- Owner: Product Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: project_brief.md, ../architecture/runtime_flows.md, ../operations/deployment_runbook.md
- Exit Criteria: Each major actor has a documented journey that maps cleanly to system behavior and supporting docs.

## Actor 1: Field User On The Mesh

1. User sees a public oracle broadcast on channel 0.
2. User sends a direct message with `help` or `ask <question>`.
3. The node parses the message and checks that it is private.
4. For `ask`, the node retrieves local material and returns a short answer.
5. If the user needs the full archive, they send `where`.
6. The node returns a short confirmation and a private position packet.

## Actor 2: Explorer At The Hotspot

1. User reaches the physical node.
2. User joins the hotspot SSID.
3. User browses the local archive through Kiwix or a similar local web interface.
4. User accesses richer material than fits over LoRa.

## Actor 3: Node Operator

1. Operator provisions the Raspberry Pi and installs the service stack.
2. Operator stages corpora, builds the local index, and verifies hotspot availability.
3. Operator enables the bot and index services.
4. Operator monitors health, storage, and power conditions.
5. Operator handles failures using the incident and recovery runbooks.

## Actor 4: Builder Or Maintainer

1. Builder reads the hardware pack and assembles the prototype bill of materials.
2. Builder follows architecture and AI docs to implement or extend the system.
3. Builder validates changes with the test strategy and field protocol.
4. Builder records major design decisions through ADRs.

## Journey Constraints

- Mesh answers must remain short.
- Public broadcasts must not leak private data.
- Hotspot access assumes physical proximity.
- Offline content quality determines answer quality.
