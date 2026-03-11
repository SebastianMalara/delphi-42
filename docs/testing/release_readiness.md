# Release Readiness

- Purpose: Provide the go/no-go checklist for declaring Prototype v1 ready for a field trial or controlled release.
- Audience: Project leads, QA, and operations.
- Owner: Project Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: test_strategy.md, field_acceptance_protocol.md, ../project/risk_register.md
- Exit Criteria: Decision-makers have a single checklist for release readiness and open-risk review.

## Scope

This checklist applies to Prototype v1 milestone reviews and field-trial approval.

## Test Levels

- integration verification complete
- system verification complete
- field acceptance complete

## Environments

- local dev
- Pi bench
- field site

## Fixtures

- current code revision
- runtime config snapshot
- benchmark corpus
- prototype hardware kit

## Acceptance Criteria

- all critical test-matrix items complete
- no open privacy-critical incident
- execution-plan milestone dependencies satisfied
- open risks are either mitigated or explicitly accepted

## Evidence

- latest `pytest` result
- field acceptance sign-off
- execution plan status snapshot
- risk register review notes

## Go/No-Go Checklist

- required services start cleanly
- representative `ask` questions are grounded and useful
- `where` remains private
- hotspot archive is reachable
- backup and recovery steps were rehearsed
- no critical ADR remains undecided for the tested configuration
