// Dashboard.jsx - Entry point component with mobile-first responsive design
import React from 'react';
import QuickDashboard from './dashboard/QuickDashboard';

const Dashboard = ({ agentId }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <QuickDashboard agentId={agentId} />
    </div>
  );
};

export default Dashboard;
