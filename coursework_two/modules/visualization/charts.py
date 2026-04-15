"""
UCL -- Institute of Finance & Technology
Author  : Team 09
Topic   : Visualization — all 12 charts for report
Project : CW2 - Value-Sentiment Investment Strategy

Generates all required charts from Part C §C1:
  1. Cumulative return (4 portfolios + benchmark, log scale)
  2. Drawdown underwater chart
  3. Monthly returns heatmap
  4. Rolling 12-month Sharpe ratio
  5. Weight sensitivity heatmap
  6. Fama-French factor loadings with CIs
  7. Sector allocation (portfolio vs benchmark)
  8. Random portfolio Sharpe histogram
  9. Screening threshold sensitivity
  10. Turnover per rebalance date
  11. OLD vs NEW value score sector concentration
  12. Pipeline flowchart (CW1→CW2)

Ref: Part C §C1
"""

import logging
import os

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# Consistent styling
STYLE_PARAMS = {
    'figure.figsize': (12, 6),
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'legend.fontsize': 10,
    'figure.dpi': 150,
}
plt.rcParams.update(STYLE_PARAMS)

COLORS = {
    'combined': '#2196F3',
    'value_only': '#4CAF50',
    'sentiment_only': '#FF9800',
    'benchmark': '#9E9E9E',
    'ew_universe': '#BDBDBD',
}


def plot_cumulative_returns(
    portfolio_returns: dict,
    benchmark_returns: pd.Series = None,
    output_path: str = 'charts/cumulative_returns.png',
):
    """Chart 1: Cumulative return of all portfolios + benchmark.

    :param portfolio_returns: Dict mapping name → daily return Series
    :type portfolio_returns: dict
    :param benchmark_returns: Benchmark daily returns
    :type benchmark_returns: pd.Series or None
    :param output_path: File path to save the chart
    :type output_path: str
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    for name, returns in portfolio_returns.items():
        cum = (1 + returns).cumprod()
        color = COLORS.get(name, None)
        ax.plot(cum.index, cum.values, label=name, color=color, linewidth=1.5)

    if benchmark_returns is not None:
        cum_bm = (1 + benchmark_returns).cumprod()
        ax.plot(cum_bm.index, cum_bm.values, label='S&P 500',
                color=COLORS['benchmark'], linewidth=1.5, linestyle='--')

    ax.set_yscale('log')
    ax.set_title('Cumulative Returns (Log Scale)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Growth of $1 (log)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    _save_fig(fig, output_path)


def plot_drawdown(
    returns: pd.Series,
    portfolio_name: str = 'Combined',
    output_path: str = 'charts/drawdown.png',
):
    """Chart 2: Drawdown underwater chart.

    :param returns: Daily portfolio returns
    :type returns: pd.Series
    :param portfolio_name: Portfolio label
    :type portfolio_name: str
    :param output_path: File path
    :type output_path: str
    """
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(drawdown.index, drawdown.values, 0, color='#EF5350', alpha=0.6)
    ax.plot(drawdown.index, drawdown.values, color='#B71C1C', linewidth=0.8)
    ax.set_title(f'Drawdown — {portfolio_name}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown')
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.grid(True, alpha=0.3)
    _save_fig(fig, output_path)


def plot_monthly_heatmap(
    returns: pd.Series,
    output_path: str = 'charts/monthly_heatmap.png',
):
    """Chart 3: Monthly returns heatmap.

    :param returns: Daily portfolio returns
    :type returns: pd.Series
    :param output_path: File path
    :type output_path: str
    """
    monthly = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    monthly_df = pd.DataFrame({
        'year': monthly.index.year,
        'month': monthly.index.month,
        'return': monthly.values,
    })
    pivot = monthly_df.pivot(index='year', columns='month', values='return')
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot.columns = [month_names[m - 1] for m in pivot.columns]

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        pivot * 100, annot=True, fmt='.1f', center=0,
        cmap='RdYlGn', linewidths=0.5, ax=ax,
        cbar_kws={'label': 'Return (%)'},
    )
    ax.set_title('Monthly Returns Heatmap (%)')
    ax.set_ylabel('Year')
    _save_fig(fig, output_path)


def plot_rolling_sharpe(
    portfolio_returns: dict,
    window: int = 252,
    output_path: str = 'charts/rolling_sharpe.png',
):
    """Chart 4: Rolling 12-month Sharpe ratio.

    :param portfolio_returns: Dict of name → return Series
    :type portfolio_returns: dict
    :param window: Rolling window in days
    :type window: int
    :param output_path: File path
    :type output_path: str
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    for name, returns in portfolio_returns.items():
        excess = returns - 0.04 / 252
        rolling_mean = excess.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        rolling_sharpe = rolling_mean / rolling_std * np.sqrt(252)
        color = COLORS.get(name, None)
        ax.plot(rolling_sharpe.index, rolling_sharpe.values, label=name, color=color)

    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title(f'Rolling {window}-Day Sharpe Ratio')
    ax.set_xlabel('Date')
    ax.set_ylabel('Sharpe Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    _save_fig(fig, output_path)


def plot_weight_sensitivity_heatmap(
    sensitivity_df: pd.DataFrame,
    output_path: str = 'charts/weight_sensitivity.png',
):
    """Chart 5: Weight sensitivity heatmap (Sharpe vs value/sentiment mix).

    :param sensitivity_df: Weight sensitivity results
    :type sensitivity_df: pd.DataFrame
    :param output_path: File path
    :type output_path: str
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        sensitivity_df['value_weight'],
        sensitivity_df['sharpe_ratio'],
        'o-', color=COLORS['combined'], linewidth=2,
    )
    ax.axvline(x=0.6, color='red', linestyle='--', label='Chosen (60/40)')
    ax.set_title('Sharpe Ratio vs Value/Sentiment Weight Mix')
    ax.set_xlabel('Value Weight (Sentiment = 1 - Value)')
    ax.set_ylabel('Sharpe Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    _save_fig(fig, output_path)


def plot_factor_loadings(
    ff_result: dict,
    output_path: str = 'charts/factor_loadings.png',
):
    """Chart 6: Fama-French factor loadings with confidence intervals.

    :param ff_result: Fama-French regression result dict
    :type ff_result: dict
    :param output_path: File path
    :type output_path: str
    """
    if not ff_result.get('betas'):
        logger.warning("No FF betas to plot")
        return

    factors = list(ff_result['betas'].keys())
    betas = [ff_result['betas'][f] for f in factors]
    tstats = [ff_result['tstats'].get(f, 0) for f in factors]

    # Approximate 95% CI: beta ± 1.96 * (beta / t_stat)
    ci_widths = [abs(b / t * 1.96) if abs(t) > 0 else 0 for b, t in zip(betas, tstats)]

    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = range(len(factors))
    bars = ax.bar(x_pos, betas, yerr=ci_widths, capsize=5,
                  color=COLORS['combined'], alpha=0.7, edgecolor='black')

    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(factors, rotation=45)
    ax.set_title('Fama-French 5-Factor Loadings (with 95% CI)')
    ax.set_ylabel('Beta Coefficient')
    ax.grid(True, alpha=0.3, axis='y')

    # Add t-stat annotations
    for i, (b, t) in enumerate(zip(betas, tstats)):
        ax.annotate(
            f't={t:.2f}', (i, b + ci_widths[i] * np.sign(b) + 0.02),
            ha='center', fontsize=9,
        )

    _save_fig(fig, output_path)


def plot_sector_allocation(
    portfolio_sectors: pd.Series,
    benchmark_sectors: pd.Series = None,
    output_path: str = 'charts/sector_allocation.png',
):
    """Chart 7: Sector allocation (portfolio vs benchmark).

    :param portfolio_sectors: Portfolio sector weights
    :type portfolio_sectors: pd.Series
    :param benchmark_sectors: Benchmark sector weights (optional)
    :type benchmark_sectors: pd.Series or None
    :param output_path: File path
    :type output_path: str
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    sectors = portfolio_sectors.index.tolist()
    x = np.arange(len(sectors))
    width = 0.35

    ax.barh(x, portfolio_sectors.values * 100, width, label='Portfolio',
            color=COLORS['combined'], alpha=0.8)
    if benchmark_sectors is not None:
        bm_aligned = benchmark_sectors.reindex(sectors, fill_value=0)
        ax.barh(x + width, bm_aligned.values * 100, width, label='Benchmark',
                color=COLORS['benchmark'], alpha=0.8)

    ax.set_yticks(x + width / 2)
    ax.set_yticklabels(sectors)
    ax.set_xlabel('Weight (%)')
    ax.set_title('Sector Allocation: Portfolio vs Benchmark')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    _save_fig(fig, output_path)


def plot_random_portfolio_histogram(
    random_result: dict,
    output_path: str = 'charts/random_portfolios.png',
):
    """Chart 8: Random portfolio Sharpe histogram.

    :param random_result: Random portfolio test result dict
    :type random_result: dict
    :param output_path: File path
    :type output_path: str
    """
    sharpes = random_result.get('random_sharpes', np.array([]))
    strategy = random_result.get('strategy_sharpe', 0)
    pctl = random_result.get('percentile_rank', 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(sharpes, bins=50, color='#90CAF9', edgecolor='white', alpha=0.8)
    ax.axvline(x=strategy, color='red', linewidth=2, linestyle='--',
               label=f'Strategy: {strategy:.3f} ({pctl:.1f}th pctl)')
    ax.set_title(f'Strategy vs {len(sharpes):,} Random Portfolios')
    ax.set_xlabel('Sharpe Ratio')
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True, alpha=0.3)
    _save_fig(fig, output_path)


def plot_turnover_per_rebalance(
    rebalance_info: pd.DataFrame,
    output_path: str = 'charts/turnover.png',
):
    """Chart 10: Turnover per rebalance date.

    :param rebalance_info: DataFrame with date and turnover columns
    :type rebalance_info: pd.DataFrame
    :param output_path: File path
    :type output_path: str
    """
    if len(rebalance_info) == 0:
        return

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(rebalance_info['date'], rebalance_info['turnover'] * 100,
           color=COLORS['combined'], alpha=0.8, width=20)
    ax.set_title('One-Way Turnover per Rebalance')
    ax.set_xlabel('Rebalance Date')
    ax.set_ylabel('Turnover (%)')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    _save_fig(fig, output_path)


def _save_fig(fig, output_path: str):
    """Save figure and close.

    :param fig: Matplotlib figure
    :param output_path: File path
    :type output_path: str
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Chart saved: %s", output_path)


def plot_threshold_sensitivity(
    threshold_df: pd.DataFrame,
    output_path: str = 'charts/threshold_sensitivity.png',
):
    """Chart 9: Screening threshold sensitivity.

    Shows how Sharpe ratio varies across selection percentile and
    D/E filter combinations (heatmap or grouped bar chart).

    :param threshold_df: DataFrame from threshold_sensitivity_analysis
                         with columns selection_percentile, max_debt_equity,
                         sharpe_ratio
    :type threshold_df: pd.DataFrame
    :param output_path: File path to save the chart
    :type output_path: str
    """
    if len(threshold_df) == 0:
        logger.warning("Empty threshold DataFrame — skipping Chart 9")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left panel: Sharpe by selection percentile
    ax1 = axes[0]
    for de_val in sorted(threshold_df['max_debt_equity'].unique()):
        subset = threshold_df[threshold_df['max_debt_equity'] == de_val]
        ax1.plot(
            subset['selection_percentile'] * 100,
            subset['sharpe_ratio'],
            'o-', label=f'D/E < {de_val}', linewidth=1.5,
        )
    ax1.axvline(x=20, color='red', linestyle='--', alpha=0.7, label='Chosen (20%)')
    ax1.set_title('Sharpe Ratio by Selection Threshold')
    ax1.set_xlabel('Selection Percentile (%)')
    ax1.set_ylabel('Sharpe Ratio')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Right panel: Sharpe by D/E limit
    ax2 = axes[1]
    for pctl in sorted(threshold_df['selection_percentile'].unique()):
        subset = threshold_df[threshold_df['selection_percentile'] == pctl]
        ax2.plot(
            subset['max_debt_equity'],
            subset['sharpe_ratio'],
            's-', label=f'Top {int(pctl*100)}%', linewidth=1.5,
        )
    ax2.axvline(x=2.0, color='red', linestyle='--', alpha=0.7, label='Chosen (2.0)')
    ax2.set_title('Sharpe Ratio by D/E Filter')
    ax2.set_xlabel('Max Debt/Equity Ratio')
    ax2.set_ylabel('Sharpe Ratio')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    _save_fig(fig, output_path)


def plot_old_vs_new_value_scores(
    old_scores: pd.DataFrame,
    new_scores: pd.DataFrame,
    sector_map: dict,
    output_path: str = 'charts/old_vs_new_value.png',
):
    """Chart 11: OLD vs NEW value score sector concentration comparison.

    Compares CW1 cross-sectional percentile ranking against CW2
    sector-relative z-score ranking.  Shows how sector concentration
    changes under the new methodology.

    Key insight (Ehsani et al. 2023): standard HML overweights
    Financials and Utilities.  Sector-relative scoring should produce
    more balanced sector exposure in the top quintile.

    :param old_scores: CW1 composite_rankings with value_score (0–100 pctl)
    :type old_scores: pd.DataFrame
    :param new_scores: CW2 sector-relative value_score (z-score ±3)
    :type new_scores: pd.DataFrame
    :param sector_map: Dict mapping company_id → GICS sector
    :type sector_map: dict
    :param output_path: File path to save the chart
    :type output_path: str
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)

    for ax, scores, title, col_name in [
        (axes[0], old_scores, 'CW1: Cross-Sectional Percentile', 'value_score'),
        (axes[1], new_scores, 'CW2: Sector-Relative Z-Score', 'value_score'),
    ]:
        if scores is None or len(scores) == 0:
            ax.set_title(f'{title}\n(no data)')
            continue

        df = scores.copy()
        id_col = 'company_id' if 'company_id' in df.columns else df.index.name
        if id_col and id_col in df.columns:
            df['sector'] = df[id_col].map(sector_map)
        elif df.index.name:
            df['sector'] = df.index.map(sector_map)
        else:
            ax.set_title(f'{title}\n(no sector data)')
            continue

        if col_name not in df.columns:
            ax.set_title(f'{title}\n(no scores)')
            continue

        # Select top 20% by value_score
        valid = df[df[col_name].notna()]
        if len(valid) == 0:
            continue
        cutoff = int(len(valid) * 0.20)
        top_quintile = valid.nlargest(cutoff, col_name)

        # Sector breakdown of top quintile
        sector_counts = top_quintile['sector'].value_counts()
        total = sector_counts.sum()
        sector_pcts = (sector_counts / total * 100).sort_values(ascending=True)

        colors_list = plt.cm.Set3(np.linspace(0, 1, len(sector_pcts)))
        sector_pcts.plot(kind='barh', ax=ax, color=colors_list, edgecolor='white')
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('% of Top Quintile')

        # Annotate percentages
        for i, (sector, pct) in enumerate(sector_pcts.items()):
            ax.text(pct + 0.5, i, f'{pct:.1f}%', va='center', fontsize=9)

    fig.suptitle(
        'Value Score Top Quintile — Sector Concentration\n'
        'OLD (CW1 Percentile) vs NEW (CW2 Sector-Relative)',
        fontsize=13, fontweight='bold', y=1.02,
    )
    _save_fig(fig, output_path)


def plot_diversification_over_time(
    diversification_df: pd.DataFrame,
    output_path: str = 'charts/diversification_over_time.png',
):
    """Chart 13: HHI / Effective N / sector concentration through time.

    Plots three diversification metrics across all rebalance dates:
        * Effective number of holdings (1/HHI)
        * Number of distinct GICS sectors with ≥1% weight
        * Maximum sector weight

    :param diversification_df: DataFrame indexed by rebalance date with
                               columns ``effective_n``, ``n_sectors``,
                               ``max_sector_weight``, ``hhi``
    :type diversification_df: pd.DataFrame
    :param output_path: File path to save the chart
    :type output_path: str
    """
    if diversification_df is None or len(diversification_df) == 0:
        logger.warning("Empty diversification DataFrame — skipping diversification-over-time chart")
        return

    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)

    # Effective N
    ax1 = axes[0]
    ax1.plot(
        diversification_df.index, diversification_df['effective_n'],
        marker='o', linewidth=1.8, color=COLORS['combined'], label='Effective N (1/HHI)',
    )
    ax1.axhline(y=40, color='gray', linestyle='--', alpha=0.6, label='Target = 40')
    ax1.set_ylabel('Effective N')
    ax1.set_title('Diversification Through Time (per rebalance)')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Sector count
    ax2 = axes[1]
    ax2.bar(
        diversification_df.index, diversification_df['n_sectors'],
        color=COLORS['value_only'], alpha=0.75, width=20,
    )
    ax2.set_ylabel('# GICS sectors')
    ax2.grid(True, alpha=0.3, axis='y')

    # Max sector weight
    ax3 = axes[2]
    ax3.plot(
        diversification_df.index, diversification_df['max_sector_weight'] * 100,
        marker='s', linewidth=1.8, color=COLORS['sentiment_only'], label='Max sector weight',
    )
    ax3.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Cap = 25%')
    ax3.set_ylabel('Max sector weight (%)')
    ax3.set_xlabel('Rebalance date')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)

    _save_fig(fig, output_path)


def plot_cumulative_cost_impact(
    rebalance_info: pd.DataFrame,
    output_path: str = 'charts/cost_impact.png',
):
    """Chart 14: Cumulative transaction-cost drag over time.

    Visualises the dollar drag from 25 bps one-way trading costs as a
    cumulative sum, plus per-rebalance cost bars on a secondary axis.

    :param rebalance_info: DataFrame with ``date`` and ``cost`` columns
    :type rebalance_info: pd.DataFrame
    :param output_path: File path to save the chart
    :type output_path: str
    """
    if rebalance_info is None or len(rebalance_info) == 0:
        return

    df = rebalance_info.sort_values('date').copy()
    df['cum_cost'] = df['cost'].cumsum()

    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax1.bar(df['date'], df['cost'] * 10000, color='#FFB74D',
            alpha=0.7, width=20, label='Per-rebalance cost (bps)')
    ax1.set_ylabel('Per-rebalance cost (bps)', color='#E65100')
    ax1.tick_params(axis='y', labelcolor='#E65100')
    ax1.set_xlabel('Rebalance date')
    ax1.grid(True, alpha=0.3, axis='y')

    ax2 = ax1.twinx()
    ax2.plot(df['date'], df['cum_cost'] * 10000, color='#1565C0',
             linewidth=2.2, marker='o', label='Cumulative cost (bps)')
    ax2.set_ylabel('Cumulative cost (bps)', color='#1565C0')
    ax2.tick_params(axis='y', labelcolor='#1565C0')

    ax1.set_title('Transaction-Cost Drag Over Time (25 bps one-way)')
    plt.xticks(rotation=45)
    _save_fig(fig, output_path)


def plot_pipeline_flowchart(
    output_path: str = 'charts/pipeline_flowchart.png',
):
    """Chart 12: CW1→CW2 pipeline flowchart.

    Renders a visual representation of how data flows from CW1
    extraction through CW2 signal construction, portfolio building,
    and performance analysis.

    :param output_path: File path to save the chart
    :type output_path: str
    """
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Define boxes as (x, y, width, height, label, color)
    boxes = [
        # CW1 Layer
        (0.5, 8.5, 2.0, 1.0, 'Yahoo Finance\nGDELT\nNewsAPI', '#E3F2FD'),
        (3.0, 8.5, 2.0, 1.0, 'PostgreSQL\n(daily_prices\nvalue_metrics)', '#E8F5E9'),
        (5.5, 8.5, 2.0, 1.0, 'MongoDB\n(raw_news\narticles)', '#E8F5E9'),
        (8.0, 8.5, 1.5, 1.0, 'CW1 Composite\nRankings', '#FFF3E0'),

        # CW2 Signal Layer
        (1.0, 6.0, 2.5, 1.0, 'Sector-Relative\nValue Signal\n(MSCI 4-Stage)', '#E1F5FE'),
        (5.0, 6.0, 2.5, 1.0, 'Quality-Weighted\nSentiment Signal\n(Bayesian Shrinkage)', '#E1F5FE'),

        # CW2 Composite
        (3.0, 4.0, 3.0, 0.8, 'Composite Score\n0.6 × Value + 0.4 × Sentiment', '#FFF9C4'),

        # Portfolio
        (3.0, 2.5, 3.0, 0.8, 'Portfolio Construction\nScreen → Weight → Constrain', '#F3E5F5'),

        # Output
        (1.0, 0.5, 2.0, 1.0, 'Performance\nMetrics\n(Sharpe, FF, DD)', '#FFEBEE'),
        (3.5, 0.5, 2.0, 1.0, 'Robustness\nTests\n(6 tests)', '#FFEBEE'),
        (6.0, 0.5, 2.0, 1.0, 'Charts &\nTearsheet\n(12 charts)', '#FFEBEE'),
    ]

    for (x, y, w, h, label, color) in boxes:
        rect = plt.Rectangle((x, y), w, h, facecolor=color,
                              edgecolor='#455A64', linewidth=1.5, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=8, fontweight='bold', zorder=3)

    # Draw arrows
    arrow_style = dict(arrowstyle='->', color='#455A64', lw=1.5, connectionstyle='arc3,rad=0')

    # CW1 → Signals
    ax.annotate('', xy=(2.25, 6.95), xytext=(2.0, 8.5), arrowprops=arrow_style)
    ax.annotate('', xy=(4.0, 6.95), xytext=(4.0, 8.5), arrowprops=arrow_style)
    ax.annotate('', xy=(6.25, 6.95), xytext=(6.5, 8.5), arrowprops=arrow_style)

    # Signals → Composite
    ax.annotate('', xy=(3.5, 4.75), xytext=(2.25, 6.0), arrowprops=arrow_style)
    ax.annotate('', xy=(5.0, 4.75), xytext=(6.25, 6.0), arrowprops=arrow_style)

    # Composite → Portfolio
    ax.annotate('', xy=(4.5, 3.25), xytext=(4.5, 4.0), arrowprops=arrow_style)

    # Portfolio → Outputs
    ax.annotate('', xy=(2.0, 1.45), xytext=(3.5, 2.5), arrowprops=arrow_style)
    ax.annotate('', xy=(4.5, 1.45), xytext=(4.5, 2.5), arrowprops=arrow_style)
    ax.annotate('', xy=(7.0, 1.45), xytext=(5.5, 2.5), arrowprops=arrow_style)

    # Section labels
    ax.text(0.1, 9.7, 'CW1: Data Pipeline', fontsize=11, fontweight='bold',
            fontstyle='italic', color='#1565C0')
    ax.text(0.1, 7.2, 'CW2: Signal Construction', fontsize=11, fontweight='bold',
            fontstyle='italic', color='#1565C0')
    ax.text(0.1, 4.9, 'CW2: Portfolio Engine', fontsize=11, fontweight='bold',
            fontstyle='italic', color='#1565C0')
    ax.text(0.1, 1.7, 'CW2: Analysis & Output', fontsize=11, fontweight='bold',
            fontstyle='italic', color='#1565C0')

    fig.suptitle('CW1 → CW2 Pipeline Architecture', fontsize=14, fontweight='bold')
    _save_fig(fig, output_path)
