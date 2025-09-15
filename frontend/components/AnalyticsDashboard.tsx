"use client";

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  EyeIcon, 
  HeartIcon, 
  ShareIcon, 
  ChatBubbleLeftIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

interface AnalyticsData {
  overview: {
    total_posts: number;
    total_views: number;
    total_likes: number;
    total_shares: number;
    total_comments: number;
    engagement_rate: number;
  };
  growth_rates: {
    views_growth: number;
    likes_growth: number;
    engagement_growth: number;
  };
  platform_breakdown: {
    [platform: string]: {
      views: number;
      likes: number;
      shares: number;
      comments: number;
      clicks: number;
      posts: number;
    };
  };
  recent_activity: {
    [date: string]: {
      views: number;
      likes: number;
      shares: number;
      comments: number;
      clicks: number;
    };
  };
  top_posts: Array<{
    post_id: string;
    total_views: number;
    total_likes: number;
    total_shares: number;
    total_comments: number;
    engagement_score: number;
    platforms: string[];
  }>;
}

interface AnalyticsDashboardProps {
  userId: string;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ userId }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    loadAnalyticsData();
  }, [userId, dateRange]);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/analytics/dashboard`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load analytics data');
      }

      const data = await response.json();
      setAnalyticsData(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) {
      return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
    } else if (growth < 0) {
      return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
    }
    return null;
  };

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return 'text-green-600';
    if (growth < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No analytics data</h3>
        <p className="mt-1 text-sm text-gray-500">Start creating posts to see analytics.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="mt-2 text-gray-600">Track your post performance and engagement</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <CalendarIcon className="h-5 w-5 text-gray-400 mr-2" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <EyeIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Views</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {formatNumber(analyticsData.overview.total_views)}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${getGrowthColor(analyticsData.growth_rates.views_growth)}`}>
                      {getGrowthIcon(analyticsData.growth_rates.views_growth)}
                      <span className="ml-1">{Math.abs(analyticsData.growth_rates.views_growth)}%</span>
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <HeartIcon className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Likes</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {formatNumber(analyticsData.overview.total_likes)}
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${getGrowthColor(analyticsData.growth_rates.likes_growth)}`}>
                      {getGrowthIcon(analyticsData.growth_rates.likes_growth)}
                      <span className="ml-1">{Math.abs(analyticsData.growth_rates.likes_growth)}%</span>
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShareIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Shares</dt>
                  <dd className="text-2xl font-semibold text-gray-900">
                    {formatNumber(analyticsData.overview.total_shares)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChatBubbleLeftIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Engagement Rate</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {analyticsData.overview.engagement_rate.toFixed(1)}%
                    </div>
                    <div className={`ml-2 flex items-baseline text-sm font-semibold ${getGrowthColor(analyticsData.growth_rates.engagement_growth)}`}>
                      {getGrowthIcon(analyticsData.growth_rates.engagement_growth)}
                      <span className="ml-1">{Math.abs(analyticsData.growth_rates.engagement_growth)}%</span>
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Platform Performance</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(analyticsData.platform_breakdown).map(([platform, metrics]) => (
                <div key={platform} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-3 w-3 rounded-full bg-blue-600"></div>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 capitalize">{platform}</p>
                      <p className="text-sm text-gray-500">{metrics.posts} posts</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{formatNumber(metrics.views)} views</p>
                    <p className="text-sm text-gray-500">{formatNumber(metrics.likes)} likes</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Performing Posts */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Top Performing Posts</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analyticsData.top_posts.slice(0, 5).map((post, index) => (
                <div key={post.post_id} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">#{index + 1}</span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Post {post.post_id.slice(-8)}</p>
                      <p className="text-sm text-gray-500">
                        {post.platforms.join(', ')} • {post.engagement_score.toFixed(1)} engagement
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{formatNumber(post.total_views)}</p>
                    <p className="text-sm text-gray-500">{formatNumber(post.total_likes)} likes</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Chart Placeholder */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">Chart visualization would go here</p>
              <p className="text-xs text-gray-400">Integration with charting library needed</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};