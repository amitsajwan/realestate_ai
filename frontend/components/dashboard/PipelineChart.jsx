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
import ChartContainer from './common/ChartContainer';
import { chartColors, tooltipConfig, gridConfig } from './utils/chartUtils';
import { formatPercentage } from './utils/formatUtils';

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

  // Use pipeline stage colors from chartUtils

  const stages = Object.keys(pipelineData);
  const values = Object.values(pipelineData);

  const chartData = {
    labels: stages.map(stage => stage.charAt(0).toUpperCase() + stage.slice(1)),
    datasets: [
      {
        data: values,
        backgroundColor: stages.map(stage => chartColors.pipelineStages[stage]),
        borderColor: stages.map(stage => chartColors.pipelineStages[stage]),
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
        ...tooltipConfig,
        callbacks: {
          label: function(context) {
            const total = values.reduce((a, b) => a + b, 0);
            const percentage = formatPercentage(context.raw, total);
            return `${context.raw} leads (${percentage})`;
          }
        }
      }
    },
    scales: {
      x: {
        ...gridConfig.x,
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      },
      y: {
        ...gridConfig.y,
        grid: {
          display: false
        }
      }
    }
  };

  // Calculate conversion rates
  const totalLeads = values.reduce((a, b) => a + b, 0);
  const conversionRate = totalLeads > 0 ? ((pipelineData.closed / totalLeads) * 100).toFixed(1) : 0;
  const activeDeals = pipelineData.proposal + pipelineData.negotiation;

  // Pipeline insights component for footer
  const PipelineInsights = () => (
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
  );

  // Quick action buttons component for footer
  const QuickActions = () => (
    <div className="mt-4 flex gap-2">
      <button className="flex-1 px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors">
        View Pipeline Details
      </button>
      <button className="flex-1 px-3 py-2 text-xs font-medium text-green-600 bg-green-50 rounded-md hover:bg-green-100 transition-colors">
        Follow Up Leads
      </button>
    </div>
  );

  return (
    <ChartContainer
      title="Lead Pipeline"
      subtitle={`${totalLeads} total leads`}
      footerContent={
        <>
          <PipelineInsights />
          <QuickActions />
        </>
      }
    >
      <div className="h-48">
        <Bar data={chartData} options={options} />
      </div>
    </ChartContainer>
  );
};

export default PipelineChart;
