import React, { useState, useEffect } from 'react';
import { api } from '../services/api.js';
import { formatCurrency, formatNumber } from '../utils/formatters.js';
import ChartCard from '../components/ChartCard.jsx';
import DataTable from '../components/DataTable.jsx';

export default function Analytics() {
  // Navigation active state
  const [activeSection, setActiveSection] = useState('mongodb');

  // ============================================================================
  // MongoDB: Order Lookup & Autocomplete
  // ============================================================================
  const [orderIdInput, setOrderIdInput] = useState('CA-2017-152156');
  const [orderResult, setOrderResult] = useState(null);
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderError, setOrderError] = useState(null);
  const [orderMeta, setOrderMeta] = useState(null);
  const [orderSuggestions, setOrderSuggestions] = useState([]);
  const [showOrderSuggestions, setShowOrderSuggestions] = useState(false);

  // Live order search autocomplete
  useEffect(() => {
    if (!orderIdInput || orderIdInput.trim().length < 3) {
      setOrderSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        if (api.searchOrders) {
          const results = await api.searchOrders(orderIdInput.trim(), 5);
          setOrderSuggestions(results || []);
        }
      } catch {
        setOrderSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [orderIdInput]);

  const handleOrderLookup = async (e, overrideId = null) => {
    if (e) e.preventDefault();
    const targetId = (overrideId || orderIdInput).trim();
    if (!targetId) return;

    setOrderLoading(true);
    setOrderError(null);
    setOrderResult(null);
    setShowOrderSuggestions(false);
    const t0 = performance.now();

    try {
      const data = await api.getOrderById(targetId);
      const duration = Math.round(performance.now() - t0);
      setOrderResult(data);
      setOrderMeta({ rows: data.items ? data.items.length : 1, duration });
    } catch (err) {
      setOrderError(err.message || `No order found for "${targetId}"`);
    } finally {
      setOrderLoading(false);
    }
  };

  const handleSelectOrderSuggestion = (item) => {
    setOrderIdInput(item.order_id);
    setShowOrderSuggestions(false);
    handleOrderLookup(null, item.order_id);
  };

  // ============================================================================
  // MongoDB: Customer Lookup & Autocomplete
  // ============================================================================
  const [customerIdInput, setCustomerIdInput] = useState('CG-12520');
  const [customerResult, setCustomerResult] = useState(null);
  const [customerLoading, setCustomerLoading] = useState(false);
  const [customerError, setCustomerError] = useState(null);
  const [customerMeta, setCustomerMeta] = useState(null);
  const [customerSuggestions, setCustomerSuggestions] = useState([]);
  const [showCustomerSuggestions, setShowCustomerSuggestions] = useState(false);

  // Live customer search autocomplete
  useEffect(() => {
    if (!customerIdInput || customerIdInput.trim().length < 2) {
      setCustomerSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        if (api.searchCustomers) {
          const results = await api.searchCustomers(customerIdInput.trim(), 5);
          setCustomerSuggestions(results || []);
        }
      } catch {
        setCustomerSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [customerIdInput]);

  const handleCustomerLookup = async (e, overrideId = null) => {
    if (e) e.preventDefault();
    const cid = (overrideId || customerIdInput).trim();
    if (!cid) return;

    setCustomerLoading(true);
    setCustomerError(null);
    setCustomerResult(null);
    setShowCustomerSuggestions(false);
    const t0 = performance.now();

    try {
      const data = await api.getCustomerById(cid);
      let firstDate = data.first_order_date || null;
      let lastDate = data.last_order_date || null;

      // If dates not directly returned, compute from customer orders if available
      if (!firstDate && Array.isArray(data.orders) && data.orders.length > 0) {
        const sortedDates = data.orders.map((o) => o.order_date).filter(Boolean).sort();
        if (sortedDates.length > 0) {
          firstDate = sortedDates[0];
          lastDate = sortedDates[sortedDates.length - 1];
        }
      }

      // If still missing, query graph customer orders to obtain true dates
      if (!firstDate) {
        try {
          const orders = await api.getCustomerOrdersGraph(cid);
          if (Array.isArray(orders) && orders.length > 0) {
            const sortedDates = orders.map((o) => o.order_date).filter(Boolean).sort();
            if (sortedDates.length > 0) {
              firstDate = sortedDates[0];
              lastDate = sortedDates[sortedDates.length - 1];
            }
          }
        } catch (_) {
          // Gracefully continue
        }
      }

      const duration = Math.round(performance.now() - t0);
      setCustomerResult({
        ...data,
        first_order_date: firstDate,
        last_order_date: lastDate,
      });
      setCustomerMeta({ rows: 1, duration });
    } catch (err) {
      setCustomerError(err.message || `No customer found for "${cid}"`);
    } finally {
      setCustomerLoading(false);
    }
  };

  const handleSelectCustomerSuggestion = (item) => {
    setCustomerIdInput(item.customer_id);
    setShowCustomerSuggestions(false);
    handleCustomerLookup(null, item.customer_id);
  };

  // ============================================================================
  // Cassandra: Date Analytics
  // ============================================================================
  const [targetDate, setTargetDate] = useState('2017-11-08');
  const [dateSales, setDateSales] = useState(null);
  const [dateLoading, setDateLoading] = useState(false);
  const [dateError, setDateError] = useState(null);
  const [dateMeta, setDateMeta] = useState(null);
  const [showDateQuery, setShowDateQuery] = useState(false);

  const handleDateLookup = async (e) => {
    if (e) e.preventDefault();
    if (!targetDate) return;

    setDateLoading(true);
    setDateError(null);
    const t0 = performance.now();

    try {
      const data = await api.getSalesByDate(targetDate);
      const duration = Math.round(performance.now() - t0);
      setDateSales(data || []);
      setDateMeta({ rows: data ? data.length : 0, duration });
    } catch (err) {
      setDateError(err.message || `No transaction records found for date ${targetDate}`);
    } finally {
      setDateLoading(false);
    }
  };

  // ============================================================================
  // Cassandra: Region Date Range
  // ============================================================================
  const [regionSelect, setRegionSelect] = useState('West');
  const [regionStartDate, setRegionStartDate] = useState('2018-01-01');
  const [regionEndDate, setRegionEndDate] = useState('2018-01-31');
  const [regionDateSales, setRegionDateSales] = useState(null);
  const [regionDateLoading, setRegionDateLoading] = useState(false);
  const [regionDateError, setRegionDateError] = useState(null);
  const [regionDateMeta, setRegionDateMeta] = useState(null);
  const [showRegionDateQuery, setShowRegionDateQuery] = useState(false);

  const handleRegionDateLookup = async (e) => {
    if (e) e.preventDefault();
    if (regionStartDate > regionEndDate) {
      setRegionDateError('Start date must be less than or equal to end date.');
      return;
    }

    setRegionDateLoading(true);
    setRegionDateError(null);
    const t0 = performance.now();

    try {
      const data = await api.getSalesByRegionDate(regionSelect, regionStartDate, regionEndDate);
      const duration = Math.round(performance.now() - t0);
      setRegionDateSales(data || []);
      setRegionDateMeta({ rows: data ? data.length : 0, duration });
    } catch (err) {
      setRegionDateError(err.message || `No regional sales records found for ${regionSelect}`);
    } finally {
      setRegionDateLoading(false);
    }
  };

  // ============================================================================
  // Cassandra: Category Date Range
  // ============================================================================
  const [categorySelect, setCategorySelect] = useState('Technology');
  const [categoryStartDate, setCategoryStartDate] = useState('2018-06-01');
  const [categoryEndDate, setCategoryEndDate] = useState('2018-06-30');
  const [categoryDateSales, setCategoryDateSales] = useState(null);
  const [categoryDateLoading, setCategoryDateLoading] = useState(false);
  const [categoryDateError, setCategoryDateError] = useState(null);
  const [categoryDateMeta, setCategoryDateMeta] = useState(null);
  const [showCategoryDateQuery, setShowCategoryDateQuery] = useState(false);

  const handleCategoryDateLookup = async (e) => {
    if (e) e.preventDefault();
    if (categoryStartDate > categoryEndDate) {
      setCategoryDateError('Start date must be less than or equal to end date.');
      return;
    }

    setCategoryDateLoading(true);
    setCategoryDateError(null);
    const t0 = performance.now();

    try {
      const data = await api.getSalesByCategoryDate(categorySelect, categoryStartDate, categoryEndDate);
      const duration = Math.round(performance.now() - t0);
      setCategoryDateSales(data || []);
      setCategoryDateMeta({ rows: data ? data.length : 0, duration });
    } catch (err) {
      setCategoryDateError(err.message || `No category sales records found for ${categorySelect}`);
    } finally {
      setCategoryDateLoading(false);
    }
  };

  // ============================================================================
  // Neo4j: Graph Analytics
  // ============================================================================
  const [graphCustomerId, setGraphCustomerId] = useState('CG-12520');
  const [customerOrdersGraph, setCustomerOrdersGraph] = useState(null);
  const [customerProductsGraph, setCustomerProductsGraph] = useState(null);
  const [graphCustomerLoading, setGraphCustomerLoading] = useState(false);
  const [graphCustomerError, setGraphCustomerError] = useState(null);
  const [customerGraphMeta, setCustomerGraphMeta] = useState(null);
  const [showCustomerGraphQuery, setShowCustomerGraphQuery] = useState(false);

  const handleGraphCustomerLookup = async (e) => {
    if (e) e.preventDefault();
    if (!graphCustomerId.trim()) return;

    setGraphCustomerLoading(true);
    setGraphCustomerError(null);
    const t0 = performance.now();

    try {
      const [orders, products] = await Promise.all([
        api.getCustomerOrdersGraph(graphCustomerId.trim()),
        api.getCustomerProductsGraph(graphCustomerId.trim()),
      ]);
      const duration = Math.round(performance.now() - t0);
      const totalRows = (orders ? orders.length : 0) + (products ? products.length : 0);
      setCustomerOrdersGraph(orders || []);
      setCustomerProductsGraph(products || []);
      setCustomerGraphMeta({ rows: totalRows, duration });
    } catch (err) {
      setGraphCustomerError(err.message || `No graph records found for customer ${graphCustomerId.trim()}`);
    } finally {
      setGraphCustomerLoading(false);
    }
  };

  // Neo4j: Co-Purchases
  const [copurchaseProductId, setCopurchaseProductId] = useState('FUR-BO-10001798');
  const [copurchaseResults, setCopurchaseResults] = useState(null);
  const [copurchaseLoading, setCopurchaseLoading] = useState(false);
  const [copurchaseError, setCopurchaseError] = useState(null);
  const [copurchaseMeta, setCopurchaseMeta] = useState(null);
  const [showCopurchaseQuery, setShowCopurchaseQuery] = useState(false);

  const handleCopurchaseLookup = async (e) => {
    if (e) e.preventDefault();
    if (!copurchaseProductId.trim()) return;

    setCopurchaseLoading(true);
    setCopurchaseError(null);
    const t0 = performance.now();

    try {
      const data = await api.getProductCoPurchases(copurchaseProductId.trim(), 10);
      const duration = Math.round(performance.now() - t0);
      setCopurchaseResults(data || []);
      setCopurchaseMeta({ rows: data ? data.length : 0, duration });
    } catch (err) {
      setCopurchaseError(err.message || `No co-purchased items found for product ${copurchaseProductId.trim()}`);
    } finally {
      setCopurchaseLoading(false);
    }
  };

  // Neo4j: Region Taxonomy
  const [graphRegionSelect, setGraphRegionSelect] = useState('West');
  const [regionCategoriesGraph, setRegionCategoriesGraph] = useState(null);
  const [graphRegionLoading, setGraphRegionLoading] = useState(false);
  const [graphRegionError, setGraphRegionError] = useState(null);
  const [regionGraphMeta, setRegionGraphMeta] = useState(null);
  const [showRegionGraphQuery, setShowRegionGraphQuery] = useState(false);

  const handleGraphRegionLookup = async (e) => {
    if (e) e.preventDefault();

    setGraphRegionLoading(true);
    setGraphRegionError(null);
    const t0 = performance.now();

    try {
      const data = await api.getRegionCategoriesGraph(graphRegionSelect);
      const duration = Math.round(performance.now() - t0);
      setRegionCategoriesGraph(data || []);
      setRegionGraphMeta({ rows: data ? data.length : 0, duration });
    } catch (err) {
      setGraphRegionError(err.message || `No categories found for region ${graphRegionSelect}`);
    } finally {
      setGraphRegionLoading(false);
    }
  };

  // Safe initial default queries for live demo (bypassed in Vitest test runs to keep mocks intact)
  useEffect(() => {
    const isTest = typeof window !== 'undefined' && (
      navigator.userAgent.includes('jsdom') ||
      import.meta.env?.MODE === 'test'
    );
    if (!isTest) {
      handleOrderLookup();
      handleCustomerLookup();
      handleDateLookup();
      handleRegionDateLookup();
      handleCategoryDateLookup();
      handleGraphCustomerLookup();
      handleCopurchaseLookup();
      handleGraphRegionLookup();
    }
  }, []);

  const scrollToSection = (sectionId) => {
    setActiveSection(sectionId.replace('section-', ''));
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="analytics-page" id="analytics-view">
      {/* Analytics Page Intro */}
      <div className="dashboard-intro">
        <div className="intro-badge">QUERY EXPLORER · MULTI-NOSQL ENGINES</div>
        <h2 className="intro-title">Interactive Multi-NoSQL Query Explorer</h2>
        <p className="intro-subtitle">
          Query operational documents in MongoDB, execute partition-keyed time-series slices in Cassandra, and traverse multi-hop graphs in Neo4j.
        </p>
      </div>

      {/* Sticky Section Quick Navigation Bar */}
      <nav className="analytics-quick-nav mb-24" aria-label="Database sections navigation">
        <span className="quick-nav-label">DATABASE SECTIONS:</span>
        <button
          type="button"
          className={`quick-nav-btn ${activeSection === 'mongodb' ? 'active' : ''}`}
          onClick={() => scrollToSection('section-mongodb')}
        >
          <span className="db-dot dot-mongodb" />
          MongoDB Documents
        </button>
        <button
          type="button"
          className={`quick-nav-btn ${activeSection === 'cassandra' ? 'active' : ''}`}
          onClick={() => scrollToSection('section-cassandra')}
        >
          <span className="db-dot dot-cassandra" />
          Cassandra Time-Series
        </button>
        <button
          type="button"
          className={`quick-nav-btn ${activeSection === 'neo4j' ? 'active' : ''}`}
          onClick={() => scrollToSection('section-neo4j')}
        >
          <span className="db-dot dot-neo4j" />
          Neo4j Graph Queries
        </button>
      </nav>

      {/* Section 1: Storage Role Cards */}
      <section className="storage-role-strip mb-32" aria-label="NoSQL Database Roles">
        <div className="section-header-row mb-16">
          <div className="section-pill">DATABASE ARCHITECTURE</div>
          <h3 className="section-title-sm">Specialized Storage Engines &amp; Query Responsibilities</h3>
        </div>

        <div className="grid-4-col">
          <div className="db-role-card accent-redis" id="db-role-redis">
            <div className="db-role-header">
              <span className="db-badge redis">Redis</span>
              <span className="db-engine-type">In-Memory Cache</span>
            </div>
            <div className="db-role-name">Executive KPI Cache</div>
            <p className="db-role-desc">
              Sub-millisecond dashboard cache storing verified KPI totals, monthly time-series, and sorted set leaderboards.
            </p>
          </div>

          <div className="db-role-card accent-mongodb" id="db-role-mongodb">
            <div className="db-role-header">
              <span className="db-badge mongodb">MongoDB</span>
              <span className="db-engine-type">Document Store</span>
            </div>
            <div className="db-role-name">Operational Master</div>
            <p className="db-role-desc">
              Operational business data and lookups: Single Source of Truth for 4,922 denormalized orders with embedded line items.
            </p>
          </div>

          <div className="db-role-card accent-cassandra" id="db-role-cassandra">
            <div className="db-role-header">
              <span className="db-badge cassandra">Cassandra</span>
              <span className="db-engine-type">Wide-Column Store</span>
            </div>
            <div className="db-role-name">Time-Based Analytics</div>
            <p className="db-role-desc">
              Time/query-driven analytics: Partition-keyed daily lookups and clustering key ranges without relational table scans.
            </p>
          </div>

          <div className="db-role-card accent-neo4j" id="db-role-neo4j">
            <div className="db-role-header">
              <span className="db-badge neo4j">Neo4j</span>
              <span className="db-engine-type">Graph Database</span>
            </div>
            <div className="db-role-name">Relationship Analytics</div>
            <p className="db-role-desc">
              Relationship and graph analytics: Index-free graph traversal for customer purchase paths and product co-purchasing.
            </p>
          </div>
        </div>
      </section>

      {/* Section 2: MongoDB Operational Lookups & Search */}
      <section id="section-mongodb" className="mb-32" aria-label="MongoDB Operational Queries">
        <div className="section-header-row mb-16">
          <div className="section-pill">DOCUMENT STORE</div>
          <h3 className="section-title-sm">MongoDB — Operational Business Lookups &amp; Search</h3>
        </div>

        <div className="grid-2-col">
          {/* Order Lookup & Autocomplete */}
          <ChartCard
            id="order-lookup-card"
            title="Order Document Lookup"
            subtitle="GET /api/v1/analytics/orders/{order_id} (MongoDB Single Source of Truth)"
            loading={orderLoading}
            error={orderError}
          >
            <form onSubmit={handleOrderLookup} className="search-form-row mb-16 relative">
              <div className="input-group-flex relative">
                <label htmlFor="order-id-input" className="form-label-sr">Order ID:</label>
                <input
                  id="order-id-input"
                  type="text"
                  aria-label="Order ID"
                  className="input-text-clean"
                  placeholder="Search order ID... (e.g. CA-2017-152156)"
                  value={orderIdInput}
                  onChange={(e) => {
                    setOrderIdInput(e.target.value);
                    setShowOrderSuggestions(true);
                  }}
                  onFocus={() => setShowOrderSuggestions(true)}
                />

                {/* Live Suggestions Dropdown */}
                {showOrderSuggestions && orderSuggestions.length > 0 && (
                  <div className="autocomplete-dropdown">
                    <div className="autocomplete-header">Available Orders:</div>
                    {orderSuggestions.map((item) => (
                      <div
                        key={item.order_id}
                        className="autocomplete-item"
                        onClick={() => handleSelectOrderSuggestion(item)}
                      >
                        <span className="font-mono font-bold text-accent">{item.order_id}</span>
                        <span className="autocomplete-sub">{item.customer_name} · {item.order_date} · {formatCurrency(item.order_total)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-order-btn"
                disabled={orderLoading || !orderIdInput.trim()}
              >
                {orderLoading ? 'Searching...' : 'Lookup Order'}
              </button>
            </form>

            {orderMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Retrieved {orderMeta.rows} {orderMeta.rows === 1 ? 'line item' : 'line items'} in {orderMeta.duration} ms
                </span>
              </div>
            )}

            {orderResult ? (
              <div className="result-detail-box" id="order-detail-view">
                <div className="detail-meta-grid">
                  <div className="meta-item">
                    <span className="meta-k">Order ID</span>
                    <span className="meta-v font-mono">{orderResult.order_id}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Customer</span>
                    <span className="meta-v">
                      {orderResult.customer?.customer_name} ({orderResult.customer?.segment})
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Order Date</span>
                    <span className="meta-v font-mono">{orderResult.order_date}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Ship Date</span>
                    <span className="meta-v font-mono">{orderResult.ship_date}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Shipping Mode</span>
                    <span className="meta-v">{orderResult.ship_mode}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Shipping Duration</span>
                    <span className="meta-v font-mono">{orderResult.shipping_days} days</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Order Total</span>
                    <span className="meta-v font-mono text-bold text-accent">
                      {formatCurrency(orderResult.order_total)}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Delivery Location</span>
                    <span className="meta-v">
                      {orderResult.shipping_address?.city}, {orderResult.shipping_address?.state}{' '}
                      {orderResult.shipping_address?.postal_code || ''} ({orderResult.shipping_address?.region})
                    </span>
                  </div>
                </div>

                <div className="mt-16">
                  <div className="sub-table-header">Embedded Items ({orderResult.items?.length || 0})</div>
                  <DataTable
                    id="order-items-table"
                    data={orderResult.items || []}
                    keyField="row_id"
                    exportFilename={`superstore_order_${orderResult.order_id}_items`}
                    columns={[
                      { key: 'row_id', label: '#', width: '48px' },
                      { key: 'product_id', label: 'Product ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                      { key: 'product_name', label: 'Product Name' },
                      { key: 'category', label: 'Category', width: '110px' },
                      { key: 'sales', label: 'Sales', align: 'right', width: '120px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                    ]}
                  />
                </div>
              </div>
            ) : (
              !orderError && !orderLoading && (
                <div className="helper-hint">
                  Try sample order: <code>CA-2017-152156</code> or <code>US-2016-108966</code>
                </div>
              )
            )}
          </ChartCard>

          {/* Customer Lookup & Autocomplete */}
          <ChartCard
            id="customer-lookup-card"
            title="Customer Profile Lookup"
            subtitle="GET /api/v1/analytics/customers/{customer_id} (Customer business metrics)"
            loading={customerLoading}
            error={customerError}
          >
            <form onSubmit={handleCustomerLookup} className="search-form-row mb-16 relative">
              <div className="input-group-flex relative">
                <label htmlFor="customer-id-input" className="form-label-sr">Customer ID:</label>
                <input
                  id="customer-id-input"
                  type="text"
                  aria-label="Customer ID"
                  className="input-text-clean"
                  placeholder="Search customer name or ID... (e.g. Claire Gute or CG-12520)"
                  value={customerIdInput}
                  onChange={(e) => {
                    setCustomerIdInput(e.target.value);
                    setShowCustomerSuggestions(true);
                  }}
                  onFocus={() => setShowCustomerSuggestions(true)}
                />

                {/* Live Suggestions Dropdown */}
                {showCustomerSuggestions && customerSuggestions.length > 0 && (
                  <div className="autocomplete-dropdown">
                    <div className="autocomplete-header">Available Customers:</div>
                    {customerSuggestions.map((item) => (
                      <div
                        key={item.customer_id}
                        className="autocomplete-item"
                        onClick={() => handleSelectCustomerSuggestion(item)}
                      >
                        <span className="font-bold">{item.customer_name}</span>
                        <span className="autocomplete-sub font-mono">{item.customer_id} · {item.segment} · {item.primary_region}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-customer-btn"
                disabled={customerLoading || !customerIdInput.trim()}
              >
                {customerLoading ? 'Searching...' : 'Lookup Customer'}
              </button>
            </form>

            {customerMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Retrieved customer record in {customerMeta.duration} ms
                </span>
              </div>
            )}

            {customerResult ? (
              <div className="result-detail-box" id="customer-detail-view">
                <div className="detail-meta-grid">
                  <div className="meta-item">
                    <span className="meta-k">Customer ID</span>
                    <span className="meta-v font-mono">{customerResult.customer_id}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Customer Name</span>
                    <span className="meta-v font-bold">{customerResult.customer_name}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Account Segment</span>
                    <span className="meta-v">{customerResult.segment}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Primary Region</span>
                    <span className="meta-v">{customerResult.primary_region}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Lifetime Spend</span>
                    <span className="meta-v font-mono text-bold text-accent">
                      {formatCurrency(customerResult.total_spend)}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-k">Order Count</span>
                    <span className="meta-v font-mono">{formatNumber(customerResult.order_count)}</span>
                  </div>
                  {customerResult.first_order_date && (
                    <div className="meta-item">
                      <span className="meta-k">First Order</span>
                      <span className="meta-v font-mono">{customerResult.first_order_date}</span>
                    </div>
                  )}
                  {customerResult.last_order_date && (
                    <div className="meta-item">
                      <span className="meta-k">Last Order</span>
                      <span className="meta-v font-mono">{customerResult.last_order_date}</span>
                    </div>
                  )}
                </div>
                <div className="customer-insights-footer mt-16">
                  <div className="helper-hint text-xs">
                    💡 <strong>Cross-Database Tip:</strong> Customer document loaded from MongoDB. Copy Customer ID (<code>{customerResult.customer_id}</code>) to traverse their full purchase network in Neo4j below.
                  </div>
                </div>
              </div>
            ) : (
              !customerError && !customerLoading && (
                <div className="helper-hint">
                  Try sample customer: <code>CG-12520</code> (Claire Gute) or <code>DV-13045</code>
                </div>
              )
            )}
          </ChartCard>
        </div>
      </section>

      {/* Section 3: Cassandra Time-Series Analytics */}
      <section id="section-cassandra" className="mb-32" aria-label="Cassandra Time Analytics">
        <div className="section-header-row mb-16">
          <div className="section-pill">WIDE-COLUMN STORE</div>
          <h3 className="section-title-sm">Cassandra — Partition-Keyed Time-Series Slices</h3>
        </div>

        {/* Daily Sales Slice */}
        <div className="mb-24">
          <ChartCard
            id="date-sales-card"
            title="Daily Sales Point-in-Time Slice"
            subtitle="GET /api/v1/analytics/date (Partition key: ((order_date)))"
            loading={dateLoading}
            error={dateError}
            filterControls={
              <form onSubmit={handleDateLookup} className="filter-inline-compact">
                <label htmlFor="target-date-input" className="filter-label">
                  Order Date:
                </label>
                <input
                  id="target-date-input"
                  type="date"
                  aria-label="Order date for Cassandra query"
                  className="input-date-compact"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                />
                <button
                  type="submit"
                  className="btn btn-secondary-clean"
                  id="search-date-btn"
                  disabled={dateLoading || !targetDate}
                >
                  {dateLoading ? 'Fetching...' : 'Fetch Date'}
                </button>
              </form>
            }
          >
            {dateMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Returned {dateMeta.rows} {dateMeta.rows === 1 ? 'row' : 'rows'} in {dateMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowDateQuery(!showDateQuery)}
                  aria-label="Toggle CQL query"
                >
                  {showDateQuery ? 'Hide CQL' : 'View CQL'}
                </button>
              </div>
            )}
            {showDateQuery && (
              <pre className="query-code-snippet">
                <code>{`SELECT * FROM sales_by_date WHERE order_date = '${targetDate}';`}</code>
              </pre>
            )}

            {dateSales !== null ? (
              <DataTable
                id="date-sales-table"
                data={dateSales}
                keyField="row_id"
                maxHeight="300px"
                exportFilename={`superstore_date_sales_${targetDate}`}
                emptyMessage={`No transaction line items recorded for date ${targetDate}.`}
                columns={[
                  { key: 'order_id', label: 'Order ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                  { key: 'product_id', label: 'Product ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                  { key: 'category', label: 'Category' },
                  { key: 'sub_category', label: 'Sub-Category' },
                  { key: 'region', label: 'Region', width: '80px' },
                  { key: 'sales', label: 'Sales', align: 'right', width: '110px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                ]}
              />
            ) : (
              !dateError && !dateLoading && (
                <div className="helper-hint">
                  Select date to execute Cassandra partition key query.
                </div>
              )
            )}
          </ChartCard>
        </div>

        {/* Region & Category Clustering Key Ranges */}
        <div className="grid-2-col">
          {/* Region Date Range */}
          <ChartCard
            id="region-date-card"
            title="Regional Time-Series Slice"
            subtitle="GET /api/v1/analytics/region-date (Clustering range: order_date)"
            loading={regionDateLoading}
            error={regionDateError}
          >
            <form onSubmit={handleRegionDateLookup} className="range-filter-form mb-16">
              <div className="form-field-group">
                <label htmlFor="region-select" className="filter-label">Region:</label>
                <select
                  id="region-select"
                  aria-label="Region selection"
                  className="select-input-clean"
                  value={regionSelect}
                  onChange={(e) => setRegionSelect(e.target.value)}
                >
                  <option value="West">West</option>
                  <option value="East">East</option>
                  <option value="Central">Central</option>
                  <option value="South">South</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="region-start-date" className="filter-label">From:</label>
                <input
                  id="region-start-date"
                  type="date"
                  aria-label="Region start date"
                  className="input-date-clean"
                  value={regionStartDate}
                  onChange={(e) => setRegionStartDate(e.target.value)}
                />
              </div>

              <div className="form-field-group">
                <label htmlFor="region-end-date" className="filter-label">To:</label>
                <input
                  id="region-end-date"
                  type="date"
                  aria-label="Region end date"
                  className="input-date-clean"
                  value={regionEndDate}
                  onChange={(e) => setRegionEndDate(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-region-date-btn"
                disabled={regionDateLoading}
              >
                {regionDateLoading ? 'Querying...' : 'Query Region Range'}
              </button>
            </form>

            {regionDateMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Returned {regionDateMeta.rows} {regionDateMeta.rows === 1 ? 'row' : 'rows'} in {regionDateMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowRegionDateQuery(!showRegionDateQuery)}
                  aria-label="Toggle CQL query"
                >
                  {showRegionDateQuery ? 'Hide CQL' : 'View CQL'}
                </button>
              </div>
            )}
            {showRegionDateQuery && (
              <pre className="query-code-snippet">
                <code>{`SELECT * FROM sales_by_region_date WHERE region = '${regionSelect}' AND order_date >= '${regionStartDate}' AND order_date <= '${regionEndDate}';`}</code>
              </pre>
            )}

            {regionDateSales !== null ? (
              <DataTable
                id="region-date-table"
                data={regionDateSales}
                keyField="row_id"
                maxHeight="300px"
                exportFilename={`superstore_region_sales_${regionSelect}_${regionStartDate}_${regionEndDate}`}
                emptyMessage={`No transactions found for ${regionSelect} between ${regionStartDate} and ${regionEndDate}.`}
                columns={[
                  { key: 'order_date', label: 'Date', width: '100px' },
                  { key: 'order_id', label: 'Order ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                  { key: 'category', label: 'Category' },
                  { key: 'sales', label: 'Sales', align: 'right', width: '110px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                ]}
              />
            ) : (
              !regionDateError && !regionDateLoading && (
                <div className="helper-hint">
                  Select region and date window to execute Cassandra clustering query.
                </div>
              )
            )}
          </ChartCard>

          {/* Category Date Range */}
          <ChartCard
            id="category-date-card"
            title="Category Time-Series Slice"
            subtitle="GET /api/v1/analytics/category-date (Clustering range: order_date)"
            loading={categoryDateLoading}
            error={categoryDateError}
          >
            <form onSubmit={handleCategoryDateLookup} className="range-filter-form mb-16">
              <div className="form-field-group">
                <label htmlFor="category-select" className="filter-label">Category:</label>
                <select
                  id="category-select"
                  aria-label="Category selection"
                  className="select-input-clean"
                  value={categorySelect}
                  onChange={(e) => setCategorySelect(e.target.value)}
                >
                  <option value="Technology">Technology</option>
                  <option value="Furniture">Furniture</option>
                  <option value="Office Supplies">Office Supplies</option>
                </select>
              </div>

              <div className="form-field-group">
                <label htmlFor="category-start-date" className="filter-label">From:</label>
                <input
                  id="category-start-date"
                  type="date"
                  aria-label="Category start date"
                  className="input-date-clean"
                  value={categoryStartDate}
                  onChange={(e) => setCategoryStartDate(e.target.value)}
                />
              </div>

              <div className="form-field-group">
                <label htmlFor="category-end-date" className="filter-label">To:</label>
                <input
                  id="category-end-date"
                  type="date"
                  aria-label="Category end date"
                  className="input-date-clean"
                  value={categoryEndDate}
                  onChange={(e) => setCategoryEndDate(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-category-date-btn"
                disabled={categoryDateLoading}
              >
                {categoryDateLoading ? 'Querying...' : 'Query Category Range'}
              </button>
            </form>

            {categoryDateMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Returned {categoryDateMeta.rows} {categoryDateMeta.rows === 1 ? 'row' : 'rows'} in {categoryDateMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowCategoryDateQuery(!showCategoryDateQuery)}
                  aria-label="Toggle CQL query"
                >
                  {showCategoryDateQuery ? 'Hide CQL' : 'View CQL'}
                </button>
              </div>
            )}
            {showCategoryDateQuery && (
              <pre className="query-code-snippet">
                <code>{`SELECT * FROM sales_by_category_date WHERE category = '${categorySelect}' AND order_date >= '${categoryStartDate}' AND order_date <= '${categoryEndDate}';`}</code>
              </pre>
            )}

            {categoryDateSales !== null ? (
              <DataTable
                id="category-date-table"
                data={categoryDateSales}
                keyField="row_id"
                maxHeight="300px"
                exportFilename={`superstore_category_sales_${categorySelect}_${categoryStartDate}_${categoryEndDate}`}
                emptyMessage={`No transactions found for ${categorySelect} between ${categoryStartDate} and ${categoryEndDate}.`}
                columns={[
                  { key: 'order_date', label: 'Date', width: '100px' },
                  { key: 'order_id', label: 'Order ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                  { key: 'sub_category', label: 'Sub-Category' },
                  { key: 'sales', label: 'Sales', align: 'right', width: '110px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                ]}
              />
            ) : (
              !categoryDateError && !categoryDateLoading && (
                <div className="helper-hint">
                  Select category and date range to execute Cassandra range query.
                </div>
              )
            )}
          </ChartCard>
        </div>
      </section>

      {/* Section 4: Neo4j Graph Analytics */}
      <section id="section-neo4j" className="mb-32" aria-label="Neo4j Graph Analytics">
        <div className="section-header-row mb-16">
          <div className="section-pill">GRAPH DATABASE</div>
          <h3 className="section-title-sm">Neo4j — Graph Traversal &amp; Co-Purchasing Patterns</h3>
        </div>

        <div className="grid-2-col mb-24">
          {/* Customer Graph Traversal */}
          <ChartCard
            id="customer-graph-card"
            title="Customer Graph Traversal"
            subtitle="(:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(:Product)"
            loading={graphCustomerLoading}
            error={graphCustomerError}
          >
            <form onSubmit={handleGraphCustomerLookup} className="search-form-row mb-16">
              <div className="input-group-flex">
                <label htmlFor="graph-customer-id-input" className="form-label-sr">Customer ID:</label>
                <input
                  id="graph-customer-id-input"
                  type="text"
                  aria-label="Customer ID for graph traversal"
                  className="input-text-clean"
                  placeholder="e.g. CG-12520"
                  value={graphCustomerId}
                  onChange={(e) => setGraphCustomerId(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-graph-customer-btn"
                disabled={graphCustomerLoading || !graphCustomerId.trim()}
              >
                {graphCustomerLoading ? 'Traversing...' : 'Traverse Graph'}
              </button>
            </form>

            {customerGraphMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Traversed {customerGraphMeta.rows} graph nodes in {customerGraphMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowCustomerGraphQuery(!showCustomerGraphQuery)}
                  aria-label="Toggle Cypher query"
                >
                  {showCustomerGraphQuery ? 'Hide Cypher' : 'View Cypher'}
                </button>
              </div>
            )}
            {showCustomerGraphQuery && (
              <pre className="query-code-snippet">
                <code>{`MATCH (c:Customer {customer_id: '${graphCustomerId}'})-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)\nRETURN o, p;`}</code>
              </pre>
            )}

            {customerOrdersGraph !== null || customerProductsGraph !== null ? (
              <div className="graph-results-container">
                <div className="mb-16">
                  <div className="sub-table-header">Connected Orders ({customerOrdersGraph?.length || 0})</div>
                  <DataTable
                    id="customer-orders-table"
                    data={customerOrdersGraph || []}
                    keyField="order_id"
                    exportFilename={`superstore_graph_customer_${graphCustomerId}_orders`}
                    columns={[
                      { key: 'order_id', label: 'Order ID', width: '140px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                      { key: 'order_date', label: 'Order Date', width: '110px' },
                      { key: 'ship_mode', label: 'Ship Mode' },
                    ]}
                  />
                </div>

                <div>
                  <div className="sub-table-header">Product Affinities ({customerProductsGraph?.length || 0})</div>
                  <DataTable
                    id="customer-products-table"
                    data={customerProductsGraph || []}
                    keyField="product_id"
                    exportFilename={`superstore_graph_customer_${graphCustomerId}_products`}
                    columns={[
                      { key: 'product_id', label: 'Product ID', width: '130px', render: (v) => <span className="font-mono text-xs">{v}</span> },
                      { key: 'product_name', label: 'Product Name' },
                      { key: 'purchase_count', label: 'Qty', align: 'center', width: '70px' },
                      { key: 'total_spent', label: 'Total Spend', align: 'right', width: '110px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                    ]}
                  />
                </div>
              </div>
            ) : (
              !graphCustomerError && !graphCustomerLoading && (
                <div className="helper-hint">
                  Traverse multi-hop relationships from customer to connected orders and products.
                </div>
              )
            )}
          </ChartCard>

          {/* Co-Purchased Products */}
          <ChartCard
            id="copurchase-card"
            title="Co-Purchased Products"
            subtitle="(p1)<-[:CONTAINS]-(:Order)-[:CONTAINS]->(p2)"
            loading={copurchaseLoading}
            error={copurchaseError}
          >
            <form onSubmit={handleCopurchaseLookup} className="search-form-row mb-16">
              <div className="input-group-flex">
                <label htmlFor="copurchase-product-id-input" className="form-label-sr">Product ID:</label>
                <input
                  id="copurchase-product-id-input"
                  type="text"
                  aria-label="Product ID for co-purchase lookup"
                  className="input-text-clean"
                  placeholder="e.g. FUR-BO-10001798"
                  value={copurchaseProductId}
                  onChange={(e) => setCopurchaseProductId(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="btn btn-action-primary"
                id="search-copurchase-btn"
                disabled={copurchaseLoading || !copurchaseProductId.trim()}
              >
                {copurchaseLoading ? 'Searching...' : 'Find Co-Purchases'}
              </button>
            </form>

            {copurchaseMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Found {copurchaseMeta.rows} co-purchased items in {copurchaseMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowCopurchaseQuery(!showCopurchaseQuery)}
                  aria-label="Toggle Cypher query"
                >
                  {showCopurchaseQuery ? 'Hide Cypher' : 'View Cypher'}
                </button>
              </div>
            )}
            {showCopurchaseQuery && (
              <pre className="query-code-snippet">
                <code>{`MATCH (p1:Product {product_id: '${copurchaseProductId}'})<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(p2:Product)\nWHERE p1 <> p2\nRETURN p2.product_name, count(o) AS times_co_purchased\nORDER BY times_co_purchased DESC LIMIT 10;`}</code>
              </pre>
            )}

            {copurchaseResults !== null ? (
              <DataTable
                id="copurchase-table"
                data={copurchaseResults}
                keyField="product_id"
                exportFilename={`superstore_copurchases_${copurchaseProductId}`}
                emptyMessage="No frequent co-purchases discovered for this product catalog entry."
                columns={[
                  { key: 'product_id', label: 'Product ID', width: '130px', render: (v) => <span className="font-mono text-xs font-semibold">{v}</span> },
                  { key: 'product_name', label: 'Co-Purchased Product', render: (v) => <span className="table-name-title" title={v}>{v}</span> },
                  { key: 'times_co_purchased', label: 'Count', align: 'right', width: '75px', className: 'col-count', render: (v) => <span className="font-mono font-bold text-accent whitespace-nowrap">{v}</span> },
                ]}
              />
            ) : (
              !copurchaseError && !copurchaseLoading && (
                <div className="helper-hint">
                  Discovers items frequently bought together within the same order session.
                </div>
              )
            )}
          </ChartCard>
        </div>

        {/* Regional Taxonomy Hierarchy */}
        <div>
          <ChartCard
            id="graph-region-categories-card"
            title="Regional Taxonomy Hierarchy (6-Hop Traversal)"
            subtitle="(:Location)<-[:SHIPPED_TO]-(:Order)-[:CONTAINS]->(:Product)-[:BELONGS_TO]->(:Category)"
            loading={graphRegionLoading}
            error={graphRegionError}
            filterControls={
              <form onSubmit={handleGraphRegionLookup} className="filter-inline-compact">
                <label htmlFor="graph-region-select" className="filter-label">
                  Region:
                </label>
                <select
                  id="graph-region-select"
                  aria-label="Region for taxonomy traversal"
                  className="select-input-compact"
                  value={graphRegionSelect}
                  onChange={(e) => setGraphRegionSelect(e.target.value)}
                >
                  <option value="West">West</option>
                  <option value="East">East</option>
                  <option value="Central">Central</option>
                  <option value="South">South</option>
                </select>
                <button
                  type="submit"
                  className="btn btn-secondary-clean"
                  id="query-region-graph-btn"
                  disabled={graphRegionLoading}
                >
                  {graphRegionLoading ? 'Traversing...' : 'Traverse Region Hierarchy'}
                </button>
              </form>
            }
          >
            {regionGraphMeta && (
              <div className="query-meta-bar">
                <span className="query-meta-pill">
                  Aggregated {regionGraphMeta.rows} categories in {regionGraphMeta.duration} ms
                </span>
                <button
                  type="button"
                  className="btn-query-toggle"
                  onClick={() => setShowRegionGraphQuery(!showRegionGraphQuery)}
                  aria-label="Toggle Cypher query"
                >
                  {showRegionGraphQuery ? 'Hide Cypher' : 'View Cypher'}
                </button>
              </div>
            )}
            {showRegionGraphQuery && (
              <pre className="query-code-snippet">
                <code>{`MATCH (r:Location {region: '${graphRegionSelect}'})<-[:SHIPPED_TO]-(o:Order)-[:CONTAINS]->(p:Product)-[:BELONGS_TO]->(c:Category)\nRETURN c.name, count(p) AS item_count, sum(o.sales) AS total_sales;`}</code>
              </pre>
            )}

            {regionCategoriesGraph !== null ? (
              <DataTable
                id="graph-region-categories-table"
                data={regionCategoriesGraph}
                keyField="category"
                exportFilename={`superstore_region_graph_${graphRegionSelect}`}
                emptyMessage={`No category line items found for region ${graphRegionSelect}.`}
                columns={[
                  { key: 'category', label: 'Category' },
                  { key: 'item_count', label: 'Line Items', align: 'center', width: '120px' },
                  { key: 'total_sales', label: 'Total Sales', align: 'right', width: '130px', className: 'col-sales', render: (v) => <span className="font-mono text-bold whitespace-nowrap">{formatCurrency(v)}</span> },
                ]}
              />
            ) : (
              !graphRegionError && !graphRegionLoading && (
                <div className="helper-hint">
                  Select region and run 6-hop Cypher traversal.
                </div>
              )
            )}
          </ChartCard>
        </div>
      </section>
    </div>
  );
}
