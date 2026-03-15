// App.jsx
//
// Root application component.
// Defines the top-level layout and client-side routing.
// Fixed sidebar on the left, scrollable main content area on the right.
// React Router v6 handles navigation between the six pages without full page reloads.
//
// Route map:
//   /        -> DashboardPage - system status and run history
//   /backtest-> BacktestPage - configure and run a full backtest pipeline
//   /regime  -> RegimePage - standalone market-regime detection
//   /ranking -> RankingPage - ETF cross-sectional ranking model
//   /compare -> ComparePage - side-by-side comparison of saved backtest runs
//   /replay  -> ReplayPage - step through a backtest one rebalance at a time

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import DashboardPage from './pages/DashboardPage';
import BacktestPage from './pages/BacktestPage';
import RegimePage from './pages/RegimePage';
import ComparePage from './pages/ComparePage';
import RankingPage from './pages/RankingPage';
import ReplayPage from './pages/ReplayPage';

export default function App() {
  return (
    // BrowserRouter wraps everything so Routes and NavLink work
    <BrowserRouter>
      {/* Full height flex container: sidebar is fixed-width, main fills the rest */}
      <div className="flex min-h-screen bg-gray-50 text-gray-800">
        <Sidebar />
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/backtest" element={<BacktestPage />} />
            <Route path="/regime" element={<RegimePage />} />
            <Route path="/ranking" element={<RankingPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/replay" element={<ReplayPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
