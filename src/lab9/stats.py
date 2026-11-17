"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite
from numbers import Real

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive; accept only exact PASS/FAIL labels.

    Unequal lengths or invalid labels raise ValueError. Empty pairs give zeros.
    """
    if len(human) != len(judge):
        raise ValueError("human and judge labels must have equal lengths")
    counts = dict(tp=0, fp=0, fn=0, tn=0)
    for h, j in zip(human, judge):
        if h not in ("PASS", POS) or j not in ("PASS", POS):
            raise ValueError("labels must be PASS or FAIL")
        key = ("tp" if h == POS else "fp") if j == POS else ("fn" if h == POS else "tn")
        counts[key] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """FAIL precision and recall; return 0.0 for each zero denominator."""
    cm = confusion(human, judge)
    predicted = cm["tp"] + cm["fp"]
    actual = cm["tp"] + cm["fn"]
    return (cm["tp"] / predicted if predicted else 0.0,
            cm["tp"] / actual if actual else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    if not n:
        raise ValueError("kappa is undefined for empty labels")
    # Integer agreement counts avoid rounding p_e to one on imbalanced data.
    chance = ((cm["tp"] + cm["fn"]) * (cm["tp"] + cm["fp"])
              + (cm["tn"] + cm["fp"]) * (cm["tn"] + cm["fn"]))
    denominator = n * n - chance
    if denominator == 0:
        raise ValueError("kappa is undefined when chance agreement is one")
    return (n * (cm["tp"] + cm["tn"]) - chance) / denominator


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Rogan-Gladen estimate clipped to [0, 1].

    Raise ValueError for non-real, boolean, nonfinite or out-of-range inputs,
    or sensitivity + specificity == 1 (unidentifiable prevalence).
    Negative nonzero denominators are supported for an inverted classifier.
    """
    for value in (observed_rate, sensitivity, specificity):
        if isinstance(value, bool) or not isinstance(value, Real) or not 0 <= value <= 1 or not isfinite(value):
            raise ValueError("probabilities must be finite real numbers in [0, 1]")
    denominator = sensitivity + specificity - 1
    if denominator == 0:
        raise ValueError("Rogan-Gladen is undefined when sensitivity + specificity == 1")
    return float(min(1.0, max(0.0, (observed_rate + specificity - 1) / denominator)))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    try:
        x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("paired inputs must be finite numeric vectors") from exc
    if x.ndim != 1 or y.ndim != 1 or x.size != y.size or not x.size:
        raise ValueError("paired inputs must be nonempty one-dimensional vectors of equal length")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("paired inputs must be finite")
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, int) or n_resamples <= 0:
        raise ValueError("n_resamples must be a positive integer")
    if isinstance(confidence, bool) or not isinstance(confidence, Real) or not isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must be finite and strictly between zero and one")
    if isinstance(rng, bool) or not isinstance(rng, int) or rng < 0:
        raise ValueError("rng must be a nonnegative integer seed")
    if np.array_equal(x, y):
        return 0.0, 0.0, 0.0
    if x.size < 2:
        raise ValueError("nonidentical inputs need at least two paired items for scipy bootstrap")

    def difference(u, v, axis=-1):
        return np.mean(u, axis=axis) - np.mean(v, axis=axis)

    result = bootstrap((x, y), difference, paired=True, method="percentile",
                       n_resamples=n_resamples, confidence_level=confidence,
                       rng=np.random.default_rng(rng))
    return float(difference(x, y)), float(result.confidence_interval.low), float(result.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
