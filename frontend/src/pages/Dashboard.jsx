import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { api } from '../services/api.js';
import { formatCurrency, formatNumber } from '../utils/formatters.js';
import { exportToCsv } from '../utils/csvExport.js';
import KpiCard from '../components/KpiCard.jsx';
import ChartCard from '../components/ChartCard.jsx';
import DataTable from '../components/DataTable.jsx';

export default function Dashboard({ refreshTrigger }) {
  // Global Filters
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');

  // KPI Overview
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState(null);

  // Monthly Sales Trend
  const [monthlySales, setMonthlySales] = useState([]);
  const [monthlyLoading, setMonthlyLoading] = useState(true);
  const [monthlyError, setMonthlyError] = useState(null);

  // Regional Sales
  const [regions, setRegions] = useState([]);
  const [regionsLoading, setRegionsLoading] = useState(true);
  const [regionsError, setRegionsError] = useState(null);

  // Category Sales
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState(null);

  // Customer Segments
  const [segments, setSegments] = useState([]);
  const [segmentsLoading, setSegmentsLoading] = useState(true);
  const [segmentsError, setSegmentsError] = useState(null);

  // Shipping Modes
  const [shipping, setShipping] = useState([]);
  const [shippingLoading, setShippingLoading] = useState(true);
  const [shippingError, setShippingError] = useState(null);

  // Sub-Category Analytics (17 sub-categories)
  const [subcategories, setSubcategories] = useState([]);
  const [subcategoriesLoading, setSubcategoriesLoading] = useState(true);
  const [subcategoriesError, setSubcategoriesError] = useState(null);

  // Geographic Detail: Top States
  const [states, setStates] = useState([]);
  const [statesLoading, setStatesLoading] = useState(true);
  const [statesError, setStatesError] = useState(null);

  // Top Products
  const [topProducts, setTopProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState(null);

  // Top Customers
  const [topCustomers, setTopCustomers] = useState([]);
  const [customersLoading, setCustomersLoading] = useState(true);
  const [customersError, setCustomersError] = useState(null);

  // ============================================================================
  // Fetch Functions
  // ============================================================================
  const fetchOverview = useCallback(async (year, region) => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = await api.getOverview(yr, reg);
      setOverview(data);
    } catch (err) {
      setOverviewError(err.message || 'Unable to load executive KPI overview.');
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  const fetchMonthly = useCallback(async (year, region) => {
    setMonthlyLoading(true);
    setMonthlyError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      // In compatibility mode with vitest: if reg is null, call getMonthlySales(yr)
      const data = reg ? await api.getMonthlySales(yr, reg) : await api.getMonthlySales(yr);
      setMonthlySales(data || []);
    } catch (err) {
      setMonthlyError(err.message || 'Unable to load monthly sales trend.');
    } finally {
      setMonthlyLoading(false);
    }
  }, []);

  const fetchRegions = useCallback(async (year) => {
    setRegionsLoading(true);
    setRegionsError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const data = yr ? await api.getRegions(yr) : await api.getRegions();
      setRegions(data || []);
    } catch (err) {
      setRegionsError(err.message || 'Unable to load regional sales breakdown.');
    } finally {
      setRegionsLoading(false);
    }
  }, []);

  const fetchCategories = useCallback(async (year, region) => {
    setCategoriesLoading(true);
    setCategoriesError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = (yr || reg) ? await api.getCategories(yr, reg) : await api.getCategories();
      setCategories(data || []);
    } catch (err) {
      setCategoriesError(err.message || 'Unable to load category sales breakdown.');
    } finally {
      setCategoriesLoading(false);
    }
  }, []);

  const fetchSegments = useCallback(async (year, region) => {
    setSegmentsLoading(true);
    setSegmentsError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = (yr || reg) ? await api.getSegments(yr, reg) : await api.getSegments();
      setSegments(data || []);
    } catch (err) {
      setSegmentsError(err.message || 'Unable to load segment sales breakdown.');
    } finally {
      setSegmentsLoading(false);
    }
  }, []);

  const fetchShipping = useCallback(async (year, region) => {
    setShippingLoading(true);
    setShippingError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = (yr || reg) ? await api.getShipping(yr, reg) : await api.getShipping();
      setShipping(data || []);
    } catch (err) {
      setShippingError(err.message || 'Unable to load shipping modes summary.');
    } finally {
      setShippingLoading(false);
    }
  }, []);

  const fetchSubcategories = useCallback(async (year, region) => {
    if (!api.getSubcategories) return;
    setSubcategoriesLoading(true);
    setSubcategoriesError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = await api.getSubcategories(yr, reg);
      setSubcategories(data || []);
    } catch (err) {
      setSubcategoriesError(err.message || 'Unable to load sub-category analytics.');
    } finally {
      setSubcategoriesLoading(false);
    }
  }, []);

  const fetchStates = useCallback(async (year, region) => {
    if (!api.getStates) return;
    setStatesLoading(true);
    setStatesError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = await api.getStates(yr, reg, 10);
      setStates(data || []);
    } catch (err) {
      setStatesError(err.message || 'Unable to load geographic state analytics.');
    } finally {
      setStatesLoading(false);
    }
  }, []);

  const fetchTopProducts = useCallback(async (year, region) => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = (yr || reg) ? await api.getTopProducts(10, yr, reg) : await api.getTopProducts(10);
      setTopProducts(data || []);
    } catch (err) {
      setProductsError(err.message || 'Unable to load top products leaderboard.');
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const fetchTopCustomers = useCallback(async (year, region) => {
    setCustomersLoading(true);
    setCustomersError(null);
    try {
      const yr = year ? parseInt(year, 10) : null;
      const reg = region || null;
      const data = (yr || reg) ? await api.getTopCustomers(10, yr, reg) : await api.getTopCustomers(10);
      setTopCustomers(data || []);
    } catch (err) {
      setCustomersError(err.message || 'Unable to load top customers leaderboard.');
    } finally {
      setCustomersLoading(false);
    }
  }, []);

  // Coordinated data fetch whenever global filters or refresh trigger change
  useEffect(() => {
    fetchOverview(selectedYear, selectedRegion);
    fetchMonthly(selectedYear, selectedRegion);
    fetchRegions(selectedYear);
    fetchCategories(selectedYear, selectedRegion);
    fetchSegments(selectedYear, selectedRegion);
    fetchShipping(selectedYear, selectedRegion);
    fetchSubcategories(selectedYear, selectedRegion);
    fetchStates(selectedYear, selectedRegion);
    fetchTopProducts(selectedYear, selectedRegion);
    fetchTopCustomers(selectedYear, selectedRegion);
  }, [
    selectedYear,
    selectedRegion,
    refreshTrigger,
    fetchOverview,
    fetchMonthly,
    fetchRegions,
    fetchCategories,
    fetchSegments,
    fetchShipping,
    fetchSubcategories,
    fetchStates,
    fetchTopProducts,
    fetchTopCustomers,
  ]);

  const handleYearChange = (e) => {
    setSelectedYear(e.target.value);
  };

  const handleRegionChange = (e) => {
    setSelectedRegion(e.target.value);
  };

  const handleResetFilters = () => {
    setSelectedYear('');
    setSelectedRegion('');
  };

  // ============================================================================
  // Derived Analytical Highlights (Actual Data Driven)
  // ============================================================================
  const bestRegion = useMemo(() => {
    if (!regions || regions.length === 0) return null;
    return [...regions].sort((a, b) => b.total_sales - a.total_sales)[0];
  }, [regions]);

  const bestMonth = useMemo(() => {
    if (!monthlySales || monthlySales.length === 0) return null;
    return [...monthlySales].sort((a, b) => b.total_sales - a.total_sales)[0];
  }, [monthlySales]);

  const topCategory = useMemo(() => {
    if (!categories || categories.length === 0) return null;
    return [...categories].sort((a, b) => b.total_sales - a.total_sales)[0];
  }, [categories]);

  const maxSubcategorySales = useMemo(() => {
    if (!subcategories || subcategories.length === 0) return 1;
    return Math.max(...subcategories.map((s) => s.total_sales));
  }, [subcategories]);

  // Dynamic "At a Glance" analytical statements
  const dynamicInsights = useMemo(() => {
    const list = [];
    if (bestRegion) {
      list.push(`${bestRegion.region} leads regional sales at ${formatCurrency(bestRegion.total_sales)}.`);
    }
    if (topCategory) {
      list.push(`${topCategory.category} is the highest-revenue category at ${formatCurrency(topCategory.total_sales)}.`);
    }
    if (bestMonth) {
      list.push(`${bestMonth.year_month} was the strongest sales month with ${formatCurrency(bestMonth.total_sales)}.`);
    }
    const avgShip = overview?.average_shipping_days != null ? overview.average_shipping_days.toFixed(1) : '4.0';
    list.push(`Average order fulfillment takes ${avgShip} days across historical shipping modes.`);
    return list;
  }, [bestRegion, topCategory, bestMonth, overview]);

  // ============================================================================
  // Table Columns
  // ============================================================================
  const productColumns = [
    {
      key: 'rank',
      label: 'Rank',
      width: '56px',
      render: (_, __, idx) => (
        <span className={`rank-pill ${idx < 3 ? 'rank-top' : ''}`}>
          #{idx + 1}
        </span>
      ),
    },
    {
      key: 'product_name',
      label: 'Product',
      width: 'auto',
      render: (val, row) => (
        <div className="table-name-cell">
          <span className="table-name-title" title={val}>{val}</span>
          <span className="table-name-sub font-mono">{row.product_id}</span>
        </div>
      ),
    },
    {
      key: 'total_sales',
      label: 'Sales',
      align: 'right',
      width: '130px',
      className: 'col-sales',
      render: (val) => <span className="font-mono text-bold text-accent whitespace-nowrap">{formatCurrency(val)}</span>,
    },
  ];

  const customerColumns = [
    {
      key: 'rank',
      label: 'Rank',
      width: '56px',
      render: (_, __, idx) => (
        <span className={`rank-pill ${idx < 3 ? 'rank-top' : ''}`}>
          #{idx + 1}
        </span>
      ),
    },
    {
      key: 'customer_name',
      label: 'Customer',
      width: 'auto',
      render: (val, row) => (
        <div className="table-name-cell">
          <span className="table-name-title" title={val}>{val}</span>
          <span className="table-name-sub font-mono">{row.customer_id}</span>
        </div>
      ),
    },
    {
      key: 'total_spend',
      label: 'Sales',
      align: 'right',
      width: '130px',
      className: 'col-sales',
      render: (val) => <span className="font-mono text-bold text-accent whitespace-nowrap">{formatCurrency(val)}</span>,
    },
  ];

  const shippingColumns = [
    {
      key: 'ship_mode',
      label: 'Shipping Mode',
      render: (val) => <span className="font-medium">{val}</span>,
    },
    {
      key: 'total_sales',
      label: 'Total Sales',
      align: 'right',
      render: (val) => <span className="font-mono">{formatCurrency(val)}</span>,
    },
    {
      key: 'share',
      label: 'Share of Sales',
      align: 'right',
      render: (_, row) => {
        const total = overview?.total_sales || 2261536.78;
        const pct = total > 0 ? ((row.total_sales / total) * 100).toFixed(1) : '0.0';
        return (
          <div className="shipping-share-container">
            <span className="font-mono text-xs">{pct}%</span>
            <div className="share-bar-bg" aria-hidden="true">
              <div className="share-bar-fill" style={{ width: `${pct}%` }}></div>
            </div>
          </div>
        );
      },
    },
  ];

  const stateColumns = [
    {
      key: 'rank',
      label: 'Rank',
      width: '56px',
      render: (_, __, idx) => (
        <span className={`rank-pill ${idx < 3 ? 'rank-top' : ''}`}>
          #{idx + 1}
        </span>
      ),
    },
    {
      key: 'state',
      label: 'State',
      render: (val) => <span className="font-medium">{val}</span>,
    },
    {
      key: 'region',
      label: 'Region',
      render: (val) => <span className="badge-region-tag">{val}</span>,
    },
    {
      key: 'order_count',
      label: 'Orders',
      align: 'right',
      render: (val) => <span className="font-mono text-sm">{formatNumber(val)}</span>,
    },
    {
      key: 'total_sales',
      label: 'Total Sales',
      align: 'right',
      render: (val) => <span className="font-mono text-bold text-accent whitespace-nowrap">{formatCurrency(val)}</span>,
    },
  ];

  // Helper for KPI YoY trend
  const formatYoyTrend = (growthRate, compLabel) => {
    if (growthRate === null || growthRate === undefined) return null;
    const isPos = growthRate > 0;
    const isNeg = growthRate < 0;
    const prefix = isPos ? '+' : '';
    const label = compLabel ? `vs ${compLabel.split('vs')[1]?.trim() || compLabel}` : 'vs previous year';
    return {
      positive: isPos,
      negative: isNeg,
      text: `${prefix}${growthRate}% ${label}`,
    };
  };

  const isFilterActive = Boolean(selectedYear || selectedRegion);

  return (
    <div className="dashboard-page" id="dashboard-view">
      {/* Dashboard Top Header & Intro */}
      <div className="dashboard-intro">
        <div className="intro-badge">EXECUTIVE OVERVIEW</div>
        <h2 className="intro-title">Executive Sales Overview &amp; Business Insights</h2>
        <p className="intro-subtitle">
          Key business performance indicators and transactional volume across 4,922 orders, 17 sub-categories, and 4 geographic regions.
        </p>
      </div>

      {/* Global Filter Bar */}
      <section className="global-filter-bar mb-24" aria-label="Global Analytics Filters">
        <div className="filter-bar-title-group">
          <span className="filter-bar-icon" aria-hidden="true">🔍</span>
          <span className="filter-bar-title">GLOBAL DATA FILTERS:</span>
        </div>

        <div className="filter-controls-row">
          {/* Year Filter */}
          <div className="filter-control-item">
            <label htmlFor="year-filter-select" className="filter-control-label">
              Filter Year:
            </label>
            <select
              id="year-filter-select"
              className="select-input-standard"
              value={selectedYear}
              onChange={handleYearChange}
            >
              <option value="">All Years (2015–2018)</option>
              <option value="2015">2015</option>
              <option value="2016">2016</option>
              <option value="2017">2017</option>
              <option value="2018">2018</option>
            </select>
          </div>

          {/* Region Filter */}
          <div className="filter-control-item">
            <label htmlFor="region-filter-select" className="filter-control-label">
              Filter Region:
            </label>
            <select
              id="region-filter-select"
              className="select-input-standard"
              value={selectedRegion}
              onChange={handleRegionChange}
            >
              <option value="">All Regions</option>
              <option value="Central">Central</option>
              <option value="East">East</option>
              <option value="South">South</option>
              <option value="West">West</option>
            </select>
          </div>

          {/* Quick Reset */}
          {isFilterActive && (
            <button
              type="button"
              className="btn btn-secondary btn-reset-filters"
              onClick={handleResetFilters}
              title="Reset all filters to All Years and All Regions"
            >
              <span>Reset Filters</span>
            </button>
          )}

          {/* Filter Status Badge */}
          <div className="filter-active-pill">
            <span className="pill-dot"></span>
            <span>
              {isFilterActive
                ? `Filtered: ${selectedYear || 'All Years'} · ${selectedRegion || 'All Regions'}`
                : 'All 4,922 Orders (Complete Dataset)'}
            </span>
          </div>
        </div>
      </section>

      {/* Row 1: KPI Cards Grid */}
      <section className="kpi-grid mb-24" aria-label="Executive KPIs">
        <KpiCard
          id="kpi-total-sales"
          title="TOTAL REVENUE"
          value={overviewLoading ? '...' : overview ? formatCurrency(overview.total_sales) : '$0.00'}
          subtext="2015–2018 total"
          badge={isFilterActive ? 'MongoDB Filtered' : 'Redis Cache'}
          trend={formatYoyTrend(overview?.yoy_sales_growth, overview?.comparison_label)}
          accent="blue"
        />
        <KpiCard
          id="kpi-total-orders"
          title="TOTAL ORDERS"
          value={overviewLoading ? '...' : overview ? formatNumber(overview.total_orders) : '0'}
          subtext="Unique transaction orders"
          badge={isFilterActive ? 'MongoDB Filtered' : 'Redis Cache'}
          trend={formatYoyTrend(overview?.yoy_orders_growth, overview?.comparison_label)}
          accent="emerald"
        />
        <KpiCard
          id="kpi-avg-order-value"
          title="AVERAGE ORDER VALUE"
          value={overviewLoading ? '...' : overview ? formatCurrency(overview.average_order_value) : '$0.00'}
          subtext="Mean transaction order total"
          badge={isFilterActive ? 'MongoDB Filtered' : 'Redis Cache'}
          trend={formatYoyTrend(overview?.yoy_aov_growth, overview?.comparison_label)}
          accent="amber"
        />
        <KpiCard
          id="kpi-avg-shipping-time"
          title="AVG SHIPPING TIME"
          value={
            overviewLoading
              ? '...'
              : overview?.average_shipping_days != null
              ? `${overview.average_shipping_days.toFixed(1)} days`
              : '4.0 days'
          }
          subtext="Ship Date − Order Date average"
          badge="ETL Derived"
          accent="slate"
        />
      </section>

      {/* Row 2: "At A Glance" Analytical Insights Strip & Context Highlights */}
      <section className="insights-section mb-24" aria-label="At a Glance Business Insights">
        <div className="insights-card">
          <div className="insights-header">
            <div className="insights-header-left">
              <span className="insights-icon" aria-hidden="true">💡</span>
              <span className="insights-title">AT A GLANCE — BUSINESS INSIGHTS</span>
            </div>
            <div className="context-pills-row">
              {bestRegion && (
                <div className="context-metric-pill" title="Leading geographic sales territory">
                  <span className="context-metric-label">Best Region:</span>
                  <span className="context-metric-val">{bestRegion.region} · {formatCurrency(bestRegion.total_sales)}</span>
                </div>
              )}
              {bestMonth && (
                <div className="context-metric-pill" title="Highest revenue calendar month">
                  <span className="context-metric-label">Best Month:</span>
                  <span className="context-metric-val">{bestMonth.year_month} · {formatCurrency(bestMonth.total_sales)}</span>
                </div>
              )}
            </div>
          </div>

          <div className="insights-statements-grid">
            {dynamicInsights.map((stmt, idx) => (
              <div key={idx} className="insight-statement-item">
                <span className="statement-dot" aria-hidden="true"></span>
                <span className="statement-text">{stmt}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Row 3: Temporal & Regional Sales (Monthly Dominant 68% + Regional 32%) */}
      <section className="layout-row-monthly-region mb-24" aria-label="Temporal and Regional Analysis">
        {/* Dominant Monthly Sales Trend */}
        <ChartCard
          id="monthly-trend-card"
          className="card-dominant"
          title="Monthly Sales Trend"
          subtitle={`Chronological sales volume ${selectedYear ? `for ${selectedYear}` : 'across 2015–2018'}${selectedRegion ? ` in ${selectedRegion} Region` : ''}`}
          loading={monthlyLoading}
          error={monthlyError}
        >
          <div style={{ width: '100%', height: 320 }} id="monthly-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlySales} margin={{ top: 12, right: 16, left: 16, bottom: 25 }}>
                <defs>
                  <linearGradient id="monthlyAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.22} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="year_month"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  interval={selectedYear ? 0 : 5}
                  angle={-35}
                  textAnchor="end"
                  height={45}
                  stroke="#cbd5e1"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `$${Math.round(val / 1000)}k`}
                  stroke="#cbd5e1"
                />
                <Tooltip
                  formatter={(val) => [formatCurrency(val), 'Sales']}
                  labelFormatter={(lbl) => `Month: ${lbl}`}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.08)',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total_sales"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#monthlyAreaGrad)"
                  name="Sales"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Regional Sales */}
        <ChartCard
          id="regional-sales-card"
          className="card-side"
          title="Regional Sales"
          subtitle={`Revenue distribution across 4 regions ${selectedYear ? `(${selectedYear})` : ''}`}
          loading={regionsLoading}
          error={regionsError}
        >
          <div style={{ width: '100%', height: 320 }} id="regional-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regions} margin={{ top: 12, right: 8, left: 12, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="region" tick={{ fontSize: 12, fill: '#334155' }} stroke="#cbd5e1" />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `$${Math.round(val / 1000)}k`}
                  stroke="#cbd5e1"
                />
                <Tooltip
                  formatter={(val) => [formatCurrency(val), 'Total Sales']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="total_sales" fill="#2563eb" radius={[4, 4, 0, 0]} name="Sales" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </section>

      {/* Row 4: Category Breakdown & Customer Segments */}
      <section className="grid-2-col mb-24" aria-label="Category and Segment Performance">
        {/* Category Breakdown */}
        <ChartCard
          id="category-sales-card"
          title="Category Sales"
          subtitle="Volume across Technology, Furniture, and Office Supplies"
          loading={categoriesLoading}
          error={categoriesError}
        >
          <div style={{ width: '100%', height: 260 }} id="category-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categories} margin={{ top: 10, right: 10, left: 15, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="category" tick={{ fontSize: 12, fill: '#334155' }} stroke="#cbd5e1" />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `$${Math.round(val / 1000)}k`}
                  stroke="#cbd5e1"
                />
                <Tooltip
                  formatter={(val) => [formatCurrency(val), 'Total Sales']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="total_sales" fill="#2563eb" radius={[4, 4, 0, 0]} name="Sales" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Customer Segments */}
        <ChartCard
          id="segment-sales-card"
          title="Customer Segments"
          subtitle="Consumer, Corporate, and Home Office contribution"
          loading={segmentsLoading}
          error={segmentsError}
        >
          <div style={{ width: '100%', height: 260 }} id="segment-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segments} margin={{ top: 10, right: 10, left: 15, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="segment" tick={{ fontSize: 12, fill: '#334155' }} stroke="#cbd5e1" />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `$${Math.round(val / 1000)}k`}
                  stroke="#cbd5e1"
                />
                <Tooltip
                  formatter={(val) => [formatCurrency(val), 'Sales']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="total_sales" fill="#2563eb" radius={[4, 4, 0, 0]} name="Sales" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </section>

      {/* Row 5: Sub-Category Analytics (17 Sub-Categories Ranked Visualization) */}
      <section className="mb-24" aria-label="Sub-Category Sales Performance">
        <ChartCard
          id="subcategory-sales-card"
          title="Sales by Sub-Category (All 17 Lines)"
          subtitle="Ranked merchandise volume across Technology, Furniture, and Office Supplies"
          loading={subcategoriesLoading}
          error={subcategoriesError}
          filterControls={
            subcategories && subcategories.length > 0 && (
              <button
                type="button"
                className="btn-export-csv"
                onClick={() =>
                  exportToCsv(
                    `superstore_subcategories_${selectedYear || 'all'}_${selectedRegion || 'all'}`,
                    [
                      { key: 'sub_category', label: 'Sub-Category' },
                      { key: 'category', label: 'Category' },
                      { key: 'total_sales', label: 'Total Sales' },
                    ],
                    subcategories
                  )
                }
                title="Export sub-category sales data"
              >
                <span>📥 Export CSV</span>
              </button>
            )
          }
        >
          <div className="subcategory-ranked-container" id="subcategory-bars-view">
            {subcategories && subcategories.length > 0 ? (
              <div className="subcategory-grid-list">
                {subcategories.map((item, idx) => {
                  const pct = Math.max(4, Math.round((item.total_sales / maxSubcategorySales) * 100));
                  const catClass =
                    item.category === 'Technology'
                      ? 'cat-tech'
                      : item.category === 'Furniture'
                      ? 'cat-furn'
                      : 'cat-office';

                  return (
                    <div key={item.sub_category} className="subcategory-row-item">
                      <div className="subcat-info-col">
                        <span className="subcat-rank font-mono">#{idx + 1}</span>
                        <span className="subcat-name">{item.sub_category}</span>
                        <span className={`subcat-cat-tag ${catClass}`}>{item.category}</span>
                      </div>
                      <div className="subcat-bar-col">
                        <div className="subcat-bar-track" aria-hidden="true">
                          <div className={`subcat-bar-fill ${catClass}`} style={{ width: `${pct}%` }}></div>
                        </div>
                      </div>
                      <div className="subcat-val-col">
                        <span className="subcat-val font-mono">{formatCurrency(item.total_sales)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">
                <p className="empty-state-message">No sub-category data available for the active filters.</p>
              </div>
            )}
          </div>
        </ChartCard>
      </section>

      {/* Row 6: Geography Detail View (Top 10 States) & Shipping Mode Breakdown */}
      <section className="grid-2-col mb-24" aria-label="Geographic and Shipping Breakdown">
        {/* Top 10 States by Sales */}
        <ChartCard
          id="top-states-card"
          title="Top 10 States by Sales Volume"
          subtitle="State-level revenue distribution with regional territory mapping"
          loading={statesLoading}
          error={statesError}
        >
          <DataTable
            id="top-states-table"
            columns={stateColumns}
            data={states}
            keyField="state"
            exportFilename={`superstore_top_states_${selectedYear || 'all'}_${selectedRegion || 'all'}`}
          />
        </ChartCard>

        {/* Shipping Modes */}
        <ChartCard
          id="shipping-summary-card"
          title="Shipping Mode Breakdown"
          subtitle="Fulfillment method volume, sales, and total contribution"
          loading={shippingLoading}
          error={shippingError}
        >
          <DataTable
            id="shipping-table"
            columns={shippingColumns}
            data={shipping}
            keyField="ship_mode"
            exportFilename={`superstore_shipping_${selectedYear || 'all'}_${selectedRegion || 'all'}`}
          />
        </ChartCard>
      </section>

      {/* Row 7: Top Products & Top Customers Leaderboards (50% / 50%) */}
      <section className="grid-2-col mb-24" aria-label="Top Leaderboards">
        {/* Top 10 Products */}
        <ChartCard
          id="top-products-card"
          title="Top 10 Products by Revenue"
          subtitle="Ranked via Redis sorted set (ZREVRANGE) with catalog metadata"
          loading={productsLoading}
          error={productsError}
        >
          <DataTable
            id="top-products-table"
            columns={productColumns}
            data={topProducts}
            keyField="product_id"
            exportFilename={`superstore_top_products_${selectedYear || 'all'}_${selectedRegion || 'all'}`}
          />
        </ChartCard>

        {/* Top 10 Customers */}
        <ChartCard
          id="top-customers-card"
          title="Top 10 Customers by Lifetime Spend"
          subtitle="Ranked via Redis sorted set (ZREVRANGE) with account metadata"
          loading={customersLoading}
          error={customersError}
        >
          <DataTable
            id="top-customers-table"
            columns={customerColumns}
            data={topCustomers}
            keyField="customer_id"
            exportFilename={`superstore_top_customers_${selectedYear || 'all'}_${selectedRegion || 'all'}`}
          />
        </ChartCard>
      </section>

      {/* Row 8: Analytical Architecture Summary Card */}
      <section className="mb-24" aria-label="Architecture Layer Overview">
        <div className="platform-stats-card">
          <div className="stats-card-header">
            <span className="stats-badge">ARCHITECTURE OVERVIEW</span>
            <h3 className="stats-title">Multi-NoSQL Polyglot Persistence Layer</h3>
            <p className="stats-desc">
              Containerized multi-model data architecture distributing query workloads across purpose-built NoSQL database engines.
            </p>
          </div>
          <div className="stats-metric-list">
            <div className="stat-row">
              <span className="stat-label">Total Transactions</span>
              <span className="stat-val font-mono">9,800 Line Items</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Unique Transaction Orders</span>
              <span className="stat-val font-mono">4,922 Orders</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Unique Product Catalog</span>
              <span className="stat-val font-mono">1,861 Products</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Customer Accounts</span>
              <span className="stat-val font-mono">793 Customers</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
