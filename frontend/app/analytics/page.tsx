import React from 'react';
import BusinessDashboard from '@/components/analytics/BusinessDashboard';

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Analytics Dashboard</h1>
          <p className="text-gray-300">AI-powered insights and performance metrics</p>
        </div>
        
        <BusinessDashboard />
      </div>
    </div>
  );
}