---
id: versions-and-migration
title: Versions and migration
sidebar_label: Versions & migration
sidebar_position: 4
tags: [langchain, versions, migration, breaking-changes]
---

# Versions and migration

![PyPI](https://img.shields.io/pypi/v/langchain?label=langchain)
![PyPI](https://img.shields.io/pypi/v/langgraph?label=langgraph)

This section documents **LangChain 1.x (Python)**, the split-package layout
(`langchain-core`, `langchain`, provider packages such as `langchain-openai`, and
`langchain-community`). LangChain released 1.0 in October 2025, replacing its earlier chain and
agent abstractions with a single high-level agent abstraction (originally built in LangGraph, then
moved into `langchain`).

:::warning[Pitfalls]
Most LangChain tutorials and blog posts online still target the 0.x line. Imports like
`from langchain.chains import LLMChain` look correct but are deprecated — they will run under a
compatibility shim for a time, then stop working. Check the import against the tables below before
trusting an older example.
:::

## The 0.x → 1.x split

By mid-2024 LangChain had grown to hundreds of provider integrations living in one package. These
were split out: stable, provider-agnostic abstractions moved to `langchain-core`; each provider got
its own package (`langchain-openai`, `langchain-anthropic`, ...); community-maintained, less stable
integrations moved to `langchain-community`. See the setup section's package layout page for the
dependency shape this produced.

## Deprecated constructs and their replacements

| Deprecated | Replacement |
| --- | --- |
| `LLMChain` | LCEL: `prompt \| model \| parser` |
| `ConversationChain` | `MessagesPlaceholder` + explicit message history (see the memory section) |
| `initialize_agent` | `create_agent` (`langchain.agents`) |
| `ConversationBufferMemory` | Explicit message list management, or a LangGraph checkpointer for durable state |

## See also

- [What is LangChain?](./what-is-langchain.md)
