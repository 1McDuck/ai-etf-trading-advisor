// components/results/StatsTable.jsx
//
// Performance statistics key-value table.
// Renders the backtest summary stats (Sharpe, CAGR, max drawdown, etc.) as a two-column table.
// Small numbers (ratios, decimal returns) are shown to 4 dp; larger numbers use locale formatting.
//
// Props:
// - stats: plain key-value object from the backend result payload; null = render nothing

export default function StatsTable({ stats }) {
  if (!stats) return null;

  const entries = Object.entries(stats);

  return (
    <div>
      <h3 className="text-sm font-bold text-gray-700 mb-3">Performance Summary</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key} className="border-b border-gray-200">
                {/* -- Metric name */}
                <td className="py-2 pr-4 text-gray-600 whitespace-nowrap">{key}</td>
                {/* Value */}
                <td className="py-2 font-medium text-right text-gray-800">
                  {formatStat(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Format a single statistic value for display.
// Numbers < 10 in absolute value are shown to 4 dp; larger numbers use locale formatting.
function formatStat(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    if (Math.abs(value) < 10) return value.toFixed(4);
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return String(value);
}
