import React from 'react';
import LoadingState from '../common/LoadingState.jsx';
import ErrorState from '../common/ErrorState.jsx';
import EmptyState from '../common/EmptyState.jsx';

/**
 * Reusable card container for charts and visualization panels,
 * with standard headers, action slots, and loading/error/empty state handling.
 */
export default function ChartCard({
  title,
  subtitle,
  children,
  filterControls,
  loading = false,
  error = null,
  empty = false,
  emptyMessage = 'No data available for the selected filters.',
  className = '',
  id,
}) {
  return (
    <div className={`chart-card ${className}`} id={id}>
      <div className="chart-card-header">
        <div className="chart-title-group">
          <h2 className="chart-title">{title}</h2>
          {subtitle && <p className="chart-subtitle">{subtitle}</p>}
        </div>
        {filterControls && <div className="chart-actions">{filterControls}</div>}
      </div>

      <div className="chart-card-body">
        {loading ? (
          <LoadingState message="Loading data from API..." />
        ) : error ? (
          <ErrorState error={error} />
        ) : empty ? (
          <EmptyState message={emptyMessage} />
        ) : (
          children
        )}
      </div>
    </div>
  );
}
