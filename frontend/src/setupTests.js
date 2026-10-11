import '@testing-library/jest-dom/vitest';

// Polyfill ResizeObserver for JSDOM / Recharts testing
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
