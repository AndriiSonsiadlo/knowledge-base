"""Insert <Figure> blocks into the machine-learning docs from a manifest.

Every ML page follows the same shape: frontmatter, an H1, an intro paragraph, a
`:::info[Key idea]` admonition, then `## sections`. The manifest below says, for
each figure, which page it belongs to and where on that page it goes:

    ("<doc path>", "<anchor>", "<img path>", "<alt>", "<caption>")

`anchor` is either the literal text of a heading line (the figure is inserted
just after that heading) or `@hero`, meaning "after the Key idea admonition" —
the top-of-page slot.

The script is idempotent: a page that already references the image is skipped,
so it can be re-run after editing the manifest.

    python insert_figures.py            # apply
    python insert_figures.py --check    # report only
"""

from __future__ import annotations

import pathlib
import sys

DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs" / "machine-learning"

F = "00-foundations"
C = "01-classical-ml"
D = "02-deep-learning"
N = "03-sequence-and-nlp"
V = "04-computer-vision"
G = "05-generative-models"
R = "06-reinforcement-learning"
M = "07-production-mlops"

MANIFEST: list[tuple[str, str, str, str, str]] = [
    # ---------------------------------------------------------------- foundations
    (f"{F}/learning-paradigms.md", "@hero", "foundations/learning-paradigms.png",
     "Three panels: labelled points with a boundary, unlabelled points with discovered groups, and a trajectory collecting rewards",
     "The three paradigms on the same scatter of points. Supervised learning is told the answer; unsupervised must find structure; reinforcement learning only ever sees how good the outcome was."),
    (f"{F}/gradient-descent.md", "## Learning rate: too small, too large, just right",
     "foundations/learning-rate-regimes.png",
     "Three contour plots of the same elongated bowl showing a crawling path, a converging path, and a diverging oscillation",
     "The same loss surface and starting point, three learning rates. Too small never arrives in the budget you have; too large diverges. Note the middle path still bends — it descends the steep axis first, then travels the shallow one."),
    (f"{F}/gradient-descent.md", "## Batch vs. stochastic vs. mini-batch",
     "foundations/gradient-descent-variants.png",
     "Three loss curves: a smooth batch curve, a slightly noisy mini-batch curve, and a very noisy stochastic curve",
     "Gradient noise rises as the batch shrinks. The noise is not purely a cost — it is what lets SGD escape shallow local minima that full-batch descent settles into."),
    (f"{F}/bias-variance-tradeoff.md", "@hero", "foundations/bias-variance-tradeoff.png",
     "Left: degree 1, 3 and 12 polynomial fits to 14 noisy points. Right: bias squared falling, variance rising, and their sum forming a U",
     "Left, the same 14 points fitted at three capacities — the degree-12 curve chases noise at the edges. Right, the decomposition: total error is a U because bias falls and variance rises, and the irreducible noise floor never moves."),
    (f"{F}/overfitting-and-regularization.md", "@hero", "foundations/learning-curves-overfitting.png",
     "Training loss falling steadily while validation loss falls then turns upward, with the minimum marked",
     "Overfitting is visible as a gap that opens between the two curves. The validation minimum is the early-stopping point; everything to the right of it buys training loss at the cost of generalisation."),
    (f"{F}/overfitting-and-regularization.md", "## L1 and sparsity",
     "foundations/l1-l2-constraint-geometry.png",
     "Two panels showing elliptical loss contours meeting a circular L2 region off-axis and a diamond L1 region exactly on its corner",
     "Why L1 zeroes coefficients and L2 only shrinks them. The solution is where the loss contour first touches the constraint region — the diamond's corners sit on the axes, so contact there sets a coefficient to exactly zero. Both solutions here are solved for, not drawn by eye."),
    (f"{F}/loss-functions.md", "@hero", "foundations/loss-functions.png",
     "Left: squared error, absolute error and Huber loss against residual. Right: cross-entropy and hinge loss against predicted probability",
     "Squared error punishes outliers quadratically; absolute error does not; Huber is quadratic near zero and linear beyond it. On the right, cross-entropy is unbounded — a confident wrong prediction is penalised without limit."),
    (f"{F}/evaluation-metrics-classification.md", "@hero", "foundations/confusion-matrix.png",
     "A two-by-two confusion matrix with 850 true negatives, 50 false positives, 30 false negatives and 70 true positives",
     "Every classification metric is a ratio computed from these four cells. With 10 % positives, predicting 'negative' always would score 90 % accuracy while catching nothing."),
    (f"{F}/evaluation-metrics-classification.md", "## ROC curve and AUC",
     "foundations/roc-vs-precision-recall.png",
     "An ROC curve with high AUC beside a precision-recall curve for the same model showing much weaker performance",
     "The same model on the same imbalanced data. ROC looks strong because true negatives dominate the false-positive rate; the precision–recall curve, which ignores true negatives, shows the real weakness. On imbalanced problems, trust the right-hand plot."),
    (f"{F}/evaluation-metrics-classification.md", "## The threshold is a choice",
     "foundations/threshold-tradeoff.png",
     "Overlapping score distributions for positives and negatives with a threshold line, shading the false positives and false negatives it creates",
     "The model produces a score; you choose the threshold. Moving it left catches more positives at the cost of more false alarms. Where you put it is a business decision, not a modelling one."),
    (f"{F}/evaluation-metrics-regression.md", "## Residual analysis as the real diagnostic",
     "foundations/residual-diagnostics.png",
     "Three residual plots: structureless, curved, and fanning outward",
     "A single R² cannot distinguish these three. Curvature means a missing non-linear term; a fan means the variance depends on the prediction, which breaks the constant-variance assumption behind most confidence intervals."),
    (f"{F}/train-validation-test-splits.md", "@hero", "foundations/cross-validation-schemes.png",
     "Top: five-fold cross-validation with each fold validated once. Bottom: time-series splits where validation always follows training in time",
     "k-fold reuses every block for validation exactly once. For time series it is invalid — training on the future to predict the past leaks information — so the split must always move forward in time."),
    (f"{F}/data-preprocessing-and-features.md", "## Pipeline and ColumnTransformer",
     "foundations/preprocessing-leakage.png",
     "Two diagrams: scaling before splitting, which leaks test statistics into training, versus fitting the scaler inside the training fold only",
     "Fitting a scaler before splitting leaks the test set's mean and variance into training. The result is an optimistic validation score that vanishes in production. Fit on train, apply to test — always in that order."),
    (f"{F}/data-preprocessing-and-features.md", "## Numeric scaling",
     "foundations/feature-scaling.png",
     "The same two-feature cloud shown raw, standardised, and min-max scaled",
     "Raw features spanning different ranges dominate any distance- or gradient-based method. Standardisation centres and rescales; min–max squeezes into a fixed interval and is far more sensitive to outliers."),
    (f"{F}/curse-of-dimensionality.md", "@hero", "foundations/curse-of-dimensionality.png",
     "Left: the ratio of farthest to nearest distance collapsing as dimensions rise. Right: the fraction of a cube near its centre falling exponentially",
     "As dimensions grow, all pairwise distances converge — so 'nearest neighbour' stops being meaningful — and the volume of a cube flees to its corners, leaving the centre essentially empty."),
    (f"{F}/probability-and-distributions.md", "@hero", "foundations/common-distributions.png",
     "A six-panel grid of normal, binomial, Poisson, exponential and beta distributions plus a central limit theorem demonstration",
     "The distributions that recur throughout ML. The last panel is the central limit theorem in action: averages of uniform samples become normal remarkably quickly, which is why the normal assumption is so often defensible."),
    (f"{F}/information-theory.md", "@hero", "foundations/information-theory.png",
     "Binary entropy peaking at p equals one half, surprisal rising as probability falls, and two bar distributions illustrating KL divergence",
     "Entropy is maximised by maximum uncertainty; surprisal makes rare events expensive to encode. KL divergence measures the extra bits spent coding the true distribution P with the model's Q — which is exactly what cross-entropy loss minimises."),
    (f"{F}/linear-algebra.md", "@hero", "foundations/linear-algebra-geometry.png",
     "Three panels: a unit circle transformed into an ellipse with eigenvectors marked, a vector projection, and an SVD decomposition",
     "The three geometric facts that matter. A matrix is a transformation; eigenvectors are the directions it merely scales; the dot product is a projection; and SVD says any matrix is a rotation, a stretch, and another rotation."),
    (f"{F}/calculus-and-gradients.md", "@hero", "foundations/derivatives-and-gradients.png",
     "Left: a cubic curve with tangent lines at three points. Right: contours of a quadratic bowl with gradient arrows pointing outward",
     "The derivative is the slope of the tangent. In more than one dimension the gradient points in the direction of steepest *increase* — which is why gradient descent subtracts it."),
    (f"{F}/statistics-and-estimation.md", "@hero", "foundations/sampling-and-confidence.png",
     "Left: sampling distributions narrowing as sample size grows. Right: twenty-five confidence intervals, most containing the true value",
     "Standard error shrinks as 1/√n, so quartering your error costs sixteen times the data. On the right, '95 % confident' describes the procedure: run it many times and about 95 % of the intervals it produces will contain the truth."),

    # ---------------------------------------------------------------- classical ML
    (f"{C}/linear-regression.md", "@hero", "classical/linear-regression-fit.png",
     "A fitted regression line with vertical residual segments drawn to each point, and the corresponding residual plot",
     "Least squares minimises the sum of the squared vertical distances — the grey segments. Squaring is what makes distant points dominate the fit, and why a single outlier can tilt the whole line."),
    (f"{C}/linear-regression.md", "## Assumptions and what breaks when they fail", "classical/anscombe-quartet.png",
     "Four scatter plots with visibly different shapes that all share the same fitted line and summary statistics",
     "Anscombe's quartet: four datasets with identical means, variances, correlation and regression line. Summary statistics alone cannot tell them apart — which is the entire argument for plotting your data first."),
    (f"{C}/logistic-regression.md", "@hero", "classical/logistic-regression.png",
     "The sigmoid function mapping real values to probabilities, and a linear decision boundary separating two classes",
     "The sigmoid turns an unbounded score into a probability. The boundary it produces is always linear in the input features — the curve is in the probability, not in the separator."),
    (f"{C}/k-nearest-neighbors.md", "## Choosing k", "classical/knn-k-effect.png",
     "Three decision boundaries for k of 1, 15 and 75 on the same two-moons data, progressing from jagged to nearly linear",
     "k is the bias–variance dial made visible. At k = 1 every noisy point carves out its own island; at k = 75 the boundary is almost linear and the moons are lost. Nothing about the model changes but that one number."),
    (f"{C}/support-vector-machines.md", "## The maximum-margin idea", "classical/svm-margin.png",
     "Two linearly separable classes with a maximum-margin separator, its two margin lines, and three circled support vectors",
     "The separator is placed to maximise the distance to the nearest point of either class. Only the three circled points — the support vectors, which sit exactly on the margin — determine it; deleting any other point changes nothing."),
    (f"{C}/kernel-methods.md", "@hero", "classical/kernel-trick.png",
     "Concentric rings that no line can separate in two dimensions, then the same points lifted into three dimensions where a flat plane separates them",
     "The kernel trick in one picture. Data that needs a circular boundary in 2-D needs only a flat plane once lifted by a radial feature — and the kernel computes the inner products in that higher space without ever building it."),
    (f"{C}/decision-trees.md", "@hero", "classical/decision-tree-depth.png",
     "Three decision boundaries from trees of depth 1, 3 and 12, all composed of axis-aligned rectangles",
     "Every tree boundary is a union of axis-aligned rectangles — a diagonal separation always costs a staircase of splits. Depth is the capacity knob: at 12 the tree is fencing off individual noise points."),
    (f"{C}/random-forests-and-bagging.md", "@hero", "classical/random-forest-smoothing.png",
     "A single deep tree's jagged boundary beside the smooth boundary of sixty averaged bootstrapped trees",
     "Averaging many high-variance trees, each fitted to a bootstrap sample, cancels their individual errors. The forest's boundary is smooth even though every tree composing it is a staircase."),
    (f"{C}/gradient-boosting.md", "@hero", "classical/boosting-stages.png",
     "A sequence showing the data, then the boosted fit after 1, 5 and 40 decision stumps progressively approaching the true curve",
     "Each stump is fitted to what the ensemble still gets wrong. Individually they are useless; summed with a small learning rate they converge on the target — which is why boosting reduces bias where bagging reduces variance."),
    (f"{C}/ensembles-and-stacking.md", "@hero", "classical/bagging-vs-boosting.png",
     "Bagging shown as independent parallel trees feeding an average, and boosting as a chain of trees each correcting the previous",
     "The structural difference. Bagging trains independently and in parallel, attacking variance; boosting trains sequentially with each model correcting its predecessor, attacking bias. That dependency is also why boosting cannot be parallelised across trees."),
    (f"{C}/k-means-clustering.md", "@hero", "classical/kmeans-iterations.png",
     "Four snapshots of k-means converging from a deliberately poor initialisation to three well-separated clusters",
     "k-means alternates two steps: assign each point to its nearest centroid, then move each centroid to the mean of its points. From this deliberately bad initialisation it still converges — but only to a local optimum, which is why k-means++ and restarts exist."),
    (f"{C}/k-means-clustering.md", "## Choosing k", "classical/kmeans-limitations.png",
     "k-means splitting two crescent moons incorrectly, splitting an elongated cluster, and an elbow plot with a clear bend at four",
     "k-means assumes roughly spherical, similarly sized clusters. Crescents and unequal spreads both defeat it. The elbow plot on the right is the standard heuristic for k — here bending cleanly at the true value of four."),
    (f"{C}/hierarchical-and-density-clustering.md", "@hero", "classical/dbscan-vs-kmeans.png",
     "k-means cutting straight through two crescent moons beside DBSCAN correctly following each crescent and marking outliers",
     "DBSCAN follows connected regions of high density, so it recovers the crescents k-means cannot — and it labels genuine outliers as noise rather than forcing every point into a cluster."),
    (f"{C}/hierarchical-and-density-clustering.md", "## Reading a dendrogram", "classical/dendrogram.png",
     "A dendrogram of eight points with a horizontal cut line producing two clusters",
     "Hierarchical clustering produces the whole merge tree; you choose k afterwards by picking a cut height. The tall vertical gap just below the cut is the visual signal that two clusters is the natural answer here."),
    (f"{C}/gaussian-mixture-models.md", "@hero", "classical/gmm-vs-kmeans.png",
     "k-means hard spherical assignments beside a GMM's soft elliptical components fitted by expectation maximisation",
     "A GMM generalises k-means in two ways: components can be elliptical rather than spherical, and membership is a probability rather than a hard label. The colour gradient in the right panel is that soft assignment."),
    (f"{C}/pca-and-svd.md", "@hero", "classical/pca-explained.png",
     "Correlated data with principal component arrows, the same data rotated into the component basis, and a scree plot of explained variance",
     "PC1 is the direction of maximum variance and PC2 is orthogonal to it. Rotating into that basis leaves the data uncorrelated; the scree plot then tells you how many components you can keep before losing real signal."),
    (f"{C}/manifold-learning.md", "@hero", "classical/manifold-swiss-roll.png",
     "A Swiss roll in three dimensions and its unrolled two-dimensional structure",
     "Points close in Euclidean distance can be far apart along the manifold — the two facing surfaces of the roll are adjacent in 3-D but distant along the sheet. Manifold learning recovers the intrinsic coordinates on the right."),
    (f"{C}/anomaly-detection.md", "@hero", "classical/anomaly-detection.png",
     "Mahalanobis distance contours around a dense cluster, and the same points with those beyond a threshold flagged",
     "Anomaly detection models what normal looks like and flags whatever falls far outside it. The contour you pick as the boundary sets the false-positive rate — and that is a business decision, not a statistical one."),
    (f"{C}/imbalanced-data.md", "@hero", "classical/imbalanced-resampling.png",
     "A heavily imbalanced dataset, the same data after undersampling the majority, and after SMOTE has interpolated synthetic minority points",
     "Three views of a 94/6 split. Undersampling is cheap but discards real data; SMOTE interpolates new minority points between existing ones. Both change the base rate, so any probability the model outputs afterwards needs recalibrating."),
    (f"{C}/model-selection-and-tuning.md", "@hero", "classical/grid-vs-random-search.png",
     "Grid search covering only five distinct values of the important parameter, versus random search covering twenty-five",
     "With the same 25 trials, grid search tests only 5 distinct values of the parameter that actually matters, because it spends the rest varying one that does not. Random search tests 25 — which is why it wins whenever some parameters matter far more than others."),
    (f"{C}/model-selection-and-tuning.md", "## Coarse-to-fine search", "classical/validation-curve.png",
     "Training error falling monotonically while validation error forms a U, with the minimum marked",
     "Sweeping one hyperparameter while holding the rest fixed. The gap between the curves is overfitting; the validation minimum is the setting to keep."),
    (f"{C}/regularization-ridge-lasso-elasticnet.md", "## Coefficient paths",
     "foundations/ridge-vs-lasso-paths.png",
     "Ridge coefficient paths shrinking smoothly toward zero beside lasso paths hitting exactly zero one by one",
     "Both penalties shrink coefficients as α rises, but only lasso sets them to exactly zero — and it does so one at a time, which is what makes it a feature selector. Ridge keeps every coefficient, however small."),
    (f"{C}/regularization-ridge-lasso-elasticnet.md", "## Lasso (L1) and why the corner causes sparsity",
     "foundations/l1-l2-constraint-geometry.png",
     "Loss contours meeting a round L2 constraint region off-axis and a diamond L1 region exactly on a corner",
     "The corner is the whole mechanism. Because the L1 region's vertices lie on the axes, the first point of contact with the loss contour is very often one of them — and at that point a coefficient is exactly zero."),
    (f"{C}/naive-bayes.md", "@hero", "classical/naive-bayes.png",
     "Class-conditional density curves for two classes, and a decision boundary on correlated data fitted under the independence assumption",
     "Naive Bayes models each feature's class-conditional density independently. The right panel shows it working on visibly correlated data — the probability estimates are badly calibrated, but the arg-max, and therefore the classification, often survives."),

    # ---------------------------------------------------------------- deep learning
    (f"{D}/from-perceptron-to-mlp.md", "@hero", "deep/xor-problem.png",
     "AND and OR shown as linearly separable, and XOR shown with no single line able to separate its classes",
     "AND and OR need one line; XOR needs two. A single perceptron can only draw one, which is the limitation that stalled neural networks for years — and the reason a hidden layer exists."),
    (f"{D}/forward-pass-and-computational-graphs.md", "@hero", "deep/computational-graph.png",
     "A computational graph with input, weight and bias leaves flowing through matrix multiply, add, sigmoid and loss nodes",
     "The forward pass computes values left to right; the backward pass applies the chain rule right to left. Every framework builds this graph so it can walk it backwards automatically."),
    (f"{D}/training-loop-anatomy.md", "@hero", "deep/training-loop.png",
     "The six stages of a training loop shown as a cycle: batch, forward, loss, backward, optimizer step, and zero grad",
     "The loop every training script runs. `zero_grad()` is the step that is easiest to omit and hardest to notice missing — PyTorch accumulates gradients, so forgetting it silently sums them across batches."),
    (f"{D}/activation-functions.md", "@hero", "deep/activation-functions.png",
     "Six activation functions plotted with their derivatives, plus the sigmoid gradient bounded at one quarter and its effect compounded over depth",
     "Each activation with its derivative dashed. The bottom-right panels are the reason ReLU displaced sigmoid: the sigmoid's gradient never exceeds ¼, so twenty stacked layers multiply the signal by at most 4⁻²⁰."),
    (f"{D}/weight-initialization.md", "@hero", "deep/weight-init-and-gradient-flow.png",
     "Activation standard deviation across thirty layers under four initialisation scales, and gradient magnitude compounding across twenty layers",
     "Initialisation scale decides whether a signal survives depth at all. He initialisation (√(2/n)) holds the activation variance roughly constant through thirty ReLU layers; being off by a constant factor collapses or explodes it exponentially."),
    (f"{D}/vanishing-and-exploding-gradients.md", "@hero", "deep/weight-init-and-gradient-flow.png",
     "Gradient magnitude across layers under vanishing, healthy and exploding regimes on a log scale",
     "Gradients are a product of per-layer Jacobians, so any consistent deviation from 1.0 compounds geometrically. The right-hand panel is the whole problem: ×0.6 per layer leaves the early layers with nothing to learn from."),
    (f"{D}/optimizers.md", "@hero", "deep/optimizer-trajectories.png",
     "Four optimizer trajectories on an elongated ravine, with SGD zigzagging and stalling while momentum, RMSProp and Adam reach the minimum",
     "A ravine — steep across, shallow along — is the surface that separates the optimizers. At a well-tuned rate SGD still flips sign on all 60 steps and stops short; momentum reaches the minimum with 13 oscillations. These paths are simulated, not sketched."),
    (f"{D}/learning-rate-schedules.md", "@hero", "deep/lr-schedules.png",
     "Constant, step, exponential and cosine learning-rate schedules, plus linear warmup followed by cosine decay",
     "Warmup plus cosine decay is the transformer default. The warmup exists because early gradients are large and poorly conditioned — starting at full rate can move the weights somewhere training never recovers from."),
    (f"{D}/normalization-layers.md", "@hero", "deep/normalization-axes.png",
     "Four grids showing which batch and channel elements are averaged together by batch, layer, instance and group normalization",
     "The only thing separating these four is which axes get averaged into one mean and variance. Batch norm reaches across the batch — which is why it misbehaves at batch size 1 and why transformers use layer norm instead."),
    (f"{D}/normalization-layers.md", "## The problem: distribution shift between layers", "deep/normalization-effect.png",
     "Pre-activation distributions drifting across layers without normalization and staying centred with it, plus faster loss convergence",
     "Without normalization the pre-activation distribution drifts and widens with depth. Keeping it centred is what allows a higher learning rate, which is where most of the speed-up actually comes from."),
    (f"{D}/skip-connections-and-depth.md", "@hero", "deep/skip-connections.png",
     "A residual block with an identity shortcut bypassing two weight layers, and error curves showing plain networks degrading with depth while residual ones improve",
     "The shortcut means the block only has to learn the *change* to its input, and gives the gradient an unobstructed path backwards. Before it, adding layers to a plain network made test error worse — the degradation problem ResNet solved."),
    (f"{D}/regularization-in-deep-nets.md", "## Dropout: the algorithm", "deep/dropout.png",
     "A fully connected network beside the same network with half its hidden units and their edges removed by a dropout mask",
     "Dropout samples a different subnetwork every batch, so no unit can rely on any specific other unit being present. At test time the full network is used with activations scaled to match the training-time expectation."),
    (f"{D}/model-capacity-and-scaling.md", "@hero", "deep/scaling-laws.png",
     "Log-log plot of test loss against parameter count for three compute budgets, each with a marked optimum",
     "Loss falls as a power law in parameters, data and compute — straight lines on log–log axes. Each compute budget has its own optimal model size, which is the result Chinchilla made concrete."),
    (f"{D}/gpu-training-and-mixed-precision.md", "@hero", "deep/float-formats.png",
     "Bit layouts for FP32, TF32, BF16, FP16 and FP8 showing sign, exponent and mantissa widths",
     "Exponent bits buy dynamic range; mantissa bits buy precision. BF16 keeps FP32's full 8-bit exponent and sacrifices mantissa — which is exactly why it trains stably where FP16 needs loss scaling to avoid underflow."),
    (f"{D}/distributed-training.md", "@hero", "deep/parallelism-strategies.png",
     "Data parallelism replicating the model across GPUs, pipeline parallelism splitting it by layer, and tensor parallelism splitting individual matrices",
     "Three ways to split training across devices. Data parallel is the simplest and the default; the other two exist for when the model itself no longer fits on one GPU, and both pay for it in communication."),

    # ---------------------------------------------------------------- sequences & NLP
    (f"{N}/text-preprocessing-and-tokenization.md", "@hero", "nlp/tokenization-granularity.png",
     "The word tokenization split into characters, into two subword pieces, and kept as a single word token",
     "Characters give a tiny vocabulary but very long sequences; whole words give short sequences but a huge vocabulary that still breaks on unseen words. Subword tokenisation is the compromise every modern model uses."),
    (f"{N}/word-embeddings.md", "@hero", "nlp/word-embeddings.png",
     "Word vectors showing a consistent gender offset between related pairs, and clusters of semantically similar words",
     "Embeddings place words so that geometry carries meaning: the offset from *king* to *queen* is roughly the offset from *man* to *woman*. Similar words cluster, which is what makes nearest-neighbour retrieval over embeddings work."),
    (f"{N}/recurrent-neural-networks.md", "@hero", "nlp/rnn-unrolled.png",
     "An RNN unrolled across five timesteps sharing one set of weights, with the backpropagation-through-time path marked",
     "Unrolled, an RNN is a very deep network that reuses one weight matrix at every step. The red path is backpropagation through time — and repeatedly multiplying by the same matrix is precisely why the gradient vanishes or explodes."),
    (f"{N}/lstm-and-gru.md", "@hero", "nlp/lstm-cell.png",
     "An LSTM cell with forget, input and output gates operating on a cell-state highway, and gradient decay curves for RNN versus LSTM",
     "The cell state runs across the top almost untouched — information passes along it by addition rather than repeated multiplication. That additive path is what keeps the gradient alive over long spans, as the right panel shows."),
    (f"{N}/seq2seq-and-encoder-decoder.md", "@hero", "nlp/seq2seq-bottleneck.png",
     "An encoder compressing a source sentence into one context vector feeding a decoder, with attention links drawn between all positions",
     "The original design forced the entire source sentence through one fixed-size vector — the bottleneck that capped translation quality on long sentences. Attention, drawn faintly here, removed it by letting every output position read every input position."),
    (f"{N}/attention-mechanism.md", "@hero", "nlp/attention-weights.png",
     "An attention weight heatmap over a sentence where the verb attends to its true subject, beside a causal mask matrix",
     "Attention weights over a sentence with a relative clause: *was* attends back to *cat*, its actual subject, rather than to the nearer *mouse*. The causal mask on the right is what stops a decoder reading tokens it has not generated yet."),
    (f"{N}/self-attention-in-depth.md", "@hero", "nlp/qkv-attention.png",
     "The scaled dot-product attention pipeline from input through query, key and value projections to the softmax-weighted output",
     "Queries and keys produce the scores; values carry the content that gets mixed. The √d divisor keeps the dot products from growing with dimension and driving the softmax into a near-one-hot regime where gradients vanish."),
    (f"{N}/self-attention-in-depth.md", "## The O(n²) memory problem", "nlp/attention-quadratic-cost.png",
     "Log-log plot of attention cost growing quadratically with sequence length while feed-forward cost grows linearly",
     "Attention is O(n²) in sequence length while the feed-forward layers are linear. Below a few thousand tokens the MLPs dominate the cost; past that, attention takes over — which is what every long-context method is trying to fix."),
    (f"{N}/transformer-architecture.md", "@hero", "nlp/transformer-block.png",
     "Post-LN and pre-LN transformer blocks side by side, showing LayerNorm after the residual add versus before the sublayer",
     "The 2017 paper put LayerNorm after the residual add; every modern model puts it before. Pre-LN leaves a clean identity path from input to output, which is why it trains without the warmup schedule Post-LN requires."),
    (f"{N}/positional-encodings.md", "@hero", "nlp/positional-encoding.png",
     "A sinusoidal positional encoding heatmap, individual dimension waves at different frequencies, and a position-similarity matrix",
     "Self-attention is permutation-invariant, so position has to be injected. Each dimension is a wave of a different frequency; the similarity matrix on the right shows the payoff — the encoding of two positions depends on the distance between them."),
    (f"{N}/decoding-strategies.md", "@hero", "nlp/decoding-strategies.png",
     "The same next-token distribution reshaped by low temperature, high temperature, top-k truncation and nucleus sampling",
     "All four operate on the same logits. Temperature rescales before the softmax; top-k keeps a fixed number of candidates; nucleus sampling keeps the smallest set reaching probability p, so the number of candidates adapts to how confident the model is."),
    (f"{N}/parameter-efficient-finetuning.md", "@hero", "nlp/lora.png",
     "A frozen weight matrix beside a low-rank product of two thin matrices, merged at inference",
     "LoRA freezes the pretrained matrix and trains a low-rank update beside it. At rank 8 that is roughly 0.4 % of the original parameter count — and because the product merges back at inference, it costs no extra latency."),

    # ---------------------------------------------------------------- computer vision
    (f"{V}/images-as-tensors.md", "@hero", "vision/images-as-tensors.png",
     "An RGB image decomposed into its separate red, green and blue channel matrices",
     "An image is a tensor of numbers: height × width × channels. Every convolution, augmentation and normalisation in this section is arithmetic on exactly this array."),
    (f"{V}/convolution-operation.md", "@hero", "vision/convolution-mechanics.png",
     "A 5×5 input, a 3×3 vertical-edge kernel, and the resulting 3×3 output with the top-left computation shown",
     "One kernel position: multiply the patch elementwise by the kernel and sum. Sliding that operation across the input produces the output — and with no padding a 5×5 input and 3×3 kernel give a 3×3 result."),
    (f"{V}/convolution-operation.md", "## Classic hand-designed kernels, as intuition", "vision/convolution-kernels.png",
     "The same input image processed by identity, blur, two Sobel edge detectors and a sharpening kernel",
     "The operation is fixed; only the nine numbers change. Classical vision hand-designed these kernels — a CNN learns them from data instead, which is the whole shift the architecture represents."),
    (f"{V}/convolution-operation.md", "## Receptive field", "vision/receptive-field.png",
     "Successive 3×3 convolutions shrinking a 9×9 input to a single unit, illustrating receptive field growth",
     "Each 3×3 convolution widens the receptive field by 2. Stacking three of them sees the same 7×7 region as one 7×7 kernel, using fewer parameters and inserting two extra non-linearities along the way."),
    (f"{V}/pooling-and-shape-arithmetic.md", "@hero", "vision/pooling.png",
     "A 4×4 input reduced to 2×2 by max pooling and by average pooling, with the pooling windows outlined",
     "Pooling halves the spatial dimensions by summarising each window. Max pooling keeps the strongest response and discards where exactly it occurred — a deliberate trade of spatial precision for translation tolerance."),
    (f"{V}/cnn-architectures.md", "@hero", "vision/cnn-architectures.png",
     "Log-log scatter of classic CNN architectures by depth and parameter count from LeNet to ResNet-152",
     "Depth grew by more than an order of magnitude while parameter counts did not — VGG-16 has more parameters than ResNet-152. Skip connections and 1×1 bottlenecks are what decoupled the two."),
    (f"{V}/data-augmentation.md", "@hero", "vision/data-augmentation.png",
     "One image shown under flip, rotation, crop, brightness, contrast, noise and cutout transformations",
     "Every panel carries the same label. Augmentation encodes the invariances you believe the task has — and picking wrong matters: a horizontal flip is free for pet photos and fatal for reading digits."),
    (f"{V}/transfer-learning-for-vision.md", "@hero", "vision/transfer-learning.png",
     "A convolutional stack with early layers frozen and the final layers and classifier head marked for retraining",
     "Early layers learn edges and textures that transfer across almost any vision task; later layers are specific to the original labels. Freeze the general part, retrain the specific part — and with little data, freeze more."),
    (f"{V}/object-detection.md", "@hero", "vision/vision-task-types.png",
     "The same scene under classification, object detection, semantic segmentation and instance segmentation",
     "Four tasks on one image, in increasing order of output detail. Semantic segmentation labels every pixel but cannot separate two adjacent animals; instance segmentation can, which is exactly the harder problem."),
    (f"{V}/object-detection.md", "## Intersection over Union (IoU)", "vision/iou.png",
     "Four pairs of overlapping boxes with IoU values of 0.05, 0.35, 0.62 and 0.88",
     "IoU is the overlap divided by the combined area. A detection usually counts as correct above 0.5 — an arbitrary line, which is why detection benchmarks report mAP averaged over several thresholds instead."),
    (f"{V}/semantic-and-instance-segmentation.md", "@hero", "vision/vision-task-types.png",
     "Classification, detection, semantic segmentation and instance segmentation compared on one scene",
     "Semantic segmentation assigns a class to every pixel; instance segmentation additionally separates individual objects of that class. The distinction only matters when objects of the same class touch — which in practice is most of the time."),
    (f"{V}/vision-transformers.md", "@hero", "vision/vit-patches.png",
     "An image divided into sixteen patches on a grid and then flattened into a sequence of sixteen tokens",
     "A ViT cuts the image into fixed patches, flattens each into a vector, and feeds the result to a standard transformer. There is no convolution anywhere — the locality a CNN has built in must instead be learned from data, which is why ViTs need far more of it."),
    (f"{V}/cnn-interpretability.md", "@hero", "vision/gradcam.png",
     "An input image, a Grad-CAM heatmap, and the two overlaid showing which region drove the prediction",
     "Grad-CAM weights the final convolutional feature maps by the gradient of the target class, producing a coarse map of what the model actually used. It shows *where* the evidence was, not *why* it counted as evidence."),

    # ---------------------------------------------------------------- generative
    (f"{G}/what-is-a-generative-model.md", "@hero", "generative/discriminative-vs-generative.png",
     "A discriminative model drawing only a boundary between two classes, beside a generative model fitting the density of each class",
     "A discriminative model needs only the boundary; a generative model learns the whole distribution. That is more work and more error-prone — but it is what makes sampling new data possible at all."),
    (f"{G}/what-is-a-generative-model.md", "## The three-way trade: quality, coverage, speed", "generative/generative-trilemma.png",
     "A scatter of generative model families positioned by sample quality and mode coverage with bubble size showing sampling speed",
     "The generative trilemma: high sample quality, broad mode coverage, and fast sampling — pick two. Diffusion buys quality and coverage with slow iterative sampling; GANs are fast and sharp but drop modes."),
    (f"{G}/autoencoders.md", "@hero", "generative/autoencoder.png",
     "An encoder narrowing to a latent bottleneck and a decoder widening back to a reconstruction",
     "An autoencoder is trained only to reproduce its input. The bottleneck is what forces it to learn a compressed representation rather than the identity function — and a plain autoencoder's latent space has no structure that makes sampling meaningful."),
    (f"{G}/variational-autoencoders.md", "@hero", "generative/vae.png",
     "A VAE encoding to a mean and standard deviation with the reparameterisation trick, and a latent grid decoded into smoothly varying outputs",
     "A VAE encodes to a *distribution* rather than a point, and the reparameterisation trick moves the sampling off the gradient path so backpropagation still works. The KL term is what keeps the latent space continuous enough for the grid on the right to vary smoothly."),
    (f"{G}/generative-adversarial-networks.md", "@hero", "generative/gan-architecture.png",
     "A generator turning noise into fake samples and a discriminator judging them against real samples, with the generator's gradient fed back",
     "Two networks with opposing objectives: the discriminator learns to spot fakes, the generator learns to defeat it. There is no loss to minimise jointly — training seeks an equilibrium, which is why GANs are so much less stable than everything else here."),
    (f"{G}/gan-training-challenges.md", "@hero", "generative/mode-collapse.png",
     "A target distribution with eight modes, a collapsed generator covering only two, and a healthy generator covering all eight",
     "Mode collapse: the generator finds a small set of outputs the discriminator cannot reject and stops exploring. The loss curves can look entirely healthy while this happens, which is why GAN evaluation needs coverage metrics rather than loss."),
    (f"{G}/diffusion-models.md", "@hero", "generative/diffusion-process.png",
     "A structured two-dimensional distribution progressively destroyed by noise across six steps, and the reverse denoising sequence beneath it",
     "The forward process destroys structure with noise on a fixed schedule and requires no learning at all. The model learns only to undo one step — and chaining those small reversals from pure noise is what generates a sample."),
    (f"{G}/diffusion-models.md", "## Noise schedules and what they change", "generative/diffusion-schedule.png",
     "Linear and cosine noise schedules plotted as signal remaining against timestep, and the signal-noise blend at each step",
     "The schedule fixes how much signal survives at each timestep. The linear schedule destroys information too early in the trajectory, which is why the cosine schedule replaced it for image models."),
    (f"{G}/ddpm-sampling-and-guidance.md", "## Classifier-free guidance, and the guidance scale as a quality/diversity dial", "generative/guidance-scale.png",
     "Four sample distributions at guidance scales of 0, 1.5, 5 and 15, tightening and losing diversity as the scale rises",
     "The guidance scale extrapolates away from the unconditional prediction. Raising it tightens adherence to the prompt and visibly destroys diversity — the characteristic over-saturated look of an over-guided image."),
    (f"{G}/normalizing-flows.md", "@hero", "generative/normalizing-flow.png",
     "A Gaussian base density transformed through invertible layers into an increasingly complex target density",
     "A flow is a chain of *invertible* maps from a simple base density to a complex one. Invertibility is what makes the exact likelihood computable — and also what constrains the architecture severely, since every layer must have a tractable Jacobian determinant."),

    # ---------------------------------------------------------------- RL
    (f"{R}/rl-problem-setup.md", "@hero", "rl/agent-environment-loop.png",
     "An agent sending actions to an environment which returns states and rewards in a closed loop",
     "The whole of RL is this loop. Crucially the agent is never told the correct action — only how good the outcome was — which is what separates it from supervised learning."),
    (f"{R}/markov-decision-processes.md", "@hero", "rl/gridworld-value-iteration.png",
     "A gridworld MDP with goal and trap states, the optimal value function computed by value iteration, and the greedy policy arrows",
     "A 4×4 gridworld solved by value iteration. The values and arrows are computed, not drawn — note the cell below the trap points *down and away* from the +1 goal, because reaching it via the trap is worse than the longer route."),
    (f"{R}/markov-decision-processes.md", "## The objective: expected return", "rl/discount-factor.png",
     "Exponential decay curves for discount factors of 0.5, 0.9, 0.99 and 0.999 against steps into the future",
     "γ sets how far ahead the agent effectively plans — roughly 1/(1−γ) steps. At γ = 0.9 a reward fifty steps away is worth half a percent of an immediate one, so the agent is functionally blind to it."),
    (f"{R}/value-functions-and-bellman-equations.md", "@hero", "rl/gridworld-value-iteration.png",
     "A gridworld with its optimal value function and the greedy policy derived from it",
     "V*(s) is the expected return from each state under optimal play. Once you have it the policy is free: at every state, take the action leading to the highest-valued neighbour — which is what the arrows in the third panel are."),
    (f"{R}/q-learning-and-sarsa.md", "## The cliff-walking example", "rl/cliff-walking.png",
     "The cliff-walking grid with Q-learning taking the optimal path along the edge and SARSA taking a safer route, plus their learning curves",
     "The classic separation between the two. Q-learning learns the optimal path and hugs the cliff; SARSA learns the value of the ε-greedy policy it actually follows, so it accounts for the chance of a random step into the cliff and detours. Under exploration SARSA therefore earns more — −25 against −53 in this run."),
    (f"{R}/exploration-strategies.md", "@hero", "rl/exploration-strategies.png",
     "Average reward and percentage of optimal actions for greedy, epsilon-greedy, decaying epsilon and UCB on a ten-armed bandit",
     "A ten-armed bandit averaged over 300 runs. Pure greedy locks onto whichever arm happened to look good first and plateaus well below optimal — the clearest possible demonstration that some exploration is not optional."),
    (f"{R}/ppo-and-trust-regions.md", "@hero", "rl/ppo-clipping.png",
     "The PPO clipped objective plotted against the probability ratio for positive and negative advantage",
     "PPO's clipping flattens the objective once the policy ratio leaves [1−ε, 1+ε], so there is no gradient rewarding a further move. That is what keeps the update inside a trust region without TRPO's second-order machinery."),
    (f"{R}/rlhf-and-preference-optimization.md", "@hero", "rl/rlhf-pipeline.png",
     "The four RLHF stages: pretraining, supervised fine-tuning, reward model training, and reinforcement learning against the reward",
     "Four stages, each with a different objective and dataset. The KL penalty in the final stage is essential — without it the policy drifts into whatever exploits the reward model rather than what humans actually preferred."),
    (f"{R}/actor-critic-methods.md", "@hero", "rl/algorithm-map.png",
     "The RL algorithm landscape grouped into value-based, policy-based, actor-critic and model-based families",
     "Where the algorithms sit relative to each other. Actor–critic methods are the middle ground this page occupies: a policy that acts, plus a value estimate that criticises, which cuts the variance that plagues pure policy gradients."),

    # ---------------------------------------------------------------- MLOps
    (f"{M}/data-and-concept-drift.md", "@hero", "mlops/drift-types.png",
     "Three panels contrasting no drift, covariate drift where the input distribution moves, and concept drift where the input-output relationship changes",
     "Covariate drift moves P(x) and is visible from inputs alone. Concept drift changes P(y|x) with the inputs unchanged — invisible without labels, which is why it is the dangerous one."),
    (f"{M}/data-and-concept-drift.md", "## Detecting input drift without labels: PSI, KL divergence, Kolmogorov-Smirnov", "mlops/drift-detection.png",
     "A population stability index rising past warning thresholds weeks before measured accuracy visibly declines",
     "Input drift is measurable the moment it starts; accuracy only moves once labels arrive, which can be weeks later. Monitoring inputs buys you that gap."),
    (f"{M}/serving-patterns.md", "@hero", "mlops/deployment-strategies.png",
     "Blue-green, canary and shadow deployment strategies shown as traffic splits between the current and new model",
     "Three ways to put a new model in front of traffic. Shadow is the only one with no user-visible risk — the new model scores real requests but its output is discarded — which makes it the right first step for a model you do not yet trust."),
    (f"{M}/serving-patterns.md", "## Real-time synchronous serving", "mlops/latency-percentiles.png",
     "A long-tailed latency histogram with p50, p95 and p99 marked far apart, and the mean sitting misleadingly low",
     "Serving latency is long-tailed, so the mean is close to the median and describes almost nobody's experience of the slow requests. SLAs are written in percentiles for this reason."),
    (f"{M}/inference-optimization.md", "@hero", "mlops/batching-tradeoff.png",
     "Throughput rising with batch size while per-request latency also rises, with an SLA ceiling marking the largest usable batch",
     "Batching amortises fixed per-call overhead, so throughput climbs — but every request now waits for the whole batch. The SLA sets the ceiling, and that is what picks the batch size."),
    (f"{M}/inference-optimization.md", "## Quantisation: dynamic, static, and quantisation-aware training", "mlops/quantization.png",
     "Memory footprint falling from FP32 to INT4 alongside relative task quality holding to INT8 then dropping",
     "Quantization is mostly a memory and bandwidth win. Quality holds remarkably well down to INT8; below that the drop becomes real, and INT4 needs careful per-channel schemes to stay usable."),
    (f"{M}/online-evaluation-and-ab-testing.md", "@hero", "mlops/ab-testing.png",
     "Statistical power against sample size for three effect sizes, and a daily-peeking confidence interval that briefly crosses significance by chance",
     "Small effects need enormous samples: detecting a 1 % relative lift takes roughly twenty-five times the traffic of a 5 % one. The right panel shows why fixed horizons matter — check daily and you will eventually see a 'significant' result that is pure noise."),
    (f"{M}/feature-stores.md", "@hero", "mlops/training-serving-skew.png",
     "A training pipeline and a serving pipeline computing the same feature differently, producing silent quality loss",
     "Training–serving skew: the same feature computed twice, in two languages, by two teams. The model is identical and the metrics look fine offline — the loss shows up only in production, which is the problem a feature store exists to remove."),
    (f"{M}/ci-cd-for-ml.md", "@hero", "mlops/ml-test-pyramid.png",
     "A four-tier test pyramid with unit tests at the base, then data validation, integration tests and model quality gates",
     "The classical test pyramid plus a tier that does not exist in ordinary software: data validation. Most production ML failures are data failures, and no amount of unit testing on the transform code catches them."),
    (f"{M}/training-infrastructure-and-cost.md", "@hero", "mlops/cost-breakdown.png",
     "Training as a small one-off share of lifetime compute spend against inference as the dominant recurring share, with cumulative cost curves crossing early",
     "Training is a headline number paid once; inference is paid on every request forever. For most deployed models the crossover arrives within months, which is why inference optimisation usually returns more than training optimisation."),
]


def insert(text: str, anchor: str, block: str) -> str | None:
    lines = text.split("\n")
    if anchor == "@hero":
        # After the closing ':::' of the Key idea admonition, else after the H1.
        opens = [i for i, l in enumerate(lines) if l.startswith(":::") and len(l) > 3]
        closes = [i for i, l in enumerate(lines) if l.strip() == ":::"]
        if opens and closes:
            idx = next((c for c in closes if c > opens[0]), None)
        else:
            idx = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
        if idx is None:
            return None
    else:
        idx = next((i for i, l in enumerate(lines) if l.strip() == anchor.strip()), None)
        if idx is None:
            return None
    lines.insert(idx + 1, "\n" + block)
    return "\n".join(lines)


def main():
    check = "--check" in sys.argv
    done = skipped = missing = 0
    problems: list[str] = []

    for doc, anchor, img, alt, caption in MANIFEST:
        path = DOCS / doc
        if not path.exists():
            problems.append(f"MISSING PAGE  {doc}")
            missing += 1
            continue
        text = path.read_text(encoding="utf-8")
        if img in text:
            skipped += 1
            continue
        block = (
            f'<Figure\n'
            f'  src="/img/ml/{img}"\n'
            f'  alt="{alt}"\n'
            f'  caption="{caption}"\n'
            f'/>'
        )
        out = insert(text, anchor, block)
        if out is None:
            problems.append(f"ANCHOR NOT FOUND  {doc}  →  {anchor!r}")
            missing += 1
            continue
        if not check:
            path.write_text(out, encoding="utf-8")
        done += 1

    print(f"inserted {done}, already present {skipped}, problems {missing}"
          + ("  [check only]" if check else ""))
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
