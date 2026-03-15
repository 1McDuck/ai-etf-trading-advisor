// utils/finance.js
//
// Client-side financial computation utilities for the backtest result charts and stats.
//
// The backend sends raw daily log returns. These functions derive the series
// the charts need - growth curve, drawdown, Sharpe, annual returns.
// Keeps the API response small since raw log returns are compact.
// No dependencies, all plain JS arrays.

// Convert log returns to a growth of $1 curve.
// exp(cumsum) gives the compounded value at each day. Nulls treated as 0.
export function cumulativeGrowth(logReturns) {
  const out = new Array(logReturns.length);
  let cumSum = 0;
  for (let i = 0; i < logReturns.length; i++) {
    cumSum += logReturns[i] ?? 0;
    out[i] = Math.exp(cumSum);
  }
  return out;
}

// How far the portfolio is below its previous high at each point.
// Tracks a running peak - result is always <= 0.
export function drawdownSeries(growth) {
  const out = new Array(growth.length);
  let peak = -Infinity;
  for (let i = 0; i < growth.length; i++) {
    // Update the running peak
    if (growth[i] > peak) peak = growth[i];
    out[i] = (growth[i] - peak) / peak;
  }
  return out;
}

// Rolling annualised Sharpe over a 252-day window (one trading year).
// First window-1 entries are null. Zero std returns 0 not NaN.
export function rollingSharpe(logReturns, window = 252) {
  const out = new Array(logReturns.length).fill(null);

  for (let i = window - 1; i < logReturns.length; i++) {
    // Sum returns over the window to compute the mean
    let sum = 0;
    for (let j = i - window + 1; j <= i; j++) sum += logReturns[j] ?? 0;
    const mean = sum / window;

    // Compute sample variance (ddof=1) for the same window
    let sqSum = 0;
    for (let j = i - window + 1; j <= i; j++) {
      const d = (logReturns[j] ?? 0) - mean;
      sqSum += d * d;
    }
    const std = Math.sqrt(sqSum / (window - 1));

    // Annualise: multiply mean by 252, divide std by sqrt(252)
    out[i] = std > 0 ? (mean * 252) / (std * Math.sqrt(252)) : 0;
  }
  return out;
}

// Sum log returns by calendar year and convert to simple returns (exp(sum) - 1).
// Returns one object per year with portfolio and benchmark values side by side.
export function annualReturns(dates, portfolioLogReturns, benchmarkLogReturns) {
  // Accumulate log-return sums keyed by 4-digit year string
  const byYear = {};
  for (let i = 0; i < dates.length; i++) {
    const year = dates[i].slice(0, 4);
    if (!byYear[year]) byYear[year] = { p: 0, b: 0 };
    byYear[year].p += portfolioLogReturns[i] ?? 0;
    byYear[year].b += benchmarkLogReturns[i] ?? 0;
  }

  // Convert log-return sums to simple returns and sort chronologically
  return Object.entries(byYear)
    .sort(([a], [b]) => (a > b ? 1 : -1))
    .map(([year, { p, b }]) => ({
      year,
      portfolio: Math.exp(p) - 1,
      benchmark: Math.exp(b) - 1
    }));
}
