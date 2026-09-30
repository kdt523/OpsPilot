# ADR 004: k3s on a single EC2 instead of EKS

Status: accepted (draft)

## Context
EKS, RDS, NAT and load balancers bill hourly.

## Decision
Run k3s on one free-tier-eligible EC2 via Terraform; deploy through SSM, no SSH.

## Consequences
Near-zero cost and identical manifests to local k3d; no HA.
