# ADR 001: Policy engine, not the LLM, decides

Status: accepted (draft)

## Context
An LLM proposing remediation actions can be wrong or manipulated via prompt injection in logs.

## Decision
The LLM only proposes. A deterministic policy engine (actions/policy.py) classifies each action as auto/approval/denied, and Kubernetes RBAC enforces the outer bound. Only actions/flow.py calls the executor.

## Consequences
Safer and auditable; some valid actions are blocked or need a human click.
