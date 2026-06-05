"""Generate appendix diagrams.

Renders the figures embedded in the CW2 Code Documentation appendix:

* ``module_architecture.png`` — five-layer module map (data flow).
* ``signal_pipeline.png`` — algorithmic flow inside the signal layer.
* ``backtest_sequence.png`` — per-rebalance loop on a horizontal time axis.
* ``eligibility_funnel.png`` — universe filtering cascade with counts.
* ``quality_weight_components.png`` — how the four sentiment components
  multiply for a representative article.

All figures share a consistent palette and are saved at 220 dpi to the
same directory as this script so they can be referenced from
``index.rst`` via ``.. figure::`` blocks.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT_DIR = Path(__file__).resolve().parent

# Consistent professional palette
PAL = {
    "data": "#1f4e79",
    "signal": "#2e7d32",
    "portfolio": "#c46f17",
    "backtest": "#6a4c93",
    "analytics": "#a83232",
    "neutral": "#555555",
    "ink": "#1a1a1a",
    "muted": "#777777",
    "bg_data": "#e7eef7",
    "bg_signal": "#e8f3e9",
    "bg_portfolio": "#fdf0e1",
    "bg_backtest": "#efe7f5",
    "bg_analytics": "#f7e6e6",
    "bg_card": "#fafafa",
}

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 9


def _box(ax, x, y, w, h, label, fc, ec, fontsize=8, weight="normal", text_color=None):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=1.0, edgecolor=ec, facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2, y + h / 2, label,
        ha="center", va="center",
        fontsize=fontsize, weight=weight,
        color=text_color or PAL["ink"],
    )


def _arrow(ax, x1, y1, x2, y2, color="#444", style="-|>", lw=1.0):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=12,
        color=color, linewidth=lw,
    )
    ax.add_patch(arrow)


# --------------------------------------------------------------------------- #
# Figure 1 — Module Architecture                                              #
# --------------------------------------------------------------------------- #
def render_module_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5))

    layers = [
        ("CW1 Data Layer", 5.6, 0.9, PAL["bg_data"], PAL["data"]),
        ("Signal Construction", 4.4, 0.9, PAL["bg_signal"], PAL["signal"]),
        ("Portfolio Engine", 3.2, 0.9, PAL["bg_portfolio"], PAL["portfolio"]),
        ("Backtester", 2.0, 0.9, PAL["bg_backtest"], PAL["backtest"]),
        ("Analytics & Output", 0.4, 1.4, PAL["bg_analytics"], PAL["analytics"]),
    ]
    for label, y, h, bg, ec in layers:
        ax.add_patch(FancyBboxPatch(
            (0.2, y), 10.6, h,
            boxstyle="round,pad=0.0,rounding_size=0.05",
            facecolor=bg, edgecolor=ec, linewidth=1.0, alpha=0.55,
        ))
        ax.text(0.35, y + h - 0.18, label, fontsize=9.5, weight="bold", color=ec)

    _box(ax, 0.6, 5.85, 1.9, 0.5, "data_loader\n(PostgreSQL + Mongo, PIT)", PAL["bg_data"], PAL["data"], 7)
    _box(ax, 2.7, 5.85, 1.7, 0.5, "universe\n(active / delisted)", PAL["bg_data"], PAL["data"], 7)
    _box(ax, 4.6, 5.85, 1.7, 0.5, "benchmark\n(S&P / MSCI / EW)", PAL["bg_data"], PAL["data"], 7)
    _box(ax, 6.5, 5.85, 1.7, 0.5, "cw1_schema\n(table/col map)", PAL["bg_data"], PAL["data"], 7)
    _box(ax, 8.4, 5.85, 2.2, 0.5, "backfill_*  (yfinance,\nAlpha Vantage history)", PAL["bg_data"], PAL["data"], 7)

    _box(ax, 1.2, 4.65, 2.6, 0.5, "value_signal\nMSCI 4-stage sector-rel z", PAL["bg_signal"], PAL["signal"], 8, "bold")
    _box(ax, 4.2, 4.65, 2.6, 0.5, "sentiment_signal\n4-component quality weight", PAL["bg_signal"], PAL["signal"], 8, "bold")
    _box(ax, 7.2, 4.65, 2.6, 0.5, "signal_combiner\n0.6V + 0.4S + screens", PAL["bg_signal"], PAL["signal"], 8, "bold")

    _box(ax, 1.2, 3.45, 2.6, 0.5, "portfolio_constructor\nscreen → weight → cap", PAL["bg_portfolio"], PAL["portfolio"], 8)
    _box(ax, 4.2, 3.45, 2.6, 0.5, "weighting\nEW / score / inv-vol", PAL["bg_portfolio"], PAL["portfolio"], 8)
    _box(ax, 7.2, 3.45, 2.6, 0.5, "constraints\n5% / 50% / 30–50 names", PAL["bg_portfolio"], PAL["portfolio"], 8)

    _box(ax, 1.2, 2.25, 2.6, 0.5, "backtester\nquarterly + drift", PAL["bg_backtest"], PAL["backtest"], 8, "bold")
    _box(ax, 4.2, 2.25, 2.6, 0.5, "rebalance_schedule\nmonths [1,4,7,10]", PAL["bg_backtest"], PAL["backtest"], 8)
    _box(ax, 7.2, 2.25, 2.6, 0.5, "transaction_costs\n25 bps one-way", PAL["bg_backtest"], PAL["backtest"], 8)

    _box(ax, 0.6, 1.05, 1.9, 0.5, "performance\nSharpe / Sortino / DD", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 2.7, 1.05, 1.9, 0.5, "risk\nFF-5 + Newey-West", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 4.8, 1.05, 1.9, 0.5, "diversification\nHHI, effective N", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 6.9, 1.05, 1.9, 0.5, "turnover\nper-rebalance + cost", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 9.0, 1.05, 1.6, 0.5, "pitfalls\naudit log", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 0.6, 0.5, 2.2, 0.45, "bootstrap (Politis 1994)", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 2.95, 0.5, 2.0, 0.45, "random_portfolios (10K)", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 5.1, 0.5, 1.9, 0.45, "sensitivity / sub-period", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 7.15, 0.5, 1.7, 0.45, "charts (16 PNG)", PAL["bg_analytics"], PAL["analytics"], 7)
    _box(ax, 9.0, 0.5, 1.6, 0.45, "tearsheet.html", PAL["bg_analytics"], PAL["analytics"], 7)

    for x in (2.3, 5.5, 8.7):
        _arrow(ax, x, 5.83, x, 5.18, color=PAL["data"])
        _arrow(ax, x, 4.63, x, 3.98, color=PAL["signal"])
        _arrow(ax, x, 3.43, x, 2.78, color=PAL["portfolio"])
        _arrow(ax, x, 2.23, x, 1.58, color=PAL["backtest"])

    ax.text(5.5, 7.30, "CW2 Module Architecture",
            ha="center", fontsize=13, weight="bold", color=PAL["ink"])
    ax.text(5.5, 7.00,
            "Five strictly-layered packages.  Each layer reads from the layer above; "
            "the backtester is the only stateful loop.",
            ha="center", fontsize=8.5, style="italic", color=PAL["muted"])

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.set_aspect("equal")
    ax.axis("off")

    out = OUT_DIR / "module_architecture.png"
    plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {out}")


# --------------------------------------------------------------------------- #
# Figure 2 — Signal Pipeline                                                  #
# --------------------------------------------------------------------------- #
def _stage_box(ax, x, y, w, h, header, body, fc, ec,
               header_size=8, body_size=7, header_weight="bold"):
    """Stage box with bold header above small-font body text — keeps every
    line visually inside the rounded rectangle."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=1.0, edgecolor=ec, facecolor=fc,
    )
    ax.add_patch(box)
    cx = x + w / 2
    # Header takes the upper third
    ax.text(cx, y + h * 0.70, header,
            ha="center", va="center",
            fontsize=header_size, weight=header_weight,
            color=PAL["ink"])
    # Body takes the lower two-thirds
    ax.text(cx, y + h * 0.28, body,
            ha="center", va="center",
            fontsize=body_size, color=PAL["muted"])


def render_signal_pipeline():
    fig, ax = plt.subplots(figsize=(13, 9))

    # Wider canvas with more breathing room
    col_w = 5.4   # column width
    col_l_x = 0.3
    col_r_x = 7.3
    col_l_cx = col_l_x + col_w / 2
    col_r_cx = col_r_x + col_w / 2

    box_h = 0.85  # taller boxes -> two-row text fits comfortably

    # ---- Title ----
    ax.text(6.5, 8.8, "CW2 Signal Pipeline",
            ha="center", fontsize=14, weight="bold", color=PAL["ink"])

    # ---- Column titles ----
    ax.text(col_l_cx, 8.30, "Value Signal — MSCI 4-Stage Pipeline",
            ha="center", fontsize=11, weight="bold", color=PAL["signal"])
    ax.text(col_r_cx, 8.30, "Sentiment Signal — 4-Component Quality Weight",
            ha="center", fontsize=11, weight="bold", color=PAL["signal"])

    # ---- Value column (left) ----
    y = 7.3
    _stage_box(ax, col_l_x, y, col_w, box_h,
               "Inputs",
               "pe_ratio · pb_ratio · ev_ebitda · dividend_yield · debt_equity",
               "#fafafa", PAL["neutral"])
    _arrow(ax, col_l_cx, y, col_l_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_l_x, y, col_w, box_h,
               "Stage 1  —  Flip + Winsorise",
               "E/P · B/P · EBITDA/EV · Div Yield   ·   clip @ 2.5 / 97.5 %ile",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_l_cx, y, col_l_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_l_x, y, col_w, box_h,
               "Stage 2  —  Cross-Sectional Z-Score",
               "z = (x − μ_all) / σ_all   for each of the 4 metrics",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_l_cx, y, col_l_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_l_x, y, col_w, box_h,
               "Stage 3  —  Composite + Within-Sector Re-Standardise",
               "Z_comp = mean(z_metrics)   →   (Z_comp − μ_sector) / σ_sector",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_l_cx, y, col_l_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_l_x, y, col_w, box_h,
               "Stage 4  —  Cap ±3  +  Bayesian Shrinkage",
               "sectors with < 15 constituents shrunk toward cross-sectional mean",
               PAL["bg_signal"], PAL["signal"])
    value_y_bottom = y

    # ---- Sentiment column (right) ----
    y = 7.3
    _stage_box(ax, col_r_x, y, col_w, box_h,
               "Inputs",
               "article-level rows (Mongo)   or   aggregated sentiment_scores (Postgres)",
               "#fafafa", PAL["neutral"])
    _arrow(ax, col_r_cx, y, col_r_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_r_x, y, col_w, box_h,
               "Per-Article Quality Weight",
               "w  =  w_source  ×  w_relevance  ×  w_recency  ×  w_length",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_r_cx, y, col_r_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_r_x, y, col_w, box_h,
               "Components  (each in [0, 1])",
               "src tier 1.0 / 0.7 / 0.4 / 0.3   ·   rel +0.5 / +0.3 / +0.2  floor 0.05",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_r_cx, y, col_r_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_r_x, y, col_w, box_h,
               "Per-Company Aggregation",
               "S = Σ(w·VADER) / Σw     c = max(0,  1 − 2σ_w)",
               PAL["bg_signal"], PAL["signal"])
    _arrow(ax, col_r_cx, y, col_r_cx, y - 0.15)

    y -= 1.0
    _stage_box(ax, col_r_x, y, col_w, box_h,
               "Bayesian Shrinkage",
               "sentiment_score = (n × S × c) / (n + 5)     confidence = n / (n + 5)",
               PAL["bg_signal"], PAL["signal"])
    sent_y_bottom = y

    # ---- Combiner band (full width) ----
    band_y = value_y_bottom - 1.05
    band_x = 0.6
    band_w = 12.4

    # Diagonal arrows from both columns into the combiner
    _arrow(ax, col_l_cx, value_y_bottom, band_x + band_w * 0.3,
           band_y + box_h, color=PAL["signal"])
    _arrow(ax, col_r_cx, sent_y_bottom, band_x + band_w * 0.7,
           band_y + box_h, color=PAL["signal"])

    _stage_box(ax, band_x, band_y, band_w, box_h,
               "Signal Combiner  —  Scale Alignment  +  Composite",
               "value_pctl = rank(value_score) → [0, 100]     "
               "sentiment_norm = (s + 1) / 2 × 100     "
               "composite = 0.6·value + 0.4·sent",
               PAL["bg_portfolio"], PAL["portfolio"], header_size=9)

    _arrow(ax, band_x + band_w / 2, band_y, band_x + band_w / 2, band_y - 0.18,
           color=PAL["portfolio"])

    # ---- Screens band (full width) ----
    screen_y = band_y - 1.05
    _stage_box(ax, band_x, screen_y, band_w, box_h,
               "Eligibility Screens  (all three must pass)  →  top 20% by composite",
               "value_score > 0     ∧     confidence > 0.3     ∧     "
               "(debt_equity ≤ 2.0  ∨  NaN)     →     invest_decision = True",
               PAL["bg_analytics"], PAL["analytics"], header_size=9)

    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis("off")

    out = OUT_DIR / "signal_pipeline.png"
    plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {out}")


# --------------------------------------------------------------------------- #
# Figure 3 — Backtest Sequence (per-rebalance flow)                           #
# --------------------------------------------------------------------------- #
def render_backtest_sequence():
    """Vertical-then-horizontal layout: pre-rebalance steps stack above the
    timeline; the drift block sits between Q and Q+1."""
    fig, ax = plt.subplots(figsize=(11.5, 9.5))

    # Title
    ax.text(5.75, 9.10, "Backtest Sequence — Per-Rebalance Loop",
            ha="center", fontsize=13, weight="bold", color=PAL["ink"])
    ax.text(5.75, 8.78,
            "Quarterly cadence at month-ends [Jan, Apr, Jul, Oct]. "
            "T+1 execution; weights drift between rebalances.",
            ha="center", fontsize=8.5, style="italic", color=PAL["muted"])

    # Legend (top, away from boxes)
    legend_items = [
        ("Signal layer", PAL["signal"], PAL["bg_signal"]),
        ("Portfolio engine", PAL["portfolio"], PAL["bg_portfolio"]),
        ("Backtester", PAL["backtest"], PAL["bg_backtest"]),
        ("Drift / carry", PAL["data"], PAL["bg_data"]),
    ]
    for i, (lab, ec, fc) in enumerate(legend_items):
        x = 0.5 + i * 2.7
        ax.add_patch(Rectangle((x, 8.30), 0.28, 0.20, facecolor=fc, edgecolor=ec))
        ax.text(x + 0.36, 8.40, lab, fontsize=8, va="center", color=PAL["ink"])

    # Pre-rebalance vertical stack
    pre_steps = [
        ("1.  Build PIT universe", "678 → ~605 active + delisted ≤ 10 trading days", PAL["bg_signal"], PAL["signal"]),
        ("2.  Load PIT inputs",    "value_metrics with 90-day lag · sentiment ≤ rebal_date", PAL["bg_signal"], PAL["signal"]),
        ("3.  Compute signals",    "value · sentiment · composite + 3 eligibility screens", PAL["bg_signal"], PAL["signal"]),
        ("4.  Construct portfolio", "rank top 20% · weight · enforce 5% / 50% caps", PAL["bg_portfolio"], PAL["portfolio"]),
    ]
    for i, (label, sub, fc, ec) in enumerate(pre_steps):
        y = 7.55 - i * 0.95
        # Numbered step box
        _box(ax, 1.5, y, 8.5, 0.7,
             f"{label}    —    {sub}",
             fc, ec, 8.5)
        # Connector arrow to next
        if i < len(pre_steps) - 1:
            _arrow(ax, 5.75, y, 5.75, y - 0.25, color=ec, lw=1.0)

    # Connector from box 4 bottom (y = 4.70) to timeline top (y = 2.87)
    _arrow(ax, 5.75, 4.62, 5.75, 2.92, color=PAL["portfolio"], lw=1.2)
    ax.text(5.95, 3.78, "set target weights",
            fontsize=8, va="center", ha="left",
            style="italic", color=PAL["portfolio"])

    # Time axis
    timeline_y = 2.65
    ax.annotate("", xy=(11.0, timeline_y), xytext=(0.4, timeline_y),
                arrowprops=dict(arrowstyle="->", color=PAL["ink"], lw=1.4))
    ax.text(11.15, timeline_y, "time", va="center", fontsize=9, color=PAL["ink"])

    # Rebalance markers on timeline
    rebalances = [
        (1.0, "Q-1\nrebalance", PAL["muted"]),
        (5.75, "Q\nrebalance\n(focus)", PAL["backtest"]),
        (10.0, "Q+1\nrebalance", PAL["muted"]),
    ]
    for x, label, c in rebalances:
        ax.plot([x, x], [timeline_y - 0.18, timeline_y + 0.22], color=c, lw=2.4)
        ax.text(x, timeline_y - 0.55, label, ha="center", fontsize=8.5,
                weight="bold", color=c)

    # Step 5 (execution) below timeline at Q
    _box(ax, 4.4, 1.10, 2.7, 0.55,
         "5.  Execute @ T+1 close",
         PAL["bg_backtest"], PAL["backtest"], 8.5)
    _box(ax, 4.4, 0.45, 2.7, 0.55,
         "6.  Deduct 25 bps one-way",
         PAL["bg_backtest"], PAL["backtest"], 8.5)
    ax.text(7.25, 1.37, "turnover = 0.5 × Σ|Δw|",
            ha="left", va="center", fontsize=7.5, style="italic", color=PAL["muted"])
    ax.text(7.25, 0.72, "applied to first-day return",
            ha="left", va="center", fontsize=7.5, style="italic", color=PAL["muted"])

    # Drift block between Q and Q+1, ABOVE timeline
    drift_y = timeline_y + 0.55
    drift_x0, drift_x1 = 5.95, 9.85
    ax.add_patch(FancyBboxPatch(
        (drift_x0, drift_y), drift_x1 - drift_x0, 0.95,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=PAL["bg_data"], edgecolor=PAL["data"],
        linewidth=1.0, alpha=0.85,
    ))
    ax.text((drift_x0 + drift_x1) / 2, drift_y + 0.65,
            "7.  Vectorised intra-period drift",
            ha="center", fontsize=9, weight="bold", color=PAL["data"])
    ax.text((drift_x0 + drift_x1) / 2, drift_y + 0.30,
            "daily weights evolve via cumulative growth factors\n"
            "no daily reapplication of target weights",
            ha="center", fontsize=7.8, color=PAL["ink"])
    # Carry-over arrow into Q+1 marker
    _arrow(ax, drift_x1, drift_y + 0.45, 9.97, timeline_y + 0.20,
           color=PAL["data"], lw=1.0)
    ax.text(9.95, drift_y + 1.05,
            "drifted weights\n→ next rebalance",
            ha="right", fontsize=7.8, style="italic", color=PAL["data"])

    ax.set_xlim(0, 11.7)
    ax.set_ylim(-0.1, 9.6)
    ax.axis("off")

    out = OUT_DIR / "backtest_sequence.png"
    plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {out}")


# --------------------------------------------------------------------------- #
# Figure 4 — Eligibility Funnel (universe filtering cascade)                  #
# --------------------------------------------------------------------------- #
def render_eligibility_funnel():
    """Constant-width labelled bands with proportional fill bars to the right.

    Earlier version made the bottom rows unreadable because the bar shrank
    with the count.  Now every band is the same readable width; the count
    is encoded by a coloured fill on a fixed-width track inside it.
    """
    fig, ax = plt.subplots(figsize=(11, 7.5))

    stages = [
        ("Total universe",        "company_static (678 tickers)",            678, PAL["data"],      PAL["bg_data"]),
        ("Active universe",       "after dynamic delisted-detection",        605, PAL["data"],      PAL["bg_data"]),
        ("Pass value screen",     "value_score > 0",                         302, PAL["signal"],    PAL["bg_signal"]),
        ("Pass sentiment screen", "confidence > 0.3  (≈ ≥ 3 articles)",      210, PAL["signal"],    PAL["bg_signal"]),
        ("Pass leverage screen",  "debt_equity ≤ 2.0  (NaN passes)",         198, PAL["signal"],    PAL["bg_signal"]),
        ("Top 20% by composite",  "0.6 × value + 0.4 × sentiment",            40, PAL["portfolio"], PAL["bg_portfolio"]),
        ("Held portfolio",        "30–50 names · 5% per stock · 50% sector",  40, PAL["backtest"],  PAL["bg_backtest"]),
    ]

    n = len(stages)
    band_x = 1.0
    band_w = 9.0
    band_h = 0.65
    gap = 0.18
    max_count = stages[0][2]

    # Track inside each band where the fill bar lives
    track_x = band_x + 4.7
    track_w = 3.8
    track_h = 0.28

    for i, (label, sub, count, ec, fc) in enumerate(stages):
        y = (n - 1 - i) * (band_h + gap) + 0.6
        # Outer band
        ax.add_patch(FancyBboxPatch(
            (band_x, y), band_w, band_h,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor=fc, edgecolor=ec, linewidth=1.2,
        ))
        # Stage label (left)
        ax.text(band_x + 0.25, y + band_h / 2, label,
                ha="left", va="center", fontsize=9.5, weight="bold",
                color=PAL["ink"])
        # Sub-caption (under label)
        ax.text(band_x + 0.25, y + 0.13, sub,
                ha="left", va="center", fontsize=7.8, style="italic",
                color=PAL["muted"])
        # Fixed-width track + proportional fill
        track_y = y + (band_h - track_h) / 2
        ax.add_patch(Rectangle(
            (track_x, track_y), track_w, track_h,
            facecolor="#ffffff", edgecolor=PAL["muted"], linewidth=0.6,
        ))
        fill_w = max(0.06, track_w * (count / max_count))  # readable floor
        ax.add_patch(Rectangle(
            (track_x, track_y), fill_w, track_h,
            facecolor=ec, edgecolor=ec, linewidth=0.0, alpha=0.85,
        ))
        # Count to the right of the track
        ax.text(track_x + track_w + 0.18, y + band_h / 2,
                f"n = {count:,}",
                ha="left", va="center", fontsize=9, weight="bold", color=ec)
        # Drop arrow between bands
        if i < n - 1:
            _arrow(
                ax,
                band_x + band_w / 2, y - 0.03,
                band_x + band_w / 2, y - gap + 0.04,
                color=PAL["muted"], lw=0.9,
            )

    ax.text(5.5, 6.85,
            "Eligibility Funnel — From Universe to Held Portfolio",
            ha="center", fontsize=12.5, weight="bold", color=PAL["ink"])
    ax.text(5.5, 6.55,
            "Counts are illustrative for a representative quarterly rebalance "
            "and vary across the 10 rebalances in the sample.",
            ha="center", fontsize=8.5, style="italic", color=PAL["muted"])

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.0)
    ax.axis("off")

    out = OUT_DIR / "eligibility_funnel.png"
    plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {out}")


# --------------------------------------------------------------------------- #
# Figure 5 — Quality-weight composition for a representative article         #
# --------------------------------------------------------------------------- #
def render_quality_components():
    fig, ax = plt.subplots(figsize=(11, 4.6))

    components = [
        ("w_source",     "Reuters → tier 1",            1.00),
        ("w_relevance",  "headline +0.5, body +0.3",    0.80),
        ("w_recency",    "exp(-ln2/7 · 3) ≈ 0.74",      0.74),
        ("w_length",     "min(820 / 500, 1) = 1.00",    1.00),
    ]

    n = len(components)
    base_y = 1.8
    h = 0.6
    bar_max_w = 2.3
    gap = 0.5
    total_w = n * bar_max_w + (n - 1) * gap
    start_x = (11 - total_w) / 2

    for i, (name, sub, value) in enumerate(components):
        x = start_x + i * (bar_max_w + gap)
        # Bar background (full)
        ax.add_patch(FancyBboxPatch(
            (x, base_y), bar_max_w, h,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor=PAL["bg_card"], edgecolor=PAL["muted"], linewidth=0.8,
        ))
        # Filled portion (value)
        ax.add_patch(Rectangle(
            (x, base_y), bar_max_w * value, h,
            facecolor=PAL["bg_signal"], edgecolor=PAL["signal"], linewidth=1.0,
        ))
        ax.text(x + bar_max_w / 2, base_y + h / 2,
                f"{value:.2f}", ha="center", va="center",
                fontsize=11, weight="bold", color=PAL["signal"])
        ax.text(x + bar_max_w / 2, base_y + h + 0.18,
                name, ha="center", fontsize=9, weight="bold", color=PAL["ink"])
        ax.text(x + bar_max_w / 2, base_y - 0.18,
                sub, ha="center", fontsize=7.5, color=PAL["muted"], style="italic")
        # Multiplication signs between
        if i < n - 1:
            ax.text(x + bar_max_w + gap / 2, base_y + h / 2,
                    "×", ha="center", va="center", fontsize=18, color=PAL["muted"])

    # Result box
    composite = 1.00 * 0.80 * 0.74 * 1.00
    ax.text(5.5, 0.95, f"= composite weight  w  =  {composite:.2f}",
            ha="center", fontsize=11, weight="bold", color=PAL["signal"])
    ax.text(5.5, 0.55,
            "Multiplicative structure: a low score on any one component "
            "pulls the whole article weight down.",
            ha="center", fontsize=8, style="italic", color=PAL["muted"])

    # Title
    ax.text(5.5, 4.05,
            "Quality-Weighted Sentiment — Worked Example",
            ha="center", fontsize=12.5, weight="bold", color=PAL["ink"])
    ax.text(5.5, 3.75,
            "Reuters story, 820 words, company in headline + body, 3 days old",
            ha="center", fontsize=9, style="italic", color=PAL["muted"])

    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    out = OUT_DIR / "quality_weight_components.png"
    plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {out}")


if __name__ == "__main__":
    render_module_architecture()
    render_signal_pipeline()
    render_backtest_sequence()
    render_eligibility_funnel()
    render_quality_components()
