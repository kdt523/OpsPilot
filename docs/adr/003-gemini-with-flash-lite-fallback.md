# ADR 003: Gemini 2.5 Flash with Flash-Lite fallback

Status: accepted (draft)

## Context
Free-tier quota is low and models can rate-limit or fail.

## Decision
Primary gemini-2.5-flash, fallback gemini-2.5-flash-lite, shared Redis rate limiter, circuit breaker, daily cap, record/replay cassettes for tests.

## Consequences
Bounded cost and deterministic tests; fallback may be less accurate.
