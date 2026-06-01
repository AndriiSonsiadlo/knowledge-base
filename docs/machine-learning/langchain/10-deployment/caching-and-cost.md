---
id: caching-and-cost
title: Caching and Cost
sidebar_label: Caching & Cost
sidebar_position: 3
tags: [langchain, caching, cost, tokens, optimization]
---

# Caching and Cost

Two independent caches matter in a LangChain app, and they solve different problems.

## LLM response caching

`set_llm_cache` caches a model call keyed on the exact prompt (and, with a semantic cache, on prompt *similarity*). A repeated or near-duplicate request skips the model call entirely.

```python
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache

set_llm_cache(InMemoryCache())
```

An exact-match in-memory cache is fine for development and for workloads with genuinely repeated prompts (a fixed classification prompt over many similar inputs). A semantic cache (Redis, Astra DB, and others expose one) matches paraphrases too, at the cost of an embedding lookup on every call and a similarity threshold that trades false-cache-hits against missed savings.

## Embedding caching

Embeddings are the cheap thing to cache and the expensive thing to recompute: re-embedding a document set on every app restart or every retriever rebuild burns real money for a deterministic result. `CacheBackedEmbeddings` wraps any embedding model with a key-value store so identical text is only embedded once.

```python
from langchain.embeddings import CacheBackedEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.storage import LocalFileStore

underlying = OpenAIEmbeddings(model="text-embedding-3-small")
store = LocalFileStore("./cache/embeddings")
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying, store, namespace=underlying.model
)
```

## Token accounting and model tiering

Track tokens per step (via [tracing](../09-langsmith/tracing.md)) before optimizing — the expensive step is rarely the one you assume. A common pattern once you know where cost concentrates: route cheap, high-volume sub-tasks (classification, extraction) to a smaller/cheaper model, and reserve the frontier model for the step that actually needs its reasoning.

| Lever | Typical saving | What it costs you |
|---|---|---|
| Exact-match LLM cache | High for repeated prompts, ~0 otherwise | Stale answers if the underlying data changes |
| Semantic LLM cache | Moderate, broader hit rate | Embedding lookup latency, false-hit risk |
| Embedding cache | High on re-index / restart | Cache invalidation when the embedding model changes |
| Model tiering by task | Often 5-10x on the delegated tasks | Extra routing logic, quality risk if misrouted |
| Prompt/context trimming | Moderate, compounds per call | Lost context, see [Trimming and Summarization](../08-memory/trimming-and-summarization.md) |

:::tip
Measure with a trace before optimizing. It's common to assume the model call is the expensive step when it's actually an uncached embedding call running on every request, or a retriever pulling far more chunks than the prompt needs.
:::

## See also

- [Tracing](../09-langsmith/tracing.md) — where per-step token and cost numbers come from.
- [Embeddings](../04-retrieval/embeddings.md) — why query and index embedding models must match, cache or not.
