---
id: serving-patterns
title: Serving Patterns
sidebar_label: Serving Patterns
sidebar_position: 11
tags: [mlops, serving, inference, api]
---

# Serving Patterns

Choosing between an overnight batch job and a 50-millisecond synchronous API is not a minor implementation detail — it changes almost every other decision downstream, from infrastructure to model architecture to error handling. The serving pattern should be chosen deliberately, before the model is designed, not bolted on after.

:::info[Key idea]
The serving pattern is set by latency and freshness requirements, and it should be chosen before the model is designed.
:::

## Batch scoring: cheapest, simplest, and sufficient more often than teams assume

Run predictions on a scheduled job over a batch of inputs, writing results somewhere to be read later — no real-time infrastructure, no latency budget to manage, the simplest and cheapest pattern by a wide margin. Many use cases (daily risk scores, weekly recommendations refreshed overnight) genuinely don't need anything more real-time than this, even when a team defaults to building real-time infrastructure out of habit.

## Real-time synchronous serving

A client sends a request, waits, and receives a prediction directly in the response — required when a decision is needed immediately as part of an interactive flow (a fraud check blocking a transaction). This is the pattern with the tightest latency budget and the most operational complexity of the options here.

## Asynchronous and queued inference for long jobs

For predictions that take longer than an interactive request can wait for (a large model, a complex pipeline), accept the request immediately, queue the actual inference work, and let the client poll or receive a callback when the result is ready — decoupling request latency from inference latency entirely.

## Streaming inference

Process a continuous stream of inputs (sensor data, log events) as they arrive, producing predictions incrementally rather than per discrete request — the same batch/streaming distinction from [Data Pipelines and Contracts](./data-pipelines-and-contracts.md), applied to inference rather than ingestion.

## Embedded and edge inference

Run the model directly on the client device (a phone, an IoT sensor) rather than calling a remote service — eliminates network latency and works offline, at the cost of the deployment and update constraints [Deploying Vision Models](../04-computer-vision/deploying-vision-models.md)'s edge-deployment discussion covers (limited memory, no easy over-the-air model swap).

## A decision table

| Pattern | Latency | Freshness | Complexity |
|---|---|---|---|
| Batch scoring | hours | stale until next run | lowest |
| Real-time synchronous | milliseconds | current | highest |
| Async/queued | seconds-minutes | current | moderate |
| Streaming | near-real-time | current | high |
| Embedded/edge | milliseconds | tied to deployed model version | moderate, different constraints |

## The API surface: request schema, validation, versioning, error contracts

A real-time serving API needs the same discipline as any production API: an explicit, validated request schema (rejecting malformed input loudly, not silently misinterpreting it — [Data Pipelines and Contracts](./data-pipelines-and-contracts.md)'s validation-on-arrival principle applied to inference requests), API versioning as the model or its input schema evolves, and a well-defined error contract clients can actually handle.

## Request batching and its latency/throughput trade

Grouping several incoming requests into a single batch before running inference improves GPU utilisation and total throughput (the [GPU Training and Mixed Precision](../02-deep-learning/gpu-training-and-mixed-precision.md) batching argument, applied at serving time) — at the direct cost of added per-request latency, since a request may wait briefly for a batch to fill. The right batch size and wait window is a deliberate trade, not a default to leave unexamined.

$$
\text{throughput} \approx \frac{\text{batch size}}{\text{batch processing time}}, \qquad \text{added latency} \approx \text{batch wait window}
$$

## Autoscaling, cold starts, and model load time

Scaling serving capacity up and down with demand saves cost, but a newly-started instance needs to *load* the model before it can serve anything — a **cold start** — which can itself take seconds for a large model, directly hurting latency for whichever request happens to trigger the scale-up. Pre-warming instances or keeping a minimum baseline running are the standard mitigations.

## Timeouts, retries, and idempotency

Every network call needs an explicit timeout (an inference request that hangs indefinitely blocks resources and degrades everything behind it), and retries need the underlying operation to be idempotent (retrying a prediction request should be safe to do, producing the same result, not a side effect that compounds on repeat).

## Graceful degradation: what to serve when the model is unavailable

Deciding *in advance* what to return when the model service is down or overloaded — a cached previous prediction, a simple rule-based fallback, an explicit "unavailable" signal the caller can handle — is meaningfully better than an unhandled failure propagating up and breaking the calling system entirely.

## Preprocessing parity between training and serving, enforced by shared code

Exactly [Deploying Vision Models](../04-computer-vision/deploying-vision-models.md)'s preprocessing-parity concern, generalised: the only reliable way to guarantee training and serving preprocess identically is for both to *import the same code*, not to maintain two separately-written implementations that are supposed to match — a supposed match is exactly where skew silently creeps in.

| Symbol | Meaning |
|---|---|
| cold start | the latency cost of loading a model into a freshly-started instance |
| batch wait window | how long requests wait to be grouped into a batch |

## Code: a minimal prediction service with validation, versioning, and shared preprocessing

```python title="serving_patterns_demo.py"
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np

# --- Shared preprocessing module, imported by BOTH training and serving (never duplicated) ---
def preprocess(age: float, income: float, score: float) -> np.ndarray:
    return np.array([[age / 100.0, income / 100000.0, score]])

class PredictionRequestV1(BaseModel):
    age: float = Field(ge=0, le=120)
    income: float = Field(ge=0)
    score: float = Field(ge=0, le=1)

class PredictionResponse(BaseModel):
    prediction: float
    model_version: str

app = FastAPI()
MODEL_VERSION = "v1.2.0"

def fake_model_predict(X: np.ndarray) -> float:
    return float(X.sum())  # stand-in for a real loaded model's .predict call

@app.post("/v1/predict", response_model=PredictionResponse)
def predict_v1(request: PredictionRequestV1):
    try:
        X = preprocess(request.age, request.income, request.score)  # identical to training's preprocessing
        prediction = fake_model_predict(X)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"inference failed: {e}")
    return PredictionResponse(prediction=prediction, model_version=MODEL_VERSION)

@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}

# --- A batch scoring script using the identical preprocessing function ---
def batch_score(records: list[dict]) -> list[float]:
    return [fake_model_predict(preprocess(**r)) for r in records]

if __name__ == "__main__":
    batch_records = [{"age": 30, "income": 50000, "score": 0.7}, {"age": 45, "income": 80000, "score": 0.4}]
    results = batch_score(batch_records)
    print(f"batch scoring results: {results}")
```

## See also

- [Inference Optimization](./inference-optimization.md) — reducing per-request latency once the serving pattern is chosen.
- [FastAPI Patterns](../langchain/10-deployment/fastapi-patterns.md) — LLM-specific serving patterns that build on the same principles.
