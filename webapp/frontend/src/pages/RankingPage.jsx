// pages/RankingPage.jsx
//
// ETF cross-sectional ranking model page.
// Trains a Random Forest classifier to rank ETFs by expected next period return.
//
// Workflow:
// 1. User provides a date range for training data
// 2. submitRanking() posts to the backend; job runs 5-fold temporal CV
// 3. useTaskPoller() polls every 3 seconds until the job finishes
// 4. On success, model evaluation metrics and a feature importance chart are shown
//
// MetricCard is defined at the bottom of this file as it's only used here. 


import { useState } from 'react';
import { submitRanking } from '../api/client';
import useTaskPoller from '../hooks/useTaskPoller';
import FeatureImportanceBar from '../components/charts/FeatureImportanceBar';

export default function RankingPage() {
  // task_id returned by the backend when a job is submitted
  const [taskId, setTaskId] = useState(null);

  // Inline form state - simple enough not to warrant a separate form component
  const [form, setForm] = useState({ start: '2000-01-01', end: '' });

  // Poll the backend for updates until the task reaches a terminal state
  const { task, error, isLoading } = useTaskPoller('ranking', taskId);

  // Submit a new ranking model training job
  // End date is sent as null when left blankk, the backend treats that as today.
  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await submitRanking({ start: form.start, end: form.end || null });
    setTaskId(res.task_id);
  };

  const result = task?.result;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">ETF Ranking Model</h2>

      {/* -- Training date range form -- */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-5 space-y-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Start date</span>
            <input
              type="date"
              value={form.start}
              onChange={(e) => setForm((p) => ({ ...p, start: e.target.value }))}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-700">End date</span>
            <input
              type="date"
              value={form.end}
              onChange={(e) => setForm((p) => ({ ...p, end: e.target.value }))}
              className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-600 text-white px-5 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Training...' : 'Train Ranking Model'}
        </button>
      </form>

      {/* Progress indicator: shown while the pipeline is running */}
      {isLoading && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800 mb-4">
          Training the ranking model - downloading data, building features, running 5-fold temporal CV.
          This usually takes 1-2 minutes...
        </div>
      )}

      {/* Backend job failure message */}
      {task?.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800 mb-4">
          Failed: {task.error}
        </div>
      )}

      {/* Network or HTTP error from the polling requests */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800 mb-4">
          Network error: {error.message}
        </div>
      )}

      {/* Results: only shown once the result sis available */}
      {result && (
        <div className="space-y-6">
          {/* -- Cross-validation model metrics -- */}
          <div className="bg-white rounded-lg shadow p-5">
            <h3 className="font-semibold mb-3">Model Metrics</h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Mean hit rate across CV folds with +- standard deviation */}
              <MetricCard
                label="CV Hit Rate"
                value={`${(result.cv_hit_rate_mean * 100).toFixed(1)}%`}
                sub={`+/- ${(result.cv_hit_rate_std * 100).toFixed(1)}%`}
              />
              {/* Log loss: lower is better */}
              <MetricCard
                label="CV Log Loss"
                value={result.cv_log_loss_mean.toFixed(4)}
              />
              <MetricCard
                label="ETFs Covered"
                value={result.etf_names.length}
              />
              {/* List of tickers used - small font to fit long comma-separated list */}
              <MetricCard
                label="ETFs"
                value={result.etf_names.join(', ')}
                small
              />
            </div>
          </div>

          {/* -- Feature importance bar chart -- */}
          <div className="bg-white rounded-lg shadow p-5">
            <FeatureImportanceBar featureImportances={result.feature_importances} />
          </div>
        </div>
      )}
    </div>
  );
}

// Small metric display card used in the Model Metrics grid.
//
// Props:
// - label:metric name shown in small grey text above the value
// - value: primary value displayed prominently
// - sub: optional secondary text (e.g. standard deviation)
// - small: if true, renders the value in a smaller font size
function MetricCard({ label, value, sub, small }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`font-semibold ${small ? 'text-xs' : 'text-lg'}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400">{sub}</div>}
    </div>
  );
}
