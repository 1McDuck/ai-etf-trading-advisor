// pages/RegimePage.jsx
//
// Standalone market regime detection page.
// User can run the GMM based regime pipeline independently of a full backtest.
//
// Workflow:
// 1. User configures parameters via RegimeForm and submits
// 2. submitRegime() posts to the backend and gets back a task_id straight away
// 3. useTaskPoller() polls every 3 seconds until the job finishes
// 4. On success three panels are shown:
//  - Benchmark price chart with coloured regime background bands
//  - Transition probability matrix heatmap
//  - Regime distribution breakdown (counts and percentages per label)

import { useState } from 'react';
import { submitRegime } from '../api/client';
import useTaskPoller from '../hooks/useTaskPoller';
import RegimeForm from '../components/forms/RegimeForm';
import RegimeOverlayChart from '../components/charts/RegimeOverlayChart';
import TransitionHeatmap from '../components/charts/TransitionHeatmap';

export default function RegimePage() {
  // task_id returned by the backend when a job is submitted; null until then
  const [taskId, setTaskId] = useState(null);

  // Poll the backend for updates until the task reaches a terminal state
  const { task, error, isLoading } = useTaskPoller('regime', taskId);

  // Submit a new regime-detection job and start polling for its result
  const handleSubmit = async (params) => {
    const res = await submitRegime(params);
    setTaskId(res.task_id);
  };

  const result = task?.result;

  // Unique regime label strings for the heatmap axis (Set removes dupes)
  const regimeDisplayLabels = result
    ? [...new Set(result.label_names.values)]
    : null;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Regime Detection</h2>

      {/* Parameter form - disabled while a job is in progress */}
      <RegimeForm onSubmit={handleSubmit} disabled={isLoading} />

      {/* Progress indicator: shown while the pipeline is running */}
      {isLoading && (
        <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          Pipeline running - downloading data and fitting GMM. This usually takes 30-60 seconds...
        </div>
      )}

      {/* Backend job failure message */}
      {task?.status === 'failed' && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          Failed: {task.error}
        </div>
      )}

      {/* Network or HTTP error from the polling requests */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
          Network error: {error.message}
        </div>
      )}

      {/* Results - only rendered once the result payload is available */}
      {result && (
        <div className="mt-6 space-y-6">
          {/* Benchmark price chart with regime background shading */}
          <div className="bg-white rounded-lg shadow p-5">
            <RegimeOverlayChart
              benchmarkPrices={result.benchmark_prices}
              labelNames={result.label_names}
            />
          </div>

          {/* Transition matrix and distribution shown side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-5">
              <TransitionHeatmap
                transitionMatrix={result.transition_matrix}
                regimeLabels={regimeDisplayLabels}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Regime Distribution
              </h3>
              <RegimeStats labelNames={result.label_names} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Breakdown of how many trading days fell into each regime.
// Counts occurrences of each label string, sorts by frequency descending,
// and renders each as a coloured badge with a day count and percentage.
//
// Props:
// - labelNames: { dates: string[], values: string[] } daily regime label series
function RegimeStats({ labelNames }) {
  if (!labelNames?.values?.length) return null;

  // Count occurrences of each regime label
  const counts = {};
  for (const v of labelNames.values) {
    counts[v] = (counts[v] || 0) + 1;
  }
  const total = labelNames.values.length;

  // Colour classes for each known regime label
  const colours = {
    'risk-on':  'bg-green-100 text-green-800',
    'neutral':  'bg-amber-100 text-amber-800',
    'risk-off': 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-2">
      {/* Sort regimes by frequency (most common first) */}
      {Object.entries(counts)
        .sort(([, a], [, b]) => b - a)
        .map(([label, count]) => (
          <div key={label} className="flex items-center justify-between text-sm">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${colours[label] || 'bg-gray-100 text-gray-700'}`}>
              {label}
            </span>
            <span className="text-gray-600">
              {count} days ({((count / total) * 100).toFixed(1)}%)
            </span>
          </div>
        ))}
      <div className="text-xs text-gray-400 pt-1">Total: {total} trading days</div>
    </div>
  );
}
