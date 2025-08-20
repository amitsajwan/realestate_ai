// formatUtils.js - Utility functions for data formatting

/**
 * Format a number with thousands separators
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
export const formatNumber = (value, decimals = 0) => {
  if (value === undefined || value === null) return '-';
  
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals
  }).format(value);
};

/**
 * Format a number as currency (INR)
 * @param {number} value - The number to format
 * @returns {string} Formatted currency
 */
export const formatCurrency = (value) => {
  if (value === undefined || value === null) return '-';
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value);
};

/**
 * Format a number as percentage
 * @param {number} value - The value to format (0-100 or 0-1)
 * @param {boolean} convertFromDecimal - Whether to convert from decimal (0-1) to percentage
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage
 */
export const formatPercentage = (value, convertFromDecimal = false, decimals = 1) => {
  if (value === undefined || value === null) return '-';
  
  const percentValue = convertFromDecimal ? value * 100 : value;
  
  return `${percentValue.toFixed(decimals)}%`;
};

/**
 * Format a date to a readable string
 * @param {Date|string} date - The date to format
 * @param {string} format - Format style ('short', 'medium', 'long')
 * @returns {string} Formatted date
 */
export const formatDate = (date, format = 'medium') => {
  if (!date) return '-';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const options = {
    short: { day: 'numeric', month: 'short' },
    medium: { day: 'numeric', month: 'short', year: 'numeric' },
    long: { day: 'numeric', month: 'long', year: 'numeric' },
    time: { hour: '2-digit', minute: '2-digit' },
    full: { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }
  };
  
  return dateObj.toLocaleDateString('en-IN', options[format] || options.medium);
};

/**
 * Format a trend value with appropriate symbol
 * @param {string|number} value - The trend value (e.g., '+12%', '-5%')
 * @param {string} direction - Trend direction ('up', 'down', 'neutral')
 * @returns {string} Formatted trend with symbol
 */
export const formatTrend = (value, direction = 'neutral') => {
  if (!value) return '';
  
  const symbols = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };
  
  // If value already has a sign, don't add one
  const hasSign = typeof value === 'string' && (value.startsWith('+') || value.startsWith('-'));
  const sign = !hasSign && direction === 'up' ? '+' : '';
  
  return `${symbols[direction]} ${sign}${value}`;
};