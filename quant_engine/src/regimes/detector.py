# quant_engine/src/regimes/detector.py

# Regime detection using Gaussian Mixture Model (GMM)

# Build:
# 3 components: risk-on, neural, risk-off
# 5 day rolling smoothing to reduce day flipping of regimes
# StandardScaler applied before the fitting

# Out:
# - regime_labels: pd.Series of int labels (0,1,2)
# - confidenceL pd.Series of max posterior probability per day
# - transition matrix: pd.DataFrame showing regime switching probabilities

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

N_COMPONENTS = 3
SMOOTH_WINDOW = 5


def fit_regime_model(
    features: pd.DataFrame,
    n_components: int = N_COMPONENTS,
    random_state: int = 42
) -> tuple[GaussianMixture, StandardScaler]:
    scaler = StandardScaler()
    X = scaler.fit_transform(features.values)

    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        random_state=random_state,
        n_init=5
    )

    gmm.fit(X)

    return gmm, scaler


def predict_regimes(
    gmm: GaussianMixture,
    scaler: StandardScaler,
    features: pd.DataFrame,
    smooth_window: int = SMOOTH_WINDOW
) -> tuple[pd.Series, pd.Series]:
    X = scaler.transform(features.values)
    raw_labels = gmm.predict(X)
    prediction = gmm.predict_proba(X)
    confidence = prediction.max(axis=1)

    labels = pd.Series(raw_labels, index=features.index, name="regime")
    confidence_series = pd.Series(confidence, index=features.index, name="confidence")

    # smooth with rolling mode to reduce noise
    smoothed = (
        labels.rolling(window=smooth_window, min_periods=1, center=False)
            .apply(lambda x: pd.Series(x).mode().iloc[0])
            .astype(int)
    )
    smoothed.name = "regime"
    return smoothed, confidence_series


def transition_matrix(labels: pd.Series) -> pd.DataFrame:
    unique = sorted(labels.unique())
    counts = pd.DataFrame(0, index=unique, columns=unique)
    for t0, t1 in zip(labels.iloc[:-1], labels.iloc[1:]):
        counts.loc[t0,t1] += 1

    probs = counts.div(counts.sum(axis=1), axis=0).fillna(0)
    probs.index.name = "from"
    probs.columns.name = "to"

    return probs
