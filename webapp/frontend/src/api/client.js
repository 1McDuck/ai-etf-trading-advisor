// api/client.js
//
// Central HTTP client for the FastAPI backend.
//

import axios from 'axios';

// Axios instance - baseURL '/api' is proxied to localhost:8000 by Vite during dev
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});


// --Health check--

// Ping the backend health endpoint. Returns { status: "ok" } when healthy.
export async function healthCheck() {
  const { data } = await api.get('/health');
  return data;
}


// --Task polling--

// Poll a task by type + ID - returns the record including result once done
export async function getTask(taskType, taskId) {
  const { data } = await api.get(`/${taskType}/${taskId}`);
  return data;
}

// -- Regime ---

// Submit a regime job, get back a task_id straight away
export async function submitRegime(params) {
  const { data } = await api.post('/regime/', params);
  return data;
}

// Get all regime tasks (all statuses)
export async function listRegimes() {
  const { data } = await api.get('/regime/');
  return data;
}

// -- Backtest ---

// Submit a backtest job, get back a task_id straight away
export async function submitBacktest(params) {
  const { data } = await api.post('/backtest/', params);
  return data;
}

// Get all backtest tasks (all statuses)
export async function listBacktests() {
  const { data } = await api.get('/backtest/');
  return data;
}

// Remove a backtest task by ID
export async function deleteBacktest(taskId) {
  const { data } = await api.delete(`/backtest/${taskId}`);
  return data;
}

// -- Ranking ---

// Submit a ranking job, get back a task_id straight away
export async function submitRanking(params) {
  const { data } = await api.post('/ranking/', params);
  return data;
}

export default api;
