/**
 * Data formatting utilities for Multi-NoSQL Business Analytics Platform.
 * Ensures consistent currency, integer, and date representations.
 */

export function formatCurrency(amount) {
  if (amount === undefined || amount === null || isNaN(Number(amount))) {
    return '$0.00';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(amount));
}

export function formatNumber(num) {
  if (num === undefined || num === null || isNaN(Number(num))) {
    return '0';
  }
  return new Intl.NumberFormat('en-US').format(Number(num));
}

export function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return dateStr;
}
