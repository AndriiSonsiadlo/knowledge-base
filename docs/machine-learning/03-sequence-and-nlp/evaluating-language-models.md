---
id: evaluating-language-models
title: Evaluating Language Models
sidebar_label: Evaluating Language Models
sidebar_position: 16
tags: [nlp, evaluation, benchmarks, metrics]
---

# Evaluating Language Models

The hardest part of working with language models isn't building one — it's knowing, with any confidence, whether the new version is actually better. There's no single number that captures "good," and the real skill in evaluation is knowing each imperfect proxy's specific blind spot well enough to know when it's lying to you.

:::info[Key idea]
There is no single number - evaluation is a portfolio of imperfect proxies, and knowing each one's blind spot is the actual skill.
:::

## Why perplexity doesn't track usefulness

[Language Modeling Basics](./language-modeling-basics.md) already flagged this: perplexity measures how well a model predicted specific held-out text — it says nothing about whether a model's actual generated responses are coherent, helpful, or correct. Two models with near-identical perplexity can differ substantially on every dimension a user actually cares about.

## n-gram overlap metrics: BLEU, ROUGE, METEOR

**BLEU** (originally for translation): the geometric mean of n-gram precision (what fraction of the candidate's n-grams appear in the reference) across several n-gram lengths, multiplied by a **brevity penalty** discouraging artificially short outputs that could otherwise game precision. **ROUGE** (originally for summarisation): n-gram *recall*-oriented — what fraction of the reference's n-grams appear in the candidate. **METEOR**: extends beyond exact n-gram matching to include stemming and synonym matching, addressing some of BLEU's brittleness to paraphrasing.

$$
\text{BLEU} = BP \cdot \exp\left(\sum_{n=1}^N w_n \log p_n\right)
$$

| Symbol | Meaning |
|---|---|
| $BP$ | brevity penalty |
| $p_n$ | n-gram precision at length $n$ |
| $w_n$ | weight for each n-gram length (typically uniform) |

## What n-gram metrics miss

A semantically perfect paraphrase that shares almost no exact n-grams with the reference scores badly on BLEU/ROUGE, despite being a genuinely correct output — these metrics measure surface overlap, not meaning, and penalise exactly the kind of legitimate rephrasing a good model might produce.

## Embedding-based metrics: BERTScore

Rather than exact token overlap, compute similarity between candidate and reference using contextual embeddings ([Word Embeddings](./word-embeddings.md), [Transformer Variants](./transformer-variants.md)) — matches semantically similar but lexically different words, addressing the paraphrase problem n-gram metrics suffer from, at the cost of depending on the quality of whatever embedding model computes the similarity.

## Exact-match and F1 for extractive tasks

For tasks with a clearly defined correct span (extractive question answering), exact-match (does the predicted span exactly equal the reference) and token-level F1 (partial credit for overlapping but not identical spans) are standard and considerably more reliable than for open-ended generation, precisely because the task has a genuinely narrow correct answer.

## Pass@k for code

For code generation: generate $k$ candidate solutions, and count success if *any* of them passes the test suite — reflects the practical reality that a developer using a code-generation tool can review and pick among several suggestions, rather than being stuck with exactly one.

## Benchmark suites and contamination

Standardised test suites probing knowledge, reasoning, or instruction-following provide comparability across models and over time. **Benchmark contamination**: if benchmark questions (or very similar ones) leaked into a model's pretraining data, its benchmark score reflects memorisation rather than the capability the benchmark was designed to measure — an increasingly serious concern as pretraining corpora scale to a large fraction of publicly available text, some of which inevitably includes benchmark content itself.

## LLM-as-judge

Use a separate (often more capable) language model to score or compare outputs, rather than a human or a fixed metric — scales far better than human evaluation, but has documented, systematic biases: a **position bias** (favouring whichever response is presented first or second, depending on the specific judge model), and a **verbosity bias** (favouring longer responses somewhat independent of actual quality). Mitigations include randomising presentation order across repeated evaluations and averaging, and explicitly controlling for length in the judging prompt or the analysis.

## Human evaluation and pairwise preference

Asking human raters to compare two outputs directly ("which response is better?") tends to produce more reliable, consistent judgments than asking for an absolute quality score on a fixed scale — comparative judgment is a substantially easier and more calibrated task for humans than absolute scoring, mirroring exactly the design choice behind [RLHF and Preference Optimization](../06-reinforcement-learning/rlhf-and-preference-optimization.md)'s preference-based training data.

## Task-specific evaluation sets as what actually matters

None of the general-purpose metrics above substitute for a curated evaluation set genuinely representative of your specific downstream task and its real failure modes — a **golden set**: a modest number (often just dozens to a few hundred) of hand-picked or hand-verified examples covering the cases that matter most for your actual use case.

## Regression testing a prompt or fine-tune

Before shipping a changed prompt, a new model version, or a fine-tune, run it against the golden set and compare scores directly against the previous version — catching a regression before it reaches users, the language-model analogue of a standard software regression test suite.

## Reporting variance, not a single run

Both generation (via sampling) and, to a lesser extent, LLM-as-judge scoring carry inherent run-to-run variance — report a score's spread across several runs (mean ± standard deviation, or a confidence interval) rather than treating a single run's number as a precise, final measurement, exactly the reproducibility discipline emphasised throughout [Model Selection and Tuning](../01-classical-ml/model-selection-and-tuning.md).

## Code: BLEU and ROUGE by hand, a paraphrase's low score, perplexity comparison

```python title="evaluating_llms_demo.py"
from collections import Counter
import numpy as np

def ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def bleu_precision(candidate, reference, n):
    cand_ngrams, ref_ngrams = Counter(ngrams(candidate, n)), Counter(ngrams(reference, n))
    overlap = sum(min(count, ref_ngrams[gram]) for gram, count in cand_ngrams.items())
    return overlap / max(len(cand_ngrams), 1)

def simple_bleu(candidate, reference, max_n=4):
    candidate, reference = candidate.split(), reference.split()
    precisions = [bleu_precision(candidate, reference, n) for n in range(1, max_n + 1)]
    if min(precisions) == 0: return 0.0
    bp = min(1.0, np.exp(1 - len(reference) / len(candidate)))
    return bp * np.exp(np.mean(np.log(precisions)))

def rouge_recall(candidate, reference, n=1):
    candidate, reference = candidate.split(), reference.split()
    cand_ngrams, ref_ngrams = Counter(ngrams(candidate, n)), Counter(ngrams(reference, n))
    overlap = sum(min(count, cand_ngrams[gram]) for gram, count in ref_ngrams.items())
    return overlap / max(len(ref_ngrams), 1)

reference = "the cat sat quietly on the warm mat"
exact_match = "the cat sat quietly on the warm mat"
paraphrase = "a feline rested calmly upon the cozy rug"

print("exact match  BLEU:", round(simple_bleu(exact_match, reference), 3))
print("paraphrase   BLEU:", round(simple_bleu(paraphrase, reference), 3),
      " <- near zero, despite being a semantically correct paraphrase")
print("exact match  ROUGE-1:", round(rouge_recall(exact_match, reference), 3))
print("paraphrase   ROUGE-1:", round(rouge_recall(paraphrase, reference), 3))

# --- Perplexity for two models on the same text ---
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def perplexity(model_name, text):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    ids = tokenizer(text, return_tensors="pt").input_ids
    with torch.no_grad():
        loss = model(ids, labels=ids).loss
    return torch.exp(loss).item()

text = "The cat sat on the mat and watched the birds outside."
print("\ndistilgpt2 perplexity:", round(perplexity("distilgpt2", text), 2))
```

## See also

- [Language Modeling Basics](./language-modeling-basics.md) — perplexity, and exactly what it does and doesn't measure.
- [Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md) — the metric-selection discipline this page applies to generation specifically.
