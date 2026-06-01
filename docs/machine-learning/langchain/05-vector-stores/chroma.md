---
id: chroma
title: Chroma
sidebar_label: Chroma
sidebar_position: 2
tags: [langchain, chroma, vector-store, local]
---

# Chroma

Chroma is a local-first, embedded vector database — no server to run, one `pip install`, data on disk. It's the default recommendation for learning and prototyping in this section.

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # omit for in-memory only
)

vector_store.add_documents(documents)
vector_store.similarity_search("query text", k=4, filter={"source": "intro"})
```

## Persistence and collections

Passing `persist_directory` writes the index to disk so it survives process restarts; omit it for a throwaway in-memory store during experimentation. A `collection_name` scopes documents — multiple collections can share one `persist_directory` without mixing results, useful for keeping test data separate from real data during development.

## Metadata filtering

The `filter` argument on `similarity_search` restricts candidates to documents whose metadata matches — set at load time in [Document Loaders](../04-retrieval/document-loaders.md), since metadata can't be recovered after chunking. Filtering runs alongside the vector search, not after it, so a narrow filter doesn't cost you full-index accuracy.

:::tip
Chroma is the right default while you're still iterating on chunking and retrieval strategy — the zero-setup cost means every dead end costs you nothing but time.
:::

## See also

- [Overview](./overview.md) — the shared `VectorStore` interface.
- [Comparison](./comparison.md) — when to graduate off Chroma.
