// components/charts/CumulativeReturnsChart.jsx
//
// Growth of $1 line chart.
// Converts daily log return series to cumulative growth curves and plots them as overlaid lines. 
// Portfolio is a solid blue line; benchmark dashed grey.
//
// Props:
// - portfolioReturns: { dates: string[], values: number[] } daily portfolio log returns
// - benchmarkReturns: { dates: string[], values: number[] } daily benchmark log returns

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

import { cumulativeGrowth } from '../../utils/finance';

export default function CumulativeReturnsChart({ portfolioReturns, benchmarkReturns }) {
  // Guard: show nothing if the data has not yet arrived
  if (!portfolioReturns?.dates?.length) return null;

  // Convert log returns to growth of $1 curves
  const pGrowth = cumulativeGrowth(portfolioReturns.values);
  const bGrowth = cumulativeGrowth(benchmarkReturns.values);

  // Merge dates and growth values into a single array for Recharts
  const data = portfolioReturns.dates.map((date, i) => ({
    date,
    portfolio: pGrowth[i],
    benchmark: bGrowth[i]
  }));

  // Compute evenly spaced tick positions: 8 labels regardless of series length
  const step = Math.max(1, Math.floor(data.length / 8));
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.date);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Cumulative Returns (Growth of $1)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis dataKey="date" ticks={ticks} tick={{ fontSize: 11 }} />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `$${v.toFixed(2)}`}
          />
          <Tooltip
            formatter={(v, name) => [`$${v.toFixed(3)}`, name]}
            labelFormatter={(d) => d}
          />
          <Legend />
          {/* Portfolio: solid blue line */}
          <Line type="monotone" dataKey="portfolio" stroke="#2563eb" dot={false} strokeWidth={1.5} />
          {/* Benchmark: dashed grey line */}
          <Line type="monotone" dataKey="benchmark" stroke="#94a3b8" dot={false} strokeWidth={1.5} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
