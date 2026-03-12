# Evaluation Plan

- Purpose: Define how Delphi-42 answer quality, retrieval behavior, and operational usefulness are evaluated for Prototype v1.
- Audience: AI, QA, and project leadership.
- Owner: QA Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: retrieval_and_response_policy.md, ../testing/test_strategy.md, ../testing/field_acceptance_protocol.md
- Exit Criteria: The team has a repeatable evaluation method for retrieval quality, answer quality, and operator readiness.

## Evaluation Tracks

- Retrieval quality: does the index return relevant passages for representative questions?
- Answer quality: is the returned answer grounded, short, and useful?
- Safety behavior: does the node refuse unsafe or ungrounded cases correctly?
- Operational behavior: can the node sustain repeated questions and restarts?

## Representative Question Set

- water purification
- hypothermia and first aid
- basic shelter construction
- field repair instructions
- location request and help flow
- unsupported or missing-corpus queries

## Metrics

| Metric | Target |
| --- | --- |
| Top-3 retrieval relevance | At least 80 percent of benchmark prompts have at least one relevant chunk |
| Grounded answer rate | At least 90 percent of accepted answers are traceable to retrieved text |
| Unsafe leakage rate | Zero public coordinate leaks and zero public answer leaks |
| Packet-budget compliance | At least 95 percent of answers respect the first-packet and continuation size contract |
| Operator recovery success | Full service recovery completed during drill |

## Evidence Collection

- saved benchmark prompts and expected source material
- retrieval hit/miss notes
- field test transcripts with sensitive details redacted
- operator drill notes for restart and recovery
- packetization test cases for short-answer and continuation behavior
