# quant_engine/src/regimes/pipeline.py
#
# End-to-end regime detection pipeline.
#
# Runs the full sequence:
# 1. Download macro and benchmark price data (yfinance)
# 2. Build the regime feature matrix (trend, volatility, drawdown, VIX, cross-asset)
# 3. Fit a Gaussian Mixture Model to the features
# 4. Predict and smooth the regime labels
# 5. Compute the regime transition probability matrix
# 6. Return everything in a RegimeResult dataclass
#
# Everything the frontend needs is in RegimeResult - labels, features, model objects, prices.
#
# Note on label assignment:
# GMM cluster IDs are arbitrary - cluster 0 isn't always "risk-off".
# _assign_regime_labels() maps them to named labels by sorting clusters by mean VIX level.

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from src.data.ingestion import get_price_data, multi_tickers, MACRO_TICKERS, BENCHMARK_TICKER
from src.features.regime_features import build_regime_features
from src.regimes.detector import fit_regime_model, predict_regimes, transition_matrix


# Container holding all the outputs from a completed regime detection run
@dataclass
class RegimeResult:
    # labels: smoothed integer regime labels (0, 1, 2) indexed by date
    # confidence: max posterior probability per day (how certain the GMM was)
    # features: the feature matrix used to fit the GMM
    # transition_matrix: regime-to-regime switching probability matrix
    # gmm: fitted GaussianMixture model
    # scaler: fitted StandardScaler used during GMM training
    # benchmark_prices: MSCI World prices aligned to the label date index
    # macro_prices: macro price series (VIX, Gold, etc.) aligned to labels
    labels: pd.Series
    confidence: pd.Series
    features: pd.DataFrame
    transition_matrix: pd.DataFrame
    gmm: GaussianMixture
    scaler: StandardScaler
    benchmark_prices: pd.Series
    macro_prices: pd.DataFrame

    # Sort clusters by mean VIX: lowest = "risk-on", middle = "neutral", highest = "risk-off"
    def label_names(self) -> pd.Series:
        regime_map = _assign_regime_labels(self.labels, self.features)
        return self.labels.map(regime_map)


# Run the full regime detection pipeline from data download to results
def run_regime_pipeline(        
        start: str = "2000-01-01",
        end: str | None = None,
        n_regimes: int = 3,
        smooth_window: int = 5,
        random_state: int = 42
) -> RegimeResult:
    # start: start date in YYYY-MM-DD format
    # end: end date in YYYY-MM-DD format (defaults to today)
    # n_regimes: number of GMM components (regime states) to fit
    # smooth_window: rolling window size for the mode smoother (days)
    # random_state: random seed for GMM reproducibility
    # returns: RegimeResult containing labels, features, model objects and price data
    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    print(f"[Pipeline] Downloading macro data start:{start} ... end:{end}")
    macro = multi_tickers(MACRO_TICKERS, start=start, end=end)

    print(f"[Pipeline] Downloading benchmark data {BENCHMARK_TICKER}")
    benchmark = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    print(f"[Pipeline] Building Regime Features")
    features = build_regime_features(
        msci=benchmark,
        gold=macro["GOLD"],
        usdidx=macro["USDIDX"],
        vix=macro["VIX"]
    )

    print(f"[Pipeline] Fitting GMM ({n_regimes} regimes, {len(features)} observations)")
    gmm, scaler = fit_regime_model(features, n_components=n_regimes, random_state=random_state)

    print(f"[Pipeline] Predicting Regimes")
    labels, confidence = predict_regimes(gmm, scaler, features, smooth_window=smooth_window)

    trans_matrix = transition_matrix(labels)

    print("[Pipeline] Done")
    print(f"--- Regime Distribution:")
    print(f"{labels.value_counts().sort_index().to_string()}")
    print(f"--- Transition Matrix:")
    print(f"{trans_matrix.to_string()}")

    result = RegimeResult(
        labels=labels,
        confidence=confidence,
        features=features,
        transition_matrix=trans_matrix,
        gmm=gmm,
        scaler=scaler,
        # Align benchmark and macro prices to the label index (features drop early NaN rows)
        benchmark_prices=benchmark.loc[labels.index],
        macro_prices=macro.loc[labels.index]
    )

    return result


# Map integer GMM cluster IDs to semantic regime names using mean VIX level
# GMM cluster IDs are arbitrary - this resolves the ambiguity by computing the
# mean VIX for each cluster and sorting: lowest = "risk-on", middle = "neutral", highest = "risk-off"
# If the VIX feature is absent (e.g. during testing), returns generic "regime_N" labels
def _assign_regime_labels(labels: pd.Series, features: pd.DataFrame) -> dict[int, str]:
    vix_col = "vix_level_1m"
    if vix_col not in features.columns:
        return {i: f"regime_{i}" for i in labels.unique()}

    # Compute mean VIX for each cluster and sort from lowest to highest
    mean_vix = (
        features[[vix_col]]
            .assign(regime=labels)
            .groupby("regime")[vix_col]
            .mean()
            .sort_values()
    )

    ordered = mean_vix.index.tolist()
    label_names = ["risk-on", "neutral", "risk-off"]
    return dict(zip(ordered, label_names))