import React from 'react';

/**
 * Metric KPI Card displaying aggregate values, trend pill, and contextual badge.
 */
export default function KpiCard({
  title,
  value,
  subtext,
  badge,
  trend,
  id,
  accent = 'blue',
}) {
  return (
    <div className={`kpi-card accent-${accent}`} id={id}>
      <div className="kpi-card-header">
        <span className="kpi-title">{title}</span>
        {badge && <span className="kpi-badge">{badge}</span>}
      </div>

      <div className="kpi-value-row">
        <span className="kpi-value">{value}</span>
      </div>

      <div className="kpi-footer-row">
        {trend && (
          <span
            className={`kpi-trend-pill ${
              trend.positive ? 'positive' : trend.negative ? 'negative' : 'neutral'
            }`}
          >
            {trend.text}
          </span>
        )}
        {subtext && <span className="kpi-subtext">{subtext}</span>}
      </div>
    </div>
  );
}
