# CW2 — Value-Sentiment Investment Strategy

## UCL Institute of Finance & Technology
**IFTE0003: Big Data in Quantitative Finance**
**Team 09 — Coursework 2** · **v2.3 (PDF Fidelity Pass)**

---

## Strategy Overview

A systematic long-only equity strategy combining **sector-relative value scoring** with **quality-weighted sentiment analysis** to construct a diversified portfolio that captures the value premium while avoiding value traps.

**Key innovations over CW1:**
- **Sector-relative value scoring**: MSCI Enhanced Value 4-stage pipeline replaces cross-sectional percentile ranking, eliminating unintended sector bets (Ehsani, Harvey & Li, 2023)
- **Quality-weighted sentiment**: 4-component quality weighting (source credibility × relevance × recency × substantiveness) replaces volume-weighted aggregation (Tetlock, 2011)
- **Bayesian shrinkage**: Applied to both value scores (small sectors) and sentiment scores (low article coverage) to reduce estimation noise
- **Vectorised intra-period drift**: Backtester computes daily portfolio returns and end-of-period drifted weights closed-form, ensuring turnover at rebalance ``i+1`` reflects organic drift (not pre-period target weights)
- **Buffer rule**: 60th-percentile buy / 40th-percentile sell no-trade band keeps existing winners while admitting only high-conviction new buys
- **Stationary block bootstrap**: 2,500-rep Politis & Romano (1994) bootstrap returns 95% CIs for **Sharpe, annualised return, volatility, and max drawdown** (not just Sharpe)

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
│   │   ├── risk.py                   # VaR, CVaR, FF 5-factor (Newey-West HAC)
│   │   ├── turnover.py               # Turnover measurement
│   │   ├── diversification.py        # HHI, effective N, sector conc.
│   │   └── pitfalls.py               # Table 11 — backtesting pitfalls audit
│   ├── robustness/
│   │   ├── sensitivity.py            # Weight/threshold/sub-period/sector tests
│   │   ├── bootstrap.py              # Stationary bootstrap CIs (Politis 1994)
│   │   └── random_portfolios.py      # 10,000 random portfolio comparison
│   └── visualization/
│       ├── charts.py                 # 14 report charts (12 mandatory + 2 sophistication)
│       └── tearsheet.py              # QuantStats HTML tearsheet
├── tests/
│   ├── conftest.py                   # Shared pytest fixtures
│   ├── test_value_signal.py
│   ├── test_sentiment_signal.py
│   ├── test_signal_combiner.py
│   ├── test_portfolio.py
│   ├── test_constraints.py
│   ├── test_backtester.py
│   ├── test_performance.py
│   ├── test_risk.py
│   ├── test_diversification.py
│   ├── test_robustness.py            # Bootstrap/random/sensitivity/sub-period
│   ├── test_pitfalls.py
│   ├── test_universe.py
│   └── test_integration.py           # End-to-end mini-backtest
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

CW2 is **strictly coupled** to CW1's data layer at the schema level via
[modules/data/cw1_schema.py](modules/data/cw1_schema.py), which is the
single source of truth for every table name, column name, MongoDB
collection name, MongoDB field name, and ticker normalisation rule.
If CW1 ever renames a column, only that file needs to change.

| CW1 Table | CW2 Usage | Join Key |
|-----------|-----------|----------|
| `company_static` | Universe definition + GICS sectors | `symbol` |
| `daily_prices` | Daily adj_close for backtest simulation | `symbol`, `cob_date` |
| `value_metrics` | P/E, P/B, EV/EBITDA, Div Yield, D/E | `company_id`, `date` |
| `sentiment_scores` | Aggregated VADER fallback | `company_id`, `date` |
| `composite_rankings` | CW1 baseline for OLD vs NEW comparison | `company_id`, `date` |

| CW1 MongoDB Collection | CW2 Usage | Key Fields |
|---|---|---|
| `raw_news_articles` (db `ift_cw1_sentiment`) | Article-level quality-weighted sentiment | `company_id`, `headline`, `description`, `source_name`, `published_at`, `compound_score` |

**Naming asymmetry warning** — CW1 uses `symbol` in `daily_prices` and
`company_static`, but `company_id` in the scoring tables for the *same*
underlying ticker. The schema constants in `cw1_schema.py` make this
explicit so it can no longer cause silent join failures.

**Connection inheritance** — CW2's `DataLoader` reads CW1's
`coursework_one/config/conf.yaml` directly (via `cw1.config_path` in
`backtest_config.yaml`) and falls back to environment variables in the
order **YAML → env var → fail-loud**:

| Field | YAML key | Env var |
|---|---|---|
| Username | `dev.config.Database.Postgres.Username` | `POSTGRES_USERNAME` |
| Password | `dev.config.Database.Postgres.Password` | `POSTGRES_PASSWORD` |
| Host | `dev.config.Database.Postgres.Host` | `POSTGRES_HOST_DEV` |
| Port | `dev.config.Database.Postgres.Port` | `POSTGRES_PORT_DEV` |
| Database | `dev.config.Database.Postgres.Database` | `POSTGRES_DATABASE` |
| Mongo username | `dev.config.Database.MongoDB.Username` | `MONGO_USERNAME` |
| Mongo password | `dev.config.Database.MongoDB.Password` | `MONGO_PASSWORD` |
| Mongo host | `dev.config.Database.MongoDB.Host` | `MONGO_HOST` |
| Mongo port | `dev.config.Database.MongoDB.Port` | `MONGO_PORT` |

To run CW2 against a production database without committing secrets:

```bash
export POSTGRES_PASSWORD='<from-vault>'
export MONGO_PASSWORD='<from-vault>'
poetry run python Main_CW2.py --config config/backtest_config.yaml
```

---

## Security

The data layer has been hardened against the classic backtester
security pitfalls. See [CHANGELOG.md](../CHANGELOG.md) v2.2.0 for the
full audit trail.

| Threat | Mitigation | Location |
|---|---|---|
| SQL injection | All value placeholders use SQLAlchemy bound parameters; identifiers (schema, table) are whitelisted via `assert_safe_identifier` against `[A-Za-z_][A-Za-z0-9_]*` | [data_loader.py](modules/data/data_loader.py), [cw1_schema.py](modules/data/cw1_schema.py) |
| Look-ahead leak (Mongo) | `published_at <= as_of_date` enforced **server-side** in the Mongo `find()` filter so future news cannot leak into a past rebalance | `_load_articles_from_mongo` |
| Hardcoded credentials | All passwords resolved via the chain YAML → env var → fail-loud `RuntimeError`. The previous literal fallbacks (`'postgres'`, `'mongo_password'`) have been removed. | `_resolve_secret`, `_create_engine` |
| Credential leak via logs | Connection URL is **never** logged (it would contain the password); fields are logged individually omitting `password` | `_create_engine` |
| Connection pool exhaustion | `pool_recycle=3600`, `pool_pre_ping=True`, Mongo `connectTimeoutMS=5000`, `socketTimeoutMS=10000`, `maxPoolSize=20` | `_create_engine`, `_load_articles_from_mongo` |
| YAML deserialisation | `yaml.safe_load` only — no arbitrary-Python loader | All YAML reads |
| Path traversal in config | CW1 config_path is read literally from CW2 config; CW2 controls the config file, not user input | `_load_cw1_conf` |
| Resource leak on partial failure | Every Mongo client is opened in a `try/finally` block that calls `client.close()` | `_load_articles_from_mongo` |
| Identifier-injection via schema config | `DataLoader.__init__` rejects any schema name containing characters outside `[A-Za-z_][A-Za-z0-9_]*` with a `ValueError` | `__init__` |

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

## Output Artifacts

After a successful run, `output/` contains:

```
output/
├── tables/
│   ├── performance_summary.csv          # Table 1 — all portfolios × all metrics
│   ├── fama_french_regression.csv       # Table 2 — FF 5-factor + Newey-West t-stats
│   ├── sub_period_analysis.csv          # Table 3 — year-by-year + regime split
│   ├── weight_sensitivity.csv           # Table 4 — value/sentiment weight sweep
│   ├── threshold_sensitivity.csv        # Table 5 — top-% × D/E grid
│   ├── weighting_scheme_comparison.csv  # Table 6 — EW vs score vs inv-vol
│   ├── top_drawdowns.csv                # Table 7 — top 3 drawdown events
│   ├── bootstrap_ci.csv                 # Table 8 — Sharpe/return/vol/MaxDD CIs
│   ├── old_vs_new_value.csv             # Table 9 — sector concentration delta
│   ├── old_vs_new_sentiment.csv         # Table 10 — sentiment quality delta
│   ├── backtesting_pitfalls.csv         # Table 11 — pitfalls audit
│   ├── sector_attribution.csv           # leave-one-sector-out
│   ├── random_portfolios.csv            # skill-vs-luck stats
│   └── diversification_over_time.csv    # HHI/effective N per rebalance
└── charts/
    ├── cumulative_returns.png           # Chart 1
    ├── drawdown.png                     # Chart 2
    ├── monthly_heatmap.png              # Chart 3
    ├── rolling_sharpe.png               # Chart 4
    ├── weight_sensitivity.png           # Chart 5
    ├── factor_loadings.png              # Chart 6
    ├── sector_allocation.png            # Chart 7
    ├── random_portfolios.png            # Chart 8
    ├── threshold_sensitivity.png        # Chart 9
    ├── turnover.png                     # Chart 10
    ├── old_vs_new_value.png             # Chart 11
    ├── pipeline_flowchart.png           # Chart 12
    ├── diversification_over_time.png    # Chart 13 (sophistication)
    ├── cost_impact.png                  # Chart 14 (sophistication)
    └── tearsheet.html                   # QuantStats HTML — Appendix D
```

---

## References

Key academic sources (full list in report):
- Ehsani, Harvey & Li (2023) — sector neutrality in factor portfolios
- Asness, Porter & Stevens (2000) — within-industry value characteristics
- Baker & Wurgler (2006) — investor sentiment and cross-section
- Tetlock (2007, 2008, 2011) — news content and stock returns
- Stambaugh, Yu & Yuan (2012) — sentiment-conditioned anomaly returns
- DeMiguel, Garlappi & Uppal (2009) — 1/N portfolio optimality
- Maillard, Roncalli & Teïletche (2010) — equal risk contribution portfolios
- Politis & Romano (1994) — stationary bootstrap
- Newey & West (1987) — HAC covariance estimator
- Fama & French (2015) — 5-factor model
- Lo (2002) — statistics of Sharpe ratios
- Bailey, Borwein, López de Prado & Zhu (2015) — backtest overfitting
- Lopez de Prado (2018) — Advances in Financial Machine Learning
