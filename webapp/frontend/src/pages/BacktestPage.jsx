// pages/BacktestPage.jsx
//
// The main backtest page. Lets the user configure and run a full backtest.
//
// Workflow:
// 1. User fills in BacktestForm and submits
// 2. submitBacktest() posts to the backend and gets back a task_id straight away
// 3. useTaskPoller() polls every 3 seconds until the job finishes
// 4. A yellow banner shows while it's running
// 5. On failure the backend error is displayed
// 6. On success BacktestResultPanel renders the full tearsheet

import { useState } from 'react';
import { submitBacktest } from '../api/client';
import useTaskPoller from '../hooks/useTaskPoller';
import BacktestForm from '../components/forms/BacktestForm';
import BacktestResultPanel from '../components/results/BacktestResultPanel';

export default function BacktestPage() {
  // task_id returned by the backend when a job is submitted; null until then
  const [taskId, setTaskId] = useState(null);

  // Poll the backend for updates until the task reaches a terminal state
  const { task, error, isLoading } = useTaskPoller('backtest', taskId);

  // Submit a new backtest job and store the returned task_id to start polling
  const handleSubmit = async (params) => {
    const res = await submitBacktest(params);
    setTaskId(res.task_id);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Run Backtest</h2>

      {/* Parameter form - disabled while a job is in progress */}
      <BacktestForm onSubmit={handleSubmit} disabled={isLoading} />

      {/* Progress indicator: shown while the pipeline is running */}
      {isLoading && (
        <div className="mt-4 bg-yellow-50 border border-yellow-300 rounded p-4 text-sm text-yellow-800">
          Running... this can take a few minutes while it downloads data, trains the model and runs the simulation.
        </div>
      )}

      {/* Backend job failure message */}
      {task?.status === 'failed' && (
        <div className="mt-4 bg-red-50 border border-red-300 rounded p-4 text-sm text-red-700">
          Error: {task.error}
        </div>
      )}

      {/* Network or HTTP error from the polling requests */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-300 rounded p-4 text-sm text-red-700">
          Network error: {error.message}
        </div>
      )}

      {/* Full tearsheet us only rendered once the result payload is available */}
      {task?.result && (
        <div className="mt-6">
          <BacktestResultPanel result={task.result} />
        </div>
      )}
    </div>
  );
}
