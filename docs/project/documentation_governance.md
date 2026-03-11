# Documentation Governance

- Purpose: Define the structure, ownership, review policy, and quality checks for the Delphi-42 documentation suite.
- Audience: Maintainers, contributors, and project leads.
- Owner: Project Lead
- Status: Active
- Last Updated: 2026-03-11
- Dependencies: ../README.md, contributing.md, ../../scripts/check_docs.py
- Exit Criteria: The team can keep documentation complete, reviewable, and synchronized with implementation changes.

## Document Contract

Every controlled document in `docs/` must include:

- purpose
- audience
- owner
- status
- last updated
- dependencies
- exit criteria

## Required Review Triggers

- change to command behavior
- change to config schema
- change to deployment steps
- change to hardware assumptions
- change to privacy or safety policy
- change to execution-plan status

## Quality Checks

Run these before marking documentation work complete:

```bash
python scripts/check_docs.py
pytest
```

If `markdownlint` is available in the environment, also run it with the repo config:

```bash
markdownlint "**/*.md"
```

## Mermaid Rules

- keep diagrams small enough to review in diff
- prefer one diagram per concept rather than one giant diagram
- update adjacent text when diagrams change

## Ownership And Review

- each document has one role owner
- cross-cutting documents require review from all affected owners
- ADRs are the decision record when prose docs alone are insufficient

## Staleness Policy

- update `Last Updated` whenever materially changing a document
- broken links and missing metadata block a documentation change
- stale procedures discovered during drills must be corrected in the same workstream
