# Retrieval And Response Policy

- Purpose: Define the retrieval-first question-answering policy, prompt rules, safety constraints, and fallback behavior.
- Audience: AI, software, QA, and operations.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: ingestion_and_indexing.md, ../../core/prompt_builder.py, ../../core/oracle_service.py, ../operations/agentic_oracle_sop.md
- Exit Criteria: Engineers can implement answer behavior and QA can verify it against explicit rules.

## Retrieval-First Policy

- Retrieval is mandatory for `ask`.
- The model is not the source of truth.
- If retrieval is empty or weak, the answer must say the archive does not contain a grounded answer.
- Direct, deterministic summaries are preferred over speculative creativity.

## Prompt Policy

- include only the question and a small set of local passages
- state the word budget explicitly
- forbid unsupported extrapolation
- instruct the model to admit insufficiency rather than guess

## Response Policy

- default answer limit: 40 words
- one concise reply message per question unless radio constraints require splitting
- preserve privacy constraints for all command types
- do not reveal operator-only metadata, file paths, or internal source layout in answers

## Safety Rules

- never answer public mesh questions
- never return coordinates publicly
- never treat model priors as evidence
- refuse or deflect if content is unsafe, missing, or not grounded

## Fallback Rules

- if the model runtime is unavailable, return a deterministic retrieval summary when possible
- if both retrieval and model paths fail, return a short archive-unavailable message
- if the radio layer is unstable, fail visibly in operator logs rather than pretend success

## Prototype V1 Defaults

- retrieval backend: SQLite FTS
- local model runtime: `llama.cpp` with GGUF model files
- top-k context: 3 passages unless testing requires adjustment
- default public broadcast interval: 90 minutes
