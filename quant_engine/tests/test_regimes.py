import numpy as np
import pandas as pd

from src.regimes.detector import fit_regime_model, predict_regimes, transition_matrix


def _make_features(n: int=500, n_cols: int=11, seed: int=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = rng.normal(size=(n, n_cols))
    cols = [f"feat_{i}" for i in range(n_cols)]
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.DataFrame(data, index=idx, columns=cols)

def test_fit_returns_gmm_and_scaler():
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    
    features = _make_features()
    gmm, scaler = fit_regime_model(features)

    assert isinstance(gmm, GaussianMixture)
    assert isinstance(scaler, StandardScaler)


def test_predict_regimes_length():
    features = _make_features()
    gmm, scaler = fit_regime_model(features)
    labels, confidence = predict_regimes(gmm, scaler, features)

    assert len(labels) == len(features)
    assert len(confidence) == len(features)

def test_regime_labels_correct():
    features = _make_features()
    gmm, scaler = fit_regime_model(features)
    labels, _ = predict_regimes(gmm, scaler, features)

    assert set(labels.unique()).issubset({0,1,2})


def test_transition_matrix_rows_sum_to_one():
    features = _make_features()
    gmm, scaler = fit_regime_model(features)
    labels, _ = predict_regimes(gmm, scaler, features)
    trans_matrix = transition_matrix(labels)
    row_sums = trans_matrix.sum(axis=1)

    assert (abs(row_sums - 1) < 1e-9).all()