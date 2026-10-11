/**
 * Operational & Graph Analytics API Service.
 *
 * Provides typed functions for Redis leaderboards, MongoDB operational lookups,
 * Cassandra partitioned time-series queries, and Neo4j graph traversals.
 */

import { get } from './client.js';

export const analyticsApi = {
  // Leaderboard Analytics (Redis with MongoDB Filter Support)
  getTopProducts: (limit = 10, year = null, region = null) =>
    get('/api/v1/analytics/products/top', { limit, year, region }),

  getTopCustomers: (limit = 10, year = null, region = null) =>
    get('/api/v1/analytics/customers/top', { limit, year, region }),

  // Search & Operational Lookups (MongoDB)
  searchCustomers: (query, limit = 10) =>
    get('/api/v1/analytics/customers/search', { q: query, limit }),

  searchOrders: (query, limit = 10) =>
    get('/api/v1/analytics/orders/search', { q: query, limit }),

  getOrderById: (orderId) =>
    get(`/api/v1/analytics/orders/${encodeURIComponent(String(orderId).trim())}`),

  getCustomerById: (customerId) =>
    get(`/api/v1/analytics/customers/${encodeURIComponent(String(customerId).trim())}`),

  // Cassandra Partitioned Time-Series
  getSalesByDate: (dateStr) =>
    get('/api/v1/analytics/date', { date: String(dateStr).trim() }),

  getSalesByRegionDate: (region, startDate, endDate) =>
    get('/api/v1/analytics/region-date', {
      region: String(region).trim(),
      start_date: String(startDate).trim(),
      end_date: String(endDate).trim(),
    }),

  getSalesByCategoryDate: (category, startDate, endDate) =>
    get('/api/v1/analytics/category-date', {
      category: String(category).trim(),
      start_date: String(startDate).trim(),
      end_date: String(endDate).trim(),
    }),

  // Neo4j Graph Traversals
  getCustomerOrdersGraph: (customerId) =>
    get(`/api/v1/analytics/graph/customer/${encodeURIComponent(String(customerId).trim())}/orders`),

  getCustomerProductsGraph: (customerId) =>
    get(`/api/v1/analytics/graph/customer/${encodeURIComponent(String(customerId).trim())}/products`),

  getProductCoPurchases: (productId, limit = 10) =>
    get(`/api/v1/analytics/graph/product/${encodeURIComponent(String(productId).trim())}/copurchases`, { limit }),

  getRegionCategoriesGraph: (region) =>
    get(`/api/v1/analytics/graph/region/${encodeURIComponent(String(region).trim())}/categories`),
};

export default analyticsApi;
