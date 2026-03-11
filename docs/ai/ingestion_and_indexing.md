# Ingestion And Indexing

- Purpose: Specify the offline ingest pipeline from raw source material to searchable local index.
- Audience: AI, search, and software engineers.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: corpus_strategy.md, ../../ingest/chunker.py, ../../ingest/build_index.py
- Exit Criteria: A maintainer can rebuild the corpus pipeline and understand the chunking and indexing expectations.

## Source Inputs

- plaintext guides staged under `data/library/plaintext`
- extracted text derived from larger archive sources
- optionally curated snippets from ZIM or other offline packages after extraction

## Pipeline

1. Acquire source materials.
2. Extract text into normalized plaintext.
3. Preserve a stable `source_id` per document.
4. Chunk text into retrieval-sized passages.
5. Rebuild the SQLite FTS index.
6. Spot-check representative queries.

## Chunking Policy

- prefer semantically compact chunks over page-sized blocks
- target small enough chunks to fit a few passages into one prompt
- preserve source ID and ordinal so answers can be traced back
- avoid duplicate boilerplate across many chunks

## Indexing Policy

- SQLite FTS is the default Prototype v1 search backend
- index rebuild is deterministic from the staged corpus
- index file stays outside git and is treated as a generated artifact

## Acceptance Gates

- no fatal extraction errors
- index build succeeds from a clean working directory
- representative queries return relevant passages
- stored source IDs remain stable between rebuilds
