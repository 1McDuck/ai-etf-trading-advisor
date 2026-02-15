
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

from src.backtest.engine import run_backtest
from src.backtest.strategy import build_weights_schedule
from src.backtest.tearsheet import build_tearsheet, _drawdown_series, _annual_returns


# Helpers
ETF_NAMES = ["XLK", "XLF", "XLY", "XLP", "XLE", "XLI", "XLV"]



def _make_etf_prices(n: int=300, seed: int=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.DataFrame({e: 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n))) for e in ETF_NAMES}, index=idx)

def _make_benchmark(n: int=300, seed: int=0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0002, 0.008, n))), index=idx)

def _make_weights_schedule(n_rebalances: int = 20) -> pd.DataFrame:
    idx = pd.bdate_range("2010-01-01", periods=n_rebalances * 21)[::21][:n_rebalances]
    equal = 1.0/len(ETF_NAMES)
    return pd.DataFrame(equal, index=idx, columns=ETF_NAMES)

def _make_wide_features(n: int=300) -> pd.DataFrame:
    from src.features.etf_features import build_etf_features
    etf = _make_etf_prices(n)
    bench = _make_benchmark(n)
    rng = np.random.default_rng(5)
    regimes = pd.Series(rng.integers(0,3, size=n), index=pd.bdate_range("2010-01-01", periods=n))
    return build_etf_features(etf, bench, regimes)

def _make_trained_model(n: int=300) -> RandomForestClassifier:
    # RF trained on synthetic data
    from src.prediction.pipeline import wide_to_long_feature_matrix, build_targets_long, FEATURE_COLUMNS
    wide = _make_wide_features(n)
    etf = _make_etf_prices(n)
    bench = _make_benchmark(n)
    long_df = wide_to_long_feature_matrix(wide, ETF_NAMES)
    long_df = build_targets_long(long_df, etf_prices=etf, benchmark=bench)
    X = long_df[FEATURE_COLUMNS]
    y = long_df["target"]
    m = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=0, n_jobs=1)
    m.fit(X, y)

    return m


# Engine tests:
def test_engine_returns_keys():
    etf = _make_etf_prices()
    bench = _make_benchmark()
    weights_schedule = _make_weights_schedule()
    result = run_backtest(etf, bench, weights_schedule)

    assert set(result.keys()) == {"portfolio_returns", "benchmark_returns", "turnover"}

def test_engine_portfolio_lenth_matches_etf():
    etf = _make_etf_prices()
    bench = _make_benchmark()
    weights_schedule = _make_weights_schedule()
    result = run_backtest(etf, bench, weights_schedule)

    assert len(result["portfolio_returns"]) == len(etf)

def test_engine_turnover_non_negative():
    etf = _make_etf_prices()
    bench = _make_benchmark()
    weights_schedule = _make_weights_schedule()
    result = run_backtest(etf, bench, weights_schedule)

    assert (result["turnover"] >= 0).all()

def test_engine_equal_weight_returns_finite():
    etf = _make_etf_prices()
    bench = _make_benchmark()
    weights_schedule = _make_weights_schedule()
    result = run_backtest(etf, bench, weights_schedule)

    assert result["portfolio_returns"].isna().sum() == 0


# Strategy tests:
def test_weights_schedule_columns_match_etfs():
    wide = _make_wide_features()
    regimes = pd.Series(np.random.default_rng(0).integers(0,3, len(wide)), index=wide.index)
    model = _make_trained_model()
    weights_schedule = build_weights_schedule(wide, regimes, model, ETF_NAMES)

    assert set(weights_schedule.columns) == set(ETF_NAMES)


def test_weights_schedule_rows_sum_to_one():
    wide = _make_wide_features()
    regimes = pd.Series(np.random.default_rng(0).integers(0,3, len(wide)), index=wide.index)
    model = _make_trained_model()
    weights_schedule = build_weights_schedule(wide, regimes, model, ETF_NAMES)
    rows_sums = weights_schedule.sum(axis=1)

    assert (abs(rows_sums - 1.0) < 1e-9).all()

def test_weights_are_non_negative():
    wide = _make_wide_features()
    regimes = pd.Series(np.random.default_rng(0).integers(0,3, len(wide)), index=wide.index)
    model = _make_trained_model()
    weights_schedule = build_weights_schedule(wide, regimes, model, ETF_NAMES)
    
    assert (weights_schedule >= 0).all().all()


# Tearsheet tests

def test_drawdown_is_non_positive():
    rng = np.random.default_rng(0)
    cum = pd.Series(np.exp(np.cumsum(rng.normal(0,0.01,252))))
    dd = _drawdown_series(cum)

    assert (dd <= 0).all()

def test_annual_returns_years_correct():
    idx = pd.bdate_range("2010-01-01", periods=500)
    returns = pd.Series(np.zeros(len(idx)), index=idx)
    annual = _annual_returns(returns)

    assert set(annual.index).issubset({2010,2011,2012})

def test_build_tearsheet_returns_fig_and_dict():
    import matplotlib
    matplotlib.use("Agg")

    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2010-01-01", periods=252)
    portfolio = pd.Series(rng.normal(0.0005, 0.01, 252), index=idx)
    benchmark = pd.Series(rng.normal(0.0004, 0.009, 252), index=idx)
    turnover = pd.Series(np.abs(rng.normal(0, 0.02, 252)), index=idx)

    fig, stats = build_tearsheet(portfolio, benchmark, turnover)

    import matplotlib.pyplot as plt
    assert isinstance(fig, plt.Figure)
    assert isinstance(stats, dict)
    assert "Sharpe (Strategy)" in stats
    plt.close("all")