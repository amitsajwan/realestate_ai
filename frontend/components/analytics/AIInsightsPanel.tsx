'use client';

import { Badge } from '@/components/UI/Badge';
import { Button } from '@/components/UI/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/UI/Card';
import {
  ArrowTrendingUpIcon,
  ChartBarIcon,
  EyeIcon,
  LightBulbIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';

interface AIInsight {
  id: string;
  type: 'performance' | 'optimization' | 'trend' | 'recommendation';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  category: string;
  actionable: boolean;
  action_text?: string;
  metric_change?: string;
  confidence_score: number;
}

interface PerformanceData {
  posts: number;
  views: number;
  likes: number;
  shares: number;
  comments: number;
  engagement_rate: number;
}

interface AIInsightsPanelProps {
  performanceData: PerformanceData;
  userId: string;
}

export default function AIInsightsPanel({ performanceData, userId }: AIInsightsPanelProps) {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    generateAIInsights();
  }, [performanceData]);

  const generateAIInsights = async () => {
    setIsLoading(true);
    try {
      // Simulate AI analysis - in production, this would call your AI service
      const mockInsights = generateMockInsights(performanceData);
      setInsights(mockInsights);
    } catch (error) {
      console.error('Error generating AI insights:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockInsights = (data: PerformanceData): AIInsight[] => {
    const insights: AIInsight[] = [];

    // Engagement rate analysis
    if (data.engagement_rate < 3) {
      insights.push({
        id: 'engagement_low',
        type: 'performance',
        title: 'Low Engagement Rate Detected',
        description: `Your engagement rate of ${data.engagement_rate.toFixed(1)}% is below industry average. Consider using more interactive content and calls-to-action.`,
        impact: 'high',
        category: 'engagement',
        actionable: true,
        action_text: 'Improve engagement',
        confidence_score: 85
      });
    }

    // Content performance analysis
    if (data.posts > 0 && data.views / data.posts < 100) {
      insights.push({
        id: 'views_per_post',
        type: 'optimization',
        title: 'Low Views Per Post',
        description: `Average views per post is ${Math.round(data.views / data.posts)}. Consider optimizing posting times and hashtags.`,
        impact: 'medium',
        category: 'content',
        actionable: true,
        action_text: 'Optimize posting strategy',
        confidence_score: 78
      });
    }

    // Growth opportunity
    if (data.shares / data.posts < 5) {
      insights.push({
        id: 'share_potential',
        type: 'recommendation',
        title: 'High Share Potential',
        description: 'Your content has potential for more shares. Try adding shareable quotes, local insights, or market trends.',
        impact: 'medium',
        category: 'growth',
        actionable: true,
        action_text: 'Create shareable content',
        confidence_score: 72
      });
    }

    // Positive performance
    if (data.engagement_rate > 5) {
      insights.push({
        id: 'high_engagement',
        type: 'trend',
        title: 'Excellent Engagement Performance',
        description: `Your engagement rate of ${data.engagement_rate.toFixed(1)}% is above average! Keep up the great content strategy.`,
        impact: 'high',
        category: 'performance',
        actionable: false,
        metric_change: '+15%',
        confidence_score: 90
      });
    }

    // Content timing optimization
    insights.push({
      id: 'posting_time',
      type: 'optimization',
      title: 'Optimal Posting Times',
      description: 'Based on your audience data, posting between 6-8 PM on weekdays could increase engagement by 25%.',
      impact: 'medium',
      category: 'timing',
      actionable: true,
      action_text: 'Schedule optimal posts',
      confidence_score: 68
    });

    // Hashtag optimization
    insights.push({
      id: 'hashtag_optimization',
      type: 'recommendation',
      title: 'Hashtag Strategy Improvement',
      description: 'Using 15-20 relevant hashtags instead of generic ones could increase reach by 30%.',
      impact: 'medium',
      category: 'reach',
      actionable: true,
      action_text: 'Optimize hashtags',
      confidence_score: 75
    });

    return insights.sort((a, b) => b.confidence_score - a.confidence_score);
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'performance': return <ChartBarIcon className="h-5 w-5" />;
      case 'optimization': return <ArrowTrendingUpIcon className="h-5 w-5" />;
      case 'trend': return <EyeIcon className="h-5 w-5" />;
      case 'recommendation': return <LightBulbIcon className="h-5 w-5" />;
      default: return <SparklesIcon className="h-5 w-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'performance': return 'text-blue-600';
      case 'optimization': return 'text-green-600';
      case 'trend': return 'text-purple-600';
      case 'recommendation': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  const filteredInsights = selectedCategory === 'all'
    ? insights
    : insights.filter(insight => insight.category === selectedCategory);

  const categories = [
    { key: 'all', label: 'All Insights', count: insights.length },
    { key: 'engagement', label: 'Engagement', count: insights.filter(i => i.category === 'engagement').length },
    { key: 'content', label: 'Content', count: insights.filter(i => i.category === 'content').length },
    { key: 'growth', label: 'Growth', count: insights.filter(i => i.category === 'growth').length },
    { key: 'timing', label: 'Timing', count: insights.filter(i => i.category === 'timing').length },
    { key: 'reach', label: 'Reach', count: insights.filter(i => i.category === 'reach').length }
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SparklesIcon className="h-5 w-5 text-purple-600" />
            AI-Powered Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <span className="ml-2 text-gray-600">Analyzing your performance...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SparklesIcon className="h-5 w-5 text-purple-600" />
          AI-Powered Insights
          <Badge variant="secondary" className="ml-2">
            {insights.length} insights
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mb-6">
          {categories.map((category) => (
            <Button
              key={category.key}
              variant={selectedCategory === category.key ? "primary" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category.key)}
              className="text-xs"
            >
              {category.label}
              {category.count > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {category.count}
                </Badge>
              )}
            </Button>
          ))}
        </div>

        {/* Insights List */}
        <div className="space-y-4">
          {filteredInsights.length === 0 ? (
            <div className="text-center py-8">
              <LightBulbIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No insights available</h3>
              <p className="mt-1 text-sm text-gray-500">Create more content to get AI-powered insights.</p>
            </div>
          ) : (
            filteredInsights.map((insight) => (
              <div
                key={insight.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className={`flex-shrink-0 ${getTypeColor(insight.type)}`}>
                      {getTypeIcon(insight.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-gray-900">{insight.title}</h4>
                        <Badge className={getImpactColor(insight.impact)}>
                          {insight.impact} impact
                        </Badge>
                        {insight.metric_change && (
                          <Badge variant="outline" className="text-green-600">
                            {insight.metric_change}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>Confidence: {insight.confidence_score}%</span>
                        <span>•</span>
                        <span className="capitalize">{insight.category}</span>
                      </div>
                    </div>
                  </div>
                  {insight.actionable && (
                    <Button size="sm" variant="outline" className="ml-4">
                      {insight.action_text}
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Action Summary */}
        {insights.length > 0 && (
          <div className="mt-6 p-4 bg-purple-50 rounded-lg">
            <h4 className="font-medium text-purple-900 mb-2">Quick Actions</h4>
            <div className="flex flex-wrap gap-2">
              {insights
                .filter(insight => insight.actionable)
                .slice(0, 3)
                .map((insight) => (
                  <Button
                    key={insight.id}
                    size="sm"
                    variant="outline"
                    className="text-purple-700 border-purple-200 hover:bg-purple-100"
                  >
                    {insight.action_text}
                  </Button>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}