# ADR-0001: Local LLM Runtime

- Purpose: Record the Prototype v1 decision for the local model runtime.
- Audience: Engineering and operations.
- Owner: AI Lead
- Status: Accepted
- Last Updated: 2026-03-11
- Dependencies: ../../ai/retrieval_and_response_policy.md, ../../architecture/interfaces_and_config.md
- Exit Criteria: The project has a clear default local runtime choice for Prototype v1.

## Context

Delphi-42 needs a local model runtime that is offline, scriptable from Python, and practical on Raspberry Pi-class hardware with GGUF model support.

## Decision

Prototype v1 uses `llama.cpp` as the default local model runtime, with GGUF model files stored outside git.

## Consequences

- aligns with the current example config
- supports deterministic fallback if the model path is unavailable
- keeps runtime choice simple for prototype deployment
- may require aggressive model-size selection and prompt constraints on the Pi
