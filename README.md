# OpsPilot

AI incident-response agent for Kubernetes: alert in, diagnosis + policy-gated remediation out.

> Status: Phase 0 (scaffold). See `SPEC.md` §14 for the phase plan.

## Windows + WSL2 setup

1. `wsl --install -d Ubuntu-24.04`
2. Create `C:\Users\<you>\.wslconfig`:
   ```ini
   [wsl2]
   memory=8GB
   processors=4
   swap=4GB
   ```
   then `wsl --shutdown` and reopen Ubuntu.
3. Install Docker Desktop with the WSL 2 engine and WSL integration for Ubuntu-24.04.
4. In WSL: `sudo apt update && sudo apt install -y make git curl jq unzip build-essential`, then install
   kubectl, helm, k3d, Go 1.22+, uv, Node 20 (nvm), Terraform and AWS CLI v2.
5. Clone into the WSL filesystem (`~/code/opspilot`), never `/mnt/c`.
6. Run Claude Code inside WSL from the repo root.

## Quickstart (Phase 0)

```bash
make tools-check
make test
```

Copy `.env.example` to `.env` and fill in `OPSPILOT_GEMINI_API_KEY` and `OPSPILOT_WEBHOOK_TOKEN`.

## Phase 1: cluster, demo shop, monitoring

```bash
make cluster-up monitoring images demo-shop
make chaos SCENARIO=bad-image-tag   # PodNotHealthy fires within ~3 min
make reset                          # back to baseline
```

Grafana: http://localhost:8080/grafana (user `admin`; password in secret `monitoring/grafana-admin`,
or `GRAFANA_ADMIN_PASSWORD` from `.env`).

Native Windows note: if `kubectl` cannot reach the cluster via `host.docker.internal`, run
`kubectl config set-cluster k3d-opspilot --server=https://127.0.0.1:<port>` (port from `docker ps`).
