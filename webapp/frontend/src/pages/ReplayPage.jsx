// pages/ReplayPage.jsx
//
// Backtest step-through replay (Live Replay mode).
// Lets the user walk through a completed backtest one rebalance period at a time, seeing what the model allocated at each step and how the portfolio performed up to that point.
// This is my version of a "live replay" mode, simulating how each trade decision would have looked to the user at the time it was made. And explaining the reasoning behind it with the regime info and charts.
//
// Phase 1 Run selector:
//  Lists all completed backtest runs. The user clicks one to load it. Full result payload is fetched via getTask() (same lazy-load pattern as ComparePage).
//
// Phase 2 Replay view:
//  Driven by a step index into weights_schedule.dates. At each step, all series (returns, regime, prices) are sliced up to the current rebalance date using sliceSeriesUpTo(). 
//  Charts receive the sliced data and recompute normally. Running stats are derived from the sliced returns.
//
// No backend changes needed, all the data is already in the backtest result payload.
//
// The trades panel computes position changes by diffing weights[step] against weights[step-1]. At step 0 every position is treated as a new open.

import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listBacktests, getTask } from '../api/client';
import { cumulativeGrowth, drawdownSeries } from '../utils/finance';
import { sliceSeriesUpTo } from '../utils/sliceByDate';
import TaskStatusBadge from '../components/common/TaskStatusBadge';
import ReplayControls from '../components/replay/ReplayControls';
import WeightsBarChart from '../components/charts/WeightsBarChart';
import CumulativeReturnsChart from '../components/charts/CumulativeReturnsChart';
import DrawdownChart from '../components/charts/DrawdownChart';
import RegimeOverlayChart from '../components/charts/RegimeOverlayChart';

// Colour classes for the regime label badge
const REGIME_BADGE = {
  'risk-on': 'bg-green-100 text-green-800',
  'neutral': 'bg-amber-100 text-amber-800',
  'risk-off': 'bg-red-100 text-red-800',
};

export default function ReplayPage() {
  const [searchParams] = useSearchParams(); // to read ?id= from the URL for pre-selecting a run
  const [tasks, setTasks] = useState([]);  // all the completed backtest tasks
  const [result, setResult] = useState(null);  // loaded backtest results
  const [loading, setLoading] = useState(false); // loading state for the result fetch
  const [step, setStep] = useState(0);  // current rebalance step index

  // Fetch the list of all completed backtest runs on mount.
  // If ?id=<taskId> is in the URL (e.g. from the Dashboard "View" link),
  // auto-load that run without requiring the user to pick from the list.
  useEffect(() => {
    const preselectedId = searchParams.get('id');
    listBacktests()
      .then((all) => {
        const completed = all.filter((t) => t.status === 'completed');
        setTasks(completed);
        if (preselectedId && completed.some((t) => t.task_id === preselectedId)) {
          selectRun(preselectedId);
        }
      })
      .catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Load the full result payload for the chosen run and reset to step 0
  const selectRun = (taskId) => {
    setLoading(true);
    setResult(null);
    setStep(0);
    getTask('backtest', taskId)
      .then((data) => setResult(data.result))
      .finally(() => setLoading(false));
  };

  // -- Derived data for the current step --

  const rebalanceDates = result?.weights_schedule?.dates ?? [];
  const totalSteps = rebalanceDates.length;
  const currentDate = rebalanceDates[step] ?? null;

  // Weights at the current rebalance step: { [etf]: number }
  // Derived by picking column[step] for each ETF ticker
  const currentWeights = (() => {
    if (!result?.weights_schedule?.columns || !currentDate) return {};
    const cols = result.weights_schedule.columns;
    return Object.fromEntries(
      Object.entries(cols).map(([etf, values]) => [etf, values[step]])
    );
  })();

  // Weights at the previous rebalance step (step - 1), or null at step 0.
  // Used to compute trade deltas.
  const previousWeights = (() => {
    if (step === 0 || !result?.weights_schedule?.columns) return null;
    const cols = result.weights_schedule.columns;
    return Object.fromEntries(
      Object.entries(cols).map(([etf, values]) => [etf, values[step - 1]])
    );
  })();

  // Position changes at the current rebalance step.
  // Each entry: { etf, prev, next, delta }
  // At step 0 every position is new (prev = 0).
  // Entries with |delta| < 0.1 pp are treated as unchanged.
  const trades = (() => {
    if (!currentWeights || Object.keys(currentWeights).length === 0) return [];
    return Object.entries(currentWeights)
      .map(([etf, next]) => {
        const prev = previousWeights?.[etf] ?? 0;
        return { etf, prev, next, delta: next - prev };
      })
      .filter((t) => Math.abs(t.delta) >= 0.001)  // drop floating-point noise
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)); // largest change first
  })();

  // Return and benchmark series sliced up to the current rebalance date.
  // Passed directly to CumulativeReturnsChart / DrawdownChart.
  const slicedPortfolio = currentDate ? sliceSeriesUpTo(result.portfolio_returns, currentDate) : null;
  const slicedBenchmark = currentDate ? sliceSeriesUpTo(result.benchmark_returns, currentDate) : null;

  // Regime data sliced to the current date (only if regime info is present)
  const slicedPrices = currentDate && result?.regime ? sliceSeriesUpTo(result.regime.benchmark_prices, currentDate) : null;
  const slicedLabels = currentDate && result?.regime ? sliceSeriesUpTo(result.regime.label_names, currentDate) : null;

  // The regime label active on the current rebalance date
  const currentRegime = slicedLabels?.values?.at(-1) ?? null;

  // Running stats derived from the sliced return series.
  // Recomputed whenever the step changes.
  const runningStats = (() => {
    if (!slicedPortfolio?.values?.length) return null;

    const pVals = slicedPortfolio.values;
    const growth = cumulativeGrowth(pVals);
    const dd = drawdownSeries(growth);
    const n = pVals.length;

    // Total simple return
    const totalReturn = growth[n - 1] - 1;

    // Annualised return (bases 252 trading days per year assumption)
    const years = n / 252;
    const annReturn = years > 0 ? Math.pow(growth[n - 1], 1 / years) - 1 : 0;

    // Maximum drawdown (most negative value in the drawdown series)
    const maxDD = Math.min(...dd);

    // Annualised Sharpe ratio (full-period, not rolling)
    const mean = pVals.reduce((s, v) => s + (v ?? 0), 0) / n;
    const variance = pVals.reduce((s, v) => s + ((v ?? 0) - mean) ** 2, 0) / (n - 1);
    const std = Math.sqrt(variance);
    const sharpe = std > 0 ? (mean * 252) / (std * Math.sqrt(252)) : 0;

    return { totalReturn, annReturn, maxDD, sharpe, days: n };
  })();

  // -- Render --

  // Phase 1: run selector
  if (!result) {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-1">Replay Mode</h2>
        <p className="text-sm text-gray-500 mb-6">
          Select a completed backtest to step through it one rebalance at a time.
        </p>

        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="font-semibold mb-3">Select a run</h3>

          {loading && (
            <p className="text-sm text-gray-400">Loading result...</p>
          )}

          {!loading && tasks.length === 0 && (
            <p className="text-sm text-gray-400">
              No completed backtests found. Run one on the Backtest page first.
            </p>
          )}

          {!loading && tasks.length > 0 && (
            <div className="space-y-2">
              {tasks.map((t) => {
                const p = t.params;
                return (
                  <button
                    key={t.task_id}
                    onClick={() => selectRun(t.task_id)}
                    className="w-full flex items-center gap-3 text-sm p-3 rounded border border-gray-200
                               hover:bg-blue-50 hover:border-blue-200 text-left"
                  >
                    <TaskStatusBadge status={t.status} />
                    <span className="text-gray-600">
                      {p.start} to {p.end || 'today'} &nbsp;|&nbsp;
                      {p.risk_level} &nbsp;|&nbsp;
                      rebal {p.rebalance_freq}d &nbsp;|&nbsp;
                      {p.n_estimators} trees
                    </span>
                    <span className="ml-auto text-xs text-gray-400">
                      {new Date(t.created_at).toLocaleTimeString()}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Phase 2: replay view
  return (
    <div>
      {/* Page header with a link back to the run selector */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Replay Mode</h2>
        <button
          onClick={() => { setResult(null); setStep(0); }}
          className="text-sm text-blue-600 hover:underline"
        >
          Choose different run
        </button>
      </div>

      <div>
        {/* Navigation controls */}
        <div className="mb-4">
          <ReplayControls
            step={step}
            total={totalSteps}
            date={currentDate}
            onPrev={() => setStep((s) => Math.max(0, s - 1))}
            onNext={() => setStep((s) => Math.min(totalSteps - 1, s + 1))}
            onSeek={(s) => setStep(s)}
          />
        </div>

        {/* Current allocation and stats side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <div className="bg-white rounded shadow p-4">
            <WeightsBarChart weights={currentWeights} />
          </div>

          <div className="bg-white rounded shadow p-4">
            {/* Running performance stats */}
            <h3 className="text-sm font-bold text-gray-700 mb-3">
              Performance to Date
            </h3>
            {runningStats ? (
              <div className="grid grid-cols-2 gap-3">
                <StatCard
                  label="Total Return"
                  value={`${(runningStats.totalReturn * 100).toFixed(2)}%`}
                  positive={runningStats.totalReturn >= 0}
                />
                <StatCard
                  label="Ann. Return"
                  value={`${(runningStats.annReturn * 100).toFixed(2)}%`}
                  positive={runningStats.annReturn >= 0}
                />
                <StatCard
                  label="Max Drawdown"
                  value={`${(runningStats.maxDD * 100).toFixed(2)}%`}
                  positive={false}
                />
                <StatCard
                  label="Sharpe Ratio"
                  value={runningStats.sharpe.toFixed(3)}
                  positive={runningStats.sharpe >= 0}
                />
              </div>
            ) : (
              <p className="text-sm text-gray-500">Not enough data yet.</p>
            )}

            {/* Current regime badge */}
            {currentRegime && (
              <div className="mt-4 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-1">Current Regime</p>
                <span className={`inline-block px-3 py-1 rounded text-sm font-bold ${REGIME_BADGE[currentRegime] || 'bg-gray-100 text-gray-700'}`}>
                  {currentRegime}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Trades at this rebalance */}
        <div className="bg-white rounded shadow p-4 mb-4">
          <TradesPanel trades={trades} isInitial={step === 0} />
        </div>

        {/* Cumulative returns so far */}
        <div className="bg-white rounded shadow p-4 mb-4">
          <CumulativeReturnsChart
            portfolioReturns={slicedPortfolio}
            benchmarkReturns={slicedBenchmark}
          />
        </div>

        {/* Drawdown so far */}
        <div className="bg-white rounded shadow p-4 mb-4">
          <DrawdownChart
            portfolioReturns={slicedPortfolio}
            benchmarkReturns={slicedBenchmark}
          />
        </div>

        {/* Regime overlay (only if data is available) */}
        {slicedPrices && slicedLabels && (
          <div className="bg-white rounded shadow p-4 mb-4">
            <RegimeOverlayChart
              benchmarkPrices={slicedPrices}
              labelNames={slicedLabels}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// Shows which positions were opened, increased, decreased, or closed
// at the current rebalance step.
//
// At step 0 every ETF is treated as a new open (no prior position).
// For subsequent steps the delta between previous and current weight is shown.
// Entries with |delta| < 0.1 pp are filtered out upstream.
//
// Props:
// - trades: array of { etf, prev, next, delta }
// - isInitial: true at step 0, so all trades are shown as opens
function TradesPanel({ trades, isInitial }) {
  if (trades.length === 0) {
    return (
      <div>
        <h3 className="text-sm font-bold text-gray-700 mb-2">Trades Executed</h3>
        <p className="text-sm text-gray-500">No position changes at this rebalance.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-bold text-gray-700 mb-3">Trades Executed</h3>
      {isInitial && (
        <p className="text-xs text-gray-500 mb-2">
          Initial allocation - all positions opened from cash.
        </p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-xs text-gray-600">
              <th className="text-left pb-2 pr-4 font-bold">ETF</th>
              <th className="text-right pb-2 px-3 font-bold">Previous</th>
              <th className="text-right pb-2 px-3 font-bold">New</th>
              <th className="text-right pb-2 pl-3 font-bold">Change</th>
              <th className="text-right pb-2 pl-3 font-bold">Action</th>
            </tr>
          </thead>
          <tbody>
            {trades.map(({ etf, prev, next, delta }) => {
              // work out what type of trade this is
              const isBuy = delta > 0 && prev < 0.001;
              const isSell = next < 0.001;
              const isIncrease = delta > 0 && !isBuy;

              const actionLabel = isBuy ? 'Open' : isSell ? 'Close' : isIncrease ? 'Increase' : 'Decrease';

              const actionColour = (isBuy || isIncrease)
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700';

              const deltaColour = delta > 0 ? 'text-green-600' : 'text-red-600';
              const deltaPrefix = delta > 0 ? '+' : '';

              return (
                <tr key={etf} className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-bold text-gray-700">{etf}</td>
                  <td className="py-2 px-3 text-right text-gray-400">
                    {isInitial ? '-' : `${(prev * 100).toFixed(1)}%`}
                  </td>
                  <td className="py-2 px-3 text-right font-medium text-gray-700">
                    {`${(next * 100).toFixed(1)}%`}
                  </td>
                  <td className={`py-2 pl-3 text-right font-medium ${deltaColour}`}>
                    {isInitial ? `+${(next * 100).toFixed(1)}%` : `${deltaPrefix}${(delta * 100).toFixed(1)}%`}
                  </td>
                  <td className="py-2 pl-3 text-right">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${actionColour}`}>
                      {actionLabel}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Small stat display card used in the "Performance to Date" panel.
//
// Props:
// - label: metric name
// - value: formatted value string
// - positive: if true, value is shown in green, otherwise grey
function StatCard({ label, value, positive }) {
  return (
    <div className="bg-gray-100 rounded p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${positive ? 'text-green-700' : 'text-gray-800'}`}>
        {value}
      </p>
    </div>
  );
}
