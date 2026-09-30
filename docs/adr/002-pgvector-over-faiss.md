# ADR 002: pgvector over FAISS

Status: accepted (draft)

## Context
Runbook RAG needs a vector store; we already run Postgres.

## Decision
Use pgvector (HNSW, cosine) with fastembed bge-small-en-v1.5 (384 dims).

## Consequences
One fewer component; adequate for ~100 chunks.
