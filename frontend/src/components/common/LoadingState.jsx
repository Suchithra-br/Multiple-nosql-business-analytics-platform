import React from 'react';

/**
 * Common loading spinner state.
 */
export default function LoadingState({ message = 'Loading analytics data...' }) {
  return (
    <div className="loading-container" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden="true"></div>
      <span className="loading-text">{message}</span>
    </div>
  );
}
