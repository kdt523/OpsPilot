#!/usr/bin/env bash
# Create the monitoring-namespace secrets Alertmanager and Grafana need (idempotent).
# Values come from .env when present; otherwise random values are generated (never committed).
set -euo pipefail

cd "$(dirname "$0")/../.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi

rand() { head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24; }

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f - >/dev/null

# Alertmanager -> OpsPilot webhook token (must equal OPSPILOT_WEBHOOK_TOKEN in Phase 2)
if ! kubectl -n monitoring get secret opspilot-webhook >/dev/null 2>&1; then
  token="${OPSPILOT_WEBHOOK_TOKEN:-$(rand)}"
  kubectl -n monitoring create secret generic opspilot-webhook --from-literal=token="$token" >/dev/null
  echo "created secret monitoring/opspilot-webhook"
fi

if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  pw="${GRAFANA_ADMIN_PASSWORD:-$(rand)}"
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-literal=admin-password="$pw" >/dev/null
  echo "created secret monitoring/grafana-admin (user: admin)"
fi
