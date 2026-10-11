import React from 'react';

/**
 * Sidebar Navigation and Polyglot Storage Status component.
 */
export default function Sidebar({ currentTab, onSelectTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: '📊' },
    { id: 'analytics', label: 'Query Explorer', icon: '🔬' },
  ];

  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      {/* Brand Identity */}
      <div className="sidebar-brand">
        <div className="brand-badge-pill">CSE CAPSTONE</div>
        <div className="brand-title">Multi-NoSQL</div>
        <div className="brand-subtitle">Superstore Analytics</div>
      </div>

      {/* Navigation */}
      <div className="sidebar-section-label">NAVIGATION</div>
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(item.id)}
              id={`nav-${item.id}`}
            >
              <span className="nav-item-indicator" aria-hidden="true"></span>
              <span className="nav-item-text">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Polyglot Storage Architecture */}
      <div className="sidebar-footer">
        <div className="sidebar-section-label">DATA ENGINE</div>
        <div className="engine-status-list">
          <div className="engine-status-item" title="Real-time KPI cache">
            <span className="engine-dot redis"></span>
            <div className="engine-info">
              <span className="engine-name">Redis</span>
              <span className="engine-desc">In-Memory Cache</span>
            </div>
          </div>

          <div className="engine-status-item" title="Master operational documents">
            <span className="engine-dot mongodb"></span>
            <div className="engine-info">
              <span className="engine-name">MongoDB</span>
              <span className="engine-desc">Document Store</span>
            </div>
          </div>

          <div className="engine-status-item" title="Time-series analytical slices">
            <span className="engine-dot cassandra"></span>
            <div className="engine-info">
              <span className="engine-name">Cassandra</span>
              <span className="engine-desc">Wide-Column Store</span>
            </div>
          </div>

          <div className="engine-status-item" title="Customer and co-purchase graph">
            <span className="engine-dot neo4j"></span>
            <div className="engine-info">
              <span className="engine-name">Neo4j</span>
              <span className="engine-desc">Graph Database</span>
            </div>
          </div>
        </div>

        <div className="sidebar-project-tag">
          <span>Dataset: 2015–2018 Retail</span>
        </div>
      </div>
    </aside>
  );
}
