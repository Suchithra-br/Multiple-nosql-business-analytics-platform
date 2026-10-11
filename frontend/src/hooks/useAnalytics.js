import { useState, useCallback } from 'react';
import { analyticsApi } from '../services/api/analyticsApi.js';

/**
 * Custom React hook for Query Explorer & Analytics.
 * Provides section management, query execution timing, error handling,
 * and direct access to polyglot NoSQL query endpoints.
 */
export function useAnalytics() {
  const [activeSection, setActiveSection] = useState('mongodb');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQueryDurationMs, setLastQueryDurationMs] = useState(null);

  /**
   * Helper that executes an async analytical query with real duration measurement.
   */
  const executeQuery = useCallback(async (queryFn) => {
    setLoading(true);
    setError(null);
    const start = performance.now();

    try {
      const data = await queryFn();
      const durationMs = Math.round(performance.now() - start);
      setLastQueryDurationMs(durationMs);
      return { data, durationMs };
    } catch (err) {
      const durationMs = Math.round(performance.now() - start);
      setLastQueryDurationMs(durationMs);
      setError(err?.message || 'Query execution failed.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    activeSection,
    setActiveSection,
    loading,
    error,
    lastQueryDurationMs,
    executeQuery,
    api: analyticsApi,
  };
}

export default useAnalytics;
