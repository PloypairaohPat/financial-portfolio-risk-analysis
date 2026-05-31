"""
test_optimization.py — Tests for src/optimization.py.

Verifies that the SLSQP optimiser finds portfolios that are strictly better
than (or equal to) the naive equal-weight baseline on the metrics each
method targets.
"""

import numpy as np
import pandas as pd
import pytest

from src.optimization import max_sharpe_slsqp, min_variance_slsqp
from src.data import TRADING_DAYS, RISK_FREE_RATE


@pytest.fixture
def small_log_returns() -> pd.DataFrame:
    """Synthetic 3-asset log-return DataFrame with non-trivial covariance.

    Asset A: high return, high vol
    Asset B: low return, low vol
    Asset C: moderate return, negative correlation with A

    This structure ensures a non-trivial efficient frontier where the
    optimised portfolios will differ from equal weight.
    """
    rng = np.random.default_rng(42)
    n = 500
    # Build via Cholesky so the covariance is controlled
    cov = np.array([
        [0.0004, -0.0001,  0.00005],
        [-0.0001, 0.0001, -0.00002],
        [0.00005, -0.00002, 0.0002],
    ])
    means = np.array([0.001, 0.0002, 0.0006])  # different per-day mean returns
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n, 3))
    data = z @ L.T + means
    return pd.DataFrame(data, columns=["A", "B", "C"])


class TestMaxSharpe:
    def test_weights_sum_to_one(self, small_log_returns):
        result = max_sharpe_slsqp(small_log_returns)
        assert abs(result["weights"].sum() - 1.0) < 1e-6, (
            f"Max-Sharpe weights sum to {result['weights'].sum()}, not 1.0"
        )

    def test_weights_non_negative(self, small_log_returns):
        result = max_sharpe_slsqp(small_log_returns, weight_bounds=(0.0, 1.0))
        assert np.all(result["weights"] >= -1e-8), (
            "Long-only constraint violated: negative weights found"
        )

    def test_beats_equal_weight_sharpe(self, small_log_returns):
        """Max-Sharpe SLSQP must achieve Sharpe ≥ equal-weight Sharpe."""
        n = small_log_returns.shape[1]
        w_eq = np.ones(n) / n
        cov = (small_log_returns.cov() * TRADING_DAYS).values
        mu = (small_log_returns.mean() * TRADING_DAYS).values
        eq_ret = float(mu @ w_eq)
        eq_vol = float(np.sqrt(w_eq @ cov @ w_eq))
        eq_sharpe = (eq_ret - RISK_FREE_RATE) / eq_vol

        result = max_sharpe_slsqp(small_log_returns)
        assert result["sharpe"] >= eq_sharpe - 1e-6, (
            f"Max-Sharpe {result['sharpe']:.4f} < equal-weight {eq_sharpe:.4f}"
        )

    def test_box_constraint_respected(self, small_log_returns):
        """With a 25% cap, no weight should exceed 0.25."""
        result = max_sharpe_slsqp(small_log_returns, weight_bounds=(0.0, 0.25))
        assert np.all(result["weights"] <= 0.25 + 1e-6), (
            "25% cap constraint violated"
        )


class TestMinVariance:
    def test_weights_sum_to_one(self, small_log_returns):
        result = min_variance_slsqp(small_log_returns)
        assert abs(result["weights"].sum() - 1.0) < 1e-6

    def test_lower_vol_than_equal_weight(self, small_log_returns):
        """Min-variance portfolio must have vol ≤ equal-weight portfolio vol."""
        n = small_log_returns.shape[1]
        w_eq = np.ones(n) / n
        cov = (small_log_returns.cov() * TRADING_DAYS).values
        eq_vol = float(np.sqrt(w_eq @ cov @ w_eq))

        result = min_variance_slsqp(small_log_returns)
        assert result["volatility"] <= eq_vol + 1e-6, (
            f"Min-variance vol {result['volatility']:.4f} > equal-weight {eq_vol:.4f}"
        )
