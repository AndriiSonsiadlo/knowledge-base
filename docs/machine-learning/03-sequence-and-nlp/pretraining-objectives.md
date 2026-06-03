---
id: pretraining-objectives
title: Pretraining Objectives
sidebar_label: Pretraining Objectives
sidebar_position: 12
tags: [nlp, pretraining, self-supervised, mlm]
---

# Pretraining Objectives

A language model isn't given labelled examples of "good writing" or "correct facts" — it's given unlabelled text and one instruction: predict something that was hidden. Where the knowledge in a modern language model actually comes from traces back to this single trick, repeated over trillions of tokens.

:::info[Key idea]
Pretraining converts unlabelled text into supervision by hiding part of it and asking the model to reconstruct what was hidden.
:::

## Self-supervision as manufactured labels

This is [Learning Paradigms](../00-foundations/learning-paradigms.md)'s self-supervised category made concrete: no human ever labels a single training example. The label is manufactured directly from the raw text — hide a word, the hidden word *is* the label; predict the next token, the next token *is* the label.

## Causal language modelling

Exactly [Language Modeling Basics](./language-modeling-basics.md)'s objective: predict $w_t$ given $w_{<t}$, at every position in the training corpus simultaneously (via the causal mask). The objective used to pretrain every decoder-only model in [Transformer Variants](./transformer-variants.md)'s GPT family.

## Masked language modelling: the 15% recipe

BERT's pretraining objective: randomly select 15% of input tokens; for those selected tokens, replace 80% with a special `[MASK]` token, 10% with a random other token, and leave the remaining 10% unchanged — then train the model to predict the *original* token at every one of those 15% selected positions, using full bidirectional context.

## Why the 80/10/10 split, specifically

If masked positions were *always* replaced with `[MASK]`, the model would only ever need to produce good representations for the artificial `[MASK]` token — a token that never appears at actual fine-tuning or inference time, creating a train/inference mismatch. Occasionally leaving the original token unchanged (10%) or replacing it with a random token (10%) forces the model to maintain a good representation for *every* position, not just the ones marked `[MASK]`, since it can never be sure in advance which positions will actually be checked against the true label.

## Next-sentence prediction, and why it was dropped

BERT's original pretraining also included a task of predicting whether two given sentences were originally adjacent in the source text — later analysis found this task added little useful signal beyond what masked language modelling alone already provided, and follow-up models (RoBERTa and others) dropped it with no loss in downstream quality, sometimes even an improvement.

## Span corruption (T5)

Rather than masking individual scattered tokens, mask contiguous *spans* of text (replacing each span with a single sentinel token), and train the decoder to generate the missing spans, one after another — a natural fit for T5's encoder-decoder architecture, unifying denoising with the sequence-generation objective the decoder needs anyway.

## Denoising objectives, more broadly

The general pattern behind BART and similar models: corrupt the input in some way (masking, deletion, sentence permutation, token shuffling), and train the model to reconstruct the original, uncorrupted text — masked language modelling and span corruption are both specific instances of this broader denoising family.

## Contrastive objectives for sentence embeddings

Rather than reconstructing corrupted text, contrastive pretraining trains a model so that semantically similar text pairs (two paraphrases, or two augmented views of the same passage) produce *close* embeddings, while unrelated pairs produce *distant* embeddings — the direct NLP analogue of [Self-Supervised Vision](../04-computer-vision/self-supervised-vision.md)'s contrastive image pretraining, and the standard approach for training dedicated sentence-embedding models.

| Symbol | Meaning |
|---|---|
| masking rate | fraction of tokens selected for the masked-LM objective (typically 15%) |
| span | a contiguous run of tokens masked as a single unit, rather than scattered individual tokens |

## Data: scale, deduplication, filtering

Pretraining corpora are now measured in trillions of tokens, scraped predominantly from web text. **Deduplication** (removing near-identical or exactly repeated passages) measurably improves downstream quality — models trained on heavily-duplicated data tend to memorise the duplicated content disproportionately. **Filtering** (removing low-quality, harmful, or off-target-language content) has increasingly been found to matter as much as, or more than, sheer data volume — a smaller, cleaner corpus frequently outperforms a larger, noisier one at the same compute budget, closely related to the compute-optimal findings in [Model Capacity and Scaling](../02-deep-learning/model-capacity-and-scaling.md).

## Compute cost and the pretrain/fine-tune division of labour

Pretraining is, by a wide margin, the most compute-expensive stage of a model's lifecycle — [Finetuning and Instruction Tuning](./finetuning-and-instruction-tuning.md)'s subsequent stages operate on a comparatively tiny fraction of that compute, since they start from an already-capable model rather than learning language structure from scratch.

## What pretraining does and does not teach

Pretraining on broad text teaches a great deal about language structure, factual associations present (and repeated) in the training data, and stylistic patterns — it does *not* reliably teach robust multi-step reasoning, does not guarantee factual accuracy (the model learns what's statistically common in its data, not what's true), and confers no inherent understanding of instructions or user intent — that behavioural shaping is exactly what [Finetuning and Instruction Tuning](./finetuning-and-instruction-tuning.md) exists to add on top.

## Continued pretraining for domain adaptation

Running additional pretraining (the same masked or causal objective) on a domain-specific corpus (legal text, medical literature, a codebase) after general pretraining, before task-specific fine-tuning — lets a model absorb the vocabulary, style, and factual associations of a specialised domain more cheaply than pretraining from scratch on that domain alone.

## Code: constructing MLM examples by hand, then a real masked prediction

```python title="pretraining_objectives_demo.py"
import random
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForMaskedLM.from_pretrained("bert-base-uncased")

def build_mlm_example(text, mask_prob=0.15, seed=0):
    rng = random.Random(seed)
    tokens = tokenizer.tokenize(text)
    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    labels = [-100] * len(input_ids)  # -100 means "not a masked position, ignore in loss"

    for i in range(len(input_ids)):
        if rng.random() < mask_prob:
            labels[i] = input_ids[i]  # the true token becomes the label at this position
            roll = rng.random()
            if roll < 0.8:
                input_ids[i] = tokenizer.mask_token_id
            elif roll < 0.9:
                input_ids[i] = rng.randint(0, tokenizer.vocab_size - 1)
            # else: leave unchanged (10% of the time)
    return input_ids, labels, tokens

text = "The transformer architecture revolutionized natural language processing"
input_ids, labels, original_tokens = build_mlm_example(text)
print("original tokens:", original_tokens)
print("masked input:   ", tokenizer.convert_ids_to_tokens(input_ids))
print("labels (only masked positions are non-trivial):", labels)

# --- A real masked-token prediction ---
masked_text = "The transformer architecture [MASK] natural language processing."
inputs = tokenizer(masked_text, return_tensors="pt")
mask_position = (inputs.input_ids[0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0]

with torch.no_grad():
    logits = model(**inputs).logits
top5 = torch.topk(logits[0, mask_position[0]], k=5)
print("\ntop-5 predictions for [MASK]:", tokenizer.convert_ids_to_tokens(top5.indices))
```

## See also

- [Language Modeling Basics](./language-modeling-basics.md) — the causal objective this page's decoder-side coverage builds on.
- [Finetuning and Instruction Tuning](./finetuning-and-instruction-tuning.md) — turning a pretrained model's capability into useful, instructable behaviour.
