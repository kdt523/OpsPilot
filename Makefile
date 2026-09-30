SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

CLUSTER ?= opspilot
SHOP_IMAGE ?= ghcr.io/kdt523/opspilot-demo-shop

define stub
	@echo "[stub] $(1): implemented in Phase $(2)"
endef

.PHONY: help tools-check cluster-up cluster-down monitoring images secrets demo-shop opspilot up down \
        chaos reset eval eval-smoke test test-python test-go test-dashboard logs port-forward

help: ## List targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

tools-check: ## Verify required tools are installed
	@ok=1; \
	for t in docker k3d kubectl helm go uv node terraform; do \
	  if command -v $$t >/dev/null 2>&1; then printf '  ok       %s\n' $$t; \
	  else printf '  MISSING  %s\n' $$t; ok=0; fi; \
	done; \
	docker info >/dev/null 2>&1 && echo "  ok       docker daemon" || { echo "  MISSING  docker daemon running"; ok=0; }; \
	[ $$ok -eq 1 ] || { echo "tools-check failed (see README section 'Windows + WSL2 setup')"; exit 1; }

cluster-up: ## Create the k3d cluster (idempotent)
	@if k3d cluster list $(CLUSTER) >/dev/null 2>&1; then echo "cluster $(CLUSTER) already exists"; \
	else k3d cluster create $(CLUSTER) --servers 1 --agents 0 -p "8080:80@loadbalancer" \
	  --k3s-arg "--disable=metrics-server@server:0"; fi

cluster-down: ## Delete the k3d cluster
	k3d cluster delete $(CLUSTER)

monitoring: ## Install kube-prometheus-stack + alert rules
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update >/dev/null
	helm repo update >/dev/null
	bash deploy/monitoring/ensure-secrets.sh
	helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
	  -n monitoring --create-namespace -f deploy/monitoring/values-local.yaml --wait --timeout 10m
	kubectl apply -f deploy/monitoring/alert-rules.yaml

images: ## Build images and import into k3d (demo-shop now; agent in Phase 2)
	docker build -t $(SHOP_IMAGE):v1 demo-shop
	docker build -t $(SHOP_IMAGE):v2-bug --build-arg FAIL_RATE_DEFAULT=0.3 demo-shop
	k3d image import $(SHOP_IMAGE):v1 $(SHOP_IMAGE):v2-bug -c $(CLUSTER)

secrets: ## Create K8s Secrets from .env (Phase 2)
	$(call stub,secrets,2)

demo-shop: ## Helm install demo-shop baseline
	kubectl create namespace demo --dry-run=client -o yaml | kubectl apply -f -
	helm upgrade --install demo-shop deploy/helm/demo-shop -n demo --wait --timeout 5m

opspilot: ## Helm install OpsPilot (Phase 2)
	$(call stub,opspilot,2)

up: cluster-up monitoring images secrets demo-shop opspilot ## Whole local stack

down: cluster-down

chaos: ## make chaos SCENARIO=<id>
	@test -n "$(SCENARIO)" || { echo "usage: make chaos SCENARIO=<id>  (list: cd agent && uv run python ../chaos/inject.py --list)"; exit 2; }
	cd agent && uv run python ../chaos/inject.py $(SCENARIO)

# --force replaces resources so out-of-band chaos edits are reverted (a plain helm patch ignores drift)
reset: ## Reset demo-shop to baseline
	helm upgrade --install demo-shop deploy/helm/demo-shop -n demo --reset-values --force-replace --server-side=false --wait --timeout 5m

eval: ## Full eval (Phase 5)
	$(call stub,eval,5)

eval-smoke: ## Smoke eval (Phase 5)
	$(call stub,eval-smoke,5)

test: test-python test-go test-dashboard ## Everything

test-python:
	cd agent && uv sync --quiet && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q
	cd demo-shop && uv sync --quiet && uv run ruff check . && uv run pytest -q

test-go:
	cd probe && go vet ./... && go test -race -cover ./...

test-dashboard:
	cd dashboard && npm ci --silent && npm run lint && npm run build

logs: ## Tail api + worker logs (Phase 2)
	$(call stub,logs,2)

port-forward: ## Prometheus 9090 / Alertmanager 9093 to localhost (debug)
	@echo "Prometheus http://localhost:9090  Alertmanager http://localhost:9093 (Ctrl-C to stop)"
	@kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 & \
	kubectl -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093; kill %1
