---
id: custom-tools
title: Custom Tools
sidebar_label: Custom Tools
sidebar_position: 2
tags: [langchain, tools, decorator, pydantic, error-handling]
---

# Custom Tools

The `@tool` decorator turns a typed, documented function into something a model can call:

```python
from langchain.tools import tool

@tool
def search_orders(customer_id: str, status: str = "any") -> str:
    """Look up a customer's orders, optionally filtered by status.

    Args:
        customer_id: The customer's account ID.
        status: One of "any", "pending", "shipped", "delivered".
    """
    return f"3 orders found for {customer_id} (status={status})"
```

:::warning[Pitfalls]
The docstring is prompt-visible — it is part of the interface, not internal documentation. A vague description ("does stuff with orders") is the number one cause of the model picking the wrong tool or the right tool with wrong arguments. Write it the way you'd write an API doc a stranger has to use correctly on the first try.
:::

The function signature (with type hints) becomes the tool's argument schema; `langchain` generates it automatically. For richer validation — nested fields, constraints, custom error messages — pass an explicit Pydantic model as `args_schema` instead of relying on inference.

## Returning errors the model can recover from

A tool that raises lets the whole run crash unless something catches it. Prefer returning a string the model can read and react to, or use `wrap_tool_call` middleware to convert exceptions centrally:

```python
from collections.abc import Callable
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest

@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )

agent = create_agent(model="claude-sonnet-4-6", tools=[search_orders], middleware=[handle_tool_errors])
```

This keeps the run alive: the model sees the error as a `ToolMessage` and can retry with different arguments, pick a different tool, or give up gracefully — instead of your process crashing on a malformed lookup.

## See also

- [Tool Calling](./tool-calling.md) — the round trip a bound tool participates in.
- [Structured Output](../02-core-primitives/structured-output.md) — Pydantic schema design advice that applies equally to `args_schema`.
