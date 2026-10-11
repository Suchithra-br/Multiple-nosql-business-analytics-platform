/**
 * Unified API Client Services.
 */

export { client, get, ApiError } from './client.js';
export { dashboardApi } from './dashboardApi.js';
export { analyticsApi } from './analyticsApi.js';

import { dashboardApi } from './dashboardApi.js';
import { analyticsApi } from './analyticsApi.js';

export const api = {
  ...dashboardApi,
  ...analyticsApi,
};

export default api;
