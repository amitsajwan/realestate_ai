// PipelineChart.jsx - Horizontal bar chart for lead pipeline
import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const PipelineChart = ({ data }) => {
  // Default pipeline data
  const defaultData = {
    new: 15,
    qualified: 12,
    meeting: 8,
    proposal: 5,
    negotiation: 3,
    closed: 2
  };

  const pipelineData = data || defaultData;

  // Pipeline stage colors (funnel visualization)
  const stageColors = {
    new: '#E5E7EB',        // Light gray
    qualified: '#FEF3C7',  // Light yellow
    meeting: '#DBEAFE',    // Light blue
    proposal: '#D1FAE5',   // Light green
    negotiation: '#FDE68A', // Yellow
    closed: '#34D399'      // Green
  };

  const stages = Object.keys(pipelineData);
  const values = Object.values(pipelineData);

  const chartData = {
    labels: stages.map(stage => stage.charAt(0).toUpperCase() + stage.slice(1)),
    datasets: [
      {
        data: values,
        backgroundColor: stages.map(stage => stageColors[stage]),
        borderColor: stages.map(stage => stageColors[stage].replace('EB', 'D1')),
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false
      }
    ]
  };

  const options = {
    indexAxis: 'y', // Horizontal bars
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        callbacks: {
          label: function(context) {
            const total = values.reduce((a, b) => a + b, 0);
            const percentage = ((context.raw / total) * 100).toFixed(1);
            return `${context.raw} leads (${percentage}%)`;
          }
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        border: {
          display: false
        },
        ticks: {
          stepSize: 1
        }
      },
      y: {
        grid: {
          display: false
        },
        border: {
          display: false
        }
      }
    }
  };

  // Calculate conversion rates
  const totalLeads = values.reduce((a, b) => a + b, 0);
  const conversionRate = totalLeads > 0 ? ((pipelineData.closed / totalLeads) * 100).toFixed(1) : 0;
  const activeDeals = pipelineData.proposal + pipelineData.negotiation;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Lead Pipeline</h3>
        <span className="text-sm text-gray-500">{totalLeads} total leads</span>
      </div>
      
      <div className="h-48 mb-4">
        <Bar data={chartData} options={options} />
      </div>

      {/* Pipeline insights */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">{conversionRate}%</div>
          <div className="text-xs text-gray-500">Conversion Rate</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-blue-600">{activeDeals}</div>
          <div className="text-xs text-gray-500">Active Deals</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-purple-600">{pipelineData.new}</div>
          <div className="text-xs text-gray-500">New Leads</div>
        </div>
      </div>

      {/* Quick action buttons */}
      <div className="mt-4 flex gap-2">
        <button className="flex-1 px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors">
          View Pipeline Details
        </button>
        <button className="flex-1 px-3 py-2 text-xs font-medium text-green-600 bg-green-50 rounded-md hover:bg-green-100 transition-colors">
          Follow Up Leads
        </button>
      </div>
    </div>
  );
};

export default PipelineChart;
