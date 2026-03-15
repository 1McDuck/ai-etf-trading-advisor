// components/forms/RegimeForm.jsx
//
// Parameter input form for regime detection.
// Collects the date range, number of GMM regimes to fit, and the smoothing
// window applied to the raw regime sequence after fitting.
//
// Props:
// - onSubmit: called with validated params on submission: (params) => void
// - disabled: disables the submit button while a job is running

import { useState } from 'react';

// Default parameter values shown when the form first loads
const DEFAULTS = {
  start: '2000-01-01',
  end: '',      
  n_regimes: 3, 
  smooth_window: 5 
};

export default function RegimeForm({ onSubmit, disabled }) {
  const [form, setForm] = useState(DEFAULTS);

  const handleChange = (key, value) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      start: form.start,
      end: form.end || null,
      n_regimes: Number(form.n_regimes),
      smooth_window: Number(form.smooth_window)
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-5 space-y-4">
      <div className="grid grid-cols-2 gap-4">

        {/* -- Date range --*/}
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Start date</span>
          <input
            type="date"
            value={form.start}
            onChange={(e) => handleChange('start', e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">End date</span>
          <input
            type="date"
            value={form.end}
            onChange={(e) => handleChange('end', e.target.value)}
            className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
            placeholder="today"
          />
        </label>

        {/* -- Number of regimes -- */}
        {/* Controls the number of Gaussian components in the GMM fit */}
        <label className="block">
          <span className="text-sm font-medium text-gray-700">
            Regimes: {form.n_regimes}
          </span>
          <input
            type="range"
            min={2}
            max={5}
            value={form.n_regimes}
            onChange={(e) => handleChange('n_regimes', e.target.value)}
            className="mt-1 block w-full"
          />
        </label>

        {/* -- Smoothing window -- */}
        {/* Applies a rolling majority-vote filter to reduce noisy transitions */}
        <label className="block">
          <span className="text-sm font-medium text-gray-700">
            Smooth window: {form.smooth_window} days
          </span>
          <input
            type="range"
            min={1}
            max={20}
            value={form.smooth_window}
            onChange={(e) => handleChange('smooth_window', e.target.value)}
            className="mt-1 block w-full"
          />
        </label>
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="bg-blue-600 text-white px-5 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {disabled ? 'Running...' : 'Run Regime Detection'}
      </button>
    </form>
  );
}
