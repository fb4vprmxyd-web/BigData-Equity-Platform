# CW2 — Value-Sentiment Investment Strategy

## UCL Institute of Finance & Technology
**IFTE0003: Big Data in Quantitative Finance**  
**Team 09 — Coursework 2**

---

## Strategy Overview

A systematic long-only equity strategy combining **sector-relative value scoring** with **quality-weighted sentiment analysis** to construct a diversified portfolio that captures the value premium while avoiding value traps.

**Key innovations over CW1:**
- **Sector-relative value scoring**: MSCI Enhanced Value 4-stage pipeline replaces cross-sectional percentile ranking, eliminating unintended sector bets (Ehsani, Harvey & Li, 2023)
- **Quality-weighted sentiment**: 4-component quality weighting (source credibility × relevance × recency × substantiveness) replaces volume-weighted aggregation (Tetlock, 2011)
- **Bayesian shrinkage**: Applied to both value scores (small sectors) and sentiment scores (low article coverage) to reduce estimation noise

**Composite formula:** `Score = 0.6 × Value_percentile + 0.4 × Sentiment_normalised`

---

## Architecture

```
coursework_two/
├── config/
│   └── backtest_config.yaml          # ALL tuneable parameters
├── modules/
│   ├── data/
│   │   ├── data_loader.py            # CW1 PostgreSQL data access
│   │   ├── universe.py               # Point-in-time universe construction
│   │   └── benchmark.py              # Benchmark data (S&P 500, MSCI Value)
│   ├── signals/
│   │   ├── value_signal.py           # Sector-relative z-scores (MSCI 4-stage)
│   │   ├── sentiment_signal.py       # Quality-weighted VADER aggregation
│   │   └── signal_combiner.py        # 0.6V + 0.4S composite
│   ├── portfolio/
│   │   ├── portfolio_constructor.py  # Screen → weight → constrain
│   │   ├── constraints.py            # Position/sector caps
│   │   └── weighting.py              # EW, score-weight, inv-vol
│   ├── backtest/
│   │   ├── backtester.py             # Quarterly rebalance loop with drift
│   │   ├── transaction_costs.py      # 25 bps baseline cost model
│   │   └── rebalance_schedule.py     # Quarterly date generation
│   ├── analytics/
│   │   ├── performance.py            # Sharpe, Sortino, Calmar, drawdown
│   │   ├── risk.py                   # VaR, CVaR, FF 5-factor regression
│   │   ├── turnover.py               # Turnover measurement
│   │   └── diversification.py        # HHI, effective N, sector conc.
│   ├── robustness/
│   │   ├── sensitivity.py            # Weight/threshold/sub-period/sector tests
│   │   ├── bootstrap.py              # Stationary bootstrap CIs (Politis 1994)
│   │   └── random_portfolios.py      # 10,000 random portfolio comparison
│   └── visualization/
│       ├── charts.py                 # All 12 report charts
│       └── tearsheet.py              # QuantStats HTML tearsheet
├── tests/
│   ├── test_value_signal.py
│   ├── test_sentiment_signal.py
│   ├── test_portfolio.py
│   └── test_backtester.py
├── Main_CW2.py                       # Single entry point
├── pyproject.toml
└── README.md
```

---

## Quick Start (Reproduction from Clean Environment)

### Prerequisites
- Docker Desktop (for CW1 database infrastructure)
- Python 3.10+
- Poetry 1.7+

### Step-by-step

```bash
# 1. Clone and navigate
git clone https://github.com/.../ift_coursework_2025.git
cd ift_coursework_2025/team_09

# 2. Start CW1 infrastructure (PostgreSQL, MongoDB, MinIO, Kafka)
cd coursework_one && docker compose up -d
# Wait for postgres-seed and mongo-seed containers to exit with code 0

# 3. Verify CW1 database is seeded
docker exec postgres-db psql -U postgres -d fift -c \
  'SELECT COUNT(*) FROM systematic_equity.company_static;'
# Expected: 678

# 4. Run CW1 pipeline to populate price/value/sentiment data
cd coursework_one && poetry install
poetry run python Main.py --env_type dev --frequency quarterly

# 5. Install CW2 dependencies
cd ../coursework_two && poetry install

# 6. Run CW2 backtest (full pipeline)
poetry run python Main_CW2.py --config config/backtest_config.yaml

# 7. Run CW2 backtest (quick mode — skip robustness)
poetry run python Main_CW2.py --config config/backtest_config.yaml --skip-robustness

# 8. Run tests
poetry run pytest tests/ -v --cov=modules

# 9. Output location
ls output/charts/     # All 12 charts + tearsheet
ls output/tables/     # Performance summary, FF regression, bootstrap CIs
```

---

## Configuration

All parameters are in `config/backtest_config.yaml` — no hardcoded values in logic code.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scoring.value_weight` | 0.6 | Weight for value in composite |
| `scoring.sentiment_weight` | 0.4 | Weight for sentiment in composite |
| `scoring.selection_percentile` | 0.20 | Top 20% for investment |
| `scoring.max_debt_equity` | 2.0 | D/E filter threshold |
| `portfolio.max_position_weight` | 0.05 | Max 5% per stock |
| `portfolio.max_sector_weight` | 0.25 | Max 25% per GICS sector |
| `costs.transaction_cost_bps` | 25 | One-way transaction cost |
| `backtest.rebalance_months` | [1,4,7,10] | Quarterly rebalancing |

---

## CW1 Integration

CW2 reads directly from CW1's PostgreSQL tables:

| CW1 Table | CW2 Usage |
|-----------|-----------|
| `company_static` | Universe definition + GICS sectors |
| `daily_prices` | Daily returns for backtest simulation |
| `value_metrics` | P/E, P/B, EV/EBITDA, Div Yield, D/E |
| `sentiment_scores` | Article-level VADER compound scores |
| `composite_rankings` | CW1 baseline for OLD vs NEW comparison |

---

## Testing

```bash
# Run all tests with coverage
poetry run pytest tests/ -v --cov=modules --cov-report=term-missing

# Run specific test module
poetry run pytest tests/test_value_signal.py -v

# Run with markers
poetry run pytest -m unit
```

Coverage target: **85%+** across all CW2 modules.

---

## Git Workflow

Consistent with CW1:
- `main` branch: stable, submission-ready
- `develop` branch: integration
- `feature/*` branches: `feature/backtester`, `feature/value-signal`, etc.
- Commit convention: `feat:`, `fix:`, `docs:`, `test:` prefixes

---

## References

Key academic sources (full list in report):
- Ehsani, Harvey & Li (2023) — sector neutrality in factor portfolios
- Baker & Wurgler (2006) — investor sentiment and cross-section
- DeMiguel et al. (2009) — 1/N portfolio optimality
- Politis & Romano (1994) — stationary bootstrap
- Fama & French (2015) — 5-factor model
