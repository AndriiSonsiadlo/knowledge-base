---
id: pgvector
title: pgvector
sidebar_label: pgvector
sidebar_position: 4
tags: [langchain, pgvector, postgres, vector-store]
---

# pgvector

pgvector is a Postgres extension that adds a vector column type and nearest-neighbour operators, so embeddings live next to the relational data they describe instead of in a separate system.

```bash
pip install -qU langchain-postgres
```

```python
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="my_docs",
    connection="postgresql+psycopg://user:password@localhost:5432/mydb",
)

vector_store.add_documents(documents)
```

## Why put vectors in Postgres

If your application already stores its relational data in Postgres, pgvector avoids running and operating a second database, keeps backups and transactions unified, and lets you join a vector search against ordinary SQL filters instead of maintaining metadata filtering logic in two places.

## Index types

| Index | Build time | Query speed | Recall | Use it when |
|---|---|---|---|---|
| None (exact) | none | slow at scale | exact | small dataset, correctness matters most |
| IVFFlat | fast | good | approximate, tunable | moderate dataset size, simpler tuning |
| HNSW | slower | fastest | approximate, high recall | larger dataset, query latency matters |

:::tip
Start with no index (exact search) while the collection is small — an approximate index is an optimization for scale, not a default you need on day one.
:::

## See also

- [Overview](./overview.md) — the shared `VectorStore` interface.
- [Comparison](./comparison.md) — pgvector against the alternatives.
