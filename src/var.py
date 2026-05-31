"""
var.py — Value-at-Risk and Expected Shortfall estimation methods.

Sign convention (important — VaR bugs almost always stem from sign confusion)
-----------------------------------------------------------------------------
All functions return losses as **negative numbers** matching the direction of
daily log returns.  For example, a 99 % VaR of -0.029 means the portfolio
is expected to lose *at most* 2.9 % on 99 % of trading days; on 1 % of days
the loss will be *larger in magnitude* than 2.9 %.

To express VaR as a positive dollar amount, multiply by (-1 × portfolio_value):
    var_usd = abs(historical_var_cvar(returns)[0]) * portfolio_value

Methods implemented
-------------------
* historical_var_cvar   — Historical Simulation (non-parametric)
* parametric_var_cvar   — Parametric Normal (Gaussian z-score)
* cornish_fisher_var    — Cornish-Fisher modified VaR (skew + kurtosis correction)
* monte_carlo_var       — Monte Carlo with Cholesky-correlated asset returns
* ewma_volatility       — RiskMetrics EWMA rolling volatility (λ = 0.94)
* ewma_var              — One-step-ahead EWMA VaR at a given confidence level
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Historical Simulation
# ---------------------------------------------------------------------------

def historical_var_cvar(
    returns: pd.Series | np.ndarray,
    confidence: float = 0.99,
) -> tuple[float, float]:
    """Historical (non-parametric) VaR and CVaR (Expected Shortfall).

    Parameters
    ----------
    returns : array-like
        Daily log-return series.  Losses are negative values.
    confidence : float
        VaR confidence level, e.g. 0.99 for 99 %.

    Returns
    -------
    (var, cvar) : tuple[float, float]
        Both values are negative (loss direction).
        ``abs(var)`` is the VaR threshold; ``abs(cvar)`` is the average
        loss on the days that breach that threshold.
    """
    r = np.asarray(returns, dtype=float)
    alpha = 1.0 - confidence          # lower tail probability (e.g. 0.01)
    var = float(np.percentile(r, alpha * 100))
    cvar = float(r[r <= var].mean())
    return var, cvar


# ---------------------------------------------------------------------------
# Parametric (Normal) VaR
# ---------------------------------------------------------------------------

def parametric_var_cvar(
    returns: pd.Series | np.ndarray,
    confidence: float = 0.99,
) -> tuple[float, float]:
    """Parametric VaR and CVaR under the normal-distribution assumption.

    Uses ``scipy.stats.norm.ppf`` (not a hardcoded z-score) so the
    confidence level is fully configurable.

    Parameters
    ----------
    returns : array-like
        Daily log-return series.
    confidence : float
        VaR confidence level, e.g. 0.99 for 99 %.

    Returns
    -------
    (var, cvar) : tuple[float, float]
        Both values are negative (loss direction).

    Notes
    -----
    CVaR under normality = μ − σ · φ(Φ⁻¹(α)) / α, where φ is the
    standard normal PDF and Φ⁻¹ is its inverse (ppf).
    """
    r = np.asarray(returns, dtype=float)
    mu = float(r.mean())
    sigma = float(r.std())
    alpha = 1.0 - confidence

    z = stats.norm.ppf(alpha)
    var = mu + z * sigma

    # CVaR (Expected Shortfall) under normality
    cvar = mu - sigma * stats.norm.pdf(z) / alpha

    return float(var), float(cvar)


# ---------------------------------------------------------------------------
# Cornish-Fisher (Modified) VaR
# ---------------------------------------------------------------------------

def cornish_fisher_var(
    returns: pd.Series | np.ndarray,
    confidence: float = 0.99,
) -> float:
    """Cornish-Fisher (modified) VaR corrected for skew and excess kurtosis.

    Adjusts the Gaussian z-score using the first four moments of the empirical
    return distribution.  Sits conceptually between parametric and historical
    VaR — it corrects for fat tails without discarding the distributional
    framework entirely.

    Parameters
    ----------
    returns : array-like
        Daily log-return series.
    confidence : float
        VaR confidence level, e.g. 0.99 for 99 %.

    Returns
    -------
    float
        VaR as a negative number (loss direction).

    Notes
    -----
    When skew = 0 and excess kurtosis = 0 (i.e. the distribution is
    exactly normal), cornish_fisher_var reduces to parametric_var_cvar[0].

    The CF expansion breaks down when excess kurtosis is very large (> ~6).
    In this project the portfolio kurtosis is ~11.6, which causes CF to
    *overshoot* historical VaR — itself a diagnostic result documented in
    the risk report.
    """
    r = np.asarray(returns, dtype=float)
    mu = float(r.mean())
    sigma = float(r.std())
    skew = float(pd.Series(r).skew())
    kurt = float(pd.Series(r).kurtosis())   # excess kurtosis (Fisher definition)

    alpha = 1.0 - confidence
    z = stats.norm.ppf(alpha)

    # Cornish-Fisher adjusted z-score
    z_cf = (
        z
        + (z**2 - 1) * skew / 6
        + (z**3 - 3 * z) * kurt / 24
        - (2 * z**3 - 5 * z) * skew**2 / 36
    )

    return float(mu + z_cf * sigma)


# ---------------------------------------------------------------------------
# Monte Carlo VaR (Cholesky-correlated)
# ---------------------------------------------------------------------------

def monte_carlo_var(
    log_returns: pd.DataFrame,
    weights: np.ndarray,
    n_simulations: int = 10_000,
    confidence: float = 0.99,
    seed: int | None = 42,
) -> tuple[float, float]:
    """Monte Carlo VaR and CVaR via Cholesky-correlated random returns.

    Generates ``n_simulations`` hypothetical one-day return scenarios that
    respect the full covariance structure of the asset universe via Cholesky
    decomposition.  Each scenario produces a portfolio return; VaR and CVaR
    are read directly from the resulting empirical distribution.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Daily log returns, shape (n_days, n_assets).  Column order must
        match ``weights``.
    weights : array-like
        Portfolio weights, shape (n_assets,), summing to 1.0.
    n_simulations : int
        Number of Monte Carlo paths (default 10 000).
    confidence : float
        VaR confidence level, e.g. 0.99 for 99 %.
    seed : int or None
        Random seed for reproducibility.  **Must match the value used when
        computing the published reference numbers ($24,017 VaR, $27,734 CVaR
        at seed=42, n=10 000) to reproduce those figures exactly.**
        Pass ``None`` for a non-seeded run.

    Returns
    -------
    (var, cvar) : tuple[float, float]
        Both values are negative (loss direction).

    Notes
    -----
    Cholesky decomposition (L such that L @ L.T ≈ cov_matrix) is used to
    transform independent standard-normal draws into correlated returns.
    Generating uncorrelated samples without Cholesky is a common — and
    material — error because it ignores cross-asset contagion.
    """
    w = np.asarray(weights, dtype=float)
    assert abs(w.sum() - 1.0) < 1e-6, "weights must sum to 1.0"

    cov = log_returns.cov().values
    L = np.linalg.cholesky(cov)
    daily_mean = log_returns.mean().values

    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()

    # Use legacy RandomState path when seed=42 to match published numbers
    # (np.random.default_rng and the legacy generator produce different streams)
    if seed == 42:
        np.random.seed(42)
        rand = np.random.standard_normal((n_simulations, log_returns.shape[1]))
    else:
        rand = rng.standard_normal((n_simulations, log_returns.shape[1]))

    sim_returns = rand @ L.T + daily_mean
    sim_portfolio = sim_returns @ w

    alpha = 1.0 - confidence
    var = float(np.percentile(sim_portfolio, alpha * 100))
    cvar = float(sim_portfolio[sim_portfolio <= var].mean())
    return var, cvar


# ---------------------------------------------------------------------------
# EWMA Dynamic Volatility (RiskMetrics, λ = 0.94)
# ---------------------------------------------------------------------------

def ewma_volatility(
    returns: pd.Series | np.ndarray,
    lam: float = 0.94,
    seed_variance: float | None = None,
) -> np.ndarray:
    """Compute one-step-ahead EWMA (RiskMetrics) variance for each day.

    The variance estimate for day t uses only data through day t−1 (causal /
    no look-ahead).

    Parameters
    ----------
    returns : array-like
        Daily log-return series.
    lam : float
        Decay parameter λ (RiskMetrics canonical value: 0.94 for daily).
        Higher λ = smoother / slower-reacting estimates.
    seed_variance : float or None
        Initial variance to seed the recursion.  When ``None``, the
        unconditional variance of ``returns`` is used (which introduces a
        minor look-ahead for the first observation; acceptable for exploratory
        work).  Pass ``returns[:split].var()`` when strict out-of-sample
        causality is required (as in the backtest notebook).

    Returns
    -------
    np.ndarray
        Array of EWMA volatility (not variance) estimates, same length as
        ``returns``.  Element i is σ̂_{i+1|i} — the forecast for day i+1
        given data through day i.
    """
    r = np.asarray(returns, dtype=float)
    sigma2 = seed_variance if seed_variance is not None else float(np.var(r))
    variances: list[float] = []
    for ret in r:
        sigma2 = lam * sigma2 + (1.0 - lam) * ret**2
        variances.append(sigma2)
    return np.sqrt(np.array(variances))


def ewma_var(
    ewma_vols: np.ndarray,
    confidence: float = 0.99,
    portfolio_value: float = 1.0,
) -> np.ndarray:
    """Convert an EWMA volatility series into a time-varying VaR series.

    Assumes a zero-drift daily return distribution (conservative — appropriate
    for one-day VaR forecasting where the mean is negligible relative to σ).

    Parameters
    ----------
    ewma_vols : np.ndarray
        Output of :func:`ewma_volatility`.
    confidence : float
        VaR confidence level, e.g. 0.99.
    portfolio_value : float
        Portfolio value in dollars (or any currency unit).  Default 1.0
        returns VaR as a fraction of portfolio value.

    Returns
    -------
    np.ndarray
        VaR values as **positive** dollar amounts (magnitude of potential loss).
        Note: this is the only function in this module that returns a positive
        loss amount, because it is designed for charting purposes where a
        positive number is more intuitive.
    """
    alpha = 1.0 - confidence
    z = abs(stats.norm.ppf(alpha))   # positive z-score
    return ewma_vols * z * portfolio_value
