---
id: installation
title: Installation
sidebar_label: Installation
sidebar_position: 1
tags: [langchain, installation, pip, uv, setup]
---

# Installation

LangChain 1.x ships as a set of small, independently-versioned packages instead of one monolith. Installing `langchain` alone gets you the orchestration layer — prompts, chains, agents — but no model provider.

:::warning
Installing `langchain` alone gives you no provider. You must also install a partner package (`langchain-openai`, `langchain-anthropic`, ...) for the model you actually want to call.
:::

## Pick your packages

| Package | What it gives you | Install it when |
|---|---|---|
| `langchain-core` | Base abstractions: `Runnable`, messages, prompt templates | Always — pulled in transitively by everything below |
| `langchain` | Chains, agents, orchestration built on `langchain-core` | You are writing application logic |
| `langchain-openai` | OpenAI / Azure OpenAI chat, embedding, and completion models | You call an OpenAI-compatible endpoint |
| `langchain-anthropic` | Anthropic Claude chat models | You call Claude |
| `langchain-community` | Third-party integrations without a dedicated partner package | You need a loader, tool, or store that has no official package |

## pip

```bash
pip install -U langchain langchain-openai
```

## uv

```bash
uv add langchain langchain-openai
```

Swap `langchain-openai` for whichever provider package you need — `langchain-anthropic`, `langchain-google-genai`, and so on follow the same pattern. Pin versions in a lockfile (`uv.lock` or `requirements.txt`) once you move past experimentation; LangChain's minor releases do carry breaking changes.

## See also

- [Versions and migration](../00-overview/versions-and-migration.md) — the version this section documents and what changed getting here.
- [Package layout](./package-layout.md) — why the packages are split this way.
- [Keys and config](./keys-and-config.md) — configuring credentials for the provider package you just installed.
