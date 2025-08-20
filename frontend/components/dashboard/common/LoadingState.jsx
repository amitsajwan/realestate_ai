// LoadingState.jsx - Reusable loading component for dashboard elements
import React from 'react';

/**
 * LoadingState - A reusable component for displaying loading states
 * 
 * @param {Object} props
 * @param {string} props.message - Custom loading message
 * @param {string} props.size - Size of the spinner ('sm', 'md', 'lg')
 * @param {boolean} props.fullScreen - Whether to display as fullscreen overlay
 * @param {boolean} props.overlay - Whether to display as an overlay on parent
 * @param {string} props.className - Additional CSS classes
 */
const LoadingState = ({
  message = 'Loading...',
  size = 'md',
  fullScreen = false,
  overlay = false,
  className = ''
}) => {
  // Determine spinner size based on prop
  const spinnerSizes = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };
  
  const spinnerSize = spinnerSizes[size] || spinnerSizes.md;
  
  // Base component
  const LoadingContent = () => (
    <div className="text-center">
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 mx-auto ${spinnerSize}`}></div>
      {message && <p className="mt-4 text-gray-600">{message}</p>}
    </div>
  );
  
  // Full screen loading state
  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-gray-50 bg-opacity-90 flex items-center justify-center z-50">
        <LoadingContent />
      </div>
    );
  }
  
  // Overlay loading state (for individual components)
  if (overlay) {
    return (
      <div className="absolute inset-0 bg-white bg-opacity-80 flex items-center justify-center z-10 rounded-lg">
        <LoadingContent />
      </div>
    );
  }
  
  // Standard loading state
  return (
    <div className={`flex items-center justify-center py-8 ${className}`}>
      <LoadingContent />
    </div>
  );
};

export default LoadingState;