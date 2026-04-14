"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Benchmark data retrieval and processing
Project : CW2 - Value-Sentiment Investment Strategy

Downloads benchmark price series from Yahoo Finance for performance
comparison.  Supports S&P 500 (primary) and MSCI World Value ETF
(secondary).

Ref: Part A §A7.3 — Benchmark Selection
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class BenchmarkLoader:
    """Download and process benchmark return series.

    :param config: Parsed backtest_config.yaml dict
    :type config: dict
    """

    def __init__(self, config: dict):
        self._config = config
        self._primary_ticker = config['benchmark']['primary']
        self._secondary_ticker = config['benchmark']['secondary']

    def load_benchmark_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> pd.Series:
        """Download adjusted close prices for a benchmark index.

        :param ticker: Yahoo Finance ticker (e.g. '^GSPC')
        :type ticker: str
        :param start_date: Start date (YYYY-MM-DD)
        :type start_date: str
        :param end_date: End date (YYYY-MM-DD)
        :type end_date: str
        :returns: Series of adjusted close prices indexed by date
        :rtype: pd.Series
        """
        logger.info("Downloading benchmark %s from %s to %s", ticker, start_date, end_date)
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if data.empty:
            logger.warning("No benchmark data returned for %s", ticker)
            return pd.Series(dtype=float)

        # Handle multi-level columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            prices = data['Close'].iloc[:, 0]
        else:
            prices = data['Close']

        prices.index = pd.to_datetime(prices.index)
        prices.index.name = 'date'
        prices.name = ticker
        logger.info("Loaded %d benchmark prices for %s", len(prices), ticker)
        return prices

    def load_primary(self, start_date: str, end_date: str) -> pd.Series:
        """Load S&P 500 benchmark prices.

        :param start_date: Start date (YYYY-MM-DD)
        :type start_date: str
        :param end_date: End date (YYYY-MM-DD)
        :type end_date: str
        :returns: S&P 500 adjusted close prices
        :rtype: pd.Series
        """
        return self.load_benchmark_prices(self._primary_ticker, start_date, end_date)

    def load_secondary(self, start_date: str, end_date: str) -> pd.Series:
        """Load MSCI World Value ETF benchmark prices.

        :param start_date: Start date (YYYY-MM-DD)
        :type start_date: str
        :param end_date: End date (YYYY-MM-DD)
        :type end_date: str
        :returns: MSCI World Value ETF adjusted close prices
        :rtype: pd.Series
        """
        return self.load_benchmark_prices(self._secondary_ticker, start_date, end_date)

    def compute_benchmark_returns(self, prices: pd.Series) -> pd.Series:
        """Convert benchmark prices to daily simple returns.

        :param prices: Adjusted close price series
        :type prices: pd.Series
        :returns: Daily simple return series
        :rtype: pd.Series
        """
        returns = prices.pct_change().dropna()
        logger.info("Computed %d daily benchmark returns", len(returns))
        return returns

    def compute_equal_weight_universe_returns(
        self,
        prices_df: pd.DataFrame,
        universe_tickers: list,
    ) -> pd.Series:
        """Compute equal-weight returns across the full universe.

        Used as a third benchmark to isolate the value of stock
        selection vs holding the entire universe.

        :param prices_df: Full price matrix (dates × tickers)
        :type prices_df: pd.DataFrame
        :param universe_tickers: List of tickers in the universe
        :type universe_tickers: list
        :returns: Equal-weight daily returns series
        :rtype: pd.Series
        """
        available = [t for t in universe_tickers if t in prices_df.columns]
        subset = prices_df[available]
        daily_returns = subset.pct_change().dropna(how='all')

        # Equal-weight: average return across all available stocks each day
        ew_returns = daily_returns.mean(axis=1)
        ew_returns.name = 'EW_Universe'
        logger.info(
            "Computed equal-weight universe returns: %d days, %d avg stocks",
            len(ew_returns), int(daily_returns.notna().sum(axis=1).mean()),
        )
        return ew_returns
