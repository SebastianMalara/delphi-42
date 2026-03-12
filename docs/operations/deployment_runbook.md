# Deployment Runbook

- Purpose: Provide the end-to-end procedure for deploying a Delphi-42 node from repo checkout to running services.
- Audience: Operators and builders.
- Owner: Ops Lead
- Status: Draft v1
- Last Updated: 2026-03-12
- Dependencies: raspberry_pi_provisioning.md, service_operations.md, ../architecture/interfaces_and_config.md
- Exit Criteria: An operator can deploy a new node using this runbook without relying on tribal knowledge.

## Preferred Packaging

Prototype v1 now prefers container packaging for the portable runtime:

- `oracle-app`, `oracle-indexer`, and `kiwix` run through `docker compose`
- the M5 `llm-openai-api` remains host-managed on the Pi
- use [`container_workflows.md`](container_workflows.md) for the default Mac and Pi Compose commands

## Deployment Steps

1. Provision the Raspberry Pi using [`raspberry_pi_provisioning.md`](raspberry_pi_provisioning.md).
2. Clone or copy the repository to `/opt/delphi-42`.
3. Create the persistent data directories used by the Pi Compose profile:
   - `data/library/plaintext`
   - `data/library/zim`
   - `data/index`
4. Copy or adapt `config/oracle.pi.yaml` for site-local values:
   - radio device path
   - index and corpus paths
   - `knowledge.zim_dir`
   - `knowledge.runtime_zim_allowlist`
   - `llm.base_url`
   - `llm.model`
   - hotspot SSID
6. Stage the initial retrieval corpus under the configured plaintext directory and the curated Kiwix ZIM set under the configured ZIM directory.
7. If the answer corpus includes `.zim` sources, export them into staged plaintext:

```bash
python -m ingest.extract_zim --zim-dir /opt/delphi-42/data/library/zim --output-dir /opt/delphi-42/data/library/plaintext --allowlist wikipedia_en_medicine_maxi_2023-12.zim
```

8. Build the initial index:

```bash
python -m ingest.build_index --input-dir /opt/delphi-42/data/library/plaintext --db /opt/delphi-42/data/index/oracle.db
```

9. Validate the local StackFlow service before starting Delphi-42:

```bash
curl http://127.0.0.1:8000/v1/models
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-" \
  -d '{"model":"qwen3-1.7B-Int8-ctx-axcl","messages":[{"role":"user","content":"Reply with READY"}]}'
```

10. Start the Compose stack:

```bash
docker compose -f compose.yaml -f compose.pi.yaml up --build -d
```

11. Validate one `help`, one `ask`, and one `where` flow before field deployment.

## Deployment Outputs

- valid runtime config
- present StackFlow model service and corpus
- populated SQLite index
- running `oracle-app` container
- reachable hotspot archive
- aligned retrieval index derived from the staged answer corpus

## Rollback Rule

If any deployment step fails after service start:

- stop containers
- restore previous config and data snapshot if available
- verify radio and storage mounts
- verify `llm-openai-api` health and visible model list
- rerun `extract_zim` if the allowlisted `.zim` corpus changed or the staged plaintext was lost
- rebuild the index before attempting restart
