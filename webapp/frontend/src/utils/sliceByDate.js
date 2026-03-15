// utils/sliceByDate.js
//
// Date-based series slicing for replay mode.
// Replay needs to show charts "up to" a given rebalance date rather than the full history.
// This filters a paired { dates, values } series to all entries on or before a cutoff.
//
// ISO-8601 date strings (YYYY-MM-DD) compare correctly with standard string comparison,
// so no Date parsing is needed.

// Return a copy of a time series containing only entries up to and including the cutoff date.
export function sliceSeriesUpTo(series, cutoffDate) {
  if (!series?.dates?.length) return { dates: [], values: [] };

  // Find the last index whose date is <= cutoffDate
  let endIndex = series.dates.length - 1;
  for (let i = 0; i < series.dates.length; i++) {
    if (series.dates[i] > cutoffDate) {
      endIndex = i - 1;
      break;
    }
  }

  return {
    dates: series.dates.slice(0, endIndex + 1),
    values: series.values.slice(0, endIndex + 1),
  };
}
