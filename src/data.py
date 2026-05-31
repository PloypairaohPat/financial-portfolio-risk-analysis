"""
data.py — Portfolio data loading helpers.

Reads the committed CSV files in ``data/`` so that all other modules and
test suites can access clean inputs without touching yfinance or Jupyter.

All functions return pandas objects.  The ``data/`` directory is resolved
relative to this file so that imports work regardless of the working
directory the caller uses.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TICKERS: list[str] = ["AAPL", "MSFT", "GOOGL", "JPM", "BRK-B", "GLD", "TLT", "SPY"]
TRADING_DAYS: int = 252
RISK_FREE_RATE: float = 0.045  # 4.5% annualised (10-year US Treasury, c.2024)


def load_prices() -> pd.DataFrame:
    """Return daily adjusted-close prices as a DataFrame (date index, ticker columns).

    Returns
    -------
    pd.DataFrame
        Shape (n_days, 8).  Index is a DatetimeIndex.
    """
    return pd.read_csv(_DATA_DIR / "prices.csv", index_col=0, parse_dates=True)


def load_log_returns() -> pd.DataFrame:
    """Return daily log returns as a DataFrame (date index, ticker columns).

    Log returns are pre-computed as ``ln(P_t / P_{t-1})``.

    Returns
    -------
    pd.DataFrame
        Shape (n_days, 8).  Index is a DatetimeIndex.
    """
    return pd.read_csv(_DATA_DIR / "log_returns.csv", index_col=0, parse_dates=True)


def load_portfolio_returns(
    weights: np.ndarray | None = None,
) -> pd.Series:
    """Return the equal-weight portfolio daily log-return series.

    Parameters
    ----------
    weights : array-like, optional
        Portfolio weights summing to 1.0.  When ``None`` (default) the
        committed ``portfolio_returns.csv`` (equal-weight 1/8 each) is
        returned directly.

    Returns
    -------
    pd.Series
        Daily log returns, DatetimeIndex.
    """
    if weights is None:
        return pd.read_csv(
            _DATA_DIR / "portfolio_returns.csv", index_col=0, parse_dates=True
        ).squeeze()

    log_returns = load_log_returns()
    w = np.asarray(weights, dtype=float)
    assert abs(w.sum() - 1.0) < 1e-6, "weights must sum to 1.0"
    return log_returns.dot(w)
