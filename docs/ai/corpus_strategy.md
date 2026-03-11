# Corpus Strategy

- Purpose: Define the Prototype v1 content scope, curation rules, and source priorities for the offline knowledge base.
- Audience: AI, ingest, and project leads.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: ../overview/scope_and_non_goals.md, ingestion_and_indexing.md, ../project/adrs/0004-corpus-scope.md
- Exit Criteria: The team can stage a prototype corpus with clear inclusion and exclusion rules.

## Corpus Priorities

Prototype v1 prioritizes high-value, low-ambiguity content:

1. first aid and emergency response
2. water purification and sanitation
3. shelter, fire, and survival basics
4. repair guides for common tools and systems
5. curated general reference content for simple factual questions

## Inclusion Rules

- offline-readable licensing or operator-rights clarity
- practical field usefulness
- plain language or extractable structure
- manageable size for local storage and indexing
- stable source identifiers for rebuilds

## Exclusion Rules

- content requiring live internet updates
- content with unclear redistribution rights for offline staging
- large low-value corpora that crowd out practical field knowledge
- sources too noisy for reliable extraction without heavy post-processing

## Corpus Packaging Strategy

- keep a curated plaintext corpus for essential answers
- support Kiwix/ZIM for larger on-site browsing collections
- treat the retrieval corpus and the browse corpus as related but not necessarily identical

## Update Cadence

- bench refresh during development
- planned content refresh before each field trial
- no autonomous live sync in Prototype v1
