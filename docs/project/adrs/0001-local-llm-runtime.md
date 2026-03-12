# ADR-0001: Local LLM Runtime

- Purpose: Record the Prototype v1 decision for the local model runtime.
- Audience: Engineering and operations.
- Owner: AI Lead
- Status: Accepted
- Last Updated: 2026-03-12
- Dependencies: ../../ai/retrieval_and_response_policy.md, ../../architecture/interfaces_and_config.md
- Exit Criteria: The project has a clear default local runtime choice for Prototype v1.

## Context

Delphi-42 needs a local model runtime that is offline, scriptable from Python, and practical on Raspberry Pi 5 hardware without asking the project to carry a large software-porting burden. The project has now chosen to include the M5 AI-8850 kit in Prototype v1 rather than treating accelerator support as a later option.

## Decision

Prototype v1 uses the M5 `StackFlow` local OpenAI-compatible API as the default model runtime on `Debian 12 arm64`, with `qwen3-1.7B-Int8-ctx-axcl` as the baseline model package.

## Consequences

- aligns the hardware, provisioning, and runtime stack around one supported accelerator path
- keeps Python integration simple by using an OpenAI-compatible HTTP client boundary
- allows the Delphi app itself to remain generic and container-friendly while the AX8850 runtime stays host-managed on the Pi
- supports deterministic fallback if the local API or model package is unavailable
- removes site-local model file management from the v1 runtime contract
- ties reproducibility to the M5 apt repository and package availability
