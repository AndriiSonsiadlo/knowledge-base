---
id: evaluating-generative-models
title: Evaluating Generative Models
sidebar_label: Evaluating Generative Models
sidebar_position: 11
tags: [generative, evaluation, fid, metrics]
---

# Evaluating Generative Models

A classifier has a right answer to check against. A generative model's output has no correct answer at all — "is this a good generated cat image" has no ground truth to compare against, only a distribution to compare against. Every metric in this page is a different proxy for that comparison, and every proxy can be gamed.

:::info[Key idea]
Every automatic metric for generation measures a proxy, and each proxy can be gamed - which is why human evaluation has not gone away.
:::

## Why held-out accuracy does not apply

[Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md)'s entire toolkit assumes a known correct label per example. Generation has no such per-example target — a generative model is evaluated against a *distribution* it's supposed to match, not a per-input answer key, which is why an entirely separate metric family exists for this setting.

## Likelihood-based evaluation, and why it does not correlate with perceived quality

Where available (autoregressive models, normalizing flows, VAEs' ELBO), likelihood measures how much probability the model assigns to real data — a principled quantity, directly tied to the training objective. But [What Is a Generative Model](./what-is-a-generative-model.md) already flagged the gap: a model can achieve excellent likelihood while producing samples a human rates as lower quality, since likelihood rewards covering the whole distribution (including unremarkable regions) rather than only the most visually striking samples.

## Inception Score and its documented flaws

**Inception Score (IS)** feeds generated images through a pretrained classifier and combines two signals: each individual image should get a confident, low-entropy class prediction (sample quality), and the predictions across many samples should be diverse (mode coverage). Documented flaws: it never looks at real data at all (so a model reproducing only a few classes very well can still score high), it's sensitive to the specific classifier used, and it can be gamed by generating images that are individually classifier-confident without actually looking realistic.

## FID: the method, the Gaussian assumption, sensitivity to sample count and to the feature extractor

**Fréchet Inception Distance (FID)** fixes IS's biggest flaw by comparing real and generated samples directly: extract features from both sets using a pretrained network, fit a Gaussian to each set's features, and compute the distance between the two Gaussians:

$$
\text{FID} = \|\mu_r - \mu_g\|^2 + \text{Tr}\left(\Sigma_r + \Sigma_g - 2(\Sigma_r \Sigma_g)^{1/2}\right)
$$

The Gaussian assumption is a real approximation, not a guarantee — true feature distributions are rarely exactly Gaussian. FID is also sensitive to the number of samples used (too few samples inflates the estimate) and to which feature extractor is used (comparing FID numbers computed with different feature extractors is meaningless), both common sources of misleading reported numbers.

## KID as the lower-bias alternative

**Kernel Inception Distance (KID)** compares feature distributions using a kernel-based statistic (maximum mean discrepancy) instead of fitting Gaussians — has no Gaussian assumption, and has a lower-bias estimator at small sample sizes than FID, at the cost of being less standard and less directly comparable across papers.

## Precision and recall for generative models: quality and coverage separated

A single scalar (FID, IS) conflates two genuinely different failure modes. **Precision** (of generated samples, with respect to the real distribution's support): what fraction of generated samples look realistic. **Recall** (of the real distribution, with respect to generated samples' support): what fraction of the real distribution's diversity is actually reproduced. A mode-collapsed model can have excellent precision and terrible recall — exactly the failure a single FID number can hide.

## Mode-coverage tests on data where you know the true modes

On synthetic data with a known, countable number of modes (e.g. a mixture of well-separated Gaussians), mode coverage can be measured directly and unambiguously — how many of the true modes does the model actually produce samples near, and how evenly. This is exactly why the toy 2-D distributions used throughout [Generative Adversarial Networks](./generative-adversarial-networks.md) and [GAN Training Challenges](./gan-training-challenges.md) are useful teaching tools: on real image data, "how many modes are there" is not even a well-defined question.

## CLIP score for text-image alignment

For text-conditioned generation specifically: embed both the prompt and the generated image using CLIP, and measure the cosine similarity between them — a proxy for "does the image match the prompt," inheriting all of CLIP's own biases and blind spots (the same failure modes CLIP itself has as a vision-language encoder).

## Perceptual metrics (LPIPS)

**LPIPS** (Learned Perceptual Image Patch Similarity) compares two specific images using distances in a pretrained network's feature space, rather than raw pixels — useful for image-to-image tasks with a specific reference to compare against (unlike FID, which compares two whole distributions rather than paired images).

## Human evaluation protocols and pairwise preference

Given the gap between every automatic metric and actual perceived quality, human evaluation — typically pairwise preference judgments ("which of these two images better matches the prompt") rather than absolute scores, since relative judgments are more consistent across raters — remains standard practice for reporting results in generative modelling, precisely because no automatic proxy has closed the gap.

| Symbol | Meaning |
|---|---|
| $\mu_r, \Sigma_r$ | mean and covariance of real-data features |
| $\mu_g, \Sigma_g$ | mean and covariance of generated-data features |

## The reporting checklist

1. Sample count used for each metric (and whether it matches the count used in compared work).
2. Feature extractor used (FID and KID numbers from different extractors are not comparable).
3. Resolution at which images were evaluated.
4. Random seed, or an explicit statement that results are averaged over multiple seeds.

## A metric selection table by model family

| Model family | Primary metric | Caveat |
|---|---|---|
| GAN / diffusion (images) | FID | sample-count and extractor sensitive |
| Text-to-image | FID + CLIP score | neither alone captures prompt alignment |
| Autoregressive / flow (density available) | held-out log-likelihood | doesn't correlate with perceived quality |
| Any family, mode-coverage concern | precision/recall | needs a reference feature extractor |
| Image-to-image (paired) | LPIPS | requires a paired reference image |

## Code: FID from scratch, verified analytically, and precision/recall catching mode collapse

```python title="evaluating_generative_models_demo.py"
import numpy as np
from scipy import linalg

def compute_fid(real_features, gen_features):
    mu_r, mu_g = real_features.mean(axis=0), gen_features.mean(axis=0)
    sigma_r = np.cov(real_features, rowvar=False)
    sigma_g = np.cov(gen_features, rowvar=False)
    diff = mu_r - mu_g
    covmean = linalg.sqrtm(sigma_r @ sigma_g)
    if np.iscomplexobj(covmean):
        covmean = covmean.real  # numerical artefact from sqrtm on near-singular matrices
    return diff @ diff + np.trace(sigma_r + sigma_g - 2 * covmean)

rng = np.random.default_rng(0)

# --- Verify FID against a case with a known analytical answer: identical distributions -> FID ~ 0 ---
real_features = rng.normal(0, 1, size=(2000, 32))
identical_features = rng.normal(0, 1, size=(2000, 32))
print(f"FID(same distribution)  = {compute_fid(real_features, identical_features):.3f}  (should be near 0)")

# --- FID between two clearly different distributions ---
shifted_features = rng.normal(3, 1, size=(2000, 32))
print(f"FID(shifted mean by 3)  = {compute_fid(real_features, shifted_features):.3f}  (should be large)")

# --- FID's sensitivity to sample count ---
for n in [50, 200, 1000, 5000]:
    subset_real = rng.normal(0, 1, size=(n, 32))
    subset_gen = rng.normal(0, 1, size=(n, 32))
    print(f"FID at n={n:5d} samples: {compute_fid(subset_real, subset_gen):.3f}  (should shrink toward 0 as n grows)")

# --- Precision/recall on 2-D toy data, catching mode collapse a single FID number could hide ---
def sample_two_modes(n, rng):
    centers = rng.choice([-3, 3], size=n)
    return np.stack([centers + rng.normal(0, 0.3, n), rng.normal(0, 0.3, n)], axis=1)

def precision_recall(real, gen, radius=1.0):
    from scipy.spatial import cKDTree
    real_tree, gen_tree = cKDTree(real), cKDTree(gen)
    precision = np.mean([real_tree.query_ball_point(g, radius, return_length=True) > 0 for g in gen])
    recall = np.mean([gen_tree.query_ball_point(r, radius, return_length=True) > 0 for r in real])
    return precision, recall

real_2d = sample_two_modes(500, rng)
collapsed_2d = np.stack([np.full(500, 3.0) + rng.normal(0, 0.3, 500), rng.normal(0, 0.3, 500)], axis=1)
precision, recall = precision_recall(real_2d, collapsed_2d)
print(f"\nmode-collapsed generator: precision={precision:.2f} (samples look real), "
      f"recall={recall:.2f} (misses half the real distribution)")
```

## See also

- [GAN Training Challenges](./gan-training-challenges.md) — the mode-collapse failure precision/recall is specifically designed to catch.
- [Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md) — the supervised-learning evaluation toolkit this page's metrics deliberately depart from.
