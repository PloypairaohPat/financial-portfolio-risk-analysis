"""
conftest.py — Shared pytest fixtures for the test suite.

All fixtures use fixed seeds and synthetic data so that tests are:
  * deterministic (no yfinance calls, no external I/O)
  * fast (synthetic series, not the full 5-year CSV)
  * independent of the data/ directory contents
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_normal_returns() -> pd.Series:
    """250 daily returns drawn from N(0.0005, 0.01²) — approximately normal."""
    rng = np.random.default_rng(0)
    r = rng.normal(loc=0.0005, scale=0.01, size=250)
    return pd.Series(r, name="returns")


@pytest.fixture
def synthetic_log_returns_df() -> pd.DataFrame:
    """Multi-asset log-return DataFrame with a known covariance structure.

    2 assets, 500 observations, drawn from a bivariate normal with
    a pre-specified covariance matrix so that Cholesky tests can use
    exact expected values.
    """
    rng = np.random.default_rng(1)
    n = 500
    cov = np.array([[0.0001, 0.00005], [0.00005, 0.0002]])
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n, 2))
    data = z @ L.T
    return pd.DataFrame(data, columns=["A", "B"])


@pytest.fixture
def equal_weights_2() -> np.ndarray:
    """Equal weights for a 2-asset portfolio."""
    return np.array([0.5, 0.5])
