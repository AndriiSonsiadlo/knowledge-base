---
id: chat-models
title: Chat Models
sidebar_label: Chat Models
sidebar_position: 2
tags: [langchain, chat-models, providers, temperature]
---

# Chat Models

`init_chat_model` builds a chat model from a model name and provider string, so switching providers is a one-line change rather than a different import per vendor.

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai")
# model = init_chat_model("claude-sonnet-4-5", model_provider="anthropic")

response = model.invoke("What is retrieval-augmented generation?")
print(response.content)
```

## Common parameters

| Parameter | Effect | Sane default |
|---|---|---|
| `temperature` | randomness of sampling; 0 is near-deterministic | `0` for extraction/tool-calling, `0.7` for creative text |
| `max_tokens` | caps output length | set explicitly — providers cap differently and unbounded output costs money |
| `timeout` | seconds before the call is abandoned | 30–60s for interactive use |
| `max_retries` | automatic retry count on transient errors | 2 |

```python
model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    temperature=0,
    max_tokens=512,
    timeout=30,
    max_retries=2,
)
```

:::tip
Provider portability is real for the basics (`invoke`, `stream`, `temperature`) and leaky for the advanced features — batch structured-output modes, prompt caching controls, and reasoning-effort knobs differ per provider. Check the provider's integration page before relying on anything beyond the core `Runnable` methods.
:::

## See also

- [Structured Output](./structured-output.md) — constraining a chat model's response to a schema.
- [Config and Fallbacks](../03-composition/config-and-fallbacks.md) — retrying and failing over between models.
