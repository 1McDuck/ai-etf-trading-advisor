# quant_engine/src/regimes/visualisation.py
#
# Matplotlib charts for visualising regime detection results.
#
# Two charts are produced:
# 1. Regime overlay: benchmark price history with coloured background shading
#                    showing which regime was active during each period.
# 2. Transition heatmap: the regime-to-regime switching probability matrix shown
#                        as a colour-coded grid.
#
# Both return a Figure - can save it, show it, or send it via the API.

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# Colours for named regime labels (used when label_names are available)
REGIME_COLOURS = {
    "risk-on":  "#2ecc71", # green: bullish
    "neutral":  "#f39c12", # orange: uncertainty/doubt 
    "risk-off": "#e74c3c" # red: bearish
}

# Fallback colours for raw integer labels (before semantic mapping is applied)
DEFAULT_INT_COLOURS = {
    0: "#e74c3c",
    1: "#f39c12",
    2: "#2ecc71"
}


# Shade the chart background with coloured vertical spans for each regime block
# Instead of colouring every individual day, this finds contiguous runs of the same
# label and draws a single axvspan per block - much faster and cleaner visuals
def _add_regime_spans(ax: plt.Axes, labels: pd.Series, colour_map: dict) -> None:
    # ax: matplotlib Axes to draw on
    # labels: Series of regime labels (int or str) indexed by date
    # colour_map: dict mapping label value -> hex colour string
    dates = labels.index
    current_regime = labels.iloc[0]
    block_start = dates[0]

    for date, regime in zip(dates[1:], labels.iloc[1:]):
        if regime != current_regime:
            # Close the current block and start a new one
            ax.axvspan(block_start, date,
                       color=colour_map.get(current_regime, "#999999"),
                       alpha=0.25, linewidth=0)
            block_start = date
            current_regime = regime

    # Close the final block at the last date in the series
    ax.axvspan(block_start, dates[-1],
               color=colour_map.get(current_regime, "#999999"),
               alpha=0.25, linewidth=0)


# Plot benchmark price history with regime-shaded background
# If label_names (human-readable strings) are provided, the named colour scheme is used
# Otherwise the raw integer colours are used as a fallback
# Price axis is log-scaled so early periods don't get visually compressed
def plot_regime_overlay(
        prices: pd.Series,
        labels: pd.Series,
        label_names: pd.Series | None = None,
        title: str = "Market Regime Detection: MSCI World",
        figsize: tuple[int, int] = (14, 5)
) -> plt.Figure:
    # prices: Series of daily benchmark closing prices
    # labels: Series of integer regime labels aligned to the same index
    # label_names: optional Series of string regime labels ("risk-on", etc)
    # title: chart title
    # figsize: figure dimensions as (width, height) in inches
    # returns: matplotlib Figure

    # Align both series to their common date range
    common = prices.index.intersection(labels.index)
    prices = prices.loc[common]
    labels = labels.loc[common]

    if label_names is not None:
        label_names = label_names.loc[common]
        colour_map = {v: REGIME_COLOURS.get(v, "#999999") for v in label_names.unique()}
        display_labels = label_names
    else:
        colour_map = {k: DEFAULT_INT_COLOURS.get(k, "#999999") for k in labels.unique()}
        display_labels = labels

    fig, ax = plt.subplots(figsize=figsize)

    # Draw the coloured background spans first so the price line sits on top
    _add_regime_spans(ax, display_labels, colour_map)

    ax.plot(prices.index, prices.values, color="black", linewidth=1.2, zorder=5)
    ax.set_yscale("log")
    ax.set_ylabel("Price (log scale)", fontsize=11)
    ax.set_xlabel("")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Build a legend patch for each unique regime colour
    patches = [
        mpatches.Patch(color=col, label=str(lab))
        for lab, col in sorted(colour_map.items(), key=lambda x: str(x[0]))
    ]
    ax.legend(handles=patches, loc="upper left", framealpha=0.8, fontsize=10)

    fig.tight_layout()
    return fig


# Plot the regime transition probability matrix as a colour-coded heatmap
# Cell colour intensity encodes probability (light=low, dark=high)
# Each cell is annotated with its numeric value
# Text colour inverts to white for dark cells (probability > .7) to stay readable
def plot_transition_heatmap(
        trans_matrix: pd.DataFrame,
        title: str = "Regime Transition Probabilities",
        figsize: tuple[int, int] = (5, 4)
) -> plt.Figure:
    # trans_matrix: square DataFrame of transition probabilities (output of transition_matrix()) 
    #               rows = from-regime, cols = to-regime
    # title: chart title
    # figsize: figure dimensions as (width, height)
    # returns: matplotlib Figure
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(trans_matrix.values, vmin=0, vmax=1, cmap="YlOrRd")
    fig.colorbar(im, ax=ax, label="Probability")

    labels = [str(c) for c in trans_matrix.columns]
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("To Regime")
    ax.set_ylabel("From Regime")
    ax.set_title(title, fontsize=12, fontweight="bold")

    # Annotate each cell with its probability value
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = trans_matrix.values[i, j]
            text_colour = "white" if val > 0.7 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=10, color=text_colour)

    fig.tight_layout()
    return fig
