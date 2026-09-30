# ADR 005: Grafana memory limit 384Mi (SPEC 4.3 says 192Mi)

Status: accepted

## Context
On the local k3d cluster the Grafana container was OOMKilled repeatedly at the 192Mi limit from SPEC 4.3.

## Decision
Raise Grafana to request 128Mi / limit 384Mi in `deploy/monitoring/values-local.yaml`.

## Consequences
Total cluster limits grow by ~192Mi, still within the ~5.5 GB budget.
