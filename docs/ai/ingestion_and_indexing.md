# Archive Staging

- Purpose: Specify the offline archive staging workflow for runtime `.zim` retrieval.
- Audience: AI, search, and software engineers.
- Owner: AI Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: corpus_strategy.md, ../../core/retriever.py
- Exit Criteria: A maintainer can stage allowlisted archives and understand the runtime retrieval expectations.

## Source Inputs

- allowlisted `.zim` archives staged under `data/library/zim`
- stable local aliases such as `medicine.zim`
- source manifests describing which archives feed a runtime

## Pipeline

1. Acquire source materials.
2. Preserve a stable runtime alias per archive, such as `medicine.zim`.
3. Spot-check representative queries with `python -m scripts.inspect_retrieval --config ... --question ...`.
4. If the source set changed, record the refresh manifest and validation notes.

## Retrieval Policy

- runtime retrieval comes directly from allowlisted `.zim` archives
- `llm-tools-kiwix` provides article search and read primitives
- Delphi-42 extracts sentence windows from read articles at answer time
- source IDs stay stable as `archive-name:path/to/article`

## Acceptance Gates

- allowlisted `.zim` archives are present under stable aliases
- representative queries return relevant passages
- stored source IDs remain stable between archive refreshes
- Kiwix or ZIM refreshes can be repeated without changing the runtime contract
