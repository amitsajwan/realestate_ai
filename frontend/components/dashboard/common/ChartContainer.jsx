// ChartContainer.jsx - Reusable container for all chart components
import React from 'react';
import LoadingState from './LoadingState';

/**
 * ChartContainer - A reusable wrapper component for charts
 * 
 * @param {Object} props
 * @param {string} props.title - Chart title
 * @param {string} props.subtitle - Optional subtitle or description
 * @param {React.ReactNode} props.children - Chart component
 * @param {string} props.className - Optional additional CSS classes
 * @param {React.ReactNode} props.headerRight - Optional content for header right side
 * @param {React.ReactNode} props.footerContent - Optional content for footer
 * @param {boolean} props.loading - Whether the chart is in loading state
 * @param {string} props.loadingMessage - Custom loading message
 */
const ChartContainer = ({ 
  title, 
  subtitle, 
  children, 
  className = '',
  headerRight = null,
  footerContent = null,
  loading = false,
  loadingMessage = 'Loading chart data...'
}) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 ${className} relative`}>
      {/* Loading overlay */}
      {loading && <LoadingState overlay={true} message={loadingMessage} size="sm" />}
      
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && <span className="text-sm text-gray-500">{subtitle}</span>}
        </div>
        {headerRight}
      </div>
      
      {children}
      
      {footerContent && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {footerContent}
        </div>
      )}
    </div>
  );
};

export default ChartContainer;