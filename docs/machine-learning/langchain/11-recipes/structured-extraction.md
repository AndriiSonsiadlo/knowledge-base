---
id: structured-extraction
title: Structured Extraction
sidebar_label: Structured Extraction
sidebar_position: 4
tags: [langchain, extraction, structured-output, recipe]
---

# Structured Extraction

Turn a pile of unstructured documents into validated records — [structured output](../02-core-primitives/structured-output.md) run in a batch loop, with a place to put the ones that don't validate.

```python
from pydantic import BaseModel, Field, ValidationError

from langchain.chat_models import init_chat_model


class Invoice(BaseModel):
    """Key fields extracted from an invoice."""
    vendor: str = Field(description="Name of the vendor issuing the invoice")
    invoice_number: str = Field(description="The invoice's unique identifier")
    total_amount: float = Field(description="Total amount due, in USD")
    due_date: str = Field(description="Due date, ISO 8601 format")


model = init_chat_model("gpt-4o-mini", model_provider="openai")
extractor = model.with_structured_output(Invoice, include_raw=True)

documents = [
    "Invoice #INV-2024-001 from Acme Supplies, due 2024-03-15, total $1,240.00",
    "Invoice #INV-2024-002 from Widget Co, due 2024-03-20, total $890.50",
]

extracted: list[Invoice] = []
failed: list[dict] = []

for doc in documents:
    result = extractor.invoke(f"Extract the invoice fields from:\n\n{doc}")
    if result["parsing_error"] is not None:
        failed.append({"document": doc, "error": str(result["parsing_error"])})
        continue
    extracted.append(result["parsed"])

print(f"Extracted {len(extracted)}, failed {len(failed)}")
```

`include_raw=True` is what makes the failure path possible — without it, a parsing failure raises instead of giving you a `parsing_error` field to branch on. Route failures to a dead-letter list (or queue) rather than letting one bad document stop the batch.

:::warning[Pitfalls]
A record that validates isn't necessarily correct — the schema enforces shape, not truth. `total_amount: 0.0` and `vendor: "Unknown"` both satisfy the schema while being useless. For a real pipeline, add a validator (Pydantic `field_validator`) that rejects obviously-placeholder values, or spot-check a sample against the source documents before trusting the batch.
:::

## See also

- [Structured Output](../02-core-primitives/structured-output.md) — the `with_structured_output` mechanics this batch loop wraps.
- [Async and Batching](../03-composition/async-and-batching.md) — running this loop with `abatch` instead of a sequential `for`.
