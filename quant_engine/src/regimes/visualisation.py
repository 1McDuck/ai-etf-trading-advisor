# quant_engine/src/regimes/visualisation.py

# Regime visulisation
# Produces 2 charts:
# 1. Regime overlay, the MSCI world px history with coloured backtground showing each regime per period
# 2. Transition heatmap, regime switching probability matrix
# Both functions return a matplotlib fig so when called can choose to save, display or embed in the webapp response

from __future__ import annotations

import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


REGIME_COLOURS = {
    "risk-on" "#2ecc71", #green
    "neutral" "#f39c12", #orange
    "risk-off" "#e74c3c" #red
}

DEFAULT_INT_COLOURS = {
    0: "#e74c3c",
    1: "#f39c12",
    2: "#2ecc71"
}

# Helper

def _add_regime_spans(ax: plt.Axes, labels: pd.Series, colour_map: dict) -> None:
    # fill the background with coloured vertical spands for each regime block
    dates = labels.index
    current_regime = labels.iloc[0]
    block_start = dates[0]

    for date, regime in zip(dates[1:], labels.iloc[1:]):
        if regime != current_regime:
            ax.axvspan(block_start, date, color=colour_map.get(current_regime, "#999999"), alpha=0.25, linewidth=0)
            block_start = date
            current_regime = regime
        
    
    # last block
    ax.axvspan(block_start, dates[-1], color=colour_map.get(current_regime, "#999999"), alpha=0.25, linewidth=0)






def plot_regime_overlay(
    prices: pd.Series,
    labels: pd.Series,
    label_names: pd.Series | None = None,
    title: str = "Market Regime Detection: MSCI World",
    figsize: tuple[int,int] = (14,5)
) -> plt.Figure:
    # plot price history with shaded regimes
    # Params:
    # - prices: benchmark price series
    # - labels: int regime labels
    # - label_names: str labels (risk-on, risk-off, neutral)

    # Align series to common dates
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

    # Draw coloured background spans for each regime block
    _add_regime_spans(ax, display_labels, colour_map)

    # Plot price on top
    ax.plot(prices.index, prices.values, color="black", linewidth=1.2, zorder=5)
    ax.set_yscale("log")
    ax.set_ylabel("Price (log scale)", fontsize=11)
    ax.set_xlabel("")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Legend
    patches = [mpatches.Path(color=col, label=str(lab)) for lab, col in sorted(colour_map.items(), key=lambda x: str(x[0]))]
    ax.legend(handles=patches, loc="upper left", framealpha=0.8, fontsize=10)

    fig.tight_layout()
    return fig


def plot_transition_heatmap(
    trans_matrix: pd.DataFrame,
    title: str = "Regime Transition Probabilities",
    figsize: tuple[int, int] = (5,4)
) -> plt.Figure:
    # Plot regime transition probabilitiy matrix as heatmap
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(trans_matrix.values, vmin=0, vmax=1, cmap="YlOrRd")
    fig.colourbar(im, ax=ax, label="Probability")

    labels = [str(c) for c in trans_matrix.columns]
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("To Regime")
    ax.set_ylabel("From Regime")
    ax.set_title(title, fontsize=12, fontweight="bold")

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j,i, f"{trans_matrix.values[i,j]:.2f}", ha="center", va="center", fontsize=10, color="black" if trans_matrix.values[i,j] < 0.7 else "white")
    
    fig.tight_layout()
    return fig


