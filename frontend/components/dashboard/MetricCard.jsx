// MetricCard.jsx - Simple metric display component
import React from 'react';

const MetricCard = ({ 
  title, 
  value, 
  trend, 
  trendDirection = 'up',
  icon, 
  color = 'blue',
  subtitle 
}) => {
  const colorClasses = {
    blue: 'border-blue-500 bg-blue-50',
    green: 'border-green-500 bg-green-50', 
    orange: 'border-orange-500 bg-orange-50',
    red: 'border-red-500 bg-red-50',
    purple: 'border-purple-500 bg-purple-50'
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600'
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 p-6 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 uppercase tracking-wide">
            {title}
          </p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {value}
          </p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">
              {subtitle}
            </p>
          )}
          {trend && (
            <div className={`flex items-center mt-2 ${trendColors[trendDirection]}`}>
              <span className="text-sm font-medium">
                {trendDirection === 'up' ? '↗' : trendDirection === 'down' ? '↘' : '→'} {trend}
              </span>
            </div>
          )}
        </div>
        {icon && (
          <div className="ml-4 text-2xl text-gray-400">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
