"""Shared evaluation metrics — one definition, imported by every notebook that reports one.

Why this file exists: `evaluation.ipynb` and `extraction_validation.ipynb` each carried their
own `ece()` with a different default bin count (10 vs 5), and a 10-bin raw figure was being
compared against a 5-bin calibrated one as if it were a before/after on the same data. A
calibration error is only a number relative to its estimator, so `n_bins` here is a REQUIRED
argument -- there is no default to disagree about, and every caller has to state the bin count
it is reporting.

Nothing in this module touches the corpus, the index or any model: pure functions over arrays,
so importing it is free and its results are reproducible by construction.
"""

import math

import numpy as np

__all__ = ["bin_stats", "ece", "wilson", "oof_isotonic", "prf1", "count_bias"]


def bin_stats(conf, y, n_bins):
    """Per-bin (mean confidence, observed positive rate, n) over `n_bins` equal-width bins."""
    conf = np.asarray(conf, dtype=float)
    y = np.asarray(y, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(conf, edges) - 1, 0, n_bins - 1)
    out = []
    for b in range(n_bins):
        m = idx == b
        if m.sum():
            out.append((float(conf[m].mean()), float(y[m].mean()), int(m.sum())))
    return out


def ece(conf, y, n_bins):
    """Expected Calibration Error: sum_b (n_b/N) * |observed_b - confidence_b|.

    `n_bins` is deliberately required. Nixon et al. (2019) show that metric variants reorder
    the same predictions, so a calibration figure without its bin count is not interpretable;
    callers report the number and the estimator together.
    """
    y = np.asarray(y, dtype=float)
    if len(y) == 0:
        return float("nan")
    return float(sum(n / len(y) * abs(obs - c) for c, obs, n in bin_stats(conf, y, n_bins)))


def wilson(k, n, z=1.96):
    """95% Wilson score interval for k successes in n trials, as (lo, hi).

    Wilson rather than the normal approximation: the normal interval has ZERO width at p=0,
    which would report "fabrication risk 0.00 [0.00, 0.00]" off 20 questions. Sanity checks
    (used as doctests by the notebook): p=.10, n=20 -> [0.03, 0.30]; p=0, n=20 -> [0.00, 0.16].
    """
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def oof_isotonic(raw, y, n_splits=5, random_state=42):
    """Out-of-fold isotonic calibration: every row is predicted by a fit that never saw it.

    Returns the assembled out-of-fold vector, or None when the sample cannot support the CV
    (one class only, or a class with fewer members than folds). Protocol is fixed here so the
    factory, the validation notebook and the evaluation notebook cannot silently diverge:
    StratifiedKFold(shuffle=True, random_state=42) + IsotonicRegression(out_of_bounds="clip").
    """
    from sklearn.isotonic import IsotonicRegression
    from sklearn.model_selection import StratifiedKFold

    raw = np.asarray(raw, dtype=float)
    y = np.asarray(y)
    if len(set(y.tolist())) < 2:
        return None
    if min((y == 1).sum(), (y == 0).sum()) < n_splits:
        return None
    oof = np.full_like(raw, np.nan, dtype=float)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    for tr, te in skf.split(raw.reshape(-1, 1), y):
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(raw[tr], y[tr].astype(float))
        oof[te] = iso.predict(raw[te])
    return oof


def prf1(y_true, y_pred):
    """TP/FP/FN/TN + precision/recall/F1 for a binary field, without a sklearn import."""
    yt = np.asarray(y_true).astype(int)
    yp = np.asarray(y_pred).astype(int)
    tp = int(((yp == 1) & (yt == 1)).sum())
    fp = int(((yp == 1) & (yt == 0)).sum())
    fn = int(((yp == 0) & (yt == 1)).sum())
    tn = int(((yp == 0) & (yt == 0)).sum())
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "n": int(len(yt)),
            "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


def count_bias(tp, fp, fn):
    """Signed error in a REPORTED COUNT, which is what a Bucket-3 aggregate answer actually is.

    F1 says nothing about this: a field whose false positives and false negatives roughly
    cancel still yields a usable count, while a field with the same F1 and lopsided errors
    does not. predicted_count - true_count = FP - FN.
    """
    predicted, true = tp + fp, tp + fn
    return {"predicted_count": int(predicted), "true_count": int(true),
            "count_bias": int(fp - fn),
            "count_ratio": round(predicted / true, 3) if true else None}
