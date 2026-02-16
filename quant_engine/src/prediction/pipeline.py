# quant_engine/src/prediction/pipeline.py

# ETF ranking model
# Training and evaluation pipeline
# Data shape convention:
# Features are built wide. one row per day, all etfs as cols
# for the model, reshape to a long format with:
# - index = (date, etf_names)
# - columns = [mom_m1, mom_3m, vol_1m, vol3m, rel_str_3m, regime]
# - target = 1 if the ETF forward 60d return > bench forward 60d return

# Random forest learns a single ranking function across all etfs rather than one model per sector.

# Targets are calculated by shifting returns back in the feature space

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

# prediction window
FORWARD_WINDOW = 60 
FEATURE_COLUMNS = ["mom_1m", "mom_3m", "vol_1m", "vol_3m", "rel_str_3m", "regime"]

@dataclass
class RankingTrainResult:
    model: RandomForestClassifier
    cv_hit_rate_mean: float
    cv_hit_rate_std: float
    cv_log_loss_mean: float
    feature_importances: pd.Series
    etf_names: list[str]
    long_df: pd.DataFrame  #(date, etf) training frame with featurs and target


def wide_to_long_feature_matrix(wide_features: pd.DataFrame, etf_names: list[str]) -> pd.DataFrame:
    # Reshape wide feature df to long format for the model training
    # wide_features columns are: {ETF}_mom_1m ...
    # long output index: (date, etf)
    # long output columns: mom_1m ...

    rows = []
    for etf in etf_names:
        etf_columns = {
            "mom_1m": f"{etf}_mom_1m",
            "mom_3m": f"{etf}_mom_3m",
            "vol_1m": f"{etf}_vol_1m",
            "vol_3m": f"{etf}_vol_3m",
            "rel_str_3m": f"{etf}_rel_str_3m",
        }
        etf_df = wide_features[[*etf_columns.values(), "regime"]].copy()
        etf_df = etf_df.rename(columns={v: k for k,v in etf_columns.items()})
        etf_df["etf"] = etf
        rows.append(etf_df)

    long = pd.concat(rows).reset_index().rename(columns={"index": "date"})

    return long.set_index(["date", "etf"]).sort_index()


def build_targets_long(
    long_df: pd.DataFrame,
    etf_prices: pd.DataFrame,
    benchmark: pd.Series,
    forward_window: int= FORWARD_WINDOW,
) -> pd.DataFrame:
    # target column: 1 if ETF outperforms bench over next forward window days
    # drop rows without a valid forward return

    etf_log = np.log(etf_prices/etf_prices.shift(1))
    bench_log = np.log(benchmark/benchmark.shift(1))

    # forward cum returns: shift back by forward_window
    etf_fwd = etf_log.rolling(forward_window).sum().shift(-forward_window)
    bench_fwd = bench_log.rolling(forward_window).sum().shift(-forward_window)

    records = []
    for (date, etf), row in long_df.iterrows():
        if etf not in etf_prices.columns:
            continue
        if date not in etf_fwd.index or pd.isna(etf_fwd.loc[date, etf]):
            continue
        if pd.isna(bench_fwd.loc[date]):
            continue
        outperforms = int(etf_fwd.loc[date, etf] > bench_fwd.loc[date])
        records.append({**row.to_dict(), "date": date, "etf": etf, "target": outperforms})

    result = pd.DataFrame(records).set_index(["date", "etf"])

    return result.dropna()


def train_ranking_model(
    long_df: pd.DataFrame,
    n_splits: int = 5,
    n_estimators: int = 300,
    random_state: int = 42
) -> RankingTrainResult:
    # training a random forest on the long feature matric with temporal cv
    
    X = long_df[FEATURE_COLUMNS]
    y = long_df["target"]

    # temporal cv split on the date level which avoids look ahead leak
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
        probability = m.predict_proba(X[mask_test])[:,1]
        
        hit_rates.append(accuracy_score(y[mask_test], predictions))
        log_loss_cv.append(log_loss(y[mask_test], probability))

    # final model on all data
    final_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=5,
        min_samples_leaf=20,
        random_state=random_state,
        n_jobs=-1
    )
    
    final_model.fit(X,y)

    importances = pd.Series(final_model.feature_importances_, index=FEATURE_COLUMNS, name="importance").sort_values(ascending=False)
    
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


def run_ranking_pipeline(
    start: str = "2000-01-01",
    end: str | None = None,
    regime_result: RegimeResult | None = None
) -> RankingTrainResult:
    # full pipeline: download etf prices, get features, targets, train.

    # if regime_result is passed from a prior run it will be reused to save download calls

    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    print(f"[Ranking] Downloading sector ETF prices from {start} to {end}")
    
    etf_prices = multi_tickers(SECTOR_ETFS, start=start, end=end)
    benchmark = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    if regime_result is None:
        print(f"[Ranking] Running regime pipeline ...")
        regime_result = run_regime_pipeline(start=start, end=end)

    print(f"[Ranking] Building ETF Features")
    wide_features = build_etf_features(etf_prices=etf_prices, benchmark=benchmark, regime_labels=regime_result.labels)

    etf_names = list(etf_prices.columns)
    print(f"[Ranking] Reshaping to long format ({len(etf_names)} ETFs x{len(wide_features)} dates)")
    long_df = wide_to_long_feature_matrix(wide_features, etf_names)

    print(f"[Ranking] Building targets")
    long_df = build_targets_long(long_df, etf_prices=etf_prices, benchmark=benchmark)

    print(f"[Ranking] Training (n={len(long_df)} samples, pos rate={long_df['target'].mean():.1%})")
    result = train_ranking_model(long_df)

    print(f"[Ranking] CV hit rate: {result.cv_hit_rate_mean: .1%} plus/minus {result.cv_hit_rate_std:.1%}")
    print(f"[Ranking] Feature importances: ")
    print(f"{result.feature_importances.to_string()}")
    
    return result
