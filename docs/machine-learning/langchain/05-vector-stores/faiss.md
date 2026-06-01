---
id: faiss
title: FAISS
sidebar_label: FAISS
sidebar_position: 3
tags: [langchain, faiss, vector-store, local]
---

# FAISS

FAISS is an in-process similarity search library — the index lives in memory inside your Python process, with no server and no persistence unless you save it explicitly.

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = FAISS.from_documents(documents, embeddings)
vector_store.save_local("faiss_index")

loaded = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True,
)
```

## Save and load

`save_local`/`load_local` serialize the index to a folder on disk; there's no running service to point at, which makes FAISS well suited to batch jobs and notebooks but awkward for a multi-process web app sharing one index. The `allow_dangerous_deserialization` flag isn't decoration — see below.

:::warning[Pitfalls]
`load_local` unpickles a file. A FAISS index saved by an untrusted party is a code-execution vector, not just data — only load indexes you built or that came from a trusted source. FAISS also has no built-in metadata filtering comparable to Chroma or pgvector; filtering by metadata means post-filtering results in your own code, which costs you recall unless you over-fetch first.
:::

## See also

- [Overview](./overview.md) — the shared `VectorStore` interface.
- [Comparison](./comparison.md) — FAISS against the alternatives.
