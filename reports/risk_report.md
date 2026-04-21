# Portfolio Risk Analysis

**Portfolio:** Equal-weighted 8-asset basket — AAPL, MSFT, GOOGL, JPM, BRK-B, GLD, TLT, SPY
**Period analysed:** Jan 2019 – Dec 2024 (1,508 trading days)
**Portfolio value (assumed):** $1,000,000
**Author:** [YOUR NAME] | **Date:** [DATE]

---

## Executive Summary

Over the 2019–2024 period this equal-weighted portfolio of four US equities, a value conglomerate, gold, long-duration treasuries, and the S&P 500 delivered [FILL IN annualized return]% annualized return at [FILL IN annualized vol]% annualized volatility, yielding a Sharpe ratio of [FILL IN] against a 4.5% risk-free rate.

**The headline risk figure: 1-day 99% Value-at-Risk is $29,146 under the historical method and $23,996 under the parametric (normal) method on a $1M portfolio.** The $5,150 gap is direct evidence of fat-tail behaviour in the return distribution — real tail losses arrive more often and run deeper than a normal distribution predicts. On the 1% worst days, expected shortfall (CVaR) averages $43,829 — roughly 50% larger than the VaR threshold alone.

Backtesting on the held-out 2024 period shows the parametric 99% VaR was well-calibrated (2 actual breaches vs 2.5 expected, Kupiec p = 0.73, not rejected). The historical model, however, was too conservative in 2024 (0 breaches against 2.5 expected) — a recent-regime artifact rather than a model failure.

**Recommendation: [FILL IN once you've read the efficient-frontier output — e.g. "shift weight from AAPL/MSFT toward GLD and TLT; specific weights below reduce 99% VaR by X% while improving Sharpe from 0.Y to 0.Z."]**

---

## 1. Portfolio Composition

| Ticker | Asset | Role | Weight |
| --- | --- | --- | --- |
| AAPL | Apple | Large-cap tech growth | 12.5% |
| MSFT | Microsoft | Large-cap tech growth | 12.5% |
| GOOGL | Alphabet | Tech / advertising | 12.5% |
| JPM | JPMorgan Chase | Financials | 12.5% |
| BRK-B | Berkshire Hathaway | Value conglomerate | 12.5% |
| GLD | SPDR Gold Trust | Commodity (gold) | 12.5% |
| TLT | iShares 20+ Year Treasury | Long-duration bonds | 12.5% |
| SPY | SPDR S&P 500 | Equity market benchmark | 12.5% |

The portfolio was deliberately constructed to include three asset classes — equities, bonds, gold — to observe diversification effects.

*[INSERT: cumulative-growth chart of the 8 assets here]*

---

## 2. Return & Volatility Profile

| Metric | Value |
| --- | --- |
| Annualized return | [FILL IN]% |
| Annualized volatility | [FILL IN]% |
| Sharpe ratio (rf = 4.5%) | [FILL IN] |

The rolling 30-day correlation analysis reveals that cross-asset correlations are not static. SPY-TLT correlation, typically negative (the "bonds hedge equities" regime), flipped positive through much of 2022 as aggressive rate hikes hurt both asset classes simultaneously. SPY-GLD swings between roughly −0.68 and +0.70 across the period. **This is the most important caveat attaching to the parametric VaR results below** — the parametric model assumes a fixed covariance matrix that cannot capture these regime shifts.

*[INSERT: rolling 30-day correlation chart from portfolio_metrics.ipynb]*

---

## 3. Value-at-Risk — Three Methods Compared

All figures below assume a $1,000,000 portfolio; multiply the return figure by portfolio value to dollar-ize. 1-day horizon.

| Method | 95% VaR | 99% VaR | 99% CVaR |
| --- | --- | --- | --- |
| Historical simulation | [FILL IN] | **$29,146** | **$43,829** |
| Parametric (normal) | [FILL IN] | **$23,996** | [FILL IN] |
| Monte Carlo (10,000 paths, Cholesky) | [FILL IN] | [FILL IN from MonteCarlo.ipynb] | [FILL IN] |

**Key observation — the historical-parametric gap.** Historical 99% VaR exceeds parametric 99% VaR by $5,150. Under a strict normal-distribution assumption, this gap should not exist. It does exist because real daily returns have fatter tails than the normal distribution — extreme losses occur more often and run deeper than the bell-curve predicts. The March 2020 COVID crash is the most visible instance of this in the 2019–2024 window.

**Monte Carlo vs parametric agreement.** The MC VaR should land very close to the parametric VaR, because both draw from a multivariate normal distribution — MC just does it via simulation rather than closed form. If they disagree by more than sampling noise (~$500 on 10,000 paths), investigate.

*[INSERT: return-distribution histogram with VaR lines drawn at 95% and 99%]*

---

## 4. Backtesting — Kupiec Proportion-of-Failures Test

Training window: Jan 2019 – Dec 2023 (1,256 days). Test window: Jan–Dec 2024 (252 days). VaR was re-estimated using only training data; breaches were counted on the held-out test year.

| Confidence | Method | Expected breaches | Actual breaches | Kupiec p-value | Verdict |
| --- | --- | --- | --- | --- | --- |
| 95% | Historical | 12.6 | 6 | 0.034 | Rejected (over-conservative) |
| 95% | Parametric | 12.6 | 5 | 0.013 | Rejected (over-conservative) |
| 99% | Historical | 2.5 | 0 | 0.024 | Rejected (over-conservative) |
| 99% | Parametric | 2.5 | 2 | 0.733 | **Not rejected** |

**Interpretation.** The parametric 99% VaR was statistically well-calibrated on the 2024 hold-out — the model expected ~2.5 breaches, observed 2, and the Kupiec test cannot reject the null that the model is correctly calibrated. All three rejections are in the over-conservative direction — fewer breaches than expected, meaning the model over-estimated risk in 2024 rather than under-estimating it. This is a meaningfully different failure mode from an under-estimating model: an over-conservative VaR ties up excess risk capital but does not expose the firm to unexpected losses.

The most likely cause of the over-conservatism is that the training window (2019–2023) includes the high-volatility COVID and 2022 rate-shock periods, whereas 2024 was a comparatively calm year. A risk model trained on volatile history will over-state risk in calm regimes and vice versa. A production system would address this with a rolling-window or volatility-scaled re-estimation; this is outside the scope of this report but is called out as the natural next step.

*[INSERT: test-period return plot with VaR thresholds and breach days highlighted]*

---

## 5. Efficient Frontier & Optimization

5,000 random portfolio weightings were simulated using Dirichlet-distributed weights summing to 1, plotting annualized return against annualized volatility coloured by Sharpe ratio.

| Portfolio | Return | Volatility | Sharpe |
| --- | --- | --- | --- |
| Equal-weight (current) | [FILL IN] | [FILL IN] | [FILL IN] |
| Minimum variance | [FILL IN] | [FILL IN] | [FILL IN] |
| Maximum Sharpe | [FILL IN] | [FILL IN] | [FILL IN] |

**Maximum Sharpe weights:**

| Ticker | Current | Max Sharpe | Change |
| --- | --- | --- | --- |
| AAPL | 12.5% | [FILL IN] | [FILL IN] |
| MSFT | 12.5% | [FILL IN] | [FILL IN] |
| GOOGL | 12.5% | [FILL IN] | [FILL IN] |
| JPM | 12.5% | [FILL IN] | [FILL IN] |
| BRK-B | 12.5% | [FILL IN] | [FILL IN] |
| GLD | 12.5% | [FILL IN] | [FILL IN] |
| TLT | 12.5% | [FILL IN] | [FILL IN] |
| SPY | 12.5% | [FILL IN] | [FILL IN] |

*[INSERT: efficient frontier scatter with max-Sharpe, min-variance, and equal-weight points marked]*

---

## 6. Recommendation

[TO WRITE AFTER READING YOUR EFFICIENT-FRONTIER OUTPUT. Template for the sentence:]

> Reallocating from equal-weight toward the maximum-Sharpe composition — principally [LIST TWO OR THREE WEIGHT SHIFTS, e.g. "reducing AAPL from 12.5% to 8% and increasing GLD allocation to 18%"] — reduces 99% VaR by [X]% while improving the Sharpe ratio from [CURRENT] to [NEW]. The associated expected-return change is [+/- Y%], which the risk reduction more than compensates for on a risk-adjusted basis.

Constraints a production implementation would impose on top of this: position-size caps per name, sector caps, minimum liquidity thresholds, and rebalancing costs — none of which are modelled here.

---

## 7. Limitations

1. **Historical window dependence.** All three VaR methods are calibrated on 2019–2024. If the future regime differs materially from this window, estimates will be off. The backtest directly shows this: a model trained on volatile history over-estimated risk in the calmer 2024 test year.
2. **Normal-distribution assumption in parametric and Monte Carlo.** Both methods assume returns are multivariate normal. The historical-vs-parametric gap of $5,150 at 99% is direct evidence this assumption understates tail risk. A production model would use a Student-t distribution or a historical-simulation bootstrap for Monte Carlo.
3. **Static covariance.** The rolling-correlation analysis in Section 2 shows correlations are not stable. Parametric and Monte Carlo VaR both use a single full-period covariance matrix, which misses regime-dependent correlation breakdowns — exactly the environments where diversification matters most.
4. **1-day horizon only.** Regulatory VaR is often computed at 10-day or longer horizons. Scaling 1-day VaR by √10 assumes IID returns, which is roughly — but not exactly — true in practice.
5. **No liquidity or transaction-cost modelling.** The efficient-frontier recommendation implicitly assumes frictionless rebalancing.
