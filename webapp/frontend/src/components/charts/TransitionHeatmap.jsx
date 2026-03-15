// components/charts/TransitionHeatmap.jsx
//
// Regime transition probability heatmap.
// Shows the Markov-chain transition matrix as a colour-coded HTML table.
// High probability cells are dark blue, near-zero ones are close to white.
// Text flips to white when the cell is dark enough (prob > 0.5).
//
// Props:
// - transitionMatrix: { labels: (string|number)[], values: number[][] }
// - regimeLabels: string[]|null - human-readable labels; falls back to matrix labels

export default function TransitionHeatmap({ transitionMatrix, regimeLabels }) {
  // Guard: show nothing if the matrix has not yet arrived
  if (!transitionMatrix?.values?.length) return null;

  const { labels, values } = transitionMatrix;

  // Use provided human readable labels if available, otherwise use the raw labels
  const displayLabels = regimeLabels || labels;

  // Map a probability value [0, 1] to an RGBA blue colour.
  // Alpha is scaled by 0.7 to keep the darkest cell a readable mid-blue.
  const cellColour = (val) => {
    const alpha = Math.min(val, 1);
    return `rgba(37, 99, 235, ${alpha * 0.7})`;
  };

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Regime Transition Matrix
      </h3>
      <div className="overflow-x-auto">
        <table className="border-collapse text-sm">
          <thead>
            <tr>
              {/* Top-left cell labels the axis convention: rows = "from", columns = "to" */}
              <th className="p-2 text-left text-gray-500">From \ To</th>
              {displayLabels.map((lbl, i) => (
                <th key={i} className="p-2 text-center text-gray-600 font-medium">
                  {lbl}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {values.map((row, ri) => (
              <tr key={ri}>
                {/* Row header: the "from" regime */}
                <td className="p-2 font-medium text-gray-600">
                  {displayLabels[ri] || labels[ri]}
                </td>
                {/* Data cells: colour-coded transition probabilities */}
                {row.map((val, ci) => (
                  <td
                    key={ci}
                    className="p-2 text-center min-w-[60px] rounded"
                    style={{
                      backgroundColor: cellColour(val),
                      // Invert text colour for high-probability (dark) cells
                      color: val > 0.5 ? 'white' : '#334155',
                    }}
                  >
                    {val.toFixed(3)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
