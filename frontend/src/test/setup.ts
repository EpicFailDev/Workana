import '@testing-library/jest-dom';
import { vi, afterEach } from 'vitest';

// Mock ResizeObserver for Radix UI components under JSDOM
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock;

// Clear all mocks between tests
afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});
