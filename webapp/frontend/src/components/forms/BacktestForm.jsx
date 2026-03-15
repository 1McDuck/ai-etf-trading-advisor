// BacktestForm.jsx

// This is used in BacktestPage.jsx to collect the user inputs for backtest params, 
// it is then passed to the backend via the submitBacktest function in client.js.
// The form includes:
// - Start and end date (with validation)
// - Risk level (conservative, moderate, aggressive)
// - Rebalance frequency (1-252 days)
// - Number of estimators for the model (50-1000)

import { useState } from 'react';

// Defaults for the form fields when the component first loads
// todayISO: used as the max selectable date on the date inputs
// yesterdayISO: used as the default end date - yfinance doesn't reliably return today's data
const todayISO = () => new Date().toISOString().slice(0, 10);
const yesterdayISO = () => {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
};
// rebalance_freq: 21 trading days = monthly rebalancing
// risk_level: 0=conservative, 1=moderate, 2=aggressive (mapped to strings in the API)
// n_estimators: number of random forest trees
const DEFAULTS = {
  start: '2000-01-01',
  end: yesterdayISO(),
  risk_level: 1,
  rebalance_freq: 21,
  n_estimators: 500
};

// The form state is managed as a single object for convenience
export default function BacktestForm({ onSubmit, disabled }) {
  const [form, setForm] = useState(DEFAULTS);
  const handleChange = (key, value) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();

    const riskMap = ['conservative', 'moderate', 'aggressive'];

    onSubmit(
      {
        start: form.start,
        end: form.end || null,
        risk_level: riskMap[form.risk_level],
        rebalance_freq: Number(form.rebalance_freq),
        n_estimators: Number(form.n_estimators)
      }
    );
  };

  const riskLabels = ['Conservative', 'Moderate', 'Aggressive'];

  
  // Sliders for rebalance freq and tree count - current value shown in the label
  return (
    <form 
      onSubmit={handleSubmit} 
      className="bg-white rounded-lg shadow p-5 space-y-5"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-start">
        {/* -- Start date -- */}
        <div className="self-start w-fit">
          <label>
            <span className="text-sm font-medium text-gray-700">Start date</span>
            <div className="mt-2 rounded border border-gray-200 bg-gray-50 p-3">
              <input
                type="date"
                max={form.end || todayISO() - 1}
                min="2000-01-01"
                value={form.start}
                onChange={(e) => handleChange('start', e.target.value)}
                className="block w-36 rounded border border-gray-300 px-2 py-1 text-sm bg-white"
              />
              <p className="mt-1 text-xs text-gray-500">Min: 01/01/2000</p>
            </div>
          </label>
        </div>

        {/* -- End date -- */}
        <div className="self-start w-fit">
          <label>
            <span className="text-sm font-medium text-gray-700">End date</span>
            <div className="mt-2 rounded border border-gray-200 bg-gray-50 p-3">
              <input
                type="date"
                min={form.start}
                max={todayISO()}
                value={form.end}
                onChange={(e) => handleChange('end', e.target.value)}
                className="block w-36 rounded border border-gray-300 px-2 py-1 text-sm bg-white"
              />
              <p className="mt-1 text-xs text-gray-500">Max: {todayISO()}</p>
            </div>
          </label>
        </div>
        {/* -- Risk level -- */}
        <div className="self-start w-fit">
          <label>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700">Risk level</span>
              <span className="text-xs text-gray-500">
                {riskLabels[Number(form.risk_level)]}
              </span>
            </div>

            <div className="mt-2 flex items-center gap-3 rounded border border-gray-200 bg-gray-50 p-3">
              {/* slider */}
              <input
                type="range"
                min={0}
                max={2}
                step={1}
                value={form.risk_level}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, risk_level: Number(e.target.value) }))
                }
                className="h-24 w-3 cursor-pointer rounded accent-blue-600 [writing-mode:bt-lr] [-webkit-appearance:slider-vertical]"
              />
              {/* labels */}
              <div className="flex h-24 flex-col justify-between text-xs text-gray-500 leading-none">
                <span className={Number(form.risk_level) === 2 ? 'text-gray-900 font-medium' : ''}>
                  Aggressive
                </span>
                <span className={Number(form.risk_level) === 1 ? 'text-gray-900 font-medium' : ''}>
                  Moderate
                </span>
                <span className={Number(form.risk_level) === 0 ? 'text-gray-900 font-medium' : ''}>
                  Conservative
                </span>
              </div>
            </div>
          </label>
        </div>
        
        {/* -- Rebalance frequency -- */}
        {/* Range: 5 days (weekly) to 252 days (anually) */}
        <div className="self-start w-fit">
          <label>
            <span className="text-sm font-medium text-gray-700">
              Rebalance: every {form.rebalance_freq} days
            </span>
            <div className="mt-2 rounded border border-gray-200 bg-gray-50 p-3">
              <input
                type="range"
                min={5}
                max={252}
                value={form.rebalance_freq}
                onChange={(e) => handleChange('rebalance_freq', e.target.value)}
                className="block w-36"
              />
            </div>
          </label>
        </div>

        {/* -- Random Forest tree count -- */}
        {/* More trees = more stable predictions but takes longer to train */}
        <div className="self-start w-fit">
          <label>
            <span className="text-sm font-medium text-gray-700">
              Trees: {form.n_estimators}
            </span>
            <div className="mt-2 rounded border border-gray-200 bg-gray-50 p-3">
              <input
                type="range"
                min={50}
                max={1000}
                step={50}
                value={form.n_estimators}
                onChange={(e) => handleChange('n_estimators', e.target.value)}
                className="block w-36"
              />
            </div>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="bg-blue-600 text-white px-5 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {disabled ? 'Running...' : 'Run Backtest'}
      </button>
    </form>
  );
}
