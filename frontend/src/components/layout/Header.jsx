import React from 'react';

/**
 * Global Top Header with brand title, live API connectivity status,
 * and data refresh button.
 */
export default function Header({ apiStatus = 'connected', onRefresh, isRefreshing = false }) {
  const isHealthy = apiStatus === 'connected';

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="header-title-container">
          <h1 className="header-title">Superstore Sales Analytics</h1>
          <div className="header-sub-row">
            <span className="header-subtitle">
              Historical sales 2015–2018 · Powered by Redis, MongoDB, Cassandra &amp; Neo4j
            </span>
          </div>
        </div>
      </div>

      <div className="header-right">
        <div className="api-badge" title="FastAPI API Gateway">
          <span className={`status-dot ${isHealthy ? 'connected' : 'error'}`} aria-hidden="true"></span>
          <span className="api-badge-text">API connected</span>
        </div>

        {onRefresh && (
          <button
            type="button"
            className="btn btn-refresh"
            onClick={onRefresh}
            disabled={isRefreshing}
            id="header-refresh-btn"
            title="Re-query API metrics"
          >
            {isRefreshing ? (
              <>
                <span className="refresh-spinner" aria-hidden="true"></span>
                <span>Refreshing...</span>
              </>
            ) : (
              <span>Refresh</span>
            )}
          </button>
        )}
      </div>
    </header>
  );
}
