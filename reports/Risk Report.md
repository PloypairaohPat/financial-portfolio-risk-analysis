# Financial Portfolio Risk Analysis

![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Last commit](https://img.shields.io/github/last-commit/PloypairaohPat/financial-portfolio-risk-analysis)

Quantitative risk analysis system for an 8-asset multi-asset portfolio (US equities, long-duration treasuries, gold). Implements three Value-at-Risk methodologies — historical simulation, parametric (normal), and Monte Carlo with Cholesky decomposition — alongside SLSQP efficient-frontier optimization and Kupiec backtesting validation.

Built on 1,508 trading days of daily returns (2019–2024) spanning the COVID crash, the 2022 rate-hike bear market, and the 2023–24 bull recovery.

> **Read first:** [`reports/Risk Report.md`](reports/Risk%20Report.md) — the 2-page risk report written for a non-technical stakeholder, with concrete portfolio recommendations.
>
> **Run first:** [`notebooks/00_executive_summary.ipynb`](notebooks/00_executive_summary.ipynb) — loads cached data and reproduces every chart and headline number below in ~30 seconds.

## Quickstart

```bash
pip install -r requirements.txt && jupyter lab notebooks/00_executive_summary.ipynb
```

## Results at a glance

- **Equal-weight baseline:** 16.71% annualised return, 16.83% annualised volatility, Sharpe 0.725 against a 4.5% risk-free rate.
- **Fat tails are real, and quantified:** historical 99% VaR ($29,146) exceeds parametric 99% VaR ($24,000) by $5,146. Jarque–Bera p-value ≈ 0 with excess kurtosis +11.6 formally rejects Normality (notebook 03).
- **Model is statistically valid:** Kupiec proportion-of-failures backtest on a 252-day held-out window — 2 actual breaches against 2.5 expected, p-value 0.73 (notebook 06).
- **Concrete recommendation:** SLSQP max-Sharpe with a 25% per-asset cap improves Sharpe from 0.725 → 0.886 without concentrating into a single name. The unconstrained optimum (Sharpe 0.970) loads 90% into AAPL + GLD and is rejected as brittle.

![Cumulative growth of $1 invested 2019–2024](reports/figures/cumulative_growth.png)

## Key Findings

Equal-weight baseline portfolio, $1,000,000 notional:

| Metric | Value |
| --- | ---: |
| Annualised return | 16.71% |
| Annualised volatility | 16.83% |
| Sharpe ratio (risk-free = 4.5%) | 0.725 |
| 99% Historical VaR (1-day) | $29,146 |
| 99% Parametric VaR (1-day) | $24,000 |
| 99% Monte Carlo VaR (1-day, 10k paths, seed 42) | $24,017 |
| 99% Historical CVaR / Expected Shortfall | $43,829 |
| 99% Monte Carlo CVaR | $27,734 |
| Historical − parametric VaR gap | $5,146 |

**Fat-tail evidence.** The $5,146 gap between historical and parametric 99% VaR is direct evidence that daily returns have fatter tails than the Normal distribution predicts. The diagnostic in notebook 03 confirms this formally: sample skewness −0.54, excess kurtosis +11.6, Jarque–Bera p-value ≈ 0. The Normal-distribution assumption systematically under-states tail risk.

![Daily return distribution with 99% VaR thresholds](reports/figures/return_distribution_var.png)

**Backtesting result.** On a held-out 2024 test window (252 trading days), the parametric 99% VaR model was well-calibrated: 2 actual breaches against 2.5 expected, Kupiec likelihood-ratio p-value = 0.73 (not rejected). The historical model over-estimated risk in 2024 — a regime-effect artifact of the training window (2019–2023) including the COVID and 2022 rate-shock periods, rather than a model-correctness failure.

**Optimization result.** SLSQP mean-variance optimization identifies a maximum-Sharpe allocation reaching 0.970 (vs 0.725 equal-weight), though the unconstrained optimum concentrates 90% of weight in AAPL and GLD. Adding a 25% per-asset cap as a practical constraint produces a diversified allocation across six assets with Sharpe 0.886 — a small in-sample Sharpe cost (8 basis points) for a far more robust real-world portfolio. A 70/30 blended tilt of equal-weight toward the unconstrained optimum raises Sharpe to 0.823 while preserving diversification across all eight assets and holding 99% VaR essentially flat — the recommendation made in `reports/Risk Report.md`.

![Efficient frontier with SLSQP-optimised portfolios](reports/figures/efficient_frontier.png)

**Regime structure of correlations.** A static covariance matrix — the foundation of parametric VaR — assumes asset correlations are constant. They are not. The SPY-TLT pair (the classic "bonds hedge stocks" relationship) is reliably negative through 2019–2021, then flips positive in 2022 as aggressive rate hikes hurt both equities and long-duration treasuries simultaneously. This is the structural explanation for why parametric VaR misses tail risk during regime shifts.

![Rolling 30-day correlation, selected pairs](reports/figures/rolling_correlation.png)

## Methodology

| Method | Description |
| --- | --- |
| **Historical VaR** | Empirical percentiles of the realised return distribution. No distributional assumptions. |
| **Parametric VaR** | Closed-form Normal: μ + Φ⁻¹(α)·σ via `scipy.stats.norm.ppf` (robust to any confidence level). |
| **Monte Carlo VaR** | 10,000 paths sampled from a multivariate Normal with cross-asset correlations preserved via Cholesky decomposition. Convergence verified at 1k / 5k / 10k / 25k / 50k paths. |
| **Efficient Frontier** | 5,000 Dirichlet-random portfolios for visualization; `scipy.optimize` SLSQP with sum-to-one and non-negativity constraints for clean min-variance and max-Sharpe solutions; box-constrained variant (≤ 25% per asset) for the practical recommendation. |
| **CVaR / Expected Shortfall** | Mean of returns exceeding the VaR threshold — the regulatory-preferred measure under Basel III. Closed-form under Normality: μ − σ·φ(z)/α. |
| **Normality diagnostic** | Q-Q plot against the Normal distribution + Jarque–Bera test on skewness and excess kurtosis. |
| **Kupiec POF test** | Likelihood-ratio test of observed vs expected breach frequency on a held-out 252-day window. |

## Portfolio Composition

| Ticker | Asset | Role |
| --- | --- | --- |
| AAPL | Apple | Large-cap tech growth |
| MSFT | Microsoft | Large-cap tech growth |
| GOOGL | Alphabet | Tech / advertising |
| JPM | JPMorgan Chase | Financials |
| BRK-B | Berkshire Hathaway | Value conglomerate |
| GLD | SPDR Gold Trust | Commodity (gold) |
| TLT | iShares 20+ Year Treasury | Long-duration fixed income |
| SPY | SPDR S&P 500 | Equity market benchmark |

## Repository Structure

```
financial-portfolio-risk-analysis/
├── README.md                            # This file
├── LICENSE                              # MIT
├── requirements.txt                     # Pinned Python dependencies
├── .gitignore
├── notebooks/
│   ├── 00_executive_summary.ipynb       # Hero notebook — open this first
│   ├── 01_data_ingestion.ipynb          # Download 2019-2024 prices via yfinance
│   ├── 02_portfolio_metrics.ipynb       # Log returns, covariance, rolling correlations
│   ├── 03_var_analysis.ipynb            # Historical and parametric VaR + Q-Q + Jarque-Bera + regime slice
│   ├── 04_monte_carlo.ipynb             # 10,000-path MC via Cholesky + convergence check
│   ├── 05_efficient_frontier.ipynb      # 5,000 random portfolios + SLSQP min-var, max-Sharpe, 25%-cap
│   └── 06_backtesting.ipynb             # Kupiec POF test on held-out 2024
├── data/                                # Cached for offline reproduction; safe to delete to refresh
│   ├── prices.csv                       # Adjusted close prices
│   ├── log_returns.csv                  # Daily log returns per asset
│   └── portfolio_returns.csv            # Equal-weight portfolio return series
└── reports/
    ├── Risk Report.md                   # Executive summary & recommendation (non-technical)
    └── figures/                         # Hero charts referenced above
```

The CSVs in `data/` are committed so the analysis is fully reproducible offline. To refresh from yfinance, delete `data/prices.csv` and re-run `01_data_ingestion.ipynb` — the other CSVs are regenerated downstream.

## Running the Analysis

Tested on Python 3.11+.

```bash
# Clone and set up
git clone https://github.com/PloypairaohPat/financial-portfolio-risk-analysis.git
cd financial-portfolio-risk-analysis

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

# Install pinned dependencies
pip install -r requirements.txt

# Run the executive-summary hero notebook
jupyter lab notebooks/00_executive_summary.ipynb
```

The numbered notebooks 01–06 step through the analysis in detail. They expect cached CSVs in `data/`, which are already committed; deleting `data/prices.csv` triggers a fresh yfinance download on the next run of `01_data_ingestion.ipynb`.

## Skills demonstrated

Time-series analysis · probability & statistics · Monte Carlo simulation · constrained optimization (SLSQP) · statistical hypothesis testing (Jarque–Bera, Kupiec POF) · financial risk modeling · reproducible scientific computing.

## Tech Stack

- **Python** 3.11+
- **NumPy**, **pandas** — data manipulation
- **SciPy** — statistical testing, constrained optimization
- **Matplotlib** — visualization
- **yfinance** — market data ingestion
- **Jupyter** — notebook environment

## Limitations & Caveats

- All methods calibrated on 2019–2024 — regime-dependent and not guaranteed to generalise.
- Parametric and Monte Carlo VaR both rest on the Normal assumption; the historical–parametric gap and Jarque–Bera test quantify the error.
- Covariance matrix is treated as static despite rolling-correlation evidence of regime changes (see `02_portfolio_metrics.ipynb` and the chart above). The 2022 SPY-TLT correlation flip is exactly the kind of structural break a static matrix misses.
- 1-day VaR horizon only; scaling to longer horizons via √t assumes IID returns — which the fat-tail finding above contradicts.
- No transaction costs, liquidity constraints, or position-size caps imposed in the optimization beyond the 25% per-asset box constraint.

## License

MIT — see [LICENSE](LICENSE).