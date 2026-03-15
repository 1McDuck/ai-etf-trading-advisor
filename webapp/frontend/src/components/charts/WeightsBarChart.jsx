// components/charts/WeightsBarChart.jsx
//
// Single-rebalance allocation snapshot.
// Shows the ETF weights chosen at one specific rebalance date as a horizontal bar chart.
// Unlike WeightsStackedArea (which plots weights across the entire backtest history), 
// this component shows a single snapshot, what the model decided to allocate at the current replay step.
//
// Props:
// - weights: { [etfTicker]: number } - allocation weights for a single rebalance date

import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

// Colour assigned to each sector ETF - matches WeightsStackedArea palette
const ETF_COLOURS = {
  XLK: '#2563eb',
  XLF: '#16a34a',
  XLV: '#dc2626',
  XLY: '#f59e0b',
  XLP: '#8b5cf6',
  XLI: '#06b6d4',
  XLE: '#ea580c',
  XLB: '#84cc16',
  XLU: '#ec4899'
};

export default function WeightsBarChart({ weights }) {
  if (!weights || Object.keys(weights).length === 0) return null;

  // Convert the { etf: weight } object to a row array for Recharts,
  // sorted descending by weight so the largest allocation is at the top
  const data = Object.entries(weights)
    .map(([name, weight]) => ({ name, weight }))
    .sort((a, b) => b.weight - a.weight);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Current Allocation
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 20, bottom: 4, left: 40 }}
        >
          <XAxis
            type="number"
            domain={[0, 1]}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11 }}
            width={38}
          />
          <Tooltip
            formatter={(v) => [`${(v * 100).toFixed(1)}%`, 'Weight']}
          />
          <Bar dataKey="weight" radius={[0, 4, 4, 0]}>
            {/* Each bar gets the ETF-specific colour from the shared palette */}
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={ETF_COLOURS[entry.name] || '#94a3b8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
