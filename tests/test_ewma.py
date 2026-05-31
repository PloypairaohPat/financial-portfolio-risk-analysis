"""
test_ewma.py — Tests for ewma_volatility and ewma_var in src/var.py.
"""

import numpy as np
import pandas as pd
import pytest

from src.var import ewma_var, ewma_volatility


class TestEwmaVolatility:
    def test_output_length_matches_input(self):
        """EWMA output must have the same length as the input series."""
        r = pd.Series(np.random.default_rng(0).normal(0, 0.01, 300))
        vols = ewma_volatility(r)
        assert len(vols) == len(r), (
            f"EWMA output length {len(vols)} != input length {len(r)}"
        )

    def test_all_values_positive(self):
        """Volatility estimates must always be strictly positive."""
        rng = np.random.default_rng(1)
        r = pd.Series(rng.normal(0, 0.01, 500))
        vols = ewma_volatility(r)
        assert np.all(vols > 0), "Some EWMA volatility estimates are non-positive"

    def test_causality_zeroing_future_return_does_not_affect_past_sigma(self):
        """σ̂_t must depend only on data through day t−1 (no look-ahead).

        If we zero out return at index k, the EWMA volatility for all
        indices < k must be unchanged, and the value at k itself must change
        (because σ̂_k = λ·σ̂_{k-1} + (1-λ)·r_{k-1}² depends on r[k-1] not r[k]).

        More concretely: zeroing r[k] should NOT change σ̂[k] (it affects
        σ̂[k+1] onward).
        """
        rng = np.random.default_rng(2)
        r = rng.normal(0, 0.01, 200)
        k = 100  # the index we zero out

        # Use a fixed seed_variance so both runs have identical initialisation
        # (otherwise np.var(r) differs between the two series and affects every σ̂)
        fixed_seed_var = float(np.var(r))
        vols_original = ewma_volatility(pd.Series(r), seed_variance=fixed_seed_var)

        r_zeroed = r.copy()
        r_zeroed[k] = 0.0
        vols_zeroed = ewma_volatility(pd.Series(r_zeroed), seed_variance=fixed_seed_var)

        # σ̂ for indices 0..k-1 must be unchanged — output[i] uses r[i],
        # so output[i] is independent of r[k] for all i < k.
        assert np.allclose(vols_original[:k], vols_zeroed[:k]), (
            "Zeroing r[k] changed σ̂ at indices before k — causality violated"
        )

        # σ̂ at index k onward SHOULD differ (output[k] directly uses r[k])
        assert not np.allclose(vols_original[k:], vols_zeroed[k:]), (
            "Zeroing r[k] had no effect on σ̂[k:] — update rule may be wrong"
        )

    def test_lambda_smoothing_effect(self):
        """Higher λ should produce smoother (less reactive) volatility estimates."""
        rng = np.random.default_rng(3)
        r = pd.Series(rng.normal(0, 0.01, 500))
        vols_high_lambda = ewma_volatility(r, lam=0.97)
        vols_low_lambda  = ewma_volatility(r, lam=0.80)
        # Smoothness proxy: standard deviation of the vol series itself
        assert vols_high_lambda.std() < vols_low_lambda.std(), (
            "Higher λ should produce smoother volatility estimates"
        )

    def test_seed_variance_used_as_initial_condition(self):
        """Passing a seed_variance should change the first estimate."""
        r = pd.Series([0.01] * 100)
        vols_default = ewma_volatility(r)
        vols_seeded  = ewma_volatility(r, seed_variance=0.0001)
        # First estimates will differ because of different initial σ²
        assert vols_default[0] != vols_seeded[0], (
            "seed_variance had no effect on the first EWMA estimate"
        )


class TestEwmaVar:
    def test_var_positive_dollar_amounts(self):
        """ewma_var should return positive values (charting convention)."""
        vols = np.array([0.01, 0.015, 0.012])
        var_series = ewma_var(vols, confidence=0.99, portfolio_value=1_000_000)
        assert np.all(var_series > 0), "ewma_var should return positive dollar amounts"

    def test_higher_confidence_gives_higher_var(self):
        """99% VaR should exceed 95% VaR in the EWMA series."""
        vols = np.array([0.01, 0.02, 0.015])
        var_95 = ewma_var(vols, confidence=0.95)
        var_99 = ewma_var(vols, confidence=0.99)
        assert np.all(var_99 >= var_95), (
            "99% EWMA VaR should be >= 95% EWMA VaR at every point"
        )
