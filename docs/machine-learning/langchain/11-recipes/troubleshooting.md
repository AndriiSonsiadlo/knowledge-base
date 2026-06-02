---
id: troubleshooting
title: Troubleshooting
sidebar_label: Troubleshooting
sidebar_position: 5
tags: [langchain, troubleshooting, errors, debugging]
---

# Troubleshooting

Common failure modes across this section, and where to go for the full explanation.

| Symptom | Likely cause | Fix |
|---|---|---|
| `ImportError` / `ModuleNotFoundError` for a class that "used to work" | Following a pre-1.x tutorial; the class moved to `langchain-community` or was renamed in the [0.x → 1.x split](../00-overview/versions-and-migration.md) | Check the [migration table](../00-overview/versions-and-migration.md) for the current import path. |
| `RateLimitError` from the provider | Too many requests too fast, especially from a wide [`batch`](../03-composition/async-and-batching.md) call | Lower `max_concurrency`, add [retries and fallbacks](../03-composition/config-and-fallbacks.md). |
| Context-length / token-limit error | Chat history grew unbounded over a long conversation | Apply [trimming or summarization](../08-memory/trimming-and-summarization.md). |
| Retriever returns nothing relevant | Chunking or embedding mismatch, not a prompt problem | Print `retriever.invoke(question)` directly and inspect it — see the pitfall note in [RAG Pipeline](../04-retrieval/rag-pipeline.md); also check the query and index used the [same embedding model](../04-retrieval/embeddings.md). |
| Model never calls a tool it clearly has access to | Vague tool name or docstring | Rewrite the description — see the pitfall note in [Custom Tools](../06-tools-and-agents/custom-tools.md). |
| `with_structured_output` raises or returns `parsing_error` | Schema too large, too nested, or ambiguous for the model | Flatten the schema, add field descriptions — see [Structured Output](../02-core-primitives/structured-output.md) and the failure-routing pattern in [Structured Extraction](./structured-extraction.md). |
| Agent loops until it hits a step limit or your budget | Router never returns `END`, or the model keeps re-requesting the same tool | Set an explicit recursion/step limit — see the pitfall note in [Conditional Edges](../07-langgraph/conditional-edges.md). |
| Chain hangs, no tokens stream until the very end | A non-streaming step (e.g. an output parser) sits in the middle of the chain and buffers everything behind it | See the buffering-barrier explanation in [Streaming](../03-composition/streaming.md). |

:::tip
Most of these stop being mysterious once you look at the actual data flowing through the chain — a trace in [LangSmith](../09-langsmith/tracing.md) shows the exact input and output at every step, which is usually faster than guessing from the final error.
:::

## See also

- [Versions and Migration](../00-overview/versions-and-migration.md) — the single biggest source of stale-tutorial errors.
- [Tracing](../09-langsmith/tracing.md) — inspecting what actually happened, step by step.
