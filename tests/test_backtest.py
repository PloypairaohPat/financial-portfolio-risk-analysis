"""
test_backtest.py — Tests for src/backtest.py (Kupiec POF test).
"""

import numpy as np
import pandas as pd
import pytest

from src.backtest import kupiec_pof


class TestKupiecPof:
    def test_zero_breaches_no_crash(self):
        """Zero breaches should not raise a log(0) error; p-value = 1.0."""
        # All returns well above the VaR threshold → zero breaches
        returns = pd.Series([0.01] * 252)   # positive returns every day
        var_threshold = -0.05               # very conservative threshold
        result = kupiec_pof(returns, var_threshold, confidence=0.99)
        assert result["breaches"] == 0
        assert result["p_value"] == 1.0
        assert result["verdict"] == "PASS"

    def test_expected_breach_count_correct(self):
        """With n=252 and confidence=0.99, expected breaches = 2.52."""
        returns = pd.Series([0.01] * 252)
        result = kupiec_pof(returns, var_threshold=-0.05, confidence=0.99)
        assert abs(result["expected"] - 2.52) < 1e-9

    def test_exact_model_breach_rate_gives_lr_zero(self):
        """If breaches / n == p_model exactly, LR statistic = 0 and p-value = 1."""
        n = 100
        p_model = 0.01
        n_breaches = int(n * p_model)  # exactly 1 breach for n=100, p=0.01
        # Build a series with exactly n_breaches below threshold
        returns = np.concatenate([
            np.full(n_breaches, -0.10),    # below threshold
            np.full(n - n_breaches, 0.01), # above threshold
        ])
        result = kupiec_pof(pd.Series(returns), var_threshold=-0.05, confidence=0.99)
        # LR = 0 when p_actual == p_model → chi2.cdf(0, 1) = 0 → p_value = 1
        assert abs(result["lr_statistic"]) < 1e-9
        assert abs(result["p_value"] - 1.0) < 1e-9

    def test_high_breach_rate_rejected(self):
        """A breach rate far above expected should give a low p-value (model rejected)."""
        n = 252
        # 20% breach rate vs 1% expected — should be strongly rejected
        n_breaches = 50
        returns = np.concatenate([
            np.full(n_breaches, -0.10),
            np.full(n - n_breaches, 0.01),
        ])
        result = kupiec_pof(pd.Series(returns), var_threshold=-0.05, confidence=0.99)
        assert result["p_value"] < 0.05
        assert result["verdict"] == "FAIL"

    def test_result_keys_present(self):
        """Output dict must have all documented keys."""
        returns = pd.Series([0.01] * 252)
        result = kupiec_pof(returns, -0.05, confidence=0.99)
        for key in ["n", "breaches", "expected", "p_actual", "p_model",
                    "lr_statistic", "p_value", "verdict"]:
            assert key in result, f"Missing key '{key}' in kupiec_pof output"
