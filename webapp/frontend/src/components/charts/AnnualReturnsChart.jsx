// components/charts/AnnualReturnsChart.jsx
//
// Grouped bar chart of annual returns.
// Groups the daily returns by calendar year and plots portfolio vs benchmark side by side.
// Zero reference line makes the loss years easy to spot.
//
// Props:
// - portfolioReturns: { dates: string[], values: number[] } daily portfolio log returns
// - benchmarkReturns: { dates: string[], values: number[] } daily benchmark log returns

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

import { annualReturns } from '../../utils/finance';

export default function AnnualReturnsChart({ portfolioReturns, benchmarkReturns }) {
  // Guard: show nothing if the data has not yet arrived
  if (!portfolioReturns?.dates?.length) return null;

  // Aggregate daily log returns to annual simple returns
  const data = annualReturns(
    portfolioReturns.dates,
    portfolioReturns.values,
    benchmarkReturns.values
  );

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Annual Returns</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          {/*Y-axis: convert decimal return to percentage string */}
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <Tooltip
            formatter={(v, name) => [`${(v * 100).toFixed(2)}%`, name]}
          />
          <Legend />
          {/* Zero line to distinguish positive and negative years */}
          <ReferenceLine y={0} stroke="#94a3b8" />
          <Bar dataKey="portfolio" fill="#2563eb" radius={[2, 2, 0, 0]} />
          <Bar dataKey="benchmark" fill="#cbd5e1" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
