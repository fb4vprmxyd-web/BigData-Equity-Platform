"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Portfolio construction — screen, weight, constrain
Project : CW2 - Value-Sentiment Investment Strategy

Orchestrates the full portfolio construction pipeline:
  1. Screen: select stocks flagged invest_decision = True
  2. Weight: apply chosen weighting scheme (EW, score, inv-vol)
  3. Constrain: enforce position and sector limits
  4. Buffer: apply buy/sell buffer to reduce turnover

Implements 4 portfolio variants as required by the task:
  A: Value-Only (top 20% sector-rel value, D/E < 2)
  B: Sentiment-Only (top 20% quality-weighted sentiment)
  C: Combined (invest_decision = True from composite)
  D: Benchmark (S&P 500 / MSCI World)

Ref: Part A §A5
"""

import logging

import numpy as np
import pandas as pd

from modules.portfolio.constraints import apply_constraints
from modules.portfolio.weighting import (
    compute_equal_weight,
    compute_inverse_volatility_weight,
    compute_score_weight,
)

logger = logging.getLogger(__name__)


class PortfolioConstructor:
    """Screen, weight, and apply constraints to build portfolio.

    :param config: Parsed backtest_config.yaml dict
    :type config: dict
    """

    def __init__(self, config: dict):
        self._scheme = config['portfolio']['weighting_scheme']
        self._max_position = config['portfolio']['max_position_weight']
        self._max_sector = config['portfolio']['max_sector_weight']
        self._min_holdings = config['portfolio']['min_holdings']
        self._target_holdings = config['portfolio']['target_holdings']
        self._buffer_buy = config['portfolio']['buffer_buy_pctl']
        self._buffer_sell = config['portfolio']['buffer_sell_pctl']

    def construct(
        self,
        signals: pd.DataFrame,
        sector_map: dict,
        prices: pd.DataFrame = None,
        current_weights: pd.Series = None,
        scheme_override: str = None,
    ) -> pd.Series:
        """Build constrained portfolio weights from scored signals.

        :param signals: DataFrame with company_id, composite_score,
                        invest_decision, value_score, etc.
        :type signals: pd.DataFrame
        :param sector_map: Dict mapping ticker → GICS sector
        :type sector_map: dict
        :param prices: Price DataFrame (needed for inverse-vol)
        :type prices: pd.DataFrame or None
        :param current_weights: Current portfolio weights (for buffer rule)
        :type current_weights: pd.Series or None
        :param scheme_override: Override weighting scheme for variant testing
        :type scheme_override: str or None
        :returns: Portfolio weights indexed by ticker, summing to 1.0
        :rtype: pd.Series
        """
        scheme = scheme_override or self._scheme

        # --- Step 1: Screen ---
        selected = self._screen(signals, current_weights)

        if len(selected) == 0:
            logger.warning("No stocks selected — returning empty portfolio")
            return pd.Series(dtype=float)

        tickers = selected['company_id'].tolist()

        # --- Step 2: Weight ---
        weights = self._weight(tickers, selected, scheme, prices)

        # --- Step 3: Constrain ---
        weights = apply_constraints(
            weights,
            sector_map,
            max_position=self._max_position,
            max_sector=self._max_sector,
            min_holdings=self._min_holdings,
        )

        logger.info(
            "Portfolio constructed: %d holdings, scheme=%s, sum=%.6f",
            (weights > 1e-8).sum(), scheme, weights.sum(),
        )
        return weights

    def construct_value_only(
        self,
        signals: pd.DataFrame,
        sector_map: dict,
    ) -> pd.Series:
        """Build value-only portfolio (Portfolio A).

        Selects top 20% by value_score with D/E < 2.0, equal-weighted.

        :param signals: Scored signals DataFrame
        :type signals: pd.DataFrame
        :param sector_map: Sector mapping
        :type sector_map: dict
        :returns: Equal-weight portfolio of value-selected stocks
        :rtype: pd.Series
        """
        eligible = signals[
            (signals['value_score'] > 0) &
            ((signals['debt_equity'].isna()) | (signals['debt_equity'] <= 2.0))
        ].copy()

        if len(eligible) == 0:
            return pd.Series(dtype=float)

        n_select = max(self._min_holdings, int(len(eligible) * 0.20))
        top = eligible.nlargest(n_select, 'value_score')
        weights = compute_equal_weight(top['company_id'].tolist())
        return apply_constraints(weights, sector_map, self._max_position, self._max_sector)

    def construct_sentiment_only(
        self,
        signals: pd.DataFrame,
        sector_map: dict,
    ) -> pd.Series:
        """Build sentiment-only portfolio (Portfolio B).

        Selects top 20% by sentiment_score with confidence > 0.3,
        equal-weighted.

        :param signals: Scored signals DataFrame
        :type signals: pd.DataFrame
        :param sector_map: Sector mapping
        :type sector_map: dict
        :returns: Equal-weight portfolio of sentiment-selected stocks
        :rtype: pd.Series
        """
        eligible = signals[
            signals['confidence'].fillna(0) > 0.3
        ].copy()

        if len(eligible) == 0:
            return pd.Series(dtype=float)

        n_select = max(self._min_holdings, int(len(eligible) * 0.20))
        top = eligible.nlargest(n_select, 'sentiment_score')
        weights = compute_equal_weight(top['company_id'].tolist())
        return apply_constraints(weights, sector_map, self._max_position, self._max_sector)

    def _screen(
        self,
        signals: pd.DataFrame,
        current_weights: pd.Series = None,
    ) -> pd.DataFrame:
        """Screen stocks for portfolio inclusion.

        Uses invest_decision flag from signal combiner.
        Applies buy/sell buffer to reduce unnecessary turnover:
        - New buys: must be above 60th percentile
        - Existing holds: keep if above 40th percentile

        :param signals: Scored signals with invest_decision column
        :type signals: pd.DataFrame
        :param current_weights: Current holdings (for buffer)
        :type current_weights: pd.Series or None
        :returns: Filtered DataFrame of selected stocks
        :rtype: pd.DataFrame
        """
        if current_weights is not None and len(current_weights) > 0:
            # Buffer rule: existing holdings get more lenient threshold
            current_tickers = set(current_weights[current_weights > 0].index)
            is_current = signals['company_id'].isin(current_tickers)

            # Current holdings: keep if in top 60% (sell below 40th pctl)
            # New buys: only if invest_decision is True (top 20%)
            selected = signals[
                (signals['invest_decision']) | (is_current & signals['is_eligible'])
            ]
        else:
            selected = signals[signals['invest_decision']]

        logger.info("Screening: %d stocks selected for portfolio", len(selected))
        return selected

    def _weight(
        self,
        tickers: list,
        selected: pd.DataFrame,
        scheme: str,
        prices: pd.DataFrame = None,
    ) -> pd.Series:
        """Apply chosen weighting scheme to selected stocks.

        :param tickers: List of selected ticker symbols
        :type tickers: list
        :param selected: DataFrame with composite scores for score-weighting
        :type selected: pd.DataFrame
        :param scheme: Weighting scheme name
        :type scheme: str
        :param prices: Price data (needed for inverse-volatility)
        :type prices: pd.DataFrame or None
        :returns: Raw (unconstrained) weights
        :rtype: pd.Series
        """
        if scheme == 'equal_weight':
            return compute_equal_weight(tickers)

        elif scheme == 'score_weight':
            scores = selected.set_index('company_id')['composite_score']
            return compute_score_weight(tickers, scores)

        elif scheme == 'inverse_volatility':
            if prices is None:
                logger.warning("No price data for inv-vol — falling back to equal-weight")
                return compute_equal_weight(tickers)
            return compute_inverse_volatility_weight(tickers, prices)

        else:
            logger.warning("Unknown weighting scheme '%s' — using equal-weight", scheme)
            return compute_equal_weight(tickers)
