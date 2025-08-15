// LeadSourceChart.jsx - Donut chart for lead sources
import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const LeadSourceChart = ({ data }) => {
  // Default sample data if none provided
  const defaultData = {
    facebook: 18,
    whatsapp: 12,
    website: 10,
    referral: 3,
    phone: 2
  };

  const sourceData = data || defaultData;
  
  // Source-specific colors matching Indian social media preferences
  const sourceColors = {
    facebook: '#1877F2',
    whatsapp: '#25D366', 
    website: '#2563EB',
    referral: '#8B5CF6',
    phone: '#F59E0B'
  };

  const chartData = {
    labels: Object.keys(sourceData).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
    datasets: [
      {
        data: Object.values(sourceData),
        backgroundColor: Object.keys(sourceData).map(key => sourceColors[key]),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverBackgroundColor: Object.keys(sourceData).map(key => sourceColors[key] + 'CC'),
        hoverBorderWidth: 3
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          padding: 20,
          usePointStyle: true,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.raw / total) * 100).toFixed(1);
            return `${context.label}: ${context.raw} leads (${percentage}%)`;
          }
        }
      }
    },
    cutout: '60%'
  };

  const totalLeads = Object.values(sourceData).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Lead Sources</h3>
        <span className="text-sm text-gray-500">{totalLeads} total leads</span>
      </div>
      
      <div className="relative h-64">
        <Doughnut data={chartData} options={options} />
        
        {/* Center text showing total */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{totalLeads}</div>
            <div className="text-sm text-gray-500">Total Leads</div>
          </div>
        </div>
      </div>

      {/* Quick stats below chart */}
      <div className="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">
            {sourceData.whatsapp || 0}
          </div>
          <div className="text-xs text-gray-500">WhatsApp Leads</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-blue-600">
            {sourceData.facebook || 0}
          </div>
          <div className="text-xs text-gray-500">Facebook Leads</div>
        </div>
      </div>
    </div>
  );
};

export default LeadSourceChart;
