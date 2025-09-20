'use client'

import { Button, Card, CardBody } from '@/components/ui'
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  EyeIcon,
  HomeIcon,
  PlusIcon,
  SparklesIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'

interface DashboardStatsProps {
  stats: {
    total_properties: number
    active_listings: number
    total_leads: number
    total_users: number
    total_views: number
    monthly_leads: number
    revenue: string
  }
  onAddProperty: () => void
  onNavigateToAI: () => void
  onNavigateToAnalytics: () => void
  onNavigateToSmartForm: () => void
}

export function DashboardStats({
  stats,
  onAddProperty,
  onNavigateToAI,
  onNavigateToAnalytics,
  onNavigateToSmartForm
}: DashboardStatsProps) {
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric'
  })

  const quickActions = [
    {
      id: 'add-property',
      title: 'Add Properties',
      description: 'Start listing with AI-powered descriptions and market insights',
      icon: HomeIcon,
      variant: 'primary' as const,
      tag: 'Popular',
      onClick: onAddProperty
    },
    {
      id: 'ai-tools',
      title: 'AI Tools',
      description: 'Generate compelling content, market analysis, and property descriptions automatically',
      icon: SparklesIcon,
      variant: 'outline' as const,
      tag: 'AI Powered',
      onClick: onNavigateToAI
    },
    {
      id: 'analytics',
      title: 'Analytics',
      description: 'Track performance metrics, lead conversion rates, and market trends',
      icon: ChartBarIcon,
      variant: 'outline' as const,
      tag: 'Insights',
      onClick: onNavigateToAnalytics
    },
    {
      id: 'smart-form',
      title: 'Smart Form Demo',
      description: 'Experience our intelligent property form with step-by-step guidance & AI assistance',
      icon: PlusIcon,
      variant: 'outline' as const,
      tag: 'New',
      onClick: onNavigateToSmartForm
    }
  ]

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Good Morning! 👋</h1>
            <p className="text-blue-100 text-lg">Ready to boost your real estate business today?</p>
          </div>
          <div className="text-right">
            <p className="text-blue-100">Today</p>
            <p className="text-lg font-semibold">{currentDate}</p>
          </div>
        </div>

        {/* Primary KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-4xl font-bold">{stats.total_properties}</div>
            <div className="text-blue-100">Properties</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold">{stats.total_leads}</div>
            <div className="text-blue-100">Active Leads</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold">{stats.total_views}</div>
            <div className="text-blue-100">Total Views</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold">{stats.revenue}</div>
            <div className="text-blue-100">Revenue</div>
          </div>
        </div>
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover:shadow-md transition-shadow">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <HomeIcon className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{stats.total_properties}</div>
            <div className="text-sm text-gray-600 mb-2">Total Properties</div>
            <div className="text-xs text-green-600 font-medium">+12% this month</div>
          </CardBody>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CurrencyDollarIcon className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{stats.revenue}</div>
            <div className="text-sm text-gray-600 mb-2">Revenue</div>
            <div className="text-xs text-green-600 font-medium">+1% this quarter</div>
          </CardBody>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <EyeIcon className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{stats.total_views}</div>
            <div className="text-sm text-gray-600 mb-2">Property Views</div>
            <div className="text-xs text-green-600 font-medium">+24% vs last month</div>
          </CardBody>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <UserGroupIcon className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{stats.total_leads}</div>
            <div className="text-sm text-gray-600 mb-2">Active Leads</div>
            <div className="text-xs text-green-600 font-medium">+8% new this week</div>
          </CardBody>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Quick Actions</h2>
          <p className="text-gray-600">Get started with these essential tasks</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => (
            <Card
              key={action.id}
              className="hover:shadow-lg transition-all duration-200 cursor-pointer group"
              onClick={action.onClick}
            >
              <CardBody className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                    <action.icon className="w-6 h-6 text-gray-600 group-hover:text-blue-600 transition-colors" />
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${action.tag === 'Popular' ? 'bg-blue-100 text-blue-800' :
                      action.tag === 'AI Powered' ? 'bg-purple-100 text-purple-800' :
                        action.tag === 'Insights' ? 'bg-green-100 text-green-800' :
                          'bg-orange-100 text-orange-800'
                    }`}>
                    {action.tag}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  {action.title}
                </h3>
                <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                  {action.description}
                </p>
                <Button
                  variant={action.variant}
                  size="sm"
                  className="w-full group-hover:bg-blue-600 group-hover:text-white transition-colors"
                >
                  Get Started
                </Button>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}