---
id: multi-tool-routing
title: Multi-Tool Routing
sidebar_label: Multi-Tool Routing
sidebar_position: 5
tags: [langchain, tools, routing, guardrails]
---

# Multi-Tool Routing

Tool selection quality degrades as the tool list grows — with a handful of well-named tools the model picks correctly almost every time; past a few dozen, overlapping descriptions start colliding and the wrong tool gets called more often.

## Keeping a large tool list usable

- **Naming and description hygiene** — a tool's docstring is the only thing the model sees to decide between it and its neighbors. `get_user` and `fetch_user_by_id` reading almost identically is a routing bug waiting to happen; make the distinction explicit in both the name and the first line of the docstring.
- **Grouping and namespacing** — prefix related tools (`billing_get_invoice`, `billing_refund`) so the model can pattern-match on intent before it even reads the full description.
- **Pre-filtering per request** — don't bind every tool the application knows about to every call. Select a relevant subset (by category, by user permission, by retrieval over tool descriptions) before invoking the model. Fewer, more relevant options beat exposing everything every time.

:::danger
Tool results are untrusted input, not application output. A retrieved document, a scraped page, or an API response can carry text engineered to look like an instruction. Never let a tool's return value directly trigger a privileged action (another tool call, a write, a shell command) without your own code validating it first — the model reading it is not a security boundary. See [Security](../10-deployment/security.md) for the full trust-boundary picture.
:::

## See also

- [Custom Tools](./custom-tools.md) — writing tools with descriptions precise enough to route on.
- [Agent Concepts](./agent-concepts.md) — the loop this routing happens inside.
