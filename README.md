# BigData Equity Platform

### A Value + News-Sentiment Quantitative Equity Research Stack

**UCL Institute of Finance & Technology — IFTE0003: Big Data in Quantitative Finance**

An end-to-end systematic equity platform that ingests real market, fundamental, and
news data for a global universe of **678 companies**, engineers value and sentiment
signals from it, and uses those signals to construct, backtest, and rigorously
stress-test a long-only equity strategy that targets the value premium while avoiding
value traps.

The repository is organised as two tightly-coupled stages of a single research
pipeline:

| Stage | Directory | Role | One-line summary |
|---|---|---|---|
| **Coursework 1** | [`coursework_one/`](coursework_one/) | **Data platform** | Extract → Transform → Load pipeline that builds the data foundation (prices, fundamentals, FX, news, sentiment) into PostgreSQL / MongoDB / MinIO. |
| **Coursework 2** | [`coursework_two/`](coursework_two/) | **Strategy & backtest** | Consumes the CW1 data layer to build signals, construct portfolios, run a point-in-time backtest, and produce a full institutional research report. |

> CW2 does **not** re-fetch raw data — it reads CW1's databases directly through a
> single schema contract ([`coursework_two/modules/data/cw1_schema.py`](coursework_two/modules/data/cw1_schema.py)).
> Run CW1 first to populate the stores, then run CW2 to generate results.

---

## Table of Contents

1. [Investment Thesis](#1-investment-thesis)
2. [What the Platform Produces](#2-what-the-platform-produces)
3. [System Architecture](#3-system-architecture)
4. [Repository Layout](#4-repository-layout)
5. [Prerequisites](#5-prerequisites)
6. [Quick Start (Zero to Results)](#6-quick-start-zero-to-results)
7. [Configuration & Secrets](#7-configuration--secrets)
8. [CW1 → CW2 Data Contract](#8-cw1--cw2-data-contract)
9. [Headline Results](#9-headline-results)
10. [Testing & Code Quality](#10-testing--code-quality)
11. [Security Hardening](#11-security-hardening)
12. [Troubleshooting](#12-troubleshooting)
13. [Documentation & References](#13-documentation--references)

---

## 1. Investment Thesis

> **Hypothesis.** Companies that are *undervalued* on fundamental ratios (P/E, P/B,
> EV/EBITDA) **and** carry *positive recent news sentiment* outperform the broad
> market over the medium term. The sentiment filter removes **value traps** —
> stocks that look cheap because something is genuinely wrong.

The strategy stands on two well-documented pillars of academic finance:

- **The value premium** — cheap stocks systematically outperform expensive
  "growth" stocks (Fama & French, 1993).
- **News sentiment as a forward signal** — the tone of media coverage predicts
  future returns and flags deteriorating fundamentals (Tetlock, 2007; Baker &
  Wurgler, 2006).

The composite score blends the two:

```
Score = 0.60 × Value_percentile  +  0.40 × Sentiment_normalised
```

CW2 then sharpens this baseline with **sector-relative value scoring** (MSCI
Enhanced-Value 4-stage pipeline, eliminating unintended sector bets),
**quality-weighted sentiment** (source credibility × relevance × recency ×
substantiveness), **Bayesian shrinkage** for thin samples, and an Asness-style
**value + momentum** overlay.

---

## 2. What the Platform Produces

**Coursework 1 — the data foundation:**

- 5 years of daily OHLCV prices for 678 companies across 9 countries
- Fundamental ratios: P/E, P/B, EV/EBITDA, Dividend Yield, Debt/Equity
- FX rates for 4 currency pairs (GBP/EUR/CAD/CHF → USD)
- News articles (GDELT + Yahoo Finance) with VADER sentiment scores
- Composite value-sentiment rankings and `invest` decisions, persisted to
  PostgreSQL, MongoDB and MinIO, with events published to Kafka

**Coursework 2 — the research report:** after a full run, `coursework_two/output/`
holds **18 tables** and **16 charts + an interactive HTML tearsheet**, including the
performance summary, Fama-French 5-factor regression (Newey-West HAC), sub-period
analysis, weight/threshold sensitivity grids, stationary-block bootstrap confidence
intervals, a 10,000 random-portfolio skill-vs-luck test, and a backtesting-pitfalls
audit.

---

## 3. System Architecture

```
                          ┌──────────────────────────────────────────────┐
   EXTERNAL DATA          │              COURSEWORK 1  (ETL)              │
 ┌──────────────┐         │                                              │
 │  yfinance    │────────▶│  extraction/  → transform/  → loading/       │
 │  GDELT news  │         │  (prices,        (clean,        (upsert)      │
 │  Yahoo news  │         │   ratios, FX,     VADER,                      │
 │  Finnhub     │         │   news)           scoring)                    │
 └──────────────┘         └───────┬───────────────┬───────────────┬──────┘
                                  │               │               │
                          ┌───────▼──────┐ ┌──────▼─────┐ ┌───────▼──────┐
   DATA LAYER             │  PostgreSQL  │ │  MongoDB   │ │    MinIO     │
   (shared stores)        │ prices, ratios│ │ raw news + │ │ raw report   │
                          │ scores, rank │ │ sentiment  │ │ objects (S3) │
                          └───────┬──────┘ └──────┬─────┘ └──────────────┘
                                  │               │
                          ┌───────▼───────────────▼──────────────────────┐
                          │              COURSEWORK 2  (Strategy)         │
                          │  data/  → signals/  → portfolio/  → backtest/ │
                          │            (value,     (screen,     (quarterly │
                          │             sentiment)  weight,      rebalance,│
                          │                         constrain)   drift)    │
                          │       → analytics/ + robustness/ + visualization
                          └───────────────────┬──────────────────────────┘
                                              ▼
                                  output/tables + output/charts
```

Infrastructure is provisioned with Docker Compose: **PostgreSQL** (relational store),
**MongoDB** (raw news / document store), **MinIO** (S3-compatible object store),
**pgAdmin** (DB console), and **Kafka** (event stream for downstream consumers).

---

## 4. Repository Layout

```
bigdatatshakh/
├── docker-compose.yml            # Root infra (Postgres, Mongo, MinIO, pgAdmin)
├── .env.example                  # Template for all credentials / API keys
├── CHANGELOG.md                  # Full version history (CW1 + CW2)
│
├── coursework_one/               # ── DATA PLATFORM ──
│   ├── main.py                   # ETL entry point
│   ├── modules/
│   │   ├── extraction/           # prices, ratios, FX, GDELT + YF news
│   │   ├── processing/           # cleaning, VADER sentiment, scoring
│   │   ├── loading/              # PostgreSQL / MongoDB / MinIO writers
│   │   ├── db/                   # connection factories
│   │   ├── kafka/                # event producers
│   │   └── utils/                # config, logging, helpers
│   ├── config/                   # conf.yaml (env-specific connection config)
│   ├── test/                     # pytest suite
│   └── pyproject.toml
│
└── coursework_two/               # ── STRATEGY & BACKTEST ──
    ├── Main_CW2.py               # Single entry point
    ├── config/backtest_config.yaml   # ALL tuneable parameters (grid-tuned)
    ├── modules/
    │   ├── data/                 # CW1 data access + schema contract + backfills
    │   ├── signals/              # value, sentiment, combiner
    │   ├── portfolio/            # construction, weighting, constraints
    │   ├── backtest/             # rebalance loop, drift, transaction costs
    │   ├── analytics/            # performance, risk, turnover, diversification
    │   ├── robustness/           # bootstrap, random portfolios, sensitivity
    │   └── visualization/        # charts + QuantStats tearsheet
    ├── tests/                    # pytest suite (85%+ coverage target)
    ├── output/                   # generated tables + charts (after a run)
    └── pyproject.toml
```

---

## 5. Prerequisites

- **Docker Desktop** (for the database infrastructure)
- **Python 3.10+**
- **Poetry 1.7+** (dependency management for both courseworks)
- A `.env` file at the repository root (copy from `.env.example`)
- Optional API keys for richer data coverage — see [§7](#7-configuration--secrets)

---

## 6. Quick Start (Zero to Results)

Run from the repository root unless noted. The flow is: **infra up → CW1 ETL →
CW2 backtest**.

```bash
# 0. Clone and configure secrets
git clone https://github.com/fb4vprmxyd-web/BigData-Equity-Platform.git
cd BigData-Equity-Platform
cp .env.example .env            # then fill in credentials / API keys (see §7)

# 1. Start the data infrastructure (Postgres, Mongo, MinIO, pgAdmin)
docker compose up -d
#    Wait for the seed containers to finish and the DBs to report healthy.

# ── COURSEWORK 1: build the data foundation ──────────────────────────────
cd coursework_one
poetry install
poetry run python main.py --env_type dev --frequency quarterly
#    Extracts prices/ratios/FX/news, computes sentiment + rankings,
#    and loads everything into PostgreSQL / MongoDB / MinIO.

# (optional) sanity-check the seeded universe
docker exec postgres_db_cw psql -U postgres -d fift \
  -c 'SELECT COUNT(*) FROM systematic_equity.company_static;'   # → 678

# ── COURSEWORK 2: run the strategy + backtest ────────────────────────────
cd ../coursework_two
poetry install

# (recommended, real-data prep) correct price glitches + backfill PIT history
set -a && source ../.env && set +a
poetry run python -m modules.data.fix_prices_from_yfinance --all
poetry run python -m modules.data.backfill_real_yfinance_history
# poetry run python -m modules.data.backfill_real_alpha_vantage_sentiment  # optional

# Full pipeline (signals → portfolio → backtest → robustness → charts)
poetry run python Main_CW2.py --config config/backtest_config.yaml

# Fast iteration (skip the expensive robustness + chart stages)
poetry run python Main_CW2.py --config config/backtest_config.yaml \
  --skip-robustness --skip-charts

# Inspect results
ls output/charts/    # 16 charts + tearsheet.html
ls output/tables/    # 18 CSV tables
```

To run **CW1 inside Docker** instead of on the host, use
`--env_type docker` (and `--init_schema` on the first run to create the schema).

---

## 7. Configuration & Secrets

All connection details and API keys live in a single `.env` at the repository root
(`cp .env.example .env` to start). CW2 additionally exposes every strategy parameter
in [`coursework_two/config/backtest_config.yaml`](coursework_two/config/backtest_config.yaml)
— there are **no hardcoded values in logic code**.

**Required — infrastructure** (defaults match `docker-compose.yml`):

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` | PostgreSQL credentials | `postgres` / `postgres` |
| `POSTGRES_HOST_DEV` / `POSTGRES_PORT_DEV` | Postgres host/port (host machine) | `localhost` / `5439` |
| `POSTGRES_DATABASE` | Database name | `fift` |
| `MONGO_HOST` / `MONGO_PORT` | MongoDB host/port | `localhost` / `27019` |
| `MONGO_USERNAME` / `MONGO_PASSWORD` | MongoDB credentials | `ift_bigdata` / `mongo_password` |
| `MINIO_USER` / `MINIO_PASSWORD` / `MINIO_URL` | MinIO root user / password / endpoint | `ift_bigdata` / `minio_password` / `http://localhost:9000` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | `localhost:9092` |

**Required — CW1 data extraction:**

| Variable | Source |
|---|---|
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io) |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) |

**Optional — CW2 real-data backfill / supplementary fundamentals:**

| Variable | Notes | Source |
|---|---|---|
| `ALPHA_VANTAGE_KEY_1 … _9` | 9 keys rotated round-robin (25 calls/day each ≈ 225/day) | [alphavantage.co](https://www.alphavantage.co/support/#api-key) |
| `FMP_API_KEY` | Financial Modeling Prep | [financialmodelingprep.com](https://financialmodelingprep.com) |
| `SIMFIN_API_KEY` | SimFin bulk financials | [simfin.com](https://simfin.com) |

> `yfinance` needs no API key (it uses Yahoo's public endpoints). The
> repository's `.gitignore` excludes `.env`, logs, `postgres-data/`, and
> `output/` so secrets and bulky artifacts are never committed.

---

## 8. CW1 → CW2 Data Contract

CW2 is **strictly coupled** to CW1's data layer at the schema level. The single
source of truth for every table name, column name, MongoDB collection/field, and
ticker-normalisation rule is
[`coursework_two/modules/data/cw1_schema.py`](coursework_two/modules/data/cw1_schema.py).
If CW1 renames a column, only that file changes.

| CW1 Table | CW2 Usage | Join Key |
|---|---|---|
| `company_static` | Universe definition + GICS sectors | `symbol` |
| `daily_prices` | Daily `adj_close` for backtest simulation | `symbol`, `cob_date` |
| `value_metrics` | P/E, P/B, EV/EBITDA, Div Yield, D/E | `company_id`, `date` |
| `sentiment_scores` | Aggregated VADER fallback | `company_id`, `date` |
| `composite_rankings` | CW1 baseline for OLD-vs-NEW comparison | `company_id`, `date` |
| `raw_news_articles` (MongoDB) | Article-level quality-weighted sentiment | `company_id`, `published_at`, … |

> **Naming asymmetry warning.** CW1 uses `symbol` in `daily_prices` /
> `company_static` but `company_id` in the scoring tables for the *same* ticker.
> The schema constants make this explicit so it can no longer cause silent join
> failures. Secrets resolve in the order **YAML → environment variable →
> fail-loud**, so CW2 can run against a production DB without committing
> credentials.

---

## 9. Headline Results

Grid-tuned concentrated value-momentum portfolio over the PIT-clean backtest window:

```
Portfolio                Return     Vol    Sharpe   Sortino   Calmar    MaxDD       IR
------------------------------------------------------------------------------------------
Combined                28.50%   16.85%    1.340    1.933    1.662   -17.14%   +0.779
Value-Only              16.37%   14.68%    0.839    1.144    1.049   -15.61%   -0.108
Sentiment-Only          15.44%   16.16%    0.726    1.012    0.673   -22.94%   -0.173
S&P 500 (benchmark)     18.42%   15.37%    0.922    1.200    0.975   -18.90%    0.000
```

The Combined strategy beats the S&P 500 by **+45% on Sharpe** (1.340 vs 0.922),
**+55% on return**, and **+70% on Calmar**. Fama-French annualised alpha is
**+11.02%**, the bootstrap probability that Sharpe > 0 is **96.5%**, and the
strategy ranks in the **99.7th percentile** against 10,000 random portfolios.

---

## 10. Testing & Code Quality

```bash
# Coursework 1
cd coursework_one && poetry run pytest test/ -v

# Coursework 2 (target: 85%+ coverage)
cd coursework_two && poetry run pytest tests/ -v --cov=modules --cov-report=term-missing
```

Both courseworks ship `black` (line length 120), `isort`, `flake8`, and `bandit`
configuration, and a Sphinx documentation build under
[`coursework_two/docs/`](coursework_two/docs/).

---

## 11. Security Hardening

The data layer is hardened against the classic backtester security pitfalls
(full audit trail in [CHANGELOG.md](CHANGELOG.md)):

- **SQL injection** — all values use SQLAlchemy bound parameters; identifiers are
  whitelisted against `[A-Za-z_][A-Za-z0-9_]*`.
- **Look-ahead leakage** — `published_at <= as_of_date` is enforced *server-side*
  in the Mongo query, so future news cannot leak into a past rebalance.
- **No hardcoded credentials** — every secret resolves YAML → env var → fail-loud;
  connection URLs are never logged.
- **Safe deserialisation** — `yaml.safe_load` only; Mongo clients always closed in
  `try/finally`; pooled connections use `pool_pre_ping` + recycle.

---

## 12. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `company_static` count ≠ 678 | Seed containers not finished — re-run `docker compose up -d` and wait for healthy status. |
| CW2 cannot connect to DB | Confirm `.env` host/port match `docker-compose.yml` (host: `localhost:5439`; in-container: `postgres_db:5432`). |
| Empty / sparse value metrics | Run the CW2 backfill scripts in [§6](#6-quick-start-zero-to-results) before the backtest. |
| Alpha Vantage 429 / rate limit | Free tier is 25 calls/day per key — add more `ALPHA_VANTAGE_KEY_*` keys or skip the optional sentiment backfill. |
| Port already in use | Another Postgres/Mongo instance is bound — stop it or remap ports in `docker-compose.yml`. |

---

## 13. Documentation & References

- **[CHANGELOG.md](CHANGELOG.md)** — complete version history for both courseworks.
- **[coursework_one/README.md](coursework_one/README.md)** — deep dive on the ETL
  platform, data dictionary, lineage, and infrastructure.
- **[coursework_two/README.md](coursework_two/README.md)** — full strategy,
  configuration grid, output catalogue, and CW1 integration notes.
- **Sphinx docs** — `coursework_two/docs/` (run `make html`).

Key academic sources:

- Fama & French (1993) — the value premium
- Tetlock (2007, 2008, 2011) — news content and stock returns
- Baker & Wurgler (2006) — investor sentiment and the cross-section
- Asness, Porter & Stevens (2000) — within-industry value
- Ehsani, Harvey & Li (2023) — sector neutrality in factor portfolios
- Stambaugh, Yu & Yuan (2012) — sentiment-conditioned anomaly returns
- DeMiguel, Garlappi & Uppal (2009) — the case for equal weighting
- Politis & Romano (1994) — the stationary bootstrap
```
