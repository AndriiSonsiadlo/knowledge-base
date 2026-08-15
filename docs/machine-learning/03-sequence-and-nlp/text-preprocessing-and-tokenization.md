---
id: text-preprocessing-and-tokenization
title: Text Preprocessing and Tokenization
sidebar_label: Text Preprocessing & Tokenization
sidebar_position: 1
tags: [nlp, tokenization, preprocessing, bpe]
---

# Text Preprocessing and Tokenization

Models don't see text — they see a sequence of integers, and every choice about how those integers are assigned decides what the model can and can never learn. A tokeniser that splits "unbelievable" into three pieces lets the model reuse what it learned about "un-" and "-able" elsewhere; a tokeniser that treats it as one opaque unit has no such option.

:::info[Key idea]
Subword tokenisation is the compromise between an unbounded word vocabulary and a character sequence too long to model.
:::

<Figure
  src="/img/ml/nlp/tokenization-granularity.png"
  alt="The word tokenization split into characters, into two subword pieces, and kept as a single word token"
  caption="Characters give a tiny vocabulary but very long sequences; whole words give short sequences but a huge vocabulary that still breaks on unseen words. Subword tokenisation is the compromise every modern model uses."
/>

## The classic pipeline, and why most of it is obsolete

Older NLP pipelines lowercased text, stripped punctuation, applied stemming (crudely chopping suffixes) or lemmatisation (reducing to a dictionary root), and removed "stop words" (common function words like "the," "is"). Modern subword tokenisers and large pretrained models learn to handle case, morphology, and function words directly from data — most of this classic pipeline is now unnecessary, and can actively hurt performance by discarding information (case can be meaningful; "not" is a stop word that changes meaning entirely if removed).

## Word-level vocabularies and the out-of-vocabulary problem

The simplest tokeniser: one token per whitespace-separated word, with a fixed vocabulary built from training data. Any word not seen during vocabulary construction becomes an unknown-token, `<UNK>` — a hard ceiling that no amount of model capacity can fix, since the information in that word is simply discarded.

## Character-level and its sequence-length cost

Tokenising by individual character eliminates the out-of-vocabulary problem entirely (every possible string is representable), but produces sequences many times longer than word-level tokenisation for the same text — and since [Self-Attention in Depth](./self-attention-in-depth.md)'s cost scales quadratically with sequence length, this is a serious practical cost, not just an inconvenience.

## Subword tokenisation

The compromise: split rare/unknown words into smaller, reusable pieces, while keeping common words as single tokens. "unbelievable" might become `["un", "believ", "able"]` — three tokens the model has seen many times in other contexts, rather than one token it has never seen at all.

## BPE (Byte-Pair Encoding), walked through

Start with a vocabulary of individual characters. Repeatedly find the *most frequent adjacent pair* of tokens in the training corpus and merge it into a single new token, adding it to the vocabulary. Repeat for a fixed number of merges (the target vocabulary size).

**Worked example** on a toy corpus `"low low lower lowest"`: start with characters `l o w e r s t`; the pair `(l, o)` is most frequent, merge into `lo`; then `(lo, w)` merges into `low`; then `(e, r)` merges into `er`, and so on — each merge is chosen purely by frequency, with no linguistic rules involved.

## WordPiece and its likelihood criterion

Similar iterative merging, but instead of choosing the most *frequent* pair, WordPiece chooses the pair that most increases the training corpus's *likelihood* under a simple language model built from the current vocabulary — a subtly different objective from BPE's pure frequency count, used by BERT-family models.

## SentencePiece

Treats the input as a raw stream of Unicode characters (including spaces, encoded as a special symbol) rather than assuming whitespace-delimited words — this makes it language-agnostic, correctly handling languages like Japanese or Chinese that don't use whitespace to separate words, unlike BPE/WordPiece implementations that assume a pre-tokenisation step splits on whitespace first.

| Symbol | Meaning |
|---|---|
| vocabulary size | total number of distinct tokens the tokeniser can produce |
| merge | one BPE/WordPiece step, combining two existing tokens into a new one |

## Special tokens

`[CLS]` (a token whose final representation is used as a whole-sequence summary, common in BERT-style models), `[SEP]` (marks a boundary between two segments, e.g. question and context), `[PAD]` (fills sequences to a common length for batching), `[BOS]`/`[EOS]` (beginning/end of sequence, common in generative models).

## Vocabulary size as a design trade

A larger vocabulary means shorter sequences (more meaning packed per token) but a larger, more expensive embedding table and output layer (whose size scales with vocabulary). A smaller vocabulary means longer sequences but a smaller model. Typical modern vocabularies range from roughly 30,000 to 250,000 tokens depending on the target languages and model scale.

## Tokenisation artefacts that bite

Leading-space handling differs subtly between tokenisers (some treat `"cat"` and `" cat"` as entirely different tokens); numbers are frequently split in inconsistent, non-obvious ways (`"1234"` might become `["12", "34"]` or four separate digit tokens depending on the tokeniser); non-Latin scripts often require more tokens per character than Latin script under the same tokeniser, meaning the *same sentence meaning* costs more tokens (and therefore more compute, and more money against a per-token API price) in some languages than others; and a trailing-whitespace mismatch between a prompt's end and a generation's expected start is a classic, hard-to-spot generation bug.

## Counting tokens for cost

Because API pricing and context-window limits are denominated in tokens, not characters or words, knowing the *tokeniser*-specific token count of a piece of text (not just its length) is directly relevant to both cost estimation and fitting within context limits.

## Code: BPE from scratch, then a real tokenizer, then the script-cost demo

```python title="tokenization_demo.py"
from collections import Counter, defaultdict

def get_pair_counts(corpus):
    counts = Counter()
    for word_tuple, freq in corpus.items():
        for i in range(len(word_tuple) - 1):
            counts[(word_tuple[i], word_tuple[i+1])] += freq
    return counts

def merge_pair(pair, corpus):
    new_corpus = {}
    for word_tuple, freq in corpus.items():
        merged, i = [], 0
        while i < len(word_tuple):
            if i < len(word_tuple)-1 and (word_tuple[i], word_tuple[i+1]) == pair:
                merged.append(word_tuple[i] + word_tuple[i+1]); i += 2
            else:
                merged.append(word_tuple[i]); i += 1
        new_corpus[tuple(merged)] = freq
    return new_corpus

text = "low low lower lowest lowest"
corpus = Counter(tuple(w) + ("</w>",) for w in text.split())

print("initial:", dict(corpus))
for step in range(6):
    pairs = get_pair_counts(corpus)
    if not pairs: break
    best_pair = max(pairs, key=pairs.get)
    corpus = merge_pair(best_pair, corpus)
    print(f"merge {step+1}: {best_pair} -> vocabulary now includes {''.join(best_pair)}")

# --- A real tokenizer, for comparison ---
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
tokens = tokenizer.tokenize("unbelievable subword tokenization")
print("\nreal tokenizer output:", tokens)
print("token ids:", tokenizer.encode("unbelievable subword tokenization"))

# --- Same meaning, different token cost across scripts ---
for text, label in [("Hello, how are you?", "English"), ("こんにちは、元気ですか？", "Japanese")]:
    n_tokens = len(tokenizer.encode(text))
    print(f"{label}: {n_tokens} tokens for {len(text)} characters")
```

## See also

- [Word Embeddings](./word-embeddings.md) — turning these token ids into continuous vectors.
- [Language Modeling Basics](./language-modeling-basics.md) — what the model actually predicts, one token at a time.
