// pages/ComparePage.jsx
//
// Side to side comparison of up to 4? selected completed backtest runs.
// The user picks runs via checkboxes and the page shows a stats table, overlaid cumulative returns, and overlaid drawdown.
//
// Result payloads are fetched only when a run is selected for comparison, and then cached in state,
// so the UI is still responsive even with many completed runs.
//
// Sub-components:
// - OverlaidChart: generic multi series line chart
// - StatsComparisonTable: multicol stats table
// - runLabel: short display label from a runs stats
// - formatVal: formats a stat value for display

import { useEffect, useState } from 'react';
import { listBacktests, getTask } from '../api/client';
import TaskStatusBadge from '../components/common/TaskStatusBadge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

import { cumulativeGrowth, drawdownSeries } from '../utils/finance';

// Fixed colour for up to 4 overlaid runs
const COLOURS = ['#2563eb', '#dc2626', '#16a34a', '#f59e0b'];

// Main page component for comparing completed backtest runs. Lets the user select runs and shows the comparison charts and tables.
export default function ComparePage() {
  const [tasks, setTasks] = useState([]); // list of all completed backtest tasks from the backend
  const [selected, setSelected] = useState([]); // array of selected task_id strings
  const [results, setResults] = useState({}); // { task_id: result } cache for selected runs

  // Fetch the list of all completed backtest tasks on mount
  useEffect(() => {
    listBacktests()
      .then((all) => setTasks(all.filter((t) => t.status === 'completed')))
      .catch(() => {});
  }, []);

  // Fetch result for any newly selected run. Cached in state so it's only fetched once.
  useEffect(() => {
    for (const id of selected) {
      if (!results[id]) {
        getTask('backtest', id).then((data) => {
          if (data.result) {
            setResults((prev) => ({ ...prev, [id]: data.result }));
          }
        });
      }
    }
  }, [selected]);

  // Toggle selection. Clicking a 5th run does nothing - max is 4.
  const toggle = (id) =>
    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id) 
        : prev.length < 4 ? [...prev, id] : prev // Enforce max of 4 selected runs
    );

  // Only include runs whose result has loaded yet; assign each a colour
  const runs = selected
    .map((id, i) => ({ id, result: results[id], colour: COLOURS[i] }))
    .filter((r) => r.result);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Compare Runs</h2>

      {/* -- Run selector -- */}
      <div className="bg-white rounded-lg shadow p-5 mb-6">
        <h3 className="font-semibold mb-3"> Select runs to compare (up to 4)</h3>
        {tasks.length === 0 ? (
          <p className="text-sm text-gray-400">No completed backtests to compare.</p>
        ) : (
          <div className="space-y-2">
            {tasks.map((t) => {
              const p = t.params;
              const isSelected = selected.includes(t.task_id);
              return (
                <label
                  key={t.task_id}
                  className={`flex items-center gap-3 text-sm p-2 rounded cursor-pointer ${
                    isSelected ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggle(t.task_id)}
                    className="rounded"
                  />
                  <TaskStatusBadge status={t.status} />
                  {/* Parameter summary to identify each run */}
                  <span className="text-gray-600">
                    {p.start} to {p.end || 'today'} | {p.risk_level} | rebal {p.rebalance_freq}d | {p.n_estimators} trees
                  </span>
                </label>
              );
            })}
          </div>
        )}
      </div>

      {/* -- Comparison panels - only shown when 2+= runs are ready -- */}
      {runs.length >= 2 && (
        <>
          {/* Side by side statistics table */}
          <div className="bg-white rounded-lg shadow p-5 mb-6 overflow-x-auto">
            <h3 className="font-semibold mb-3">Stats Comparison</h3>
            <StatsComparisonTable runs={runs} />
          </div>

          {/* Overlaid cumulative growth of $1 curves */}
          <div className="bg-white rounded-lg shadow p-5 mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Cumulative Returns</h3>
            <OverlaidChart
              runs={runs}
              computeFn={cumulativeGrowth}
              yFormat={(v) => `$${v.toFixed(2)}`}
            />
          </div>

          {/* Overlaid drawdown curves */}
          <div className="bg-white rounded-lg shadow p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Drawdown</h3>
            <OverlaidChart
              runs={runs}
              computeFn={(vals) => drawdownSeries(cumulativeGrowth(vals))}
              yFormat={(v) => `${(v * 100).toFixed(0)}%`}
            />
          </div>
        </>
      )}

      {/* Hint user when only one run is selected */}
      {selected.length === 1 && (
        <p className="text-sm text-gray-400 mt-2">Select at least 2 runs to compare.</p>
      )}
    </div>
  );
}

// Generic overlaid line chart for multiple backtest runs.
// Accepts a compute function so it can render either cumulative growth or
// drawdown without duplicating the chart scaffolding. All series are aligned
// on the date axis of the first selected run.
//
// Props:
// - runs: array of { id, result, colour } objects
// - computeFn: transforms a log-return array into a plottable series
// - yFormat: formats a y-axis tick or tooltip value to a string
function OverlaidChart({ runs, computeFn, yFormat }) {
  // Use the first selected run's dates as the shared x-axis
  const dates = runs[0].result.portfolio_returns.dates;

  // Build one data point per date, with a key per run ID
  const data = dates.map((date, i) => {
    const row = { date };
    for (const run of runs) {
      const vals = computeFn(run.result.portfolio_returns.values);
      row[run.id] = vals[i];
    }
    return row;
  });

  // Thin the x-axis to 8ish spaced dt labels
  const step = Math.max(1, Math.floor(data.length / 8));
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.date);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <XAxis dataKey="date" ticks={ticks} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={yFormat} domain={['auto', 'auto']} />
        <Tooltip
          formatter={(v, name) => [yFormat(v), runLabel(runs, name)]}
          labelFormatter={(d) => d}
        />
        {/* Legend uses run labels rather than raw UUID strings */}
        <Legend formatter={(id) => runLabel(runs, id)} />
        {runs.map((run) => (
          <Line
            key={run.id}
            type="monotone"
            dataKey={run.id}
            stroke={run.colour}
            dot={false}
            strokeWidth={1.5}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// Multi-column statistics comparison table. One row per metric, one column per selected run.
// Colour code to match the shart lines.
//
// Props:
// - runs: array of { id, result, colour } objects
function StatsComparisonTable({ runs }) {
  const allKeys = Object.keys(runs[0].result.stats);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-200">
          <th className="text-left py-1.5 pr-4 text-gray-500">Metric</th>
          {runs.map((run) => (
            // Column header colour matches the chart line colour for that run
            <th key={run.id} className="text-right py-1.5 px-2" style={{ color: run.colour }}>
              {run.result.stats?.risk_level || run.id.slice(0, 8)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {allKeys.map((key) => (
          <tr key={key} className="border-b border-gray-100">
            <td className="py-1.5 pr-4 text-gray-500">{key}</td>
            {runs.map((run) => (
              <td key={run.id} className="py-1.5 px-2 text-right font-medium">
                {formatVal(run.result.stats[key])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Derive a short human readable label for a run, used in chart legends and tooltips.
// Prefers the risk_level stat string; falls back to the first 8 chars of the UUID.
function runLabel(runs, id) {
  const run = runs.find((r) => r.id === id);
  if (!run) return id.slice(0, 8);
  const p = run.result.stats;
  return p?.risk_level || id.slice(0, 8);
}

// Format a statistics value for table display.
function formatVal(v) {
  if (v === null || v === undefined) return '-';
  if (typeof v === 'number') {
    return Math.abs(v) < 10
      ? v.toFixed(4)
      : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return String(v);
}
