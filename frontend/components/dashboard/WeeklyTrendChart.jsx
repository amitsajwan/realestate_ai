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
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        pointBackgroundColor: '#3B82F6',
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
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#3B82F6',
        borderWidth: 1,
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
        grid: {
          display: false
        },
        border: {
          display: false
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        border: {
          display: false
        },
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
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Weekly Lead Trend</h3>
        <span className="text-sm text-gray-500">Last 7 days</span>
      </div>
      
      <div className="h-48 mb-4">
        <Line data={chartData} options={options} />
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
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
    </div>
  );
};

export default WeeklyTrendChart;
