# Agentic Oracle SOP

- Purpose: Define the runtime operating procedure for Delphi-42 as a retrieval-first offline oracle.
- Audience: Engineering, operations, and QA.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: ../ai/retrieval_and_response_policy.md, ../architecture/runtime_flows.md, ../../core/oracle_service.py
- Exit Criteria: The runtime behavior of the oracle is specific enough to guide implementation, tests, and operations.

## Core Principles

- retrieval before generation
- private answers only
- no public location disclosure
- short responses for mesh reliability
- deterministic fallback over invented answers

## Runtime Roles

- radio handler: receive and route Meshtastic packets
- intent handler: normalize commands and protect command boundaries
- retriever: search the local index only
- synthesis layer: generate short grounded answers from retrieved text
- safety policy: block public leaks and ungrounded responses

## Supported Behaviors

- `help`: respond immediately with command list
- `where` and `pos`: return confirmation plus private position packet
- `ask <question>`: retrieve local material, build bounded prompt, return short grounded answer

## Required Guardrails

- ignore public questions
- never broadcast coordinates
- declare insufficient context when retrieval is weak
- keep logs privacy-safe by default
- keep the system useful when the model path fails by falling back to deterministic summaries where possible

## Operator Notes

- treat public channel 0 as scarce shared bandwidth
- keep broadcasts infrequent and non-specific
- validate the question-answer and private-position flows after any upgrade
