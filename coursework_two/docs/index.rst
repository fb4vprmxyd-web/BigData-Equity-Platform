Value-Sentiment Investment Strategy — Documentation
=====================================================

**UCL Institute of Finance & Technology — IFTE0003: Big Data in Quantitative Finance**

**Team 09 — Coursework 2 — v2.8 (Maximum-Performance Tuned)**

This documentation covers the systematic long-only equity strategy that combines
**sector-relative value scoring** with **quality-weighted sentiment analysis** to
construct a diversified portfolio over the CW1 678-company universe.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
========

The strategy combines two complementary investment factors:

* **Sector-Relative Value (60% weight)**: MSCI Enhanced Value 4-stage pipeline that
  z-scores P/E, P/B, EV/EBITDA, and Dividend Yield within GICS sectors, eliminating
  the unintended sector bets produced by cross-sectional value ranking
  (Ehsani, Harvey & Li, 2023).
* **Quality-Weighted Sentiment (40% weight)**: 4-component multiplicative quality
  weighting (source credibility × relevance × recency × substantiveness) replaces
  CW1's volume-weighted aggregation (Tetlock, 2011).

The composite formula is::

    Composite Score = 0.6 × Value_percentile + 0.4 × Sentiment_normalised

Companies must pass three filters at each rebalance:

* ``value_score > 0`` (above within-sector median)
* sentiment ``confidence > 0.3`` (Bayesian shrinkage with k = 5)
* ``debt_equity ≤ 2.0`` (NaN treated as passing)

The top 20% of eligible stocks are flagged for investment, with quarterly
rebalancing at month-ends (Jan / Apr / Jul / Oct).

Installation
============

Prerequisites
-------------

* Python 3.10 or newer
* Docker and Docker Compose (for the CW1 database stack)
* Poetry 1.7 or newer
* CW1 PostgreSQL + MongoDB instances seeded with 678-company data

Step-by-Step Setup
------------------

1. Bring up the CW1 infrastructure::

    cd ../coursework_one && docker compose up -d
    poetry install && poetry run python Main.py --env_type dev --frequency quarterly

2. Install CW2 dependencies::

    cd ../coursework_two && poetry install

3. Backfill real historical fundamentals and prices::

    poetry run python -m modules.data.fix_prices_from_yfinance --all
    poetry run python -m modules.data.backfill_real_yfinance_history

4. (Optional) Backfill historical sentiment from Alpha Vantage::

    poetry run python -m modules.data.backfill_real_alpha_vantage_sentiment

Usage
=====

Basic Execution
---------------

::

    # Full pipeline with all robustness tests
    poetry run python Main_CW2.py --config config/backtest_config.yaml

    # Quick mode — skip robustness tests and chart generation
    poetry run python Main_CW2.py --config config/backtest_config.yaml \
        --skip-robustness --skip-charts

    # Run the test suite
    poetry run pytest tests/ -v --cov=modules

Output Artifacts
----------------

After a successful run, ``output/`` contains:

* ``output/tables/`` — 18 CSV tables (performance summary, FF regression,
  bootstrap CIs, weight/threshold sensitivity grids, sector attribution,
  monthly returns appendix, etc.)
* ``output/charts/`` — 16 PNG charts plus ``tearsheet.html``
  (cumulative returns, drawdown, monthly heatmap, rolling Sharpe, factor
  loadings, sector allocation, turnover, etc.)

Architecture
============

Pipeline Flow
-------------

CW2 sits on top of the CW1 data layer and adds three new layers:

1. **Signal Construction** — sector-relative value, quality-weighted sentiment,
   composite combiner (60V/40S)
2. **Portfolio Engine** — screen → weight → constrain, with vectorised intra-
   period drift in the backtester
3. **Analysis & Output** — performance metrics, FF 5-factor regression with
   Newey-West HAC, stationary block bootstrap (Politis & Romano, 1994),
   random-portfolio benchmarking, leave-one-sector-out attribution

CW1 → CW2 Data Layer
--------------------

CW2 reads CW1 outputs directly and does not maintain a separate dataset:

.. list-table::
   :header-rows: 1

   * - CW1 Source
     - CW2 Usage
     - Join Key
   * - ``company_static``
     - Universe + GICS sectors
     - ``symbol``
   * - ``daily_prices``
     - Daily ``adj_close`` for backtest
     - ``symbol``, ``cob_date``
   * - ``value_metrics``
     - P/E, P/B, EV/EBITDA, Div Yield, D/E
     - ``company_id``, ``date``
   * - ``sentiment_scores``
     - Aggregated VADER fallback
     - ``company_id``, ``date``
   * - ``raw_news_articles`` (Mongo)
     - Article-level quality weighting
     - ``company_id``, ``published_at``

Configuration
=============

All tuneable parameters live in ``config/backtest_config.yaml``. No values are
hardcoded in logic code.

.. list-table::
   :header-rows: 1

   * - Parameter
     - v2.8 Value
     - Description
   * - ``scoring.value_weight``
     - 0.6
     - Weight on value in composite
   * - ``scoring.sentiment_weight``
     - 0.4
     - Weight on sentiment in composite
   * - ``scoring.selection_percentile``
     - 0.20
     - Top 20% flagged for investment
   * - ``scoring.max_debt_equity``
     - 2.0
     - D/E filter threshold
   * - ``scoring.min_sentiment_confidence``
     - 0.3
     - ``n / (n+5) > 0.3`` ⇒ ~3 articles
   * - ``scoring.shrinkage_k_sector``
     - 20
     - Bayesian shrinkage for small sectors
   * - ``scoring.shrinkage_k_sentiment``
     - 5
     - Bayesian shrinkage on sentiment
   * - ``portfolio.max_position_weight``
     - 0.20
     - Max 20% per stock
   * - ``portfolio.max_sector_weight``
     - 0.50
     - Max 50% per sector
   * - ``costs.transaction_cost_bps``
     - 25
     - One-way transaction cost
   * - ``backtest.rebalance_months``
     - [1, 4, 7, 10]
     - Quarterly rebalancing
   * - ``backtest.reporting_lag_days``
     - 90
     - PIT lag for financial data

Testing
=======

::

    # Full test suite with coverage
    poetry run pytest tests/ -v --cov=modules --cov-report=term-missing

    # Specific test module
    poetry run pytest tests/test_value_signal.py -v

    # Markers
    poetry run pytest -m unit
    poetry run pytest -m integration

API Reference
=============

Data Layer
----------

.. automodule:: modules.data.data_loader

.. automodule:: modules.data.universe

.. automodule:: modules.data.benchmark

.. automodule:: modules.data.cw1_schema

.. automodule:: modules.data.fix_prices_from_yfinance

.. automodule:: modules.data.backfill_real_yfinance_history

.. automodule:: modules.data.backfill_real_alpha_vantage_sentiment

.. automodule:: modules.data.tune_config

Signal Construction
-------------------

.. automodule:: modules.signals.value_signal

.. automodule:: modules.signals.sentiment_signal

.. automodule:: modules.signals.signal_combiner

Portfolio Engine
----------------

.. automodule:: modules.portfolio.portfolio_constructor

.. automodule:: modules.portfolio.constraints

.. automodule:: modules.portfolio.weighting

Backtester
----------

.. automodule:: modules.backtest.backtester

.. automodule:: modules.backtest.rebalance_schedule

.. automodule:: modules.backtest.transaction_costs

Analytics
---------

.. automodule:: modules.analytics.performance

.. automodule:: modules.analytics.risk

.. automodule:: modules.analytics.turnover

.. automodule:: modules.analytics.diversification

.. automodule:: modules.analytics.pitfalls

.. automodule:: modules.analytics.appendices

Robustness
----------

.. automodule:: modules.robustness.sensitivity

.. automodule:: modules.robustness.bootstrap

.. automodule:: modules.robustness.random_portfolios

Visualization
-------------

.. automodule:: modules.visualization.charts

.. automodule:: modules.visualization.tearsheet

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
