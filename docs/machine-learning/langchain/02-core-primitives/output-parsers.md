---
id: output-parsers
title: Output Parsers
sidebar_label: Output Parsers
sidebar_position: 5
tags: [langchain, parsers, output, json]
---

# Output Parsers

An output parser sits at the end of a chain and reshapes a model's raw output into something your code can use.

```python
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

chain = prompt | model | StrOutputParser()   # AIMessage -> str
json_chain = prompt | model | JsonOutputParser()  # AIMessage -> dict, parsed from prose
```

| Parser | Input assumption | Output |
|---|---|---|
| `StrOutputParser` | any `AIMessage` | `.content` as a plain string |
| `JsonOutputParser` | model was prompted to produce JSON | parsed `dict` |
| Pydantic-based parsing | model was prompted to match a schema | validated Pydantic instance |

:::warning[Pitfalls]
A parser can only reshape what the model already produced — it cannot force the model to produce valid JSON in the first place. If the model returns prose with a stray sentence before the JSON block, or omits a field, the parser raises or silently drops data. Treat parsing as a fallible post-processing step, not a guarantee.
:::

For anything where a malformed response is a real cost — extraction, tool arguments, anything downstream code trusts — prefer [Structured Output](./structured-output.md), which constrains the model itself rather than parsing after the fact.

## See also

- [Structured Output](./structured-output.md) — the stronger, provider-enforced alternative.
- [Runnables and LCEL](./runnables-and-lcel.md) — where a parser sits in a chain.
