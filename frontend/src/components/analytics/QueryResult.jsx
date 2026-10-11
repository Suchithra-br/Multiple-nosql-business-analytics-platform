import React from 'react';

/**
 * Reusable execution metadata badge for analytical and operational query responses.
 * Displays retrieved record counts, execution latency in milliseconds, and optional database engine tag.
 */
export default function QueryResult({
  count,
  label = 'records',
  durationMs,
  engine,
  id,
}) {
  if (count === undefined && durationMs === undefined) {
    return null;
  }

  const noun = count === 1 ? (label.endsWith('s') ? label.slice(0, -1) : label) : label;

  return (
    <div className="query-meta-bar" id={id}>
      <span className="query-meta-pill">
        {engine && (
          <span className={`engine-tag ${String(engine).toLowerCase()}`}>
            {engine} ·{' '}
          </span>
        )}
        {count !== undefined && `Retrieved ${count} ${noun} `}
        {durationMs !== undefined && `in ${durationMs} ms`}
      </span>
    </div>
  );
}
