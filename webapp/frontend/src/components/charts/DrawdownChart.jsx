// components/charts/DrawdownChart.jsx
//
// Drawdown area chart.
// Shows how far the portfolio (and benchmark) are below their running peak at each date.
// All values are <= 0 so you can see loss depth and how long recoveries take.
//
// Props:
// - portfolioReturns: { dates: string[], values: number[] } daily portfolio log returns
// - benchmarkReturns: { dates: string[], values: number[] } daily benchmark log returns

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

import { cumulativeGrowth, drawdownSeries } from '../../utils/finance';

export default function DrawdownChart({ portfolioReturns, benchmarkReturns }) {
  // Guard: show nothing if the data has not yet arrived
  if (!portfolioReturns?.dates?.length) return null;

  // Derive drawdown series: log returns -> growth curve -> drawdown
  const pDD = drawdownSeries(cumulativeGrowth(portfolioReturns.values));
  const bDD = drawdownSeries(cumulativeGrowth(benchmarkReturns.values));

  // Merge dates and drawdown values into a single array for Recharts
  const data = portfolioReturns.dates.map((date, i) => ({
    date,
    portfolio: pDD[i],
    benchmark: bDD[i],
  }));

  // Thin the x-axis to ~8 date labels to avoid overcrowding
  const step = Math.max(1, Math.floor(data.length / 8));
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.date);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Drawdown</h3>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis dataKey="date" ticks={ticks} tick={{ fontSize: 11 }} />
          {/* Y-axis capped at 0 - drawdown is always non-positive */}
          <YAxis
            domain={['auto', 0]}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <Tooltip
            formatter={(v, name) => [`${(v * 100).toFixed(2)}%`, name]}
            labelFormatter={(d) => d}
          />
          <Legend />
          {/* Portfolio: red filled area to emphasise losses */}
          <Area type="monotone" dataKey="portfolio" stroke="#dc2626" fill="#dc2626" fillOpacity={0.15} dot={false} strokeWidth={1.5} />
          {/* Benchmark: light dashed grey for reference */}
          <Area type="monotone" dataKey="benchmark" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.08} dot={false} strokeWidth={1} strokeDasharray="5 5" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
