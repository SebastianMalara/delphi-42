# Retrieval And Response Policy

- Purpose: Define the retrieval-first question-answering policy, prompt rules, safety constraints, and fallback behavior.
- Audience: AI, software, QA, and operations.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-13
- Dependencies: ingestion_and_indexing.md, ../../core/prompt_builder.py, ../../core/oracle_service.py, ../operations/agentic_oracle_sop.md
- Exit Criteria: Engineers can implement answer behavior and QA can verify it against explicit rules.

## Retrieval-First Policy

- Retrieval is mandatory for `ask`.
- The model is not the source of truth.
- If retrieval is empty or weak, the answer must say the archive does not contain a grounded answer.
- Direct, deterministic summaries are preferred over speculative creativity.

## Prompt Policy

- include only the question and a small set of local passages
- request a full grounded answer, then a condensed continuation draft, then an ultra-short first packet draft
- forbid unsupported extrapolation
- instruct the model to admit insufficiency rather than guess
- ask the model to shrink oversized replies before deterministic trimming

## Response Policy

- first reply packet must fit within the configured short-answer target
- fuller explanation may follow in at most 5 additional packets, with 6 total text packets maximum
- every outbound text packet must be prefixed with `🤖 `
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

- grounded retrieval comes only from allowlisted local `.zim` archives
- if the model runtime is unavailable, return a deterministic retrieval summary when possible
- fallback output must obey the same short-packet plus bounded-continuation contract
- if both retrieval and model paths fail, return a short archive-unavailable message
- if the radio layer is unstable, fail visibly in operator logs rather than pretend success

## Prototype V1 Defaults

- retrieval backend: Kiwix-backed `.zim` search through `llm-tools-kiwix`
- local model runtime: `StackFlow` OpenAI-compatible API served from the M5 AX8850 kit
- default model: `qwen3-1.7B-Int8-ctx-axcl`
- supported runtime backends: `openai-compatible` and `deterministic`
- supported OpenAI-compatible providers: `generic`, `stackflow`, `lm-studio`, and `ovms`
- legacy compatibility alias: `axcl-openai` normalizes to `openai-compatible`
- top-k context: 3 passages unless testing requires adjustment
- default public broadcast interval: 90 minutes
- Kiwix remains the browseable archive, while allowlisted direct `.zim` lookup is also the answer-time retrieval source
