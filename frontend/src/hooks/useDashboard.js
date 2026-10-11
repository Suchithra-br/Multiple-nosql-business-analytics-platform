import { useState, useEffect, useCallback } from 'react';
import { dashboardApi } from '../services/api/dashboardApi.js';

/**
 * Custom React hook for Dashboard state and data fetching.
 * Encapsulates multi-endpoint orchestration, filtering, error handling,
 * and refresh synchronization across executive KPI panels.
 */
export function useDashboard(refreshTrigger = 0) {
  const [yearFilter, setYearFilter] = useState('all');
  const [regionFilter, setRegionFilter] = useState('all');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [overview, setOverview] = useState(null);
  const [monthlySales, setMonthlySales] = useState([]);
  const [regions, setRegions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [segments, setSegments] = useState([]);
  const [shipping, setShipping] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [states, setStates] = useState([]);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const yearParam = yearFilter === 'all' ? null : parseInt(yearFilter, 10);
    const regionParam = regionFilter === 'all' ? null : regionFilter;

    try {
      const [
        overviewData,
        monthlyData,
        regionsData,
        categoriesData,
        segmentsData,
        shippingData,
        subcategoriesData,
        statesData,
      ] = await Promise.all([
        dashboardApi.getOverview(yearParam, regionParam),
        dashboardApi.getMonthlySales(yearParam, regionParam),
        dashboardApi.getRegions(yearParam),
        dashboardApi.getCategories(yearParam, regionParam),
        dashboardApi.getSegments(yearParam, regionParam),
        dashboardApi.getShipping(yearParam, regionParam),
        dashboardApi.getSubcategories(yearParam, regionParam),
        dashboardApi.getStates(yearParam, regionParam, 10),
      ]);

      setOverview(overviewData);
      setMonthlySales(monthlyData || []);
      setRegions(regionsData || []);
      setCategories(categoriesData || []);
      setSegments(segmentsData || []);
      setShipping(shippingData || []);
      setSubcategories(subcategoriesData || []);
      setStates(statesData || []);
    } catch (err) {
      setError(err?.message || 'Failed to load dashboard metrics from backend.');
    } finally {
      setLoading(false);
    }
  }, [yearFilter, regionFilter]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData, refreshTrigger]);

  const resetFilters = useCallback(() => {
    setYearFilter('all');
    setRegionFilter('all');
  }, []);

  return {
    yearFilter,
    setYearFilter,
    regionFilter,
    setRegionFilter,
    resetFilters,
    loading,
    error,
    overview,
    monthlySales,
    regions,
    categories,
    segments,
    shipping,
    subcategories,
    states,
    refetch: fetchDashboardData,
  };
}

export default useDashboard;
