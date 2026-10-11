/**
 * HTTP Client Wrapper.
 *
 * Centralizes base URL resolution, query parameter serialization,
 * request timeouts, and clean error handling across all API requests.
 */

import { config } from '../../config/environment.js';

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Executes a GET request with query params and timeout.
 *
 * @param {string} endpoint - API path, e.g. '/api/v1/dashboard/overview'
 * @param {Record<string, any>} [params] - Optional query parameters
 * @param {number} [timeoutMs] - Request timeout in milliseconds
 * @returns {Promise<any>}
 */
export async function get(endpoint, params = {}, timeoutMs = config.requestTimeoutMs) {
  const baseUrl = config.apiBaseUrl || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');
  const url = new URL(`${baseUrl}${endpoint}`);

  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      url.searchParams.append(key, String(val));
    }
  });

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      let errorMessage = `API request failed with status ${response.status}`;
      let errorData = null;
      try {
        errorData = await response.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        } else if (errorData?.error?.message) {
          errorMessage = errorData.error.message;
        }
      } catch {
        // Fallback to default message if JSON parsing fails
      }
      throw new ApiError(errorMessage, response.status, errorData);
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new ApiError(`Request to ${endpoint} timed out after ${timeoutMs}ms`, 408);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export const client = { get, ApiError };
export default client;
