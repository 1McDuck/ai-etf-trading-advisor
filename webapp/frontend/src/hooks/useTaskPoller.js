// hooks/useTaskPoller.js
//
// Custom hook for polling async backend tasks.
// The backend queues jobs and returns a task_id straight away.
// This hook polls the status endpoint every few seconds until the job finishes or fails.
//
// Usage:
//   const { task, error, isLoading } = useTaskPoller('backtest', taskId);

import { useState, useEffect, useRef } from 'react';
import { getTask } from '../api/client';

// Polls a task endpoint until it reaches a terminal state.
//
// taskType: route prefix, e.g. "backtest" or "regime"
// taskId: UUID returned by the submit endpoint; polling disabled while null
// options: { interval: ms between polls (default 3000), enabled: pause flag }
export default function useTaskPoller(taskType, taskId, options = {}) {
  const { interval = 3000, enabled = true } = options;

  const [task, setTask] = useState(null);
  const [error, setError] = useState(null);

  // Store the interval ID in a ref to track the active polling interval and allow it to be cancelled
  const intervalRef = useRef(null);

  // Cancel the active polling interval if one is running
  const stop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    // Do nothing until a task ID is available and polling is enabled
    if (!taskId || !enabled) return;

    const poll = async () => {
      try {
        const data = await getTask(taskType, taskId);
        setTask(data);

        // Terminal states: stop polling to avoid unnecessary requests
        if (data.status === 'completed' || data.status === 'failed') {
          stop();
        }
      } catch (err) {
        // Network or server errors: record the error and stop polling
        setError(err);
        stop();
      }
    };

    // Fire immediately so the UI reflects current state without waiting for the first interval tick
    poll();
    intervalRef.current = setInterval(poll, interval);

    // Cleanup: cancel the interval when the component unmounts or when taskId / interval / enabled change
    return stop;
  }, [taskType, taskId, interval, enabled]);

  // Derived loading flag: true while the job is queued or actively running
  const isLoading = task?.status === 'pending' || task?.status === 'running';

  return { task, error, isLoading };
}
