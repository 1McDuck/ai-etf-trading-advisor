// components/charts/WeightsStackedArea.jsx
//
// Stacked area chart of portfolio weights over time.
// Each ETF is a coloured layer - all of them together always sum to 100%.
// stepAfter interpolation keeps the line flat between rebalance dates (weights don't
// change continuously, only when the portfolio is rebalanced).
//
// Props:
// - weightsSchedule: { dates: string[], columns: { [etfTicker]: number[] } }

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Fixed colour palette for the nine sector ETFs.
// Colours are chosen to be visually distinct from one another.
const ETF_COLOURS = {
  XLK: '#2563eb', // Technology (blue)
  XLF: '#16a34a', // Financials (green)
  XLV: '#dc2626', // Health Care (red)
  XLY: '#f59e0b', // Consumer Discretionary (amber)
  XLP: '#8b5cf6', // Consumer Staples (purple)
  XLI: '#06b6d4', // Industrials (cyan)
  XLE: '#ea580c', // Energy (orange)
  XLB: '#84cc16', // Materials (lime)
  XLU: '#ec4899', // Utilities (pink)
};

export default function WeightsStackedArea({ weightsSchedule }) {
  // Guard: show nothing if the data has not yet arrived
  if (!weightsSchedule?.dates?.length) return null;

  // Extract ETF tickers from the columns object
  const etfs = Object.keys(weightsSchedule.columns);

  // Reshape from column storage to the row per date format for recharts.
  const data = weightsSchedule.dates.map((date, i) => {
    const row = { date };
    for (const etf of etfs) {
      row[etf] = weightsSchedule.columns[etf][i];
    }
    return row;
  });

  // Thin the x-axis to 8ish evenly spaced date labels
  const step = Math.max(1, Math.floor(data.length / 8));
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.date);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Portfolio Weights Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis dataKey="date" ticks={ticks} tick={{ fontSize: 11 }} />
          {/* Y-axis: fixed [0, 1] domain since weights always sum to 100% */}
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <Tooltip
            formatter={(v, name) => [`${(v * 100).toFixed(1)}%`, name]}
            labelFormatter={(d) => d}
          />
          <Legend />
          {/* stackId="1" stacks all areas; stepAfter keeps lines flat between rebalances */}
          {etfs.map((etf) => (
            <Area
              key={etf}
              type="stepAfter"
              dataKey={etf}
              stackId="1"
              fill={ETF_COLOURS[etf] || '#94a3b8'}
              stroke={ETF_COLOURS[etf] || '#94a3b8'}
              fillOpacity={0.7}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
