SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

CLUSTER ?= opspilot

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

cluster-up: ## Create the k3d cluster (Phase 1)
	$(call stub,cluster-up,1)

cluster-down: ## Delete the k3d cluster
	k3d cluster delete $(CLUSTER)

monitoring: ## Install kube-prometheus-stack + alert rules (Phase 1)
	$(call stub,monitoring,1)

images: ## Build images and import into k3d (Phase 1 demo-shop, Phase 2 agent)
	$(call stub,images,1)

secrets: ## Create K8s Secrets from .env (Phase 2)
	$(call stub,secrets,2)

demo-shop: ## Helm install demo-shop baseline (Phase 1)
	$(call stub,demo-shop,1)

opspilot: ## Helm install OpsPilot (Phase 2)
	$(call stub,opspilot,2)

up: cluster-up monitoring images secrets demo-shop opspilot ## Whole local stack

down: cluster-down

chaos: ## make chaos SCENARIO=<id> (Phase 1)
	$(call stub,chaos,1)

reset: ## Reset demo-shop to baseline (Phase 1)
	$(call stub,reset,1)

eval: ## Full eval (Phase 5)
	$(call stub,eval,5)

eval-smoke: ## Smoke eval (Phase 5)
	$(call stub,eval-smoke,5)

test: test-python test-go test-dashboard ## Everything

test-python:
	cd agent && uv sync --quiet && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q

test-go:
	cd probe && go vet ./... && go test -race -cover ./...

test-dashboard:
	cd dashboard && npm ci --silent && npm run lint && npm run build

logs: ## Tail api + worker logs (Phase 2)
	$(call stub,logs,2)

port-forward: ## Prometheus 9090 / Alertmanager 9093 (Phase 1)
	$(call stub,port-forward,1)
