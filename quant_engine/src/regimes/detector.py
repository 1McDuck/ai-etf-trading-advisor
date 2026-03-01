# quant_engine/src/regimes/detector.py
#
# Regime detection using a Gaussian Mixture Model (GMM).
#
# A GMM is used rather than k-means because financial return distributions are
# non spherical - each regime tends to have its own covariance structure. 
# Using covariance_type="full" lets each component have its own shape.
#
# The raw cluster integers assigned by the GMM have no fixed semantic meaning
# (cluster 0 is not always "risk-off"). The pipeline.py module remaps them to
# named labels ("risk-on", "neutral", "risk-off") by ranking clusters by their
# mean VIX level after fitting.
#
# A 5-day rolling mode smoother is applied to the raw labels to reduce
# day-to-day regime flipping caused by borderline observations.

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

# Default number of regime states (risk-on, neutral, risk-off)
N_COMPONENTS = 3

# Number of days for the rolling mode smoothing window
SMOOTH_WINDOW = 5


# Fit a Gaussian Mixture Model to the regime feature matrix
# Features are standardised first so that scale differences don't dominate clustering
# n_init=5 reruns the EM algorithm from five different starting points to reduce
# sensitivity to initialisation — keeps whichever run had the best log-likelihood
def fit_regime_model(
        features: pd.DataFrame,
        n_components: int = N_COMPONENTS,
        random_state: int = 42
) -> tuple[GaussianMixture, StandardScaler]:
    # features: DataFrame of daily regime features (output of build_regime_features)
    # n_components: number of GMM components (regimes) to fit
    # random_state: random seed for reproducibility
    # returns: tuple of (fitted GaussianMixture, fitted StandardScaler)
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


# Predict regime labels and confidence scores for each day in the feature set
# Raw labels are smoothed with a rolling mode so transient single-day changes get absorbed
# Confidence = max posterior probability across all components for each day
def predict_regimes(
        gmm: GaussianMixture,
        scaler: StandardScaler,
        features: pd.DataFrame,
        smooth_window: int = SMOOTH_WINDOW
) -> tuple[pd.Series, pd.Series]:
    # gmm: fitted GaussianMixture model
    # scaler: fitted StandardScaler used during training
    # features: DataFrame of daily regime features (same columns as training)
    # smooth_window: rolling window size for the mode smoother
    # returns: tuple of (smoothed label Series, confidence Series), both indexed by date
    X = scaler.transform(features.values)
    raw_labels = gmm.predict(X)
    prediction = gmm.predict_proba(X)

    # Confidence = the highest posterior probability for each observation
    confidence = prediction.max(axis=1)

    labels = pd.Series(raw_labels, index=features.index, name="regime")
    confidence_series = pd.Series(confidence, index=features.index, name="confidence")

    # Apply rolling mode to smooth out noisy one-day regime changes
    smoothed = (
        labels.rolling(window=smooth_window, min_periods=1, center=False)
            .apply(lambda x: pd.Series(x).mode().iloc[0])
            .astype(int)
    )
    smoothed.name = "regime"

    return smoothed, confidence_series


# Compute the Markov-chain regime transition probability matrix
# Counts consecutive-day regime transitions (from label t to label t+1)
# and normalises each row to give probabilities
# High diagonal = regime is persistent; off-diagonal = probability of switching
def transition_matrix(labels: pd.Series) -> pd.DataFrame:
    # labels: Series of integer regime labels indexed by date
    # returns: DataFrame of shape (n_regimes, n_regimes) where entry [i, j]
    # is the probability of transitioning from regime i to regime j
    unique = sorted(labels.unique())
    counts = pd.DataFrame(0, index=unique, columns=unique)

    # Count each consecutive pair of regime labels
    for t0, t1 in zip(labels.iloc[:-1], labels.iloc[1:]):
        counts.loc[t0, t1] += 1

    # Normalise rows to convert counts into probabilities
    probs = counts.div(counts.sum(axis=1), axis=0).fillna(0)
    probs.index.name = "from"
    probs.columns.name = "to"

    return probs
