// components/common/TaskStatusBadge.jsx
//
// Colour-coded task status indicator.
// Displays the current status of an async backend task as a small inline badge.
// Each status maps to a distinct colour so users can identify job states at a glance
// across the Dashboard and Compare pages.
//
// Props:
// - status: one of: 'pending' | 'running' | 'completed' | 'failed'
//          any unrecognised value falls back to the 'pending' style

// Tailwind class pairs (background + text) indexed by task status string
const STYLES = {
  pending: 'bg-gray-100 text-gray-600',
  running: 'bg-amber-100 text-amber-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700'
};

export default function TaskStatusBadge({ status }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STYLES[status] || STYLES.pending}`}>
      {status}
    </span>
  );
}
