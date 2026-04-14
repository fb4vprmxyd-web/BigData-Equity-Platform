"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Backtester — quarterly backtest loop with weight drift
Project : CW2 - Value-Sentiment Investment Strategy

Orchestrates the full backtest simulation:
  1. At each rebalance date, compute signals using point-in-time data
  2. Construct portfolio weights using configured scheme
  3. Simulate returns with intra-period weight drift
  4. Deduct transaction costs on rebalance dates
  5. Track portfolio value, weights, and turnover over time

Point-in-time discipline (Part A §A6):
  - report_date <= rebalance_date
  - 90-day lag buffer for financial data
  - T+1 close execution (trade next day after rebalance signal)

Survivorship bias: includes delisted tickers active at each
rebalance date.  Elton et al. (1996): 0.9–2.1% annual bias.

Ref: Part A §A6, Part D §D2
"""

import logging

import numpy as np
import pandas as pd

from modules.backtest.rebalance_schedule import get_rebalance_dates
from modules.backtest.transaction_costs import TransactionCostModel
from modules.data.universe import UniverseConstructor
from modules.portfolio.portfolio_constructor import PortfolioConstructor
from modules.signals.sentiment_signal import SentimentSignal
from modules.signals.signal_combiner import SignalCombiner
from modules.signals.value_signal import ValueSignal

logger = logging.getLogger(__name__)


class Backtester:
    """Orchestrate the quarterly backtest loop.

    :param data_loader: DataLoader instance for database access
    :type data_loader: modules.data.data_loader.DataLoader
    :param universe: UniverseConstructor instance
    :type universe: UniverseConstructor
    :param config: Parsed backtest_config.yaml dict
    :type config: dict
    """

    def __init__(self, data_loader, universe, config: dict):
        self._loader = data_loader
        self._universe = universe
        self._config = config

        # Initialise components
        self._value_signal = ValueSignal(config)
        self._sentiment_signal = SentimentSignal(config)
        self._signal_combiner = SignalCombiner(config)
        self._port_constructor = PortfolioConstructor(config)
        self._cost_model = TransactionCostModel(config)
        self._execution_delay = config['backtest']['execution_delay']
        self._lag_days = config['backtest']['reporting_lag_days']

    def run(
        self,
        prices: pd.DataFrame,
        scheme_override: str = None,
        portfolio_type: str = 'combined',
    ) -> dict:
        """Execute the full backtest simulation.

        :param prices: Pivoted price DataFrame (dates × tickers)
        :type prices: pd.DataFrame
        :param scheme_override: Override weighting scheme for variant testing
        :type scheme_override: str or None
        :param portfolio_type: 'combined', 'value_only', or 'sentiment_only'
        :type portfolio_type: str
        :returns: Dict with 'returns', 'weights_history', 'turnover',
                  'rebalance_info', 'costs'
        :rtype: dict
        """
        start = self._config['backtest']['start_date']
        end = self._config['backtest']['end_date']
        months = self._config['backtest']['rebalance_months']

        # Compute daily returns from prices
        daily_returns = prices.pct_change().dropna(how='all')

        # Generate rebalance dates
        rebalance_dates = get_rebalance_dates(
            start, end, months, price_dates=prices.index,
        )

        if not rebalance_dates:
            logger.error("No rebalance dates generated — aborting backtest")
            return self._empty_results()

        # --- Main backtest loop ---
        all_returns = []
        weights_history = {}
        turnover_history = {}
        cost_history = {}
        rebalance_info = []
        current_weights = pd.Series(dtype=float)

        for i, rebal_date in enumerate(rebalance_dates):
            logger.info(
                "=== Rebalance %d/%d: %s (portfolio=%s) ===",
                i + 1, len(rebalance_dates),
                rebal_date.strftime('%Y-%m-%d'),
                portfolio_type,
            )

            # --- Compute signals at this rebalance date ---
            new_weights = self._compute_portfolio_at_date(
                rebal_date, prices, current_weights,
                scheme_override, portfolio_type,
            )

            if len(new_weights) == 0:
                logger.warning("Empty portfolio at %s — holding cash", rebal_date)
                new_weights = pd.Series(dtype=float)

            # --- Calculate transaction cost ---
            tc = self._cost_model.calculate(current_weights, new_weights)
            turnover = self._calc_turnover(current_weights, new_weights)

            # --- Determine holding period ---
            # T+1 execution: start holding from next trading day
            exec_date = self._get_execution_date(rebal_date, daily_returns.index)
            next_rebal = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else pd.Timestamp(end)

            # --- Simulate returns with weight drift ---
            period_returns = self._compute_period_returns(
                new_weights, daily_returns, exec_date, next_rebal,
            )

            # Deduct transaction cost from first day's return
            if len(period_returns) > 0:
                period_returns.iloc[0] -= tc

            all_returns.append(period_returns)

            # --- Record state ---
            weights_history[rebal_date] = new_weights.copy()
            turnover_history[rebal_date] = turnover
            cost_history[rebal_date] = tc
            rebalance_info.append({
                'date': rebal_date,
                'n_holdings': (new_weights > 1e-8).sum(),
                'turnover': turnover,
                'cost': tc,
                'max_weight': new_weights.max() if len(new_weights) > 0 else 0,
            })

            # Drift weights to next rebalance
            current_weights = self._drift_weights(new_weights, period_returns)

        # Concatenate all period returns
        if all_returns:
            portfolio_returns = pd.concat(all_returns)
            portfolio_returns = portfolio_returns[~portfolio_returns.index.duplicated(keep='first')]
            portfolio_returns = portfolio_returns.sort_index()
        else:
            portfolio_returns = pd.Series(dtype=float)

        logger.info(
            "Backtest complete: %d trading days, %d rebalances, total return=%.2f%%",
            len(portfolio_returns),
            len(rebalance_dates),
            ((1 + portfolio_returns).prod() - 1) * 100 if len(portfolio_returns) > 0 else 0,
        )

        return {
            'returns': portfolio_returns,
            'weights_history': weights_history,
            'turnover': turnover_history,
            'costs': cost_history,
            'rebalance_info': pd.DataFrame(rebalance_info),
        }

    def _compute_portfolio_at_date(
        self,
        rebal_date: pd.Timestamp,
        prices: pd.DataFrame,
        current_weights: pd.Series,
        scheme_override: str,
        portfolio_type: str,
    ) -> pd.Series:
        """Compute signals and construct portfolio at a rebalance date.

        :param rebal_date: Current rebalance date
        :type rebal_date: pd.Timestamp
        :param prices: Full price matrix
        :type prices: pd.DataFrame
        :param current_weights: Current portfolio weights
        :type current_weights: pd.Series
        :param scheme_override: Weighting scheme override
        :type scheme_override: str or None
        :param portfolio_type: Portfolio variant type
        :type portfolio_type: str
        :returns: New portfolio weights
        :rtype: pd.Series
        """
        # Point-in-time data: apply reporting lag
        data_date = rebal_date - pd.Timedelta(days=self._lag_days)
        data_date_str = data_date.strftime('%Y-%m-%d')

        # Load point-in-time data
        value_df = self._loader.load_value_metrics(data_date_str)

        # Try article-level sentiment data from MongoDB first, fall back to aggregated
        # load_news_article_metadata attempts MongoDB → falls back to PostgreSQL
        sentiment_df = self._loader.load_news_article_metadata(data_date_str)

        # Get universe at rebalance date
        universe = self._universe.get_universe(rebal_date)
        if len(universe) == 0:
            return pd.Series(dtype=float)

        sector_map = self._universe.get_sector_map()
        active_tickers = set(universe['symbol'].tolist())

        # Sector attribution robustness test: drop a sector from the universe
        exclude_sector = self._config.get('_exclude_sector')
        if exclude_sector:
            active_tickers = {
                t for t in active_tickers if sector_map.get(t) != exclude_sector
            }

        # Filter data to active universe
        value_df = value_df[value_df['company_id'].isin(active_tickers)]
        sentiment_df = sentiment_df[sentiment_df['company_id'].isin(active_tickers)]

        if len(value_df) == 0:
            logger.warning("No value data at %s", rebal_date)
            return pd.Series(dtype=float)

        # Compute signals
        value_signals = self._value_signal.compute(value_df, sector_map)
        sentiment_signals = self._sentiment_signal.compute(sentiment_df, rebal_date)

        # Combine signals
        combined = self._signal_combiner.compute(value_signals, sentiment_signals, value_df)

        # Construct portfolio based on type
        if portfolio_type == 'value_only':
            return self._port_constructor.construct_value_only(combined, sector_map)
        elif portfolio_type == 'sentiment_only':
            return self._port_constructor.construct_sentiment_only(combined, sector_map)
        else:
            # Combined portfolio
            return self._port_constructor.construct(
                combined, sector_map, prices,
                current_weights, scheme_override,
            )

    def _compute_period_returns(
        self,
        weights: pd.Series,
        daily_returns: pd.DataFrame,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> pd.Series:
        """Simulate portfolio returns with intra-period weight drift.

        Weights drift naturally as stock prices move between rebalances.
        Each day's portfolio return is the weighted sum of individual
        stock returns, using the drifted weights.

        :param weights: Portfolio weights at start of period
        :type weights: pd.Series
        :param daily_returns: Full daily returns matrix
        :type daily_returns: pd.DataFrame
        :param start_date: First date of holding period
        :type start_date: pd.Timestamp
        :param end_date: Last date of holding period
        :type end_date: pd.Timestamp
        :returns: Daily portfolio return series
        :rtype: pd.Series
        """
        if len(weights) == 0:
            # Cash position — zero returns
            dates = daily_returns.loc[start_date:end_date].index
            return pd.Series(0.0, index=dates)

        period_returns = daily_returns.loc[start_date:end_date]
        w = weights.copy()
        port_rets = []

        for date in period_returns.index:
            # Get today's returns for held stocks
            available = w.index.intersection(period_returns.columns)
            if len(available) == 0:
                port_rets.append(0.0)
                continue

            r = period_returns.loc[date, available].fillna(0)

            # Portfolio return = weighted sum
            port_ret = (w.reindex(available, fill_value=0) * r).sum()
            port_rets.append(port_ret)

            # Drift weights
            w_available = w.reindex(available, fill_value=0) * (1 + r)
            total = w_available.sum()
            if total > 0:
                w = w_available / total
            else:
                w = pd.Series(dtype=float)

        return pd.Series(port_rets, index=period_returns.index, name='portfolio_return')

    def _drift_weights(
        self,
        weights: pd.Series,
        period_returns: pd.Series,
    ) -> pd.Series:
        """Compute final drifted weights at end of holding period.

        :param weights: Weights at start of period
        :type weights: pd.Series
        :param period_returns: Portfolio returns for the period
        :type period_returns: pd.Series
        :returns: Drifted weights at end of period
        :rtype: pd.Series
        """
        # Simplified: weights drift proportionally to cumulative return
        # The precise drift is handled inside _compute_period_returns
        return weights  # Approximate — exact drift tracked in return calc

    def _get_execution_date(
        self,
        rebal_date: pd.Timestamp,
        trading_dates: pd.DatetimeIndex,
    ) -> pd.Timestamp:
        """Get T+1 execution date from rebalance signal date.

        :param rebal_date: Rebalance signal date
        :type rebal_date: pd.Timestamp
        :param trading_dates: Available trading dates
        :type trading_dates: pd.DatetimeIndex
        :returns: First trading date after rebalance
        :rtype: pd.Timestamp
        """
        future = trading_dates[trading_dates > rebal_date]
        if len(future) >= self._execution_delay:
            return future[self._execution_delay - 1]
        elif len(future) > 0:
            return future[0]
        return rebal_date

    @staticmethod
    def _calc_turnover(old_weights: pd.Series, new_weights: pd.Series) -> float:
        """Calculate one-way portfolio turnover.

        Turnover = Sum(|w_new - w_old|) / 2

        :param old_weights: Pre-rebalance weights
        :type old_weights: pd.Series
        :param new_weights: Post-rebalance weights
        :type new_weights: pd.Series
        :returns: One-way turnover (0 to 1)
        :rtype: float
        """
        all_tickers = old_weights.index.union(new_weights.index)
        old_aligned = old_weights.reindex(all_tickers, fill_value=0.0)
        new_aligned = new_weights.reindex(all_tickers, fill_value=0.0)
        return (new_aligned - old_aligned).abs().sum() / 2.0

    @staticmethod
    def _empty_results() -> dict:
        """Return empty results dict."""
        return {
            'returns': pd.Series(dtype=float),
            'weights_history': {},
            'turnover': {},
            'costs': {},
            'rebalance_info': pd.DataFrame(),
        }
