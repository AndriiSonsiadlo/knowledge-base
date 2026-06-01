---
id: comparison
title: Vector Store Comparison
sidebar_label: Comparison
sidebar_position: 6
tags: [langchain, vector-stores, comparison, tradeoffs]
---

# Vector Store Comparison

| Store | Local / Hosted | Setup effort | Metadata filtering | Scale ceiling | Cost model | Pick it when |
|---|---|---|---|---|---|---|
| [Chroma](./chroma.md) | Local | Trivial — `pip install` | Yes, built-in | Small-to-medium | Free (your disk) | Learning, prototyping |
| [FAISS](./faiss.md) | Local | Trivial — `pip install` | None built-in | Medium, bounded by RAM | Free (your disk) | Batch jobs, notebooks, single-process apps |
| [pgvector](./pgvector.md) | Local or self-hosted | Moderate — Postgres extension | Yes, full SQL | Medium-to-large | Your Postgres bill | Already running Postgres |
| [Pinecone](./pinecone.md) | Hosted | Low — managed API | Yes, built-in | Large | Per-index-hour, not per-query | Large hosted workload, no ops team |

## Recommendation

- **Learning or a new prototype:** start with Chroma — zero setup cost, easy to throw away.
- **Already running Postgres:** pgvector keeps vectors next to the relational data they describe, one system instead of two.
- **Large-scale hosted workload with no infrastructure team:** Pinecone trades cost for zero operations.

## See also

- [Overview](./overview.md) — the shared `VectorStore` interface every row above implements.
- [RAG Pipeline](../04-retrieval/rag-pipeline.md) — where a vector store plugs into a full retrieval chain.
