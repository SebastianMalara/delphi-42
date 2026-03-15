# Glossary

- Purpose: Standardize project terminology used across the documentation suite.
- Audience: All readers.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: project_brief.md, ../architecture/system_context.md, ../operations/agentic_oracle_sop.md
- Exit Criteria: Core project terms are defined consistently enough to avoid interpretation drift.

## Terms

- ADR: Architectural Decision Record.
- AX8850: The M5Stack LLM accelerator used as the Prototype v1 local generation hardware baseline.
- Corpus: The set of offline documents prepared for retrieval.
- Delphi-42: The overall oracle node project and reference implementation.
- Direct Message: A private Meshtastic message sent between nodes.
- Field User: A person interacting with the oracle over the mesh or hotspot.
- Hotspot: The local WiFi access point exposed by the node for on-site archive access.
- Kiwix: Software used to serve offline content, often backed by ZIM archives.
- Local LLM: Small model running on the node without network dependence.
- Meshtastic: LoRa-based mesh communication platform.
- Node Operator: The person who deploys and maintains the hardware.
- OpenAI-Compatible Local API: An HTTP API shaped like the OpenAI chat and models endpoints but served locally on the node.
- Oracle Broadcast: Short public message advertising the node's presence.
- Prototype v1: The first complete, documented, field-testable version defined by this suite.
- Retrieval: The process of selecting local passages relevant to a question.
- Kiwix-backed Retrieval: Runtime `.zim` search and article reads used for local text lookup.
- StackFlow: The M5 software stack and host services used to expose AX8850-backed local model inference on Debian 12.
- ZIM: Archived content format commonly used for offline web and encyclopedia datasets.
