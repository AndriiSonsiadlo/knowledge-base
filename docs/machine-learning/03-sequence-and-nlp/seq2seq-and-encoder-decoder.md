---
id: seq2seq-and-encoder-decoder
title: Seq2Seq and Encoder-Decoder
sidebar_label: Seq2Seq & Encoder-Decoder
sidebar_position: 6
tags: [nlp, seq2seq, encoder-decoder, translation]
---

# Seq2Seq and Encoder-Decoder

Translation, summarisation, and question answering all share a structural challenge: the input and output are both sequences, but rarely the same length, and the alignment between them isn't fixed. The encoder-decoder architecture solved this by splitting the problem into two halves — compress the input, then generate the output — and it framed the field's central problem for the next several years, including the one it couldn't quite solve on its own.

:::info[Key idea]
Compress the input into a state, then generate the output from it — and the compression step is exactly where the architecture fails.
:::

<Figure
  src="/img/ml/nlp/seq2seq-bottleneck.png"
  alt="An encoder compressing a source sentence into one context vector feeding a decoder, with attention links drawn between all positions"
  caption="The original design forced the entire source sentence through one fixed-size vector — the bottleneck that capped translation quality on long sentences. Attention, drawn faintly here, removed it by letting every output position read every input position."
/>

## The task shape

Unlike [Recurrent Neural Networks](./recurrent-neural-networks.md)'s sequence-to-one or one-to-sequence cases, translation genuinely needs sequence-to-sequence: variable input length, variable (and generally different) output length, with no assumed one-to-one alignment between input and output positions.

## The encoder

An RNN (typically LSTM/GRU — see [LSTM and GRU](./lstm-and-gru.md)) processes the entire input sequence, producing a final hidden state meant to summarise the whole input.

## The context vector

The encoder's final hidden state, handed off as the sole initial state for the decoder — every piece of information the decoder will ever have about the input is compressed into this single fixed-size vector.

## The decoder

Another RNN, initialised from the context vector, generating the output sequence one token at a time — at each step, it takes its own previous output as input for the next step (the autoregressive generation pattern from [Language Modeling Basics](./language-modeling-basics.md)).

## Teacher forcing in this setting

During training, the decoder is fed the *true* previous output token (from the training target sequence) rather than its own prediction — the same teacher-forcing pattern and the same exposure-bias gap described in [Language Modeling Basics](./language-modeling-basics.md), here applying specifically to the decoder half of the architecture.

## The fixed-size bottleneck, and the evidence for it

Every piece of information about a 50-word input sentence must be squeezed into the same fixed-size vector as a 5-word one — and empirically, translation quality (measured by BLEU and similar metrics) degrades measurably as input sentence length grows, exactly the symptom you'd expect if the fixed-size context vector is losing information proportional to how much it's being asked to compress.

## Why this bottleneck motivated attention

If the decoder could instead look back at *all* of the encoder's intermediate hidden states — not just the single final one — it could pull exactly the information relevant to generating each output token, rather than relying on everything having survived compression into one vector. That's precisely the fix [Attention Mechanism](./attention-mechanism.md) introduces on the next page.

| Symbol | Meaning |
|---|---|
| context vector | the encoder's final hidden state, the decoder's only view of the input |
| $P(y \mid x)$ | the conditional generation objective, factorised over output positions |

## Beam search, introduced

Rather than greedily picking the single most probable token at each decoder step (which can lock in an early mistake that a full sequence-level view would have avoided), **beam search** keeps the top-$k$ partial sequences at each step, expanding all of them and keeping only the overall top-$k$ continuations — a search strategy that trades compute for a better approximation of the highest-probability complete sequence. Full treatment, including why beam search's benefits are more nuanced than they first appear, in [Decoding Strategies](./decoding-strategies.md).

## Encoder-decoder vs. decoder-only

This page's architecture has two separate stacks (encoder, decoder) with the context vector as the sole bridge between them. [Transformer Variants](./transformer-variants.md) covers the modern landscape, including **decoder-only** architectures that dispense with a separate encoder entirely, processing input and generating output within a single stack — the architecture behind most current large language models.

## Tasks that still suit encoder-decoder

Despite decoder-only models' dominance for open-ended generation, encoder-decoder architectures (T5-style) remain a strong, sometimes preferred choice for tasks with a clear, bounded input-to-output transformation — translation, summarisation, and similar tasks where the "input" and "output" roles are genuinely distinct rather than a continuous conversational stream.

## Code: an LSTM encoder-decoder on a synthetic transduction task, quality vs. length

```python title="seq2seq_demo.py"
import torch
import torch.nn as nn

class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
    def forward(self, x):
        _, (h, c) = self.lstm(self.embed(x))
        return h, c  # the context vector (both LSTM states)

class Decoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.out = nn.Linear(hidden_dim, vocab_size)
    def forward(self, x, h, c):
        output, (h, c) = self.lstm(self.embed(x), (h, c))
        return self.out(output), h, c

# --- Toy task: reverse a sequence of digit-tokens ---
vocab_size, embed_dim, hidden_dim = 12, 16, 32  # 10 digits + <bos> + <eos>
BOS, EOS = 10, 11
encoder = Encoder(vocab_size, embed_dim, hidden_dim)
decoder = Decoder(vocab_size, embed_dim, hidden_dim)
optimizer = torch.optim.Adam(list(encoder.parameters()) + list(decoder.parameters()), lr=0.01)

def make_batch(seq_len, batch_size=32):
    src = torch.randint(0, 10, (batch_size, seq_len))
    tgt = src.flip(dims=[1])  # the "translation" task: reverse the sequence
    tgt_in = torch.cat([torch.full((batch_size, 1), BOS), tgt[:, :-1]], dim=1)  # teacher forcing input
    return src, tgt_in, tgt

for step in range(500):
    src, tgt_in, tgt = make_batch(seq_len=6)
    optimizer.zero_grad()
    h, c = encoder(src)
    logits, _, _ = decoder(tgt_in, h, c)
    loss = nn.functional.cross_entropy(logits.reshape(-1, vocab_size), tgt.reshape(-1))
    loss.backward()
    optimizer.step()

# --- Quality vs. input length: reproducing the bottleneck symptom ---
print("seq_len | accuracy")
for seq_len in [4, 6, 10, 15, 20]:
    src, tgt_in, tgt = make_batch(seq_len, batch_size=64)
    with torch.no_grad():
        h, c = encoder(src)
        logits, _, _ = decoder(tgt_in, h, c)
    preds = logits.argmax(dim=-1)
    acc = (preds == tgt).float().mean().item()
    print(f"{seq_len:7d} | {acc:.3f}")
```

Accuracy should visibly decline as `seq_len` grows well beyond what the model was trained on — the fixed-size context vector's information bottleneck, reproduced directly.

## See also

- [LSTM and GRU](./lstm-and-gru.md) — the recurrent cell typically used inside both the encoder and decoder.
- [Attention Mechanism](./attention-mechanism.md) — the fix for exactly the bottleneck this page identifies.
