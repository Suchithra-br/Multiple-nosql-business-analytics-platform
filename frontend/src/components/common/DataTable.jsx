import React from 'react';
import { exportToCsv } from '../../utils/csvExport.js';
import EmptyState from './EmptyState.jsx';

/**
 * Reusable data table with column alignment, custom cell renderers,
 * fixed header support, and CSV export capabilities.
 */
export default function DataTable({
  columns = [],
  data = [],
  keyField = 'id',
  emptyMessage = 'No data available for the selected filters.',
  id,
  exportFilename,
  maxHeight,
}) {
  if (!data || data.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className="table-wrapper-container" id={id}>
      {exportFilename && (
        <div className="table-export-bar">
          <span className="table-row-count">
            {data.length} {data.length === 1 ? 'record' : 'records'}
          </span>
          <button
            type="button"
            className="btn-export-csv"
            onClick={() => exportToCsv(exportFilename, columns, data)}
            title="Download CSV export"
          >
            <span className="export-icon" aria-hidden="true">📥</span>
            <span>Export CSV</span>
          </button>
        </div>
      )}
      <div
        className={`table-responsive ${maxHeight ? 'table-scroll-constrained' : ''}`}
        style={maxHeight ? { maxHeight } : undefined}
      >
        <table className="analytics-table">
          <colgroup>
            {columns.map((col) => (
              <col key={col.key} style={{ width: col.width || 'auto' }} />
            ))}
          </colgroup>
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{ textAlign: col.align || 'left' }}
                  className={col.className || ''}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => {
              const rowKey = row[keyField] !== undefined ? row[keyField] : idx;
              return (
                <tr key={rowKey} className="table-row-interactive">
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      style={{ textAlign: col.align || 'left' }}
                    >
                      {col.render ? col.render(row[col.key], row, idx) : row[col.key]}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
