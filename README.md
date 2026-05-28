# Financial Portfolio Risk Analysis

Quantitative risk analysis system for an 8-asset multi-asset portfolio (US equities, long-duration treasuries, gold). Implements three Value-at-Risk methodologies — historical simulation, parametric (normal), and Monte Carlo with Cholesky decomposition — alongside efficient frontier optimization and Kupiec backtesting validation.

Built on 1,508 trading days of daily returns (2019–2024) spanning the COVID crash, the 2022 rate-hike bear market, and the 2023–24 bull recovery.

## Key Findings

Equal-weight baseline portfolio, $1,000,000 notional:

| Metric | Value |
| --- | ---: |
| Annualized return | 16.71% |
| Annualized volatility | 16.83% |
| Sharpe ratio (risk-free = 4.5%) | 0.725 |
| 99% Historical VaR (1-day) | $29,146 |
| 99% Parametric VaR (1-day) | $23,996 |
| 99% CVaR / Expected Shortfall | $43,829 |
| Historical − parametric VaR gap | $5,150 |

**Fat-tail evidence.** The $5,150 gap between historical and parametric 99% VaR is direct evidence that daily returns have fatter tails than the normal distribution predicts — the normal-distribution assumption systematically under-states tail risk.

**Backtesting result.** On a held-out 2024 test window (252 trading days), the parametric 99% VaR model was well-calibrated: 2 actual breaches against 2.5 expected, Kupiec likelihood-ratio p-value = 0.73 (not rejected). The historical model over-estimated risk in 2024 — a regime-effect artifact of the training window (2019–2023) including the COVID and 2022 rate-shock periods, rather than a model-correctness failure.

**Optimization result.** Mean-variance optimization identifies a maximum-Sharpe allocation reaching 0.970 (vs 0.725 equal-weight), though the unconstrained optimum concentrates 90% of weight in AAPL and GLD. A 70/30 blended tilt toward the optimum raises Sharpe to 0.823 while preserving diversification across all eight assets and holding 99% VaR essentially flat.

## Methodology

| Method | Description |
| --- | --- |
| **Historical VaR** | Empirical percentiles of the realized return distribution. No distributional assumptions. |
| **Parametric VaR** | Closed-form via the normal distribution: μ + z·σ, with z = −2.326 for 99% confidence. |
| **Monte Carlo VaR** | 10,000 paths sampled from a multivariate normal with cross-asset correlations preserved via Cholesky decomposition of the covariance matrix. |
| **Efficient Frontier** | 5,000 Dirichlet-random portfolios for visualization; `scipy.optimize` SLSQP with sum-to-one and non-negativity constraints for clean min-variance and max-Sharpe points. |
| **CVaR / Expected Shortfall** | Mean of returns exceeding the VaR threshold — the regulatory-preferred measure under Basel III. |
| **Kupiec POF Test** | Likelihood-ratio test of observed vs expected breach frequency on a held-out 252-day window. |

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
├── README.md                         # This file
├── LICENSE                           # MIT
├── requirements.txt                  # Python dependencies
├── .gitignore
├── notebooks/
│   ├── 01_data_ingestion.ipynb       # Download 2019–2024 prices via yfinance
│   ├── 02_portfolio_metrics.ipynb    # Log returns, covariance, rolling correlations
│   ├── 03_var_analysis.ipynb         # Historical and parametric VaR / CVaR
│   ├── 04_monte_carlo.ipynb          # 10,000-path MC simulation via Cholesky
│   ├── 05_efficient_frontier.ipynb   # 5,000 random portfolios, min-var & max-Sharpe
│   └── 06_backtesting.ipynb          # Kupiec POF test on held-out 2024
├── data/
│   ├── prices.csv                    # Adjusted close prices
│   ├── log_returns.csv               # Daily log returns per asset
│   └── portfolio_returns.csv         # Equal-weight portfolio return series
└── reports/
    └── risk_report.md                # Executive summary & recommendation
```

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

# Install dependencies
pip install -r requirements.txt

# Run notebooks in order
jupyter lab notebooks/
```

Notebooks must be run in numeric order the first time — `01_data_ingestion` produces `data/prices.csv`, which downstream notebooks consume.

## Tech Stack

- **Python** 3.11+
- **NumPy**, **pandas** — data manipulation
- **SciPy** — statistical testing, constrained optimization
- **Matplotlib** — visualization
- **yfinance** — market data ingestion
- **Jupyter** — notebook environment

## Limitations & Caveats

- All methods calibrated on 2019–2024 — regime-dependent and not guaranteed to generalize.
- Parametric and Monte Carlo VaR assume multivariate-normal returns; the historical–parametric gap quantifies the error.
- Covariance matrix is treated as static despite rolling-correlation evidence of regime changes (see `02_portfolio_metrics.ipynb`).
- 1-day VaR horizon only; scaling to longer horizons assumes IID returns.
- No transaction costs, liquidity constraints, or position-size caps in the optimization.

## License

MIT — see [LICENSE](LICENSE).