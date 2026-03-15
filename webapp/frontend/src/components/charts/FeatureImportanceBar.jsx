// components/charts/FeatureImportanceBar.jsx
//
// Horizontal bar chart of Random Forest feature importances (MDI scores).
// Shows which signals had the most influence on the ETF rankings.
//
// Props:
// - featureImportances: { features: string[], values: number[] }

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';


export default function FeatureImportanceBar({ featureImportances }) {
  // Guard: show nothing if the data has not yet arrived
  if (!featureImportances?.features?.length) return null;

  // Pair each feature name with its importance score for Recharts
  const data = featureImportances.features.map((name, i) => ({
    name,
    importance: featureImportances.values[i]
  }));

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Feature Importances</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 80 }}>
          <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={75} />
          <Tooltip formatter={(v) => [v.toFixed(4), 'Importance']} />
          <Bar dataKey="importance" fill="#2563eb" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
