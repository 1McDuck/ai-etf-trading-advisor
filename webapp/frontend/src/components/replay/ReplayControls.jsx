// components/replay/ReplayControls.jsx
//
// Step navigation controls for replay mode.
// Shows a progress bar, the current rebalance number and date,
// and Prev / Next buttons that disable at the sequence boundaries.
//
// Props:
// - step: current zero-based step index
// - total: total number of rebalance steps
// - date: ISO-8601 date string for the current rebalance
// - onPrev: called when the Prev button is clicked
// - onNext: called when the Next button is clicked
// - onSeek: called with a zero-based step index when the user clicks or
//           drags the progress bar to a new position

import { useRef } from 'react';

export default function ReplayControls({ step, total, date, onPrev, onNext, onSeek }) {
  // Progress as a percentage for the progress bar width
  const progressPct = total > 1 ? (step / (total - 1)) * 100 : 100;

  const barRef = useRef(null);

  // Convert a pointer X position to a step index clamped to [0, total-1]
  function posToStep(clientX) {
    const rect = barRef.current.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    return Math.round(ratio * (total - 1));
  }

  function handlePointerDown(e) {
    e.currentTarget.setPointerCapture(e.pointerId);
    onSeek?.(posToStep(e.clientX));
  }

  function handlePointerMove(e) {
    // Only track movement while the pointer button is held (buttons & 1)
    if (e.buttons !== 1) return;
    onSeek?.(posToStep(e.clientX));
  }

  return (
    <div className="bg-white rounded shadow p-4">
      {/* -- Progress bar (click or drag to seek) -- */}
      <div
        ref={barRef}
        className="w-full h-3 bg-gray-200 rounded mb-4 cursor-pointer relative"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      >
        <div
          className="h-3 bg-blue-500 rounded"
          style={{ width: `${progressPct}%` }}
        />
        {/* Drag thumb */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-600 rounded-full shadow"
          style={{ left: `calc(${progressPct}% - 6px)` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase font-medium">Rebalance</p>
          <p className="text-xl font-bold text-gray-800">
            {step + 1} <span className="text-gray-400 font-normal">of {total}</span>
          </p>
          <p className="text-sm text-gray-500 mt-1">{date}</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onPrev}
            disabled={step === 0}
            className="px-4 py-2 rounded text-sm font-medium border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Prev 
          </button>
          <button
            onClick={onNext}
            disabled={step === total - 1}
            className="px-4 py-2 rounded text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
