"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Stationary bootstrap confidence intervals
Project : CW2 - Value-Sentiment Investment Strategy

Uses Politis & Romano (1994) stationary bootstrap to compute
95% confidence intervals for the Sharpe ratio and other metrics.
2,500 replications.

This addresses serial dependence in return data that invalidates
naive i.i.d. bootstrap.

Ref: Part A §A8 — Test 4
Academic: Politis & Romano (1994) — Stationary bootstrap, JASA.
"""

import logging

import numpy as np
import pandas as pd

from modules.analytics.performance import TRADING_DAYS_PER_YEAR

logger = logging.getLogger(__name__)


def stationary_bootstrap_sharpe(
    returns: pd.Series,
    n_reps: int = 2500,
    block_length: float = 10.0,
    risk_free_rate: float = 0.04,
    confidence: float = 0.95,
    random_seed: int = 42,
) -> dict:
    """Compute bootstrap confidence intervals for the Sharpe ratio.

    Uses the stationary bootstrap of Politis & Romano (1994), which
    generates random block lengths from a geometric distribution,
    preserving time-series dependence structure.

    :param returns: Daily portfolio return series
    :type returns: pd.Series
    :param n_reps: Number of bootstrap replications
    :type n_reps: int
    :param block_length: Expected block length (geometric parameter)
    :type block_length: float
    :param risk_free_rate: Annual risk-free rate
    :type risk_free_rate: float
    :param confidence: Confidence level for intervals (e.g. 0.95)
    :type confidence: float
    :param random_seed: Random seed for reproducibility
    :type random_seed: int
    :returns: Dict with point estimate, lower/upper CIs, bootstrap Sharpes
    :rtype: dict
    """
    rng = np.random.RandomState(random_seed)
    returns_arr = returns.dropna().values
    n = len(returns_arr)

    if n < 30:
        logger.warning("Too few observations (%d) for bootstrap", n)
        return _empty_bootstrap_result()

    rf_daily = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    p = 1.0 / block_length  # Probability of starting new block

    bootstrap_sharpes = np.zeros(n_reps)

    for rep in range(n_reps):
        # Generate stationary bootstrap sample
        sample = _stationary_bootstrap_sample(returns_arr, n, p, rng)

        # Compute Sharpe on bootstrap sample
        excess = sample - rf_daily
        mean_excess = excess.mean()
        std_excess = sample.std()
        if std_excess > 0:
            bootstrap_sharpes[rep] = mean_excess / std_excess * np.sqrt(TRADING_DAYS_PER_YEAR)
        else:
            bootstrap_sharpes[rep] = 0.0

    # Point estimate
    excess_orig = returns_arr - rf_daily
    point_sharpe = excess_orig.mean() / returns_arr.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Confidence intervals
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_sharpes, alpha / 2 * 100)
    upper = np.percentile(bootstrap_sharpes, (1 - alpha / 2) * 100)

    # Probability that Sharpe > 0
    prob_positive = (bootstrap_sharpes > 0).mean()

    result = {
        'point_estimate': point_sharpe,
        'ci_lower': lower,
        'ci_upper': upper,
        'confidence_level': confidence,
        'prob_sharpe_positive': prob_positive,
        'bootstrap_mean': bootstrap_sharpes.mean(),
        'bootstrap_std': bootstrap_sharpes.std(),
        'n_reps': n_reps,
        'block_length': block_length,
        'bootstrap_sharpes': bootstrap_sharpes,
    }

    logger.info(
        "Bootstrap Sharpe: %.3f [%.3f, %.3f] (%.0f%% CI), P(Sharpe>0)=%.1f%%",
        point_sharpe, lower, upper, confidence * 100, prob_positive * 100,
    )
    return result


def _stationary_bootstrap_sample(
    data: np.ndarray,
    n: int,
    p: float,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Generate a single stationary bootstrap sample.

    Each observation either continues the current block (prob 1-p)
    or jumps to a random position (prob p), creating random-length
    blocks from a geometric distribution.

    :param data: Original data array
    :type data: np.ndarray
    :param n: Sample size
    :type n: int
    :param p: Block-break probability (1/expected_block_length)
    :type p: float
    :param rng: Random number generator
    :type rng: np.random.RandomState
    :returns: Bootstrap sample array
    :rtype: np.ndarray
    """
    sample = np.zeros(n)
    idx = rng.randint(0, n)

    for i in range(n):
        sample[i] = data[idx]
        # With probability p, jump to a new random position
        if rng.random() < p:
            idx = rng.randint(0, n)
        else:
            idx = (idx + 1) % n  # Wrap around

    return sample


def _empty_bootstrap_result() -> dict:
    """Return empty bootstrap result dict."""
    return {
        'point_estimate': 0.0,
        'ci_lower': 0.0,
        'ci_upper': 0.0,
        'confidence_level': 0.95,
        'prob_sharpe_positive': 0.0,
        'bootstrap_mean': 0.0,
        'bootstrap_std': 0.0,
        'n_reps': 0,
        'block_length': 0.0,
        'bootstrap_sharpes': np.array([]),
    }
