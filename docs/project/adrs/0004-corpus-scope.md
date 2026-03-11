# ADR-0004: Prototype Corpus Scope

- Purpose: Record the Prototype v1 decision for corpus breadth and prioritization.
- Audience: AI, engineering, and project leadership.
- Owner: AI Lead
- Status: Accepted
- Last Updated: 2026-03-11
- Dependencies: ../../ai/corpus_strategy.md, ../../ai/evaluation_plan.md
- Exit Criteria: The team has a default corpus scope that is practical for Prototype v1 storage and evaluation.

## Context

The node cannot carry an unlimited corpus without harming storage, indexing, and relevance. Prototype v1 must prove usefulness with a manageable knowledge set.

## Decision

Prototype v1 uses a curated essential corpus focused on first aid, water, shelter, repair, and other practical field knowledge, with a separate larger browseable archive for on-site access.

## Consequences

- improves answer relevance for early field use cases
- keeps index size and evaluation scope manageable
- defers broad general-reference coverage until later iterations
