---
id: finetuning-and-instruction-tuning
title: Finetuning and Instruction Tuning
sidebar_label: Finetuning & Instruction Tuning
sidebar_position: 13
tags: [nlp, finetuning, instruction-tuning, alignment]
---

# Finetuning and Instruction Tuning

A pretrained model knows an enormous amount about language and often about the world — and none of it about how to behave. It has no notion that a question deserves a direct answer rather than a continuation of similar-looking text scraped from a forum. Fine-tuning is where capability turns into behaviour, and most complaints of "the model can't do X" are actually behaviour problems in disguise.

:::info[Key idea]
Pretraining gives capability, fine-tuning gives behaviour — and most "the model cannot do X" complaints are behaviour problems.
:::

## Feature extraction vs. full fine-tuning

**Feature extraction**: freeze the entire pretrained backbone, train only a small new task head on top — cheap, fast, but limited by however good the frozen representations already are for the target task. **Full fine-tuning**: update every parameter, including the backbone — more capable of adapting to a task that differs substantially from pretraining, at proportionally higher compute and memory cost.

## Task heads

For classification, a linear layer mapping the model's final representation to class logits; for token classification (e.g. named entity recognition), a linear layer applied at every position; for question answering, two linear layers predicting the start and end positions of the answer span within the input.

## Catastrophic forgetting

Fine-tuning aggressively on a narrow task can degrade the broad capabilities pretraining originally provided — the model "forgets" general language ability while overfitting to the fine-tuning task's specific patterns. **Layer-wise learning rates** (smaller rates for early, already-well-tuned layers; larger rates for later layers or the new task head, from [Learning Rate Schedules](../02-deep-learning/learning-rate-schedules.md)) are a common mitigation, on the reasoning that early layers encode more general, broadly-useful features that shouldn't move far from their pretrained values.

## How much data you actually need

Highly variable by task, but a striking property of fine-tuning large pretrained models is how *little* data is often needed relative to training from scratch — hundreds to low thousands of examples frequently suffice for many classification-style tasks, versus the far larger datasets a from-scratch model would require to reach comparable performance.

## Instruction tuning: the format, and what it changes

Fine-tune specifically on (instruction, response) pairs — "Summarize this text: ..." paired with an actual good summary, across a wide variety of instruction types and phrasings. This doesn't teach new *knowledge* (that's pretraining's job) — it teaches the model to interpret an instruction as a request to fulfil, rather than as text to merely continue in a plausible-sounding way.

## Chat templates, and the bug when you get one wrong

Instruction-tuned and chat models expect input formatted with specific special tokens and structure marking turn boundaries (system/user/assistant roles) — exactly matching the format the model was fine-tuned on. Feeding a chat model raw, unformatted text (or the wrong template) produces degraded, sometimes bizarre outputs, since the model is effectively receiving input unlike anything in its fine-tuning distribution — one of the most common, and most silent, bugs when switching between model providers or versions.

## Preference alignment: RLHF and DPO, stated

Beyond following instructions correctly, models are further tuned to prefer *better* responses among several correct ones — more helpful, more concise, safer. **RLHF** trains a reward model from human preference comparisons, then uses reinforcement learning to optimise the language model against that learned reward (mechanics in [RLHF and Preference Optimization](../06-reinforcement-learning/rlhf-and-preference-optimization.md)). **DPO** reformulates the same underlying preference objective as a direct supervised loss on preference pairs, skipping the separate reward model and RL loop entirely.

$$
L_{\text{SFT}} = -\frac{1}{n}\sum_i \log P(y_i \mid x_i)
$$

| Symbol | Meaning |
|---|---|
| $x_i$ | the instruction/prompt |
| $y_i$ | the target (demonstrated correct) response |
| $L_{\text{SFT}}$ | the supervised fine-tuning loss — standard cross-entropy over the target response tokens |

## Fine-tuning vs. prompting vs. retrieval

| Situation | Reach for |
|---|---|
| Need a new behaviour pattern, examples available | fine-tuning (or instruction tuning) |
| Need the model to use current/private information | retrieval-augmented generation |
| Need to steer output format/style, no training data | prompting alone |
| Need broad new knowledge the base model lacks | continued pretraining, then fine-tuning |

## Evaluating a fine-tune against the base model

Compare on the target task's held-out examples using [Evaluating Language Models](./evaluating-language-models.md)'s task-specific metrics, *and* check that general capability (broad instruction-following, unrelated tasks) hasn't regressed — a fine-tune that improves the target task while quietly breaking unrelated behaviour is exactly the catastrophic-forgetting failure mode described above, and only shows up if you specifically look for it.

## Overfitting on small fine-tuning sets

With only a few hundred to a few thousand examples, a model can memorise the fine-tuning set's specific patterns (including any quirks or biases in how the examples were written) rather than learning the intended general behaviour — showing up as excellent performance on examples resembling the fine-tuning set and poor generalisation to superficially different but task-equivalent inputs.

## Code: fine-tuning a classifier head, and a chat-template rendering example

```python title="finetuning_demo.py"
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

texts = ["I loved this movie", "Terrible waste of time", "Absolutely fantastic", "Boring and dull"] * 20
labels = [1, 0, 1, 0] * 20
dataset = Dataset.from_dict({"text": texts, "label": labels}).train_test_split(test_size=0.2)

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
def tokenize(batch): return tokenizer(batch["text"], truncation=True, padding=True)
dataset = dataset.map(tokenize, batched=True)

model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

training_args = TrainingArguments(
    output_dir="./results", num_train_epochs=3, per_device_train_batch_size=8,
    eval_strategy="epoch", report_to="none",
)
trainer = Trainer(model=model, args=training_args, train_dataset=dataset["train"], eval_dataset=dataset["test"])
trainer.train()
eval_results = trainer.evaluate()
print("fine-tuned eval results:", eval_results)

# --- Chat template rendering: the exact string the model receives ---
chat_tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
if chat_tokenizer.chat_template is None:
    chat_tokenizer.chat_template = (
        "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"
    )
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Summarize the water cycle."},
]
rendered = chat_tokenizer.apply_chat_template(messages, tokenize=False)
print("\nexact string sent to the model:\n", rendered)
```

## See also

- [Pretraining Objectives](./pretraining-objectives.md) — the capability stage this page's fine-tuning builds behaviour on top of.
- [Parameter-Efficient Finetuning](./parameter-efficient-finetuning.md) — fine-tuning large models without updating every parameter.
