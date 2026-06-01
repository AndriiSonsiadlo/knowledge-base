---
id: pinecone
title: Pinecone
sidebar_label: Pinecone
sidebar_position: 5
tags: [langchain, pinecone, vector-store, hosted]
---

# Pinecone

Pinecone is a managed, hosted vector database — no infrastructure to run, but the index itself is a billed cloud resource rather than a free local file.

```python
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="...")
index = pc.Index("example-index")

vector_store = PineconeVectorStore(embedding=embeddings, index=index)
vector_store.add_documents(documents, namespace="tenant-a")
```

## Index creation and namespaces

An index is created once (via the Pinecone console or API) with a fixed dimension and similarity metric — both must match the embedding model you plan to use, since a Pinecone index isn't automatically compatible with an arbitrary model. Namespaces partition a single index into isolated sub-collections, which is the usual pattern for multi-tenant applications instead of creating one index per tenant.

:::danger
The index dimension is set at creation and cannot be changed. If it doesn't match the embedding model's output size, every write or query fails outright — confirm the dimension before creating the index, not after.
:::

## Cost model

Pinecone bills per index-hour (roughly, capacity reserved), not per query — an idle index with low traffic still costs the same as a busy one at the same pod size. That's the opposite of a pay-per-query API and changes the calculus for spinning up throwaway indexes during development.

## See also

- [Overview](./overview.md) — the shared `VectorStore` interface.
- [Comparison](./comparison.md) — Pinecone against the alternatives.
