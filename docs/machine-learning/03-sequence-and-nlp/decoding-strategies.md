---
id: decoding-strategies
title: Decoding Strategies
sidebar_label: Decoding Strategies
sidebar_position: 15
tags: [nlp, generation, sampling, decoding]
---

# Decoding Strategies

The model outputs a probability distribution over the entire vocabulary at every step — something has to turn that distribution into an actual sequence of chosen tokens. That "something" is decoding, and it's a design decision entirely separate from the model itself: the same weights, decoded two different ways, can produce text that reads as either robotic and repetitive or lively and varied.

:::info[Key idea]
Decoding is a design decision separate from the model, and it changes output quality more than most fine-tuning does.
:::

<Figure
  src="/img/ml/nlp/decoding-strategies.png"
  alt="The same next-token distribution reshaped by low temperature, high temperature, top-k truncation and nucleus sampling"
  caption="All four operate on the same logits. Temperature rescales before the softmax; top-k keeps a fixed number of candidates; nucleus sampling keeps the smallest set reaching probability p, so the number of candidates adapts to how confident the model is."
/>

## Greedy decoding, and why it produces loops

At every step, pick the single highest-probability token. Cheap and deterministic, but prone to a specific, recognisable failure: once the model enters a locally-repetitive pattern (a phrase that scores well when repeated), greedy decoding has no mechanism to escape it, producing visible loops of repeated words or phrases.

## Beam search, and its open-ended-text problem

From [Seq2Seq and Encoder-Decoder](./seq2seq-and-encoder-decoder.md): track the top-$k$ partial sequences at each step rather than just one. Genuinely helps for tasks with a roughly "correct" answer (translation, where there's a reasonably narrow target) — but for open-ended generation, beam search tends to find the *single most probable* sequence, which is often bland, repetitive, and generic, since the most probable continuation is frequently the safest, most predictable one, not the most interesting.

## The likelihood trap

This is the core insight motivating sampling-based decoding: the highest-probability continuation of a prompt is often noticeably *worse*, by human judgement, than a continuation with somewhat lower but still substantial probability — natural human text simply isn't maximally predictable at every point, so chasing maximum likelihood produces text that reads as unnaturally repetitive and dull.

## Temperature

$$
p_i' = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}
$$

Rescales the logits before softmax. $T < 1$ sharpens the distribution (more confident, more deterministic, closer to greedy as $T \to 0$); $T > 1$ flattens it (more random, more diverse, approaching uniform sampling as $T \to \infty$); $T = 1$ leaves the original distribution unchanged.

## Top-k sampling

Restrict sampling to only the $k$ highest-probability tokens at each step, renormalising their probabilities to sum to 1, then sample from that restricted set — directly prevents the model from ever selecting from the long, low-probability tail, at the cost of a fixed $k$ that may be too restrictive in some contexts (where many tokens are plausible) and not restrictive enough in others (where very few are).

## Top-p (nucleus) sampling

Rather than a fixed count, restrict sampling to the *smallest* set of tokens whose cumulative probability exceeds a threshold $p$ (e.g. 0.9) — this set adaptively grows when the model is uncertain (probability spread across many tokens) and shrinks when the model is confident (probability concentrated in a few), addressing top-k's fixed-size limitation directly.

| Symbol | Meaning |
|---|---|
| $T$ | temperature — the logit-rescaling factor |
| $k$ | top-k sampling's fixed candidate-set size |
| $p$ | top-p sampling's cumulative-probability threshold |

## Min-p and typical sampling

**Min-p**: set a probability floor as a fraction of the top token's probability, rather than an absolute cumulative threshold — scales naturally with how confident the model is at a given step. **Typical sampling**: selects tokens whose information content (surprise) is close to the *expected* information content of the whole distribution, filtering out both the extremely predictable and the extremely surprising tokens.

## Repetition and frequency penalties

Directly penalise the logits of tokens that have already appeared in the generated text so far (a flat penalty, or one proportional to how many times the token has already appeared) — a blunter, more direct mitigation for repetition than relying on sampling randomness alone.

## Stopping criteria

Generation halts when an end-of-sequence token is produced, when a maximum length is reached, or when a user-specified stop sequence appears in the output — getting stopping criteria wrong produces either truncated (cut off mid-thought) or runaway (never stopping) generations.

## Constrained and grammar-guided decoding

For structured output (valid JSON, code matching a syntax), constrained decoding restricts the candidate token set at each step to only those tokens that would keep the output consistent with a target grammar or schema — guarantees syntactic validity by construction, rather than hoping the model happens to produce valid output and catching failures after the fact.

## Speculative decoding for latency

A small, fast "draft" model proposes several tokens ahead speculatively; the large target model then verifies all of them in a single parallel forward pass, accepting the draft tokens that match what the large model would have generated and only falling back to standard one-token-at-a-time generation where they diverge — a latency optimisation, not a quality change, since the final output is guaranteed to match what the large model would have produced on its own.

## Settings table by use case

| Use case | Suggested settings |
|---|---|
| Factual, precise answer | low temperature (or greedy), no/low top-p |
| Creative or varied text | higher temperature, top-p around 0.9–0.95 |
| Code generation | low temperature, often constrained decoding |
| Structured output (JSON, etc.) | constrained/grammar-guided decoding |

## Reproducibility: seeds and residual non-determinism

Fixing the random seed makes *sampling itself* reproducible — but identical settings can still diverge in practice due to floating-point non-determinism from parallel GPU operations (the exact order operations complete in can vary run to run), batching effects (a request's output can depend subtly on what else is in the same batch), or backend/version differences — full reproducibility discipline is covered in [Reproducibility](../07-production-mlops/reproducibility.md).

## Code: greedy, beam search, and temperature/top-p compared

```python title="decoding_strategies_demo.py"
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
model = AutoModelForCausalLM.from_pretrained("distilgpt2")
prompt = "The best way to learn machine learning is"
inputs = tokenizer(prompt, return_tensors="pt")

configs = {
    "greedy": dict(do_sample=False, num_beams=1),
    "beam search (k=5)": dict(do_sample=False, num_beams=5),
    "temperature=0.7": dict(do_sample=True, temperature=0.7, top_k=0, top_p=1.0),
    "top-p=0.9": dict(do_sample=True, temperature=1.0, top_p=0.9),
}

torch.manual_seed(0)
for name, kwargs in configs.items():
    output = model.generate(**inputs, max_new_tokens=25, pad_token_id=tokenizer.eos_token_id, **kwargs)
    print(f"[{name}]\n{tokenizer.decode(output[0], skip_special_tokens=True)}\n")

# --- The next-token distribution before/after temperature and top-p ---
with torch.no_grad():
    logits = model(**inputs).logits[0, -1]

def softmax(z): return torch.softmax(z, dim=-1)

original_probs = softmax(logits)
temp_probs = softmax(logits / 0.5)  # sharper
sorted_probs, sorted_idx = torch.sort(original_probs, descending=True)
cumulative = torch.cumsum(sorted_probs, dim=0)
top_p_cutoff = (cumulative <= 0.9).sum().item() + 1

print(f"original distribution: top token probability = {original_probs.max():.4f}")
print(f"after temperature=0.5: top token probability = {temp_probs.max():.4f}")
print(f"top-p=0.9 nucleus size: {top_p_cutoff} tokens")
```

## See also

- [Language Modeling Basics](./language-modeling-basics.md) — the next-token distribution decoding operates on.
- [Evaluating Language Models](./evaluating-language-models.md) — measuring whether a decoding strategy is actually working well.
