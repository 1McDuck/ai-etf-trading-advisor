# quant_engine/src/prediction/pipeline.py
#
# ETF ranking model: training and evaluation pipeline.
#
# Goal: predict which sector ETFs will outperform the benchmark over the next
# 60 trading days (roughly 3 months). Framed as binary classification. 
# Target = 1 if the ETF's forward return beats the benchmark's forward return, 0 otherwise.
#
# Data shape convention:
# - Features are built wide: one row per day, all ETF features as columns
# - For model training, this is reshaped to long format with index (date, etf)
#   and columns [mom_1m, mom_3m, vol_1m, vol_3m, rel_str_3m, regime]
# - The long format lets the Random Forest learn a single ranking function
#   across all ETFs rather than training a separate model per sector
#
# To avoid lookahead bias:
# - Forward returns are computed by shifting prices backward in the feature space,
#   meaning the target for date T uses prices from T to T+60
# - Cross-validation uses TimeSeriesSplit so the model is never tested on
#   data that was visible during training

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, log_loss

from src.data.ingestion import multi_tickers, get_price_data, SECTOR_ETFS, BENCHMARK_TICKER
from src.features.etf_features import build_etf_features
from src.regimes.pipeline import run_regime_pipeline, RegimeResult

# Forward prediction window in trading days (roughly 3 calendar months)
FORWARD_WINDOW = 63

# Feature columns the model is trained on - order must match at inference time
FEATURE_COLUMNS = ["mom_1m", "mom_3m", "vol_1m", "vol_3m", "rel_str_3m", "regime"]


# Container for all the outputs from a completed ranking model training run
@dataclass
class RankingTrainResult:
    # model: final RandomForest trained on the full dataset
    # cv_hit_rate_mean: mean hit rate (accuracy) across CV folds
    # cv_hit_rate_std: standard deviation of hit rate across CV folds
    # cv_log_loss_mean: mean log-loss across CV folds
    # feature_importances: feature importance scores from the final model
    # etf_names: list of ETF names the model was trained on
    # long_df: the (date, etf) training DataFrame with features and targets
    model: RandomForestClassifier
    cv_hit_rate_mean: float
    cv_hit_rate_std: float
    cv_log_loss_mean: float
    feature_importances: pd.Series
    etf_names: list[str]
    long_df: pd.DataFrame


# Reshape the wide ETF feature matrix to long format for model training
# Wide columns like "XLK_mom_1m" are renamed to "mom_1m" and stacked so each row represents one (date, ETF) observation
def wide_to_long_feature_matrix(wide_features: pd.DataFrame, etf_names: list[str]) -> pd.DataFrame:
    # wide_features: wide feature DataFrame (one row per day, columns = {ETF}_{feature})
    # etf_names: list of ETF names to extract features for
    # returns: DataFrame with MultiIndex (date, etf) and columns = FEATURE_COLUMNS
    rows = []
    for etf in etf_names:
        # Map generic feature names to their ETF-specific column names
        etf_columns = {
            "mom_1m": f"{etf}_mom_1m",
            "mom_3m": f"{etf}_mom_3m",
            "vol_1m": f"{etf}_vol_1m",
            "vol_3m": f"{etf}_vol_3m",
            "rel_str_3m": f"{etf}_rel_str_3m",
        }
        etf_df = wide_features[[*etf_columns.values(),"regime"]].copy()
        etf_df = etf_df.rename(columns={v: k for k, v in etf_columns.items()})
        etf_df["etf"] = etf
        rows.append(etf_df)

    long = pd.concat(rows).reset_index().rename(columns={"index": "date"})

    return long.set_index(["date", "etf"]).sort_index()


# Add binary outperformance targets to the long-format feature DataFrame
# Target = 1 if the ETF's forward return beats the benchmark over forward_window days
# Rows near the end without a full forward window of data are dropped
def build_targets_long(
        long_df: pd.DataFrame,
        etf_prices: pd.DataFrame,
        benchmark: pd.Series,
        forward_window: int = FORWARD_WINDOW,
) -> pd.DataFrame:
    # long_df: long-format feature DataFrame with (date, etf) index
    # etf_prices: DataFrame of daily ETF closing prices
    # benchmark: Series of daily benchmark closing prices
    # forward_window: number of trading days to look ahead for the target
    # returns: DataFrame with "target" column added, NaN rows dropped
    etf_log = np.log(etf_prices / etf_prices.shift(1))
    bench_log = np.log(benchmark / benchmark.shift(1))

    # Compute rolling forward returns and shift them back to align with today's features
    etf_fwd = etf_log.rolling(forward_window).sum().shift(-forward_window)
    bench_fwd = bench_log.rolling(forward_window).sum().shift(-forward_window)

    records = []
    for (date, etf), row in long_df.iterrows():
        if etf not in etf_prices.columns:
            continue
        # Skip rows that fall outside the available forward return window
        if date not in etf_fwd.index or pd.isna(etf_fwd.loc[date,etf]):
            continue
        if pd.isna(bench_fwd.loc[date]):
            continue
        outperforms = int(etf_fwd.loc[date, etf] > bench_fwd.loc[date])
        records.append({**row.to_dict(), "date": date, "etf": etf, "target": outperforms})

    result = pd.DataFrame(records).set_index(["date","etf"])

    return result.dropna()


# Train a Random Forest classifier to predict ETF outperformance
# Uses TimeSeriesSplit so test data is always after training data
# CV splits are made at the date level to keep all ETFs from the same day together
# After CV, a final model is trained on all data for use in the backtest
def train_ranking_model(
        long_df: pd.DataFrame,
        n_splits: int = 5,
        n_estimators: int = 300,
        random_state: int = 42
) -> RankingTrainResult:
    # long_df: long-format DataFrame with features and "target" column
    # n_splits: number of TimeSeriesSplit folds for cross-validation
    # n_estimators: number of trees in the Random Forest
    # random_state: random seed for reproducibility
    # returns: RankingTrainResult with the trained model and evaluation metrics
    X = long_df[FEATURE_COLUMNS]
    y = long_df["target"]

    # Split on unique dates to keep all ETFs from the same day in the same fold
    dates = X.index.get_level_values("date").unique().sort_values()
    time_series_cv = TimeSeriesSplit(n_splits=n_splits)
    hit_rates, log_loss_cv = [], []

    for train_idx, test_idx in time_series_cv.split(dates):
        train_dates = dates[train_idx]
        test_dates = dates[test_idx]
        mask_train = X.index.get_level_values("date").isin(train_dates)
        mask_test = X.index.get_level_values("date").isin(test_dates)

        m = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=5, 
            min_samples_leaf=20, 
            random_state=random_state,
            n_jobs=-1
        )

        m.fit(X[mask_train], y[mask_train])
        predictions = m.predict(X[mask_test])
        probability = m.predict_proba(X[mask_test])[:, 1]

        hit_rates.append(accuracy_score(y[mask_test], predictions))
        log_loss_cv.append(log_loss(y[mask_test], probability))

    # Train the final model on all available data for use in the backtest
    final_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=5,
        min_samples_leaf=20,
        random_state=random_state,
        n_jobs=-1
    )
    final_model.fit(X, y)

    importances = pd.Series(
        final_model.feature_importances_,
        index=FEATURE_COLUMNS,
        name="importance"
    ).sort_values(ascending=False)

    etf_names = list(long_df.index.get_level_values("etf").unique())

    return RankingTrainResult(
        model=final_model,
        cv_hit_rate_mean=float(np.mean(hit_rates)),
        cv_hit_rate_std=float(np.std(hit_rates)),
        cv_log_loss_mean=float(np.mean(log_loss_cv)),
        feature_importances=importances,
        etf_names=etf_names,
        long_df=long_df
    )


# Run the full ranking model pipeline end-to-end
# Downloads ETF prices, builds features, constructs targets and trains the model
# If a RegimeResult is provided from a prior run it will be reused to avoid
# redundant data downloads
def run_ranking_pipeline(
        start: str = "2000-01-01",
        end: str | None = None,
        regime_result: RegimeResult | None = None
) -> RankingTrainResult:
    # start: start date in YYYY-MM-DD format
    # end: end date in YYYY-MM-DD format (defaults to today)
    # regime_result: optional pre-computed RegimeResult to reuse
    # returns: RankingTrainResult with the trained model and CV metrics
    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    print(f"[Ranking] Downloading sector ETF prices from {start} to {end}")
    etf_prices = multi_tickers(SECTOR_ETFS, start=start, end=end)
    benchmark = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    if regime_result is None:
        print(f"[Ranking] Running regime pipeline...")
        regime_result = run_regime_pipeline(start=start, end=end)

    print(f"[Ranking] Building ETF Features")
    wide_features = build_etf_features(
        etf_prices=etf_prices,
        benchmark=benchmark,
        regime_labels=regime_result.labels
    )

    etf_names = list(etf_prices.columns)
    print(f"[Ranking] Reshaping to long format ({len(etf_names)} ETFs x {len(wide_features)} dates)")
    long_df = wide_to_long_feature_matrix(wide_features, etf_names)

    print(f"[Ranking] Building targets")
    long_df = build_targets_long(long_df, etf_prices=etf_prices, benchmark=benchmark)

    print(f"[Ranking] Training (n={len(long_df)} samples, pos rate={long_df['target'].mean():.1%})")
    result = train_ranking_model(long_df)

    print(f"[Ranking] CV hit rate: {result.cv_hit_rate_mean:.1%} +/- {result.cv_hit_rate_std:.1%}")
    print(f"[Ranking] Feature importances:")
    print(f"{result.feature_importances.to_string()}")

    return result
