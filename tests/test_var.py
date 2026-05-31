"""
test_var.py — Tests for src/var.py.

Tests are grouped by method.  Each test is self-contained, fast, and uses
only deterministic synthetic data or hand-computable reference values.
"""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.var import (
    cornish_fisher_var,
    historical_var_cvar,
    monte_carlo_var,
    parametric_var_cvar,
)


# ---------------------------------------------------------------------------
# Historical VaR
# ---------------------------------------------------------------------------

class TestHistoricalVarCvar:
    def test_var_equals_np_percentile(self, synthetic_normal_returns):
        """Historical VaR must equal np.percentile at the corresponding quantile."""
        var, _ = historical_var_cvar(synthetic_normal_returns, confidence=0.99)
        expected = float(np.percentile(synthetic_normal_returns, 1))
        assert np.isclose(var, expected), f"VaR {var} != percentile {expected}"

    def test_cvar_at_least_as_large_as_var(self, synthetic_normal_returns):
        """CVaR magnitude must be >= VaR magnitude (tail average >= threshold)."""
        var, cvar = historical_var_cvar(synthetic_normal_returns, confidence=0.99)
        assert abs(cvar) >= abs(var), (
            f"|CVaR| {abs(cvar):.6f} < |VaR| {abs(var):.6f} — violates CVaR >= VaR"
        )

    def test_var_is_negative_for_loss_series(self, synthetic_normal_returns):
        """VaR should be negative (loss direction) for a standard return series."""
        var, cvar = historical_var_cvar(synthetic_normal_returns, confidence=0.99)
        assert var < 0, "VaR should be negative (a loss)"
        assert cvar < 0, "CVaR should be negative (a loss)"

    def test_fixed_array_hand_computation(self):
        """VaR on a known array must match the hand-computed percentile exactly."""
        # 100 evenly spaced values: [-0.99, -0.98, ..., 0.00]
        r = np.linspace(-0.99, 0.0, 100)
        var, _ = historical_var_cvar(r, confidence=0.99)
        expected = float(np.percentile(r, 1))
        assert np.isclose(var, expected)


# ---------------------------------------------------------------------------
# Parametric VaR
# ---------------------------------------------------------------------------

class TestParametricVarCvar:
    def test_matches_hand_computed_value(self):
        """For μ=0, σ=0.01 at 99%: VaR = norm.ppf(0.01) * 0.01 ≈ -0.023264."""
        mu, sigma = 0.0, 0.01
        r = np.array([mu] * 1000)  # all-zero mean, but need to pass an array
        # Build synthetic series with known μ and σ
        rng = np.random.default_rng(99)
        r = rng.normal(loc=mu, scale=sigma, size=10_000)
        var, _ = parametric_var_cvar(pd.Series(r), confidence=0.99)
        expected = mu + stats.norm.ppf(0.01) * sigma  # ≈ -0.02326
        # Approximate to 4 d.p. (sampling noise in μ̂ and σ̂)
        assert abs(var - expected) < 0.0005, (
            f"Parametric VaR {var:.6f} deviates from hand value {expected:.6f}"
        )

    def test_cvar_larger_than_var(self, synthetic_normal_returns):
        """Parametric CVaR magnitude >= VaR magnitude."""
        var, cvar = parametric_var_cvar(synthetic_normal_returns, confidence=0.99)
        assert abs(cvar) >= abs(var)

    def test_higher_confidence_gives_larger_var(self, synthetic_normal_returns):
        """99% VaR should have larger magnitude than 95% VaR."""
        var_95, _ = parametric_var_cvar(synthetic_normal_returns, confidence=0.95)
        var_99, _ = parametric_var_cvar(synthetic_normal_returns, confidence=0.99)
        assert abs(var_99) > abs(var_95), (
            "99% VaR must be more extreme than 95% VaR"
        )


# ---------------------------------------------------------------------------
# Cornish-Fisher VaR
# ---------------------------------------------------------------------------

class TestCornishFisherVar:
    def test_reduces_to_parametric_when_normal(self):
        """When skew=0 and excess kurtosis=0, CF VaR must equal parametric VaR."""
        # A large N(0, σ²) sample: skew ≈ 0, kurt ≈ 0
        rng = np.random.default_rng(7)
        r = pd.Series(rng.normal(0, 0.01, size=50_000))

        cf = cornish_fisher_var(r, confidence=0.99)
        para, _ = parametric_var_cvar(r, confidence=0.99)

        # Tolerance 2e-4 (sampling noise from finite sample; exact equality only
        # holds in the population limit when skew=0, kurt=0 exactly)
        assert abs(cf - para) < 2e-4, (
            f"CF VaR {cf:.6f} should ≈ parametric VaR {para:.6f} for normal data"
        )


# ---------------------------------------------------------------------------
# Monte Carlo VaR (Cholesky)
# ---------------------------------------------------------------------------

class TestMonteCarloVar:
    def test_cholesky_satisfies_LLt_equals_cov(self, synthetic_log_returns_df):
        """L @ L.T must recover the original covariance matrix."""
        cov = synthetic_log_returns_df.cov().values
        L = np.linalg.cholesky(cov)
        assert np.allclose(L @ L.T, cov, atol=1e-12), (
            "Cholesky reconstruction L @ L.T does not match the covariance matrix"
        )

    def test_mc_var_cvar_sign(self, synthetic_log_returns_df, equal_weights_2):
        """MC VaR and CVaR should both be negative (loss direction)."""
        var, cvar = monte_carlo_var(
            synthetic_log_returns_df, equal_weights_2,
            n_simulations=5_000, confidence=0.99, seed=0,
        )
        assert var < 0, f"MC VaR should be negative, got {var}"
        assert cvar < 0, f"MC CVaR should be negative, got {cvar}"
        assert abs(cvar) >= abs(var), "|CVaR| should be >= |VaR|"

    def test_mc_reproducible_with_seed(self, synthetic_log_returns_df, equal_weights_2):
        """Same seed must produce identical VaR on two calls."""
        var1, _ = monte_carlo_var(
            synthetic_log_returns_df, equal_weights_2,
            n_simulations=2_000, confidence=0.99, seed=123,
        )
        var2, _ = monte_carlo_var(
            synthetic_log_returns_df, equal_weights_2,
            n_simulations=2_000, confidence=0.99, seed=123,
        )
        assert var1 == var2, "MC VaR must be identical for the same seed"

    def test_reference_numbers_with_project_data(self):
        """MC VaR with seed=42 on committed CSV must reproduce $24,017 headline figure."""
        log_returns = pd.read_csv(
            "data/log_returns.csv", index_col=0, parse_dates=True
        )
        weights = np.array([0.125] * 8)
        var, cvar = monte_carlo_var(log_returns, weights, seed=42)
        # Published figures: VaR = $24,017, CVaR = $27,734 on $1M portfolio
        assert abs(abs(var) * 1_000_000 - 24_017) < 5, (
            f"MC 99% VaR ${abs(var)*1e6:,.0f} deviates from published $24,017"
        )
        assert abs(abs(cvar) * 1_000_000 - 27_734) < 5, (
            f"MC 99% CVaR ${abs(cvar)*1e6:,.0f} deviates from published $27,734"
        )
