// WeeklyTrendChart.jsx - Simple line chart for weekly lead trends
import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import ChartContainer from './common/ChartContainer';
import { chartColors, tooltipConfig, gridConfig } from './utils/chartUtils';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const WeeklyTrendChart = ({ data }) => {
  // Default sample data for last 7 days
  const defaultData = [
    { day: 'Mon', date: '2025-08-09', count: 4 },
    { day: 'Tue', date: '2025-08-10', count: 7 },
    { day: 'Wed', date: '2025-08-11', count: 8 },
    { day: 'Thu', date: '2025-08-12', count: 6 },
    { day: 'Fri', date: '2025-08-13', count: 9 },
    { day: 'Sat', date: '2025-08-14', count: 5 },
    { day: 'Sun', date: '2025-08-15', count: 3 }
  ];

  const weekData = data || defaultData;

  const chartData = {
    labels: weekData.map(d => d.day),
    datasets: [
      {
        label: 'New Leads',
        data: weekData.map(d => d.count),
        borderColor: chartColors.blue,
        backgroundColor: `${chartColors.blue}1A`, // 10% opacity
        pointBackgroundColor: chartColors.blue,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        fill: true,
        tension: 0.4
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        ...tooltipConfig,
        mode: 'index',
        intersect: false,
        borderColor: chartColors.blue,
        callbacks: {
          title: function(context) {
            const dataPoint = weekData[context[0].dataIndex];
            return `${dataPoint.day}, ${dataPoint.date}`;
          },
          label: function(context) {
            return `${context.raw} new leads`;
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    scales: {
      x: {
        ...gridConfig.x,
        grid: {
          display: false
        }
      },
      y: {
        ...gridConfig.y,
        ticks: {
          stepSize: 1,
          callback: function(value) {
            return value === 0 ? '0' : value;
          }
        }
      }
    }
  };

  // Calculate week stats
  const totalWeekLeads = weekData.reduce((sum, day) => sum + day.count, 0);
  const avgDailyLeads = (totalWeekLeads / weekData.length).toFixed(1);
  const bestDay = weekData.reduce((max, day) => day.count > max.count ? day : max);
  
  // Create footer content for the chart container
  const footerContent = (
    <div className="grid grid-cols-3 gap-4">
      <div className="text-center">
        <div className="text-lg font-semibold text-blue-600">{totalWeekLeads}</div>
        <div className="text-xs text-gray-500">This Week</div>
      </div>
      <div className="text-center">
        <div className="text-lg font-semibold text-green-600">{avgDailyLeads}</div>
        <div className="text-xs text-gray-500">Daily Avg</div>
      </div>
      <div className="text-center">
        <div className="text-lg font-semibold text-purple-600">{bestDay.day}</div>
        <div className="text-xs text-gray-500">Best Day</div>
      </div>
    </div>
  );

  return (
    <ChartContainer 
      title="Weekly Lead Trend" 
      subtitle="Last 7 days"
      footerContent={footerContent}
    >
      <div className="h-48 mb-4">
        <Line data={chartData} options={options} />
      </div>
    </ChartContainer>
  );
};

export default WeeklyTrendChart;
