"""
backtest.py — VaR backtesting via the Kupiec Proportion-of-Failures (POF) test.

The Kupiec POF test is a likelihood-ratio test asking: given that we predicted
a 99 % VaR (i.e. expected 1 % breach rate), is the observed breach rate in
the test window statistically consistent with that prediction?

If p-value > 0.05 → model is **not rejected** at 5 % significance (good outcome).
If p-value ≤ 0.05 → model is **rejected** — recalibration is needed.

Reference: Kupiec, P. (1995). "Techniques for Verifying the Accuracy of Risk
Measurement Models." Journal of Derivatives, 3(2), 73–84.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def kupiec_pof(
    test_returns: pd.Series | np.ndarray,
    var_threshold: float,
    confidence: float = 0.99,
) -> dict:
    """Kupiec Proportion-of-Failures (POF) likelihood-ratio test.

    Parameters
    ----------
    test_returns : array-like
        Out-of-sample daily log-return series (the hold-out period).
        Losses are **negative** values, consistent with the sign convention
        used throughout this package.
    var_threshold : float
        The VaR estimate (a negative number, e.g. -0.029) estimated on the
        *training* period.  A breach occurs on any day where the realised
        return falls below this threshold.
    confidence : float
        The confidence level at which VaR was estimated (e.g. 0.99 for 99 %).
        This determines the *expected* breach rate (``1 - confidence``).

    Returns
    -------
    dict with keys:
        ``n``              — number of test-period observations
        ``breaches``       — observed breach count
        ``expected``       — expected breach count under the model
        ``p_actual``       — observed breach rate
        ``p_model``        — expected breach rate (= 1 - confidence)
        ``lr_statistic``   — Kupiec likelihood-ratio statistic (χ²(1))
        ``p_value``        — p-value from χ²(1) distribution
        ``verdict``        — ``"PASS"`` if p_value > 0.05 else ``"FAIL"``

    Notes
    -----
    Edge cases:
    * ``breaches == 0``: log(0) is avoided by returning ``p_value = 1.0``
      (zero breaches is vacuously consistent with the model).
    * ``breaches == n``: similarly returns ``p_value = 0.0`` (every day a
      breach is maximally inconsistent).
    """
    r = np.asarray(test_returns, dtype=float)
    n = len(r)
    p_model = 1.0 - confidence
    breaches = int((r < var_threshold).sum())
    p_actual = breaches / n
    expected = n * p_model

    if breaches == 0 or breaches == n:
        # Degenerate cases: LR statistic is undefined due to log(0).
        # Return a valid but boundary p-value.
        p_value = 1.0 if breaches == 0 else 0.0
        lr = 0.0 if breaches == 0 else np.inf
    else:
        lr = -2.0 * np.log(
            (p_model**breaches * (1.0 - p_model) ** (n - breaches))
            / (p_actual**breaches * (1.0 - p_actual) ** (n - breaches))
        )
        p_value = float(1.0 - stats.chi2.cdf(lr, df=1))

    return {
        "n": n,
        "breaches": breaches,
        "expected": expected,
        "p_actual": p_actual,
        "p_model": p_model,
        "lr_statistic": lr,
        "p_value": p_value,
        "verdict": "PASS" if p_value > 0.05 else "FAIL",
    }
