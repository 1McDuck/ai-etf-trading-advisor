// pages/DashboardPage.jsx
//
// Application landing page. Shows:
// 1. A backend connectivity indicator (live health check)
// 2. Quick-action buttons to navigate to key workflows
// 3. A history list of all backtest runs with their status
// 4. A history list of all regime-detection runs with their status
//
// Data is refreshed every 5 seconds via setInterval so the run history
// updates while jobs are in progress, without needing a manual page reload.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { healthCheck, listBacktests, listRegimes } from '../api/client';
import TaskStatusBadge from '../components/common/TaskStatusBadge';

export default function DashboardPage() {
  const [status, setStatus] = useState(null); // 'ok', 'error', or null while checking 
  const [backtests, setBacktests] = useState([]);
  const [regimes, setRegimes] = useState([]);

  // Fetch health + both history lists. Errors on the history lists are ignored -
  // don't want one bad request to break the whole page.
  const refresh = () => {
    healthCheck()
      .then((d) => setStatus(d.status))
      .catch(() => setStatus('error'));
    listBacktests().then(setBacktests).catch(() => {});
    listRegimes().then(setRegimes).catch(() => {});
  };

  useEffect(() => {
    // Fetch immediately, then poll every 5 seconds
    refresh();
    const id = setInterval(refresh, 5000);
    // Cleanup: cancel the interval when the component unmounts
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>

      {/* -- Backend status indicator abd quick nav buttons -- */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="bg-white rounded shadow border border-gray-100 px-4 py-3 flex items-center gap-2">
          <span className="text-sm text-gray-500">Backend:</span>
          {status === 'ok'    && <span className="text-green-600 font-semibold text-sm">OK</span>}
          {status === 'error' && <span className="text-red-600 font-semibold text-sm">Unreachable</span>}
          {status === null    && <span className="text-gray-400 text-sm">checking...</span>}
        </div>

        {/* Quick navigation buttons */}
        <Link to="/backtest" className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700">
          New Backtest
        </Link>
        <Link to="/regime" className="text-white px-4 py-2 rounded text-sm font-medium" style={{ backgroundColor: 'hsla(148, 13%, 35%, 1)' }}>
          Regime Detection
        </Link>
        <Link to="/compare" className="text-white px-4 py-2 rounded text-sm font-medium" style={{ backgroundColor: 'hsla(148, 13%, 35%, 1)' }}>
          Compare Runs
        </Link>
      </div>

      {/* -- Backtest run history -- */}
      <div className="bg-white rounded shadow border border-gray-100 p-4 mb-4">
        <h3 className="font-bold mb-3">Backtest Runs</h3>
        {backtests.length === 0 ? (
          <p className="text-sm text-gray-400">No backtests yet. Run one to see results here.</p>
        ) : (
          <div className="space-y-2">
            {backtests.map((t) => (
              <RunRow key={t.task_id} task={t} type="backtest" />
            ))}
          </div>
        )}
      </div>

      {/* -- Regime detection run history -- */}
      <div className="bg-white rounded shadow border border-gray-100 p-4">
        <h3 className="font-bold mb-3">Regime Detection Runs</h3>
        {regimes.length === 0 ? (
          <p className="text-sm text-gray-400">No regime runs yet.</p>
        ) : (
          <div className="space-y-2">
            {regimes.map((t) => (
              <RunRow key={t.task_id} task={t} type="regime" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// A single row in the run history lists.
// Shows the task status badge, a parameter summary, the creation time, and the "View" link for completed runs.
//
// Props:
// - task: task record from the backend
// - type: 'backtest' | 'regime', determines the summary format and View link target
function RunRow({ task, type }) {
  const p = task.params;

  // Summary format differs between backtest and regime runs
  const label =
    type === 'backtest'
      ? `${p.start} to ${p.end || 'today'} | ${p.risk_level} | rebal ${p.rebalance_freq}d`
      : `${p.start} to ${p.end || 'today'} | ${p.n_regimes} regimes`;

  return (
    <div className="flex items-center justify-between text-sm border-b border-gray-200 py-2">
      <div className="flex items-center gap-3">
        <TaskStatusBadge status={task.status} />
        <span className="text-gray-600">{label}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span>{new Date(task.created_at).toLocaleTimeString()}</span>
        {/* Only show the View link once a result is available */}
        {task.status === 'completed' && (
          <Link
            to={type === 'backtest' ? `/replay?id=${task.task_id}` : `/${type}`}
            className="text-blue-600 hover:underline font-medium"
          >
            View
          </Link>
        )}
      </div>
    </div>
  );
}
