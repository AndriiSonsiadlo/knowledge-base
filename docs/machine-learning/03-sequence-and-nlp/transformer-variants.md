---
id: transformer-variants
title: Transformer Variants
sidebar_label: Transformer Variants
sidebar_position: 11
tags: [nlp, bert, gpt, t5, architecture]
---

# Transformer Variants

One architecture, three ways to cut it — and which cut you choose determines what the resulting model can actually do. The difference between a model that reads and a model that writes turns out to come down to one thing: the shape of the attention mask.

:::info[Key idea]
Encoder-only models read, decoder-only models write, encoder-decoder models transform — the difference is entirely in the attention mask and the training objective.
:::

## Encoder-only (BERT family)

Uses only the [Transformer Architecture](./transformer-architecture.md) encoder stack, with **bidirectional** self-attention — every position can attend to every other position, both before and after it, with no causal mask at all. This produces excellent contextual representations of the input (each token's final vector genuinely incorporates the whole surrounding sentence), but the architecture has no mechanism for autoregressive generation — there's no meaningful way to "generate the next token" when every position already attends freely to every other position, including ones that would need to be generated first.

## Decoder-only (GPT family)

Uses only the decoder stack, with **causal** (masked) self-attention — each position can only attend to itself and earlier positions. This naturally supports autoregressive generation (exactly [Language Modeling Basics](./language-modeling-basics.md)'s next-token prediction, one step at a time) and, importantly, the *same* architecture and training objective work uniformly for pretraining, fine-tuning, and generation — no separate encoder/decoder split to design or maintain.

## Encoder-decoder (T5, BART)

Uses the full original architecture: a bidirectional encoder processing the input, plus a causal decoder generating the output, connected via **cross-attention** (decoder queries, encoder keys/values — see [Attention Mechanism](./attention-mechanism.md)). Suits tasks with a genuinely distinct input/output structure — translation, summarisation — where the input deserves full bidirectional understanding before any output generation begins.

## The mask is the architecture

The striking thing about these three families: the underlying transformer block ([Transformer Architecture](./transformer-architecture.md)) is identical across all three. The *entire* architectural difference comes down to which attention mask is applied (none, causal, or a combination with cross-attention) and what training objective is paired with it — a remarkably small set of design choices producing three qualitatively different model behaviours.

## Comparison table

| | Encoder-only | Decoder-only | Encoder-decoder |
|---|---|---|---|
| Attention pattern | bidirectional | causal | bidirectional (encoder) + causal (decoder) + cross-attention |
| Pretraining objective | masked language modelling | causal language modelling | span corruption / denoising |
| Typical tasks | classification, NER, embeddings | open-ended generation, chat, code | translation, summarisation |
| How you use the output | the final hidden states directly | generated tokens, one at a time | generated tokens, conditioned on the full encoded input |

## Model families and rough sizes

**BERT-family** (encoder-only): from ~100M parameters (BERT-base) up to ~1B for larger variants, primarily used for classification and embedding tasks rather than generation. **GPT-family** (decoder-only): spans from small research models to hundreds of billions of parameters in current frontier systems. **T5-family** (encoder-decoder): typically ranges from ~60M to ~11B parameters across published variants.

## Why decoder-only won the scaling race

Three converging reasons: the uniform pretrain/fine-tune/generate objective simplifies both research and engineering; causal language modelling on raw, unlabelled text scales to enormous corpora with no annotation cost at all; and generation — the capability that turned out to matter most for the current wave of applications (chat, code, agents) — is what decoder-only naturally does, while encoder-only architecturally cannot do it at all.

## Mixture-of-experts, briefly

Rather than every input passing through every parameter (a **dense** model), a mixture-of-experts model routes each input (or token) to only a small subset of specialised "expert" sub-networks — this decouples **total parameter count** (which can be very large, since most experts sit unused for any given input) from **active parameter count per forward pass** (which stays comparatively small, and is what actually determines inference compute cost) — a way to scale total capacity without proportionally scaling inference cost.

## Choosing a base model for a task

| Task | Reach for |
|---|---|
| Text classification, embeddings, retrieval | encoder-only (BERT-family) |
| Open-ended generation, chat, code, agents | decoder-only (GPT-family) |
| Translation, summarisation with a clear input/output split | encoder-decoder (T5-family) |
| Uncertain, or want one model for many tasks | decoder-only, given its current ecosystem dominance |

## Code: the same sentence through both architecture families

```python title="transformer_variants_demo.py"
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM

sentence = "The transformer architecture changed everything."

# --- Encoder-only: bidirectional embeddings, no generation ---
bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
bert_model = AutoModel.from_pretrained("bert-base-uncased")
bert_inputs = bert_tokenizer(sentence, return_tensors="pt")
with torch.no_grad():
    bert_output = bert_model(**bert_inputs)
print("BERT output shape (per-token contextual embeddings):", bert_output.last_hidden_state.shape)

# --- Decoder-only: causal generation ---
gpt_tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
gpt_model = AutoModelForCausalLM.from_pretrained("distilgpt2")
gpt_inputs = gpt_tokenizer(sentence, return_tensors="pt")
with torch.no_grad():
    generated = gpt_model.generate(**gpt_inputs, max_new_tokens=15, do_sample=False)
print("GPT continuation:", gpt_tokenizer.decode(generated[0]))

# --- Printed attention masks for each variant ---
seq_len = 5
bidirectional_mask = torch.ones(seq_len, seq_len)
causal_mask = torch.tril(torch.ones(seq_len, seq_len))
print("\nbidirectional (encoder-only) mask:\n", bidirectional_mask.int())
print("causal (decoder-only) mask:\n", causal_mask.int())
```

## See also

- [Transformer Architecture](./transformer-architecture.md) — the shared block every variant here is built from.
- [Pretraining Objectives](./pretraining-objectives.md) — the training objectives paired with each mask pattern.
