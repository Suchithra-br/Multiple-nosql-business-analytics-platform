import React from 'react';

/**
 * Common error alert banner component.
 */
export default function ErrorState({
  title = 'Unable to load data',
  message,
  error,
  onRetry,
}) {
  const displayError = error || message;

  return (
    <div className="error-banner" role="alert">
      <div className="error-title">{title}</div>
      {displayError && <p className="error-detail">{displayError}</p>}
      {onRetry && (
        <button
          type="button"
          className="btn btn-retry"
          onClick={onRetry}
          style={{ marginTop: '0.75rem' }}
        >
          Try Again
        </button>
      )}
    </div>
  );
}
