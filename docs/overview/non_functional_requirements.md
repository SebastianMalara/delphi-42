# Non-Functional Requirements

- Purpose: Define Prototype v1 operating targets for performance, privacy, maintainability, and field viability.
- Audience: Engineering, QA, and operations.
- Owner: Systems Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: project_brief.md, scope_and_non_goals.md, ../testing/requirements_traceability.md
- Exit Criteria: Each requirement has a measurable target and a corresponding verification approach.

## Requirements

| ID | Requirement | Target | Verification |
| --- | --- | --- | --- |
| NFR-001 | Offline operation | Core question/answer and archive access work without internet | Field acceptance and recovery tests |
| NFR-002 | Privacy | User questions and node position are never disclosed on public mesh channels | Unit tests, log review, field protocol |
| NFR-003 | Answer latency | Median `ask` response under 30 seconds on prototype hardware for curated corpus | Benchmarks and field test |
| NFR-004 | Response size | Default reply stays within 40 words unless operator overrides config | Unit tests and manual verification |
| NFR-005 | Recoverability | Operator can restore service from reboot or service crash using runbooks in under 15 minutes | Ops drill |
| NFR-006 | Maintainability | New contributor can stand up dev environment and run tests in under 30 minutes | Onboarding exercise |
| NFR-007 | Storage discipline | Corpus, indexes, and models remain outside git and are reproducibly rebuildable | Repo policy and ingest validation |
| NFR-008 | Power awareness | Prototype hardware plan supports 24-hour operation with documented solar and battery assumptions | Hardware review and field power test |
| NFR-009 | Observability | Service health, retrieval hits, and index status are locally observable without leaking private payloads | Ops validation |
| NFR-010 | Documentation completeness | Engineering and operations can execute build, deploy, and recovery steps from repo docs alone | Completeness review |

## Measurement Notes

- Latency targets assume a prototype corpus and a small local model.
- Power targets are planning values until field data is captured.
- Documentation completeness must be validated by a different reader than the author.
