# quant_engine/src/regimes/pipeline.py

# End to end regime detection pipeline
# 1. Downloads data 
# 2. Builds regime features
# 3. Fits GMM
# 4. Predicts
# 5. Transition matrix

# Returns a RegimeResult dataclass which has everything needed for the portfolio
# construction later.

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from src.data.ingestion import get_price_data, multi_tickers, MACRO_TICKERS, BENCHMARK_TICKER
from src.features.regime_features import build_regime_features
from src.regimes.detector import fit_regime_model, predict_regimes, transition_matrix

REGIME_LABELS = {0: "risk-off", 1: "neutral", 2: "risk-on"}

@dataclass
class RegimeResult:
    labels: pd.Series
    confidence: pd.Series
    features: pd.DataFrame
    transition_matrix: pd.DataFrame
    gmm: GaussianMixture
    scaler: StandardScaler
    benchmark_prices: pd.Series
    macro_prices: pd.DataFrame

    def label_names(self) -> pd.Series:
        regime_map = _assign_regime_labels(self.labels, self.features)
        return self.labels.map(regime_map)
    

def run_regime_pipeline(
        start: str = "2000-01-01",
        end: str | None = None,
        n_regimes: int = 3,
        smooth_window: int = 5,
        random_state: int = 42
) -> RegimeResult:
    # Full pipeline: downloads, features, GMM, regimes
    # Given
    # Start: date, start date (YYYY-MM-DD)
    # End: date, end date - default is today
    # n_regimes, number of regimes (GMM clusters)
    # smooth_window, days for the rolling smoothing
    # random_state, reproducibility seed

    # Return: RegimeResult with labels, confidence, features, transition matrix, model info

    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    print(f"[Pipeline] Downloading macro data start:{start} ... end:{end}")
    macro = multi_tickers(MACRO_TICKERS, start=start, end=end)

    print(f"[Pipeline] Downloading benchmark data {BENCHMARK_TICKER}")
    benchmark = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    print(f"[Pipeline] Building Regime Features")
    features = build_regime_features(
        msci = benchmark,
        gold = macro["GOLD"],
        usdidx = macro["USDIDX"],
        vix = macro["VIX"]
    )

    print(f"[Pipeline] Fitting GMM ({n_regimes} regimes, {len(features)} observations)")
    gmm, scaler = fit_regime_model(features, n_components=n_regimes, random_state=random_state)

    print(f"[Pipeline] Predicting Regimes")
    labels, confidence = predict_regimes(gmm, scaler, features, smooth_window=smooth_window)

    trans_matrix = transition_matrix(labels)

    print("[Pipeline] Done")
    print(f"---Regime Distribution: ")
    print(f"{labels.value_counts().sort_index().to_string()}")
    print(f"---Transition Matrix:")
    print(f"{trans_matrix.to_string()}")

    result = RegimeResult(
        labels=labels,
        confidence=confidence,
        features=features,
        transition_matrix=trans_matrix,
        gmm=gmm,
        scaler=scaler,
        benchmark_prices=benchmark.loc[labels.index],
        macro_prices=macro.loc[labels.index]
    )

    return result 

def _assign_regime_labels(labels: pd.Series, features: pd.DataFrame) -> dict[int, str]:
    # assign readable names to cluster out ints by VIX level per cluster.
    # Highest = risk-off
    # Lowest = risk-on

    vix_col = "vix_level_1m"
    if vix_col not in features.columns:
        return {i: f"regime_{i}" for i in labels.unique()}
    
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