"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Risk analysis — VaR, CVaR, Fama-French regression
Project : CW2 - Value-Sentiment Investment Strategy

Computes risk metrics:
  - Value at Risk (VaR) — historical 95% and 99%
  - Conditional VaR (CVaR / Expected Shortfall) — coherent risk measure
  - Fama-French 5-factor regression with Newey-West standard errors

Ref: Part A §A7.1, §A7.2
Academic: Newey & West (1987), Fama & French (2015)
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Compute historical Value at Risk.

    :param returns: Daily return series
    :type returns: pd.Series
    :param confidence: Confidence level (e.g. 0.95)
    :type confidence: float
    :returns: VaR (negative number representing loss threshold)
    :rtype: float
    """
    if len(returns) == 0:
        return 0.0
    alpha = 1 - confidence
    var = np.percentile(returns.dropna(), alpha * 100)
    return var


def compute_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """Compute Conditional Value at Risk (Expected Shortfall).

    CVaR is the mean of returns below the VaR threshold.
    It is a coherent risk measure, unlike VaR.

    :param returns: Daily return series
    :type returns: pd.Series
    :param confidence: Confidence level (e.g. 0.95)
    :type confidence: float
    :returns: CVaR (negative number)
    :rtype: float
    """
    if len(returns) == 0:
        return 0.0
    var = compute_var(returns, confidence)
    tail = returns[returns <= var]
    return tail.mean() if len(tail) > 0 else var


def compute_fama_french_regression(
    portfolio_returns: pd.Series,
    ff_factors: pd.DataFrame = None,
    n_lags: int = 6,
) -> dict:
    """Run Fama-French 5-factor regression with Newey-West standard errors.

    Rp - Rf = alpha + b_MKT(Rm-Rf) + b_SMB(SMB) + b_HML(HML)
            + b_RMW(RMW) + b_CMA(CMA) + epsilon

    Uses statsmodels OLS with Newey-West HAC covariance estimation
    (6 lags per Newey & West 1987).

    :param portfolio_returns: Daily portfolio excess returns
    :type portfolio_returns: pd.Series
    :param ff_factors: Fama-French factor data with columns
                       [Mkt-RF, SMB, HML, RMW, CMA, RF]
    :type ff_factors: pd.DataFrame or None
    :param n_lags: Number of Newey-West lags
    :type n_lags: int
    :returns: Dict with alpha, betas, t-stats, R-squared
    :rtype: dict
    """
    try:
        import statsmodels.api as sm
    except ImportError:
        logger.warning("statsmodels not available — skipping FF regression")
        return _empty_ff_result()

    if ff_factors is None:
        logger.info("No Fama-French factor data provided — attempting download")
        ff_factors = _download_ff_factors(portfolio_returns.index)

    if ff_factors is None or len(ff_factors) == 0:
        logger.warning("Cannot load FF factors — returning empty regression")
        return _empty_ff_result()

    # Align dates
    common_dates = portfolio_returns.index.intersection(ff_factors.index)
    if len(common_dates) < 30:
        logger.warning("Too few common dates (%d) for FF regression", len(common_dates))
        return _empty_ff_result()

    y = portfolio_returns.loc[common_dates]

    # Subtract risk-free rate if present
    if 'RF' in ff_factors.columns:
        rf = ff_factors.loc[common_dates, 'RF']
        y = y - rf

    # Factor columns
    factor_cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']
    available_factors = [c for c in factor_cols if c in ff_factors.columns]
    X = ff_factors.loc[common_dates, available_factors]
    X = sm.add_constant(X)

    # Drop any NaN rows
    valid = y.notna() & X.notna().all(axis=1)
    y = y[valid]
    X = X[valid]

    if len(y) < 30:
        return _empty_ff_result()

    # OLS with Newey-West HAC standard errors
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': n_lags})

    result = {
        'alpha': model.params.get('const', 0),
        'alpha_tstat': model.tvalues.get('const', 0),
        'alpha_pvalue': model.pvalues.get('const', 0),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'n_observations': int(model.nobs),
        'betas': {},
        'tstats': {},
        'pvalues': {},
    }

    for factor in available_factors:
        result['betas'][factor] = model.params.get(factor, 0)
        result['tstats'][factor] = model.tvalues.get(factor, 0)
        result['pvalues'][factor] = model.pvalues.get(factor, 0)

    # Annualise alpha (daily to annual)
    result['alpha_annualised'] = result['alpha'] * 252

    logger.info(
        "FF regression: alpha=%.4f (t=%.2f), R²=%.3f, n=%d",
        result['alpha_annualised'], result['alpha_tstat'],
        result['r_squared'], result['n_observations'],
    )
    return result


def _download_ff_factors(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Attempt to download Fama-French 5-factor data from Kenneth French's library.

    :param dates: Date range for factor data
    :type dates: pd.DatetimeIndex
    :returns: DataFrame with daily factor returns or None
    :rtype: pd.DataFrame or None
    """
    try:
        import pandas_datareader.data as web
        ff = web.DataReader('F-F_Research_Data_5_Factors_2x3_daily', 'famafrench',
                            start=dates.min(), end=dates.max())[0]
        ff = ff / 100  # Convert from percentage to decimal
        ff.index = pd.to_datetime(ff.index)
        return ff
    except Exception as e:
        logger.warning("Could not download FF factors: %s", e)

    # Fallback: try to create synthetic market factor from S&P 500
    try:
        import yfinance as yf
        spy = yf.download('^GSPC', start=dates.min(), end=dates.max(), progress=False, auto_adjust=True)
        if isinstance(spy.columns, pd.MultiIndex):
            mkt = spy['Close'].iloc[:, 0].pct_change().dropna()
        else:
            mkt = spy['Close'].pct_change().dropna()
        ff = pd.DataFrame({'Mkt-RF': mkt, 'RF': 0.0004})  # ~10% annual rf proxy
        ff.index = pd.to_datetime(ff.index)
        logger.info("Using synthetic market factor from S&P 500")
        return ff
    except Exception as e:
        logger.warning("Could not create synthetic factor: %s", e)
        return None


def _empty_ff_result() -> dict:
    """Return empty Fama-French regression result."""
    return {
        'alpha': 0.0,
        'alpha_tstat': 0.0,
        'alpha_pvalue': 1.0,
        'alpha_annualised': 0.0,
        'r_squared': 0.0,
        'adj_r_squared': 0.0,
        'n_observations': 0,
        'betas': {},
        'tstats': {},
        'pvalues': {},
    }
