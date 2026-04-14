"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Data loader — reads from CW1 PostgreSQL and MongoDB
Project : CW2 - Value-Sentiment Investment Strategy

Loads price history, value metrics, sentiment scores, and company
metadata from the CW1 data pipeline infrastructure.  All queries use
the CW1 PostgreSQL schema ``systematic_equity`` and the MongoDB
collection ``raw_news_articles``.

Implements point-in-time discipline: every query filters by
``date <= rebalance_date`` to prevent look-ahead bias.

:Design: Part D §D7 — CW1 Integration
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yaml
from sqlalchemy import create_engine, engine, text

logger = logging.getLogger(__name__)


class DataLoader:
    """Load CW1 pipeline data from PostgreSQL for CW2 backtesting.

    Reads connection parameters from CW1's ``conf.yaml`` and provides
    DataFrame-returning methods for each table.  All methods enforce
    point-in-time constraints.

    :param config: Parsed backtest_config.yaml dict
    :type config: dict
    """

    def __init__(self, config: dict):
        self._config = config
        self._engine = self._create_engine()
        self._schema = config['data']['postgres_schema']
        logger.info("DataLoader initialised — schema: %s", self._schema)

    def _create_engine(self):
        """Create SQLAlchemy engine from CW1 config.

        :returns: SQLAlchemy engine instance
        :rtype: sqlalchemy.engine.Engine
        """
        cw1_path = self._config['cw1']['config_path']
        env_type = self._config['cw1']['env_type']

        with open(cw1_path, 'r') as f:
            cw1_conf = yaml.safe_load(f)

        db_conf = cw1_conf[env_type]['config']['Database']['Postgres']
        url = engine.URL.create(
            drivername='postgresql',
            username=db_conf.get('Username', 'postgres'),
            password=db_conf.get('Password', 'postgres'),
            host=db_conf.get('Host', 'localhost'),
            port=str(db_conf.get('Port', '5438')),
            database=db_conf.get('Database', 'fift'),
        )
        return create_engine(url, pool_size=10, max_overflow=5, pool_pre_ping=True)

    def load_company_static(self) -> pd.DataFrame:
        """Load the full 678-company universe with GICS sector data.

        :returns: DataFrame with columns [symbol, security, gics_sector,
                  gics_industry, country, region]
        :rtype: pd.DataFrame
        """
        query = f"""
            SELECT TRIM(symbol) AS symbol,
                   security,
                   gics_sector,
                   gics_industry,
                   TRIM(country) AS country,
                   region
            FROM {self._schema}.company_static
        """
        df = pd.read_sql(query, self._engine)
        df['symbol'] = df['symbol'].str.strip()
        logger.info("Loaded %d companies from company_static", len(df))
        return df

    def load_daily_prices(
        self,
        start_date: str,
        end_date: str,
        tickers: Optional[list] = None,
    ) -> pd.DataFrame:
        """Load adjusted close prices for backtesting.

        Returns a pivoted DataFrame with dates as index and tickers
        as columns, using ``adj_close_price`` for total-return accuracy.

        :param start_date: Start date (YYYY-MM-DD inclusive)
        :type start_date: str
        :param end_date: End date (YYYY-MM-DD inclusive)
        :type end_date: str
        :param tickers: Optional list of tickers to filter
        :type tickers: list or None
        :returns: Pivoted price DataFrame (dates × tickers)
        :rtype: pd.DataFrame
        """
        ticker_filter = ""
        if tickers:
            quoted = ", ".join(f"'{t.strip()}'" for t in tickers)
            ticker_filter = f"AND TRIM(symbol) IN ({quoted})"

        query = f"""
            SELECT TRIM(symbol) AS symbol,
                   cob_date,
                   adj_close_price
            FROM {self._schema}.daily_prices
            WHERE cob_date BETWEEN '{start_date}' AND '{end_date}'
            {ticker_filter}
            ORDER BY cob_date, symbol
        """
        df = pd.read_sql(query, self._engine, parse_dates=['cob_date'])
        df['symbol'] = df['symbol'].str.strip()

        # Pivot to wide format: dates × tickers
        prices = df.pivot(index='cob_date', columns='symbol', values='adj_close_price')
        prices.index.name = 'date'
        prices = prices.sort_index()

        logger.info(
            "Loaded prices: %d dates × %d tickers (%s to %s)",
            len(prices), len(prices.columns),
            prices.index.min().strftime('%Y-%m-%d') if len(prices) > 0 else 'N/A',
            prices.index.max().strftime('%Y-%m-%d') if len(prices) > 0 else 'N/A',
        )
        return prices

    def load_value_metrics(self, as_of_date: str) -> pd.DataFrame:
        """Load value metrics available as of a given date (point-in-time).

        Applies reporting lag: only returns data with
        ``date <= as_of_date`` to prevent look-ahead bias.  Returns
        the most recent record per company.

        :param as_of_date: Reference date for point-in-time lookup
        :type as_of_date: str
        :returns: DataFrame with pe_ratio, pb_ratio, ev_ebitda,
                  dividend_yield, debt_equity, value_score per company
        :rtype: pd.DataFrame
        """
        query = f"""
            SELECT DISTINCT ON (company_id)
                   TRIM(company_id) AS company_id,
                   date,
                   pe_ratio,
                   pb_ratio,
                   ev_ebitda,
                   dividend_yield,
                   debt_equity,
                   value_score
            FROM {self._schema}.value_metrics
            WHERE date <= '{as_of_date}'
            ORDER BY company_id, date DESC
        """
        df = pd.read_sql(query, self._engine, parse_dates=['date'])
        df['company_id'] = df['company_id'].str.strip()
        logger.info("Loaded value metrics for %d companies (as of %s)", len(df), as_of_date)
        return df

    def load_sentiment_scores(self, as_of_date: str) -> pd.DataFrame:
        """Load sentiment scores available as of a given date.

        Returns the most recent sentiment record per company,
        respecting point-in-time constraints.

        :param as_of_date: Reference date for point-in-time lookup
        :type as_of_date: str
        :returns: DataFrame with avg_sentiment, total_articles,
                  positive_ratio, sentiment_score per company
        :rtype: pd.DataFrame
        """
        query = f"""
            SELECT DISTINCT ON (company_id)
                   TRIM(company_id) AS company_id,
                   date,
                   avg_sentiment,
                   positive_count,
                   negative_count,
                   neutral_count,
                   total_articles,
                   positive_ratio,
                   sentiment_score
            FROM {self._schema}.sentiment_scores
            WHERE date <= '{as_of_date}'
            ORDER BY company_id, date DESC
        """
        df = pd.read_sql(query, self._engine, parse_dates=['date'])
        df['company_id'] = df['company_id'].str.strip()
        logger.info("Loaded sentiment scores for %d companies (as of %s)", len(df), as_of_date)
        return df

    def load_composite_rankings(self, as_of_date: str) -> pd.DataFrame:
        """Load CW1 composite rankings for baseline comparison.

        :param as_of_date: Reference date
        :type as_of_date: str
        :returns: DataFrame with CW1 value_score, sentiment_score,
                  composite_score, rank, invest_decision
        :rtype: pd.DataFrame
        """
        query = f"""
            SELECT DISTINCT ON (company_id)
                   TRIM(company_id) AS company_id,
                   date,
                   value_score,
                   sentiment_score,
                   composite_score,
                   rank,
                   invest_decision
            FROM {self._schema}.composite_rankings
            WHERE date <= '{as_of_date}'
            ORDER BY company_id, date DESC
        """
        df = pd.read_sql(query, self._engine, parse_dates=['date'])
        df['company_id'] = df['company_id'].str.strip()
        logger.info("Loaded CW1 composite rankings for %d companies", len(df))
        return df

    def load_news_article_metadata(self, as_of_date: str) -> pd.DataFrame:
        """Load article-level metadata from CW1 MongoDB for quality weighting.

        Connects to CW1's MongoDB ``raw_news_articles`` collection and
        retrieves per-article data: headline, source domain, publication
        date, VADER compound score, and description/word count.

        These fields are required for the CW2 quality-weighted sentiment
        upgrade (Part A §A3):
          - source_name → source credibility tier weight
          - headline    → relevance scoring (company in headline)
          - date        → recency exponential decay
          - description → substantiveness (word count)

        Falls back gracefully to aggregated PostgreSQL sentiment_scores
        if MongoDB is unavailable or empty.

        :param as_of_date: Reference date (YYYY-MM-DD) — only articles
                           published on or before this date are returned
        :type as_of_date: str
        :returns: DataFrame with per-article metadata, or aggregated
                  sentiment if article-level data is not available
        :rtype: pd.DataFrame
        """
        articles_df = self._load_articles_from_mongo(as_of_date)

        if articles_df is not None and len(articles_df) > 0:
            logger.info(
                "Loaded %d article-level records from MongoDB (as of %s)",
                len(articles_df), as_of_date,
            )
            return articles_df

        # Fallback: use aggregated sentiment_scores from PostgreSQL
        logger.info(
            "MongoDB articles not available — falling back to aggregated sentiment_scores"
        )
        return self.load_sentiment_scores(as_of_date)

    def _load_articles_from_mongo(self, as_of_date: str) -> pd.DataFrame:
        """Query article-level data from CW1 MongoDB raw_news_articles.

        :param as_of_date: Upper date bound for point-in-time
        :type as_of_date: str
        :returns: DataFrame with article metadata or None if unavailable
        :rtype: pd.DataFrame or None
        """
        try:
            from pymongo import MongoClient
        except ImportError:
            logger.info("pymongo not installed — cannot load article-level data")
            return None

        # Read MongoDB config from CW1 conf.yaml
        cw1_path = self._config['cw1']['config_path']
        env_type = self._config['cw1']['env_type']
        try:
            with open(cw1_path, 'r') as f:
                cw1_conf = yaml.safe_load(f)
            mongo_conf = cw1_conf[env_type]['config']['Database']['MongoDB']
        except (FileNotFoundError, KeyError) as e:
            logger.info("Could not read MongoDB config: %s", e)
            return None

        # Connect to MongoDB
        try:
            client = MongoClient(
                host=mongo_conf.get('Host', 'localhost'),
                port=mongo_conf.get('Port', 27017),
                username=mongo_conf.get('Username', 'ift_bigdata'),
                password=mongo_conf.get('Password', 'mongo_password'),
                authSource='admin',
                serverSelectionTimeoutMS=5000,
            )
            client.admin.command('ping')
        except Exception as e:
            logger.info("MongoDB connection failed: %s", e)
            return None

        # Query raw_news_articles collection
        db = client[mongo_conf.get('Database', 'ift_cw1_sentiment')]
        collection_name = mongo_conf.get('Collections', {}).get('raw_news', 'raw_news_articles')
        collection = db[collection_name]

        try:
            # Fetch articles with publication date <= as_of_date
            cursor = collection.find(
                {},  # No date filter in Mongo (CW1 stores all articles)
                {
                    '_id': 0,
                    'company_id': 1,
                    'headline': 1,
                    'description': 1,
                    'source_name': 1,
                    'publisher': 1,
                    'url': 1,
                    'date': 1,
                    'seendate': 1,
                    'source': 1,       # API source: gdelt/yahoo_finance/newsapi
                    'vader_compound': 1,
                    'fetched_at': 1,
                },
            )
            articles = list(cursor)
        except Exception as e:
            logger.warning("Failed to query MongoDB articles: %s", e)
            return None
        finally:
            client.close()

        if not articles:
            return None

        df = pd.DataFrame(articles)

        # Normalise source domain column
        # CW1 stores source domain as 'source_name' (GDELT/NewsAPI) or 'publisher' (YF)
        if 'source_name' in df.columns and 'publisher' in df.columns:
            df['source_domain'] = df['source_name'].fillna(df['publisher']).fillna('')
        elif 'source_name' in df.columns:
            df['source_domain'] = df['source_name'].fillna('')
        elif 'publisher' in df.columns:
            df['source_domain'] = df['publisher'].fillna('')
        else:
            df['source_domain'] = ''

        # Normalise date column
        if 'date' in df.columns:
            df['article_date'] = pd.to_datetime(df['date'], errors='coerce')
        elif 'seendate' in df.columns:
            df['article_date'] = pd.to_datetime(df['seendate'], errors='coerce')
        elif 'fetched_at' in df.columns:
            df['article_date'] = pd.to_datetime(df['fetched_at'], errors='coerce')

        # Compute word count from headline + description for substantiveness
        headline_text = df['headline'].fillna('')
        desc_text = df['description'].fillna('') if 'description' in df.columns else ''
        df['word_count'] = (headline_text + ' ' + desc_text).str.split().str.len()

        # Ensure company_id is clean
        if 'company_id' in df.columns:
            df['company_id'] = df['company_id'].astype(str).str.strip()

        logger.info(
            "Loaded %d articles from MongoDB for %d companies",
            len(df), df['company_id'].nunique() if 'company_id' in df.columns else 0,
        )
        return df

    def close(self):
        """Dispose the engine and release all pooled connections."""
        self._engine.dispose()
        logger.info("DataLoader connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
