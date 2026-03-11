# Deployment Runbook

- Purpose: Provide the end-to-end procedure for deploying a Delphi-42 node from repo checkout to running services.
- Audience: Operators and builders.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-11
- Dependencies: raspberry_pi_provisioning.md, service_operations.md, ../architecture/interfaces_and_config.md
- Exit Criteria: An operator can deploy a new node using this runbook without relying on tribal knowledge.

## Deployment Steps

1. Provision the Raspberry Pi using [`raspberry_pi_provisioning.md`](raspberry_pi_provisioning.md).
2. Clone or copy the repository to `/opt/delphi-42`.
3. Create `.venv` and run `pip install -e .`.
4. Copy `config/oracle.example.yaml` to `config/oracle.yaml`.
5. Set site-local values:
   - radio device path
   - index and corpus paths
   - local model path
   - hotspot SSID
6. Stage the initial corpus under the configured plaintext directory.
7. Build the initial index:

```bash
python -m ingest.build_index --input-dir /opt/delphi-42/data/library/plaintext --db /opt/delphi-42/data/index/oracle.db
```

8. Install `systemd` units and reload the daemon.
9. Start the bot service and verify local logs.
10. Validate one `help`, one `ask`, and one `where` flow before field deployment.

## Deployment Outputs

- valid runtime config
- present model and corpus
- populated SQLite index
- running bot service
- reachable hotspot archive

## Rollback Rule

If any deployment step fails after service install:

- stop services
- restore previous config and data snapshot if available
- verify radio and storage mounts
- rebuild the index before attempting restart
