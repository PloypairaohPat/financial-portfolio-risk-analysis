"""
optimization.py — Portfolio optimisation helpers.

Provides two approaches:

1. **Random sampling** (``efficient_frontier_random``): generates N random
   weight combinations and returns their return / volatility / Sharpe metrics.
   Used for plotting the efficient frontier scatter.

2. **Constrained SLSQP** (``max_sharpe_slsqp``, ``min_variance_slsqp``):
   uses ``scipy.optimize.minimize`` with equality (weights sum to 1) and
   inequality (each weight within [lb, ub]) constraints to find the true
   optimal portfolios.

Sign convention
---------------
Annualised return and volatility are returned as positive fractions
(e.g. 0.1671 = 16.71 %).  Sharpe ratio uses the RISK_FREE_RATE from
``data.py`` (4.5 % annualised).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize

from .data import RISK_FREE_RATE, TRADING_DAYS


# ---------------------------------------------------------------------------
# Random-sampling efficient frontier
# ---------------------------------------------------------------------------

def efficient_frontier_random(
    log_returns: pd.DataFrame,
    n_portfolios: int = 5_000,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate random portfolios for an efficient-frontier scatter plot.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns, shape (n_days, n_assets).
    n_portfolios : int
        Number of random weight combinations to sample.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Columns: ``weights`` (list), ``return``, ``volatility``, ``sharpe``.
        ``return`` and ``volatility`` are annualised fractions.
    """
    n_assets = log_returns.shape[1]
    cov_matrix = log_returns.cov() * TRADING_DAYS
    mean_returns = log_returns.mean() * TRADING_DAYS

    rng = np.random.default_rng(seed)
    records = []

    for _ in range(n_portfolios):
        # Dirichlet draw ensures weights are non-negative and sum to 1
        w = rng.dirichlet(np.ones(n_assets))
        p_ret = float(mean_returns.dot(w))
        p_vol = float(np.sqrt(w.T @ cov_matrix.values @ w))
        p_sharpe = (p_ret - RISK_FREE_RATE) / p_vol
        records.append({"weights": w.tolist(), "return": p_ret,
                         "volatility": p_vol, "sharpe": p_sharpe})

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# SLSQP-optimised portfolios
# ---------------------------------------------------------------------------

def _portfolio_metrics(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
) -> tuple[float, float, float]:
    """Return (annualised_return, annualised_volatility, sharpe_ratio)."""
    p_ret = float(mean_returns @ weights)
    p_vol = float(np.sqrt(weights.T @ cov_matrix @ weights))
    sharpe = (p_ret - RISK_FREE_RATE) / p_vol
    return p_ret, p_vol, sharpe


def max_sharpe_slsqp(
    log_returns: pd.DataFrame,
    weight_bounds: tuple[float, float] = (0.0, 1.0),
    initial_weights: np.ndarray | None = None,
) -> dict:
    """Find the maximum-Sharpe portfolio via SLSQP.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns, shape (n_days, n_assets).
    weight_bounds : (lb, ub)
        Per-asset weight lower and upper bounds.  Default (0.0, 1.0) is
        unconstrained (long-only).  Use (0.0, 0.25) for the 25 %-cap
        constrained version recommended in the risk report.
    initial_weights : array-like or None
        Starting point for the optimiser.  Defaults to equal weights.

    Returns
    -------
    dict
        Keys: ``weights`` (np.ndarray), ``return``, ``volatility``, ``sharpe``.
    """
    n = log_returns.shape[1]
    mean_returns = (log_returns.mean() * TRADING_DAYS).values
    cov_matrix = (log_returns.cov() * TRADING_DAYS).values

    w0 = initial_weights if initial_weights is not None else np.ones(n) / n

    def neg_sharpe(w: np.ndarray) -> float:
        _, _, sharpe = _portfolio_metrics(w, mean_returns, cov_matrix)
        return -sharpe

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bounds = [weight_bounds] * n

    result = optimize.minimize(
        neg_sharpe, w0, method="SLSQP",
        bounds=bounds, constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )

    w_opt = result.x
    p_ret, p_vol, sharpe = _portfolio_metrics(w_opt, mean_returns, cov_matrix)
    return {"weights": w_opt, "return": p_ret, "volatility": p_vol, "sharpe": sharpe}


def min_variance_slsqp(
    log_returns: pd.DataFrame,
    weight_bounds: tuple[float, float] = (0.0, 1.0),
    initial_weights: np.ndarray | None = None,
) -> dict:
    """Find the minimum-variance portfolio via SLSQP.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns, shape (n_days, n_assets).
    weight_bounds : (lb, ub)
        Per-asset weight lower and upper bounds.  Default (0.0, 1.0) is
        unconstrained (long-only).
    initial_weights : array-like or None
        Starting point for the optimiser.  Defaults to equal weights.

    Returns
    -------
    dict
        Keys: ``weights`` (np.ndarray), ``return``, ``volatility``, ``sharpe``.
    """
    n = log_returns.shape[1]
    mean_returns = (log_returns.mean() * TRADING_DAYS).values
    cov_matrix = (log_returns.cov() * TRADING_DAYS).values

    w0 = initial_weights if initial_weights is not None else np.ones(n) / n

    def portfolio_vol(w: np.ndarray) -> float:
        return float(np.sqrt(w.T @ cov_matrix @ w))

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bounds = [weight_bounds] * n

    result = optimize.minimize(
        portfolio_vol, w0, method="SLSQP",
        bounds=bounds, constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )

    w_opt = result.x
    p_ret, p_vol, sharpe = _portfolio_metrics(w_opt, mean_returns, cov_matrix)
    return {"weights": w_opt, "return": p_ret, "volatility": p_vol, "sharpe": sharpe}
