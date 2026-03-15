// components/charts/RegimeOverlayChart.jsx
//
// Benchmark price chart with regime background bands.
// Overlays the detected market regime onto a benchmark price series by shading the background of each time period with a colour corresponding to its regime label.
// Recharts ReferenceArea component renders each contiguous block of the same regime as a single coloured band. The helper buildRegimeBlocks converts the raw label
// series (one entry per day) into a compact list of (label, startDate, endDate). 
//
// Props:
// - benchmarkPrices: { dates: string[], values: number[] } daily benchmark closing prices
// - labelNames: { dates: string[], values: string[] } daily regime label strings

import {
  ComposedChart,
  Line,
  ReferenceArea,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

// Colour assigned to each named regime label for background shading
const REGIME_COLOURS = {
  'risk-on':  '#22c55e', // green - bullish
  'neutral':  '#f59e0b', // amber - transitional/uncertain
  'risk-off': '#ef4444'  // red - bearish
};

// Group consecutive same-label days into (label, startDate, endDate) blocks.
// Much faster than drawing a separate ReferenceArea per day.
function buildRegimeBlocks(labelNames) {
  const blocks = [];
  if (!labelNames?.dates?.length) return blocks;

  let current = labelNames.values[0];
  let start = labelNames.dates[0];

  for (let i = 1; i < labelNames.dates.length; i++) {
    if (labelNames.values[i] !== current) {
      // Regime changed: close the current block and start a new one
      blocks.push({ label: current, startDate: start, endDate: labelNames.dates[i - 1] });
      current = labelNames.values[i];
      start = labelNames.dates[i];
    }
  }
  // Close the final block at the last date in the series
  blocks.push({
    label: current,
    startDate: start,
    endDate: labelNames.dates[labelNames.dates.length - 1]
  });
  return blocks;
}

export default function RegimeOverlayChart({ benchmarkPrices, labelNames }) {
  // Guard: show nothing if the data has not yet arrived
  if (!benchmarkPrices?.dates?.length) return null;

  
  // Build the price series for the line chart
  const data = benchmarkPrices.dates.map((date, i) => ({
    date,
    price: benchmarkPrices.values[i]
  }));

  // Convert per-day labels to compact date-range blocks for ReferenceArea
  const blocks = buildRegimeBlocks(labelNames);

  // Thin the x-axis to 8ish date labels
  const step = Math.max(1, Math.floor(data.length / 8));
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.date);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Benchmark Price with Regime Overlay
      </h3>
      <ResponsiveContainer width="100%" height={350}>
        {/* ComposedChart is used because it can mix Line and ReferenceArea elements. */}
        <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          {/* Render one ReferenceArea per contiguous regime block */}
          {blocks.map((block, i) => (
            <ReferenceArea
              key={i}
              x1={block.startDate}
              x2={block.endDate}
              fill={REGIME_COLOURS[block.label] || '#94a3b8'}
              fillOpacity={0.18}
            />
          ))}
          <XAxis dataKey="date" ticks={ticks} tick={{ fontSize: 11 }} />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => v.toLocaleString()}
          />
          <Tooltip
            formatter={(v) => [v.toFixed(2), 'Price']}
            labelFormatter={(d) => d}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#1e40af"
            dot={false}
            strokeWidth={1.5}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Manual colour legend for regime labels */}
      <div className="flex gap-4 mt-2 text-xs text-gray-600">
        {Object.entries(REGIME_COLOURS).map(([label, colour]) => (
          <div key={label} className="flex items-center gap-1">
            <span
              className="inline-block w-3 h-3 rounded"
              style={{ backgroundColor: colour, opacity: 0.5 }}
            />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
