// chartUtils.js - Common chart configuration and utility functions

/**
 * Common chart colors for consistent styling across components
 */
export const chartColors = {
  // Primary colors
  blue: '#3B82F6',
  green: '#34D399',
  red: '#EF4444',
  yellow: '#F59E0B',
  purple: '#8B5CF6',
  
  // Social media colors
  facebook: '#1877F2',
  whatsapp: '#25D366',
  
  // Pipeline stage colors
  pipelineStages: {
    new: '#E5E7EB',        // Light gray
    qualified: '#FEF3C7',  // Light yellow
    meeting: '#DBEAFE',    // Light blue
    proposal: '#D1FAE5',   // Light green
    negotiation: '#FDE68A', // Yellow
    closed: '#34D399'      // Green
  }
};

/**
 * Common tooltip configuration
 */
export const tooltipConfig = {
  backgroundColor: 'rgba(0, 0, 0, 0.8)',
  titleColor: '#ffffff',
  bodyColor: '#ffffff',
  borderWidth: 1,
  padding: 10,
  displayColors: true
};

/**
 * Format number as percentage
 * @param {number} value - The value to format
 * @param {number} total - The total value for percentage calculation
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, total, decimals = 1) => {
  if (!total) return '0%';
  return `${((value / total) * 100).toFixed(decimals)}%`;
};

/**
 * Common chart grid configuration
 */
export const gridConfig = {
  x: {
    grid: {
      color: 'rgba(0, 0, 0, 0.1)',
      display: true
    },
    border: {
      display: false
    }
  },
  y: {
    grid: {
      color: 'rgba(0, 0, 0, 0.1)',
      display: true
    },
    border: {
      display: false
    },
    beginAtZero: true
  }
};

/**
 * Get common chart options
 * @param {Object} customOptions - Custom options to merge
 * @returns {Object} Merged chart options
 */
export const getCommonChartOptions = (customOptions = {}) => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        ...tooltipConfig
      }
    },
    scales: gridConfig,
    ...customOptions
  };
};