---
id: when-not-to-use
title: When not to use LangChain
sidebar_label: When not to use it
sidebar_position: 3
tags: [langchain, tradeoffs, architecture]
---

# When not to use LangChain

A framework earns its keep when it removes real complexity. For the simplest LLM use case — one
prompt, one call, parse the text — it mostly adds an abstraction layer over something you could
write in five lines with the provider's own SDK.

| Scenario | Best fit |
| --- | --- |
| Single prompt → single response, no retrieval, no tools | Raw provider SDK |
| Swapping providers, or composing prompt → model → parser | LangChain (LCEL) |
| Retrieval-augmented answers over your own documents | LangChain (retrieval + vector stores) |
| Multi-step tool use, loops, branching on model decisions | LangGraph |
| Needing to see what a chain/agent actually did across many runs | LangChain + LangSmith |

:::tip
Start with the provider SDK directly. Reach for LangChain when you hit the second orchestration
problem — swapping providers, chaining a parser onto a call, or adding retrieval. Reach for
LangGraph when a chain needs to loop or branch on what the model decided.
:::

The cost of adopting the framework early isn't large, but it isn't zero either: another
abstraction to learn, another place an error can originate, and a dependency surface that changes
faster than most. If your entire application is "format this prompt, call the model, return the
string," that overhead buys you nothing yet.

## See also

- [What is LangChain?](./what-is-langchain.md)
- [Ecosystem map](./ecosystem-map.md)
