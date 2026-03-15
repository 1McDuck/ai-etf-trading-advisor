// components/results/BacktestResultPanel.jsx
//
// Full backtest tearsheet.
// Renders the complete set of charts and tables for a completed backtest run. 
// 
// Props:
//   result - the 'result' field from a completed task record; null while running

// Import the individual chart components that make up the tearsheet
import CumulativeReturnsChart from '../charts/CumulativeReturnsChart';
import DrawdownChart from '../charts/DrawdownChart';
import AnnualReturnsChart from '../charts/AnnualReturnsChart';
import WeightsStackedArea from '../charts/WeightsStackedArea';
import RegimeOverlayChart from '../charts/RegimeOverlayChart';
import TransitionHeatmap from '../charts/TransitionHeatmap';
import StatsTable from './StatsTable';

export default function BacktestResultPanel({ result }) {
  // Return nothing until the task has a result payload
  if (!result) return null;

  const regime = result.regime;

  // Deduplicated list of regime label strings for the heatmap axis
  const regimeDisplayLabels = regime
    ? [...new Set(regime.label_names.values)]
    : null;

  return (
    <div>
      {/* Performance summary statistics table */}
      <div className="bg-white rounded shadow border border-gray-100 p-4 mb-4">
        <StatsTable stats={result.stats} />
      </div>

      {/* Cumulative growth of $1 curve vs benchmark */}
      <div className="bg-white rounded shadow border border-gray-100 p-4 mb-4">
        <CumulativeReturnsChart
          portfolioReturns={result.portfolio_returns}
          benchmarkReturns={result.benchmark_returns}
        />
      </div>

      {/* Drawdown chart and annual bar chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded shadow border border-gray-100 p-4">
          <DrawdownChart
            portfolioReturns={result.portfolio_returns}
            benchmarkReturns={result.benchmark_returns}
          />
        </div>
        <div className="bg-white rounded shadow border border-gray-100 p-4">
          <AnnualReturnsChart
            portfolioReturns={result.portfolio_returns}
            benchmarkReturns={result.benchmark_returns}
          />
        </div>
      </div>

      {/* Stacked area chart showing how ETF allocation weights changed over time */}
      <div className="bg-white rounded shadow border border-gray-100 p-4 mb-4">
        <WeightsStackedArea weightsSchedule={result.weights_schedule} />
      </div>

      {/* Regime charts, only shown if the pipeline included regime detection */}
      {regime && (
        <>
          {/* Benchmark price series with coloured regime background bands */}
          <div className="bg-white rounded shadow border border-gray-100 p-4 mb-4">
            <RegimeOverlayChart
              benchmarkPrices={regime.benchmark_prices}
              labelNames={regime.label_names}
            />
          </div>

          {/* Regime to regime transition probability matrix */}
          <div className="bg-white rounded shadow p-4 mb-4 max-w-lg">
            <TransitionHeatmap
              transitionMatrix={regime.transition_matrix}
              regimeLabels={regimeDisplayLabels}
            />
          </div>
        </>
      )}
    </div>
  );
}
