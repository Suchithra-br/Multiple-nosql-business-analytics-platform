/**
 * Dashboard Analytics API Service.
 *
 * Provides typed functions for executive KPI overview, monthly trends,
 * regional distribution, product categories, customer segments,
 * shipping logistics, sub-categories, and state rankings.
 */

import { get } from './client.js';

export const dashboardApi = {
  /**
   * Diagnostic health check of all 4 NoSQL databases.
   */
  getHealth: () => get('/api/v1/health'),

  /**
   * Executive KPI overview with optional year/region filtering.
   */
  getOverview: (year = null, region = null) =>
    get('/api/v1/dashboard/overview', { year, region }),

  /**
   * Chronological monthly sales trend across 2015–2018.
   */
  getMonthlySales: (year = null, region = null) =>
    get('/api/v1/dashboard/monthly', { year, region }),

  /**
   * Regional sales volume breakdown.
   */
  getRegions: (year = null) =>
    get('/api/v1/dashboard/regions', { year }),

  /**
   * Product category sales volume breakdown.
   */
  getCategories: (year = null, region = null) =>
    get('/api/v1/dashboard/categories', { year, region }),

  /**
   * Customer segment sales volume breakdown.
   */
  getSegments: (year = null, region = null) =>
    get('/api/v1/dashboard/segments', { year, region }),

  /**
   * Shipping mode sales volume and order counts.
   */
  getShipping: (year = null, region = null) =>
    get('/api/v1/dashboard/shipping', { year, region }),

  /**
   * Revenue breakdown across 17 product sub-categories.
   */
  getSubcategories: (year = null, region = null) =>
    get('/api/v1/dashboard/subcategories', { year, region }),

  /**
   * State sales rankings with order counts.
   */
  getStates: (year = null, region = null, limit = 10) =>
    get('/api/v1/dashboard/states', { year, region, limit }),
};

export default dashboardApi;
