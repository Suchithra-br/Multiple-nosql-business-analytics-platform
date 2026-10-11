/**
 * Centralized Frontend Environment Configuration.
 *
 * Reads Vite environment variables with graceful local development defaults.
 */

export const config = {
  // Base URL for the FastAPI Backend Gateway:
  // Uses explicit env var if provided.
  // In remote/public tunnel access (e.g. *.trycloudflare.com), automatically uses
  // window.location.origin so requests route through the public proxy.
  // In local development/testing, falls back to http://127.0.0.1:8000.
  apiBaseUrl:
    import.meta.env.VITE_API_BASE_URL ||
    (typeof window !== 'undefined' &&
    window.location.hostname &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
      ? window.location.origin
      : 'http://127.0.0.1:8000'),

  // Request timeout in milliseconds
  requestTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 15000,

  // App Metadata
  appTitle: 'Superstore Sales Analytics',
  appVersion: '1.0.0',
};

export default config;
