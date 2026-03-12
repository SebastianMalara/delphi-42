# Retrieval And Response Policy

- Purpose: Define the retrieval-first question-answering policy, prompt rules, safety constraints, and fallback behavior.
- Audience: AI, software, QA, and operations.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: ingestion_and_indexing.md, ../../core/prompt_builder.py, ../../core/oracle_service.py, ../operations/agentic_oracle_sop.md
- Exit Criteria: Engineers can implement answer behavior and QA can verify it against explicit rules.

## Retrieval-First Policy

- Retrieval is mandatory for `ask`.
- The model is not the source of truth.
- If retrieval is empty or weak, the answer must say the archive does not contain a grounded answer.
- Direct, deterministic summaries are preferred over speculative creativity.

## Prompt Policy

- include only the question and a small set of local passages
- request a very short answer draft plus a fuller grounded explanation draft
- forbid unsupported extrapolation
- instruct the model to admit insufficiency rather than guess
- do not trust the model to enforce character limits without deterministic post-processing

## Response Policy

- first reply packet must fit within 120 characters
- fuller explanation may follow in at most 3 additional packets of at most 600 characters each
- packet splitting is deterministic application logic, not an LLM-only responsibility
- split on sentence boundaries first, then word boundaries, and hard-trim only as a last resort
- preserve privacy constraints for all command types
- do not reveal operator-only metadata, file paths, or internal source layout in answers

## Safety Rules

- never answer public mesh questions
- never return coordinates publicly
- never treat model priors as evidence
- refuse or deflect if content is unsafe, missing, or not grounded

## Fallback Rules

- if SQLite retrieval misses and runtime `.zim` fallback is enabled, search the allowlisted local `.zim` archives before declaring no grounded answer
- if the model runtime is unavailable, return a deterministic retrieval summary when possible
- fallback output must obey the same short-packet plus bounded-continuation contract
- if both retrieval and model paths fail, return a short archive-unavailable message
- if the radio layer is unstable, fail visibly in operator logs rather than pretend success

## Prototype V1 Defaults

- retrieval backend: SQLite FTS built from curated plaintext and selected Kiwix-derived extracts
- local model runtime: `StackFlow` OpenAI-compatible API served from the M5 AX8850 kit
- default model: `qwen3-1.7B-Int8-ctx-axcl`
- supported runtime backends: `axcl-openai` and `deterministic`
- top-k context: 3 passages unless testing requires adjustment
- default public broadcast interval: 90 minutes
- Kiwix remains the browseable archive, while allowlisted direct `.zim` lookup acts only as a secondary retrieval source on SQLite misses
