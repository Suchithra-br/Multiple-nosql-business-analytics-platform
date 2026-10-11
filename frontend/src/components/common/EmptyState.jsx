import React from 'react';

/**
 * Common empty results container.
 */
export default function EmptyState({
  message = 'No data available for the selected filters.',
  action,
}) {
  return (
    <div className="empty-state">
      <p className="empty-state-message">{message}</p>
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}
