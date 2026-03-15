// components/layout/Sidebar.jsx
//
// Persistent navigation sidebar.
// Renders a fixed-width left panel with the app title and navigation links.
// NavLink handles active route highlighting automatically.
// `end` on the root link stops it matching every path that starts with '/'.

import { NavLink } from 'react-router-dom';

// Navigation items rendered top to bottom
const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/backtest', label: 'Backtest' },
  { to: '/replay',  label: 'Live Replay' },
  { to: '/regime', label: 'Regime Detection' },
  { to: '/ranking', label: 'Ranking Model' },
  { to: '/compare', label: 'Compare Runs' }
];

export default function Sidebar() {
  return (
    <aside className="w-56 min-h-screen text-gray-200 flex flex-col border-r border-black/20" style={{ backgroundColor: 'hsla(148, 13%, 35%, 1)' }}>
      {/* -- Application branding header -- */}
      <div className="px-4 py-5 border-b border-black/20">
        <h1 className="text-lg font-bold tracking-tight" style={{ color: 'hsla(353, 45%, 68%, 1)' }}>AI ETF Advisor</h1>
        <p className="text-xs mt-1" style={{ color: 'hsla(353, 45%, 68%, 1)' }}>Control Panel</p>
      </div>

      {/* -- Navigation links -- */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            // `end` ensures the Dashboard link only matches the exact root path
            end={to === '/'}
            // Conditionally apply active styles via React Router's isActive flag
            className={({ isActive }) =>
              `block px-3 py-2 rounded text-sm ${isActive ? 'bg-black/20 text-white font-medium' : 'text-gray-300 hover:text-white hover:bg-black/10'}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
