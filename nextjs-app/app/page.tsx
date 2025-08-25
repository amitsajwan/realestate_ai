'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { 
  HomeIcon, 
  PlusIcon, 
  ChartBarIcon, 
  UsersIcon, 
  CogIcon,
  UserIcon,
  SparklesIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline'
import { authManager } from '@/lib/auth'
import DashboardStats from '@/components/DashboardStats'
import PropertyForm from '@/components/PropertyForm'
import AIContentGenerator from '@/components/AIContentGenerator'
import Analytics from '@/components/Analytics'
import CRM from '@/components/CRM'
import FacebookIntegration from '@/components/FacebookIntegration'
import ProfileSettings from '@/components/ProfileSettings'

const navigation = [
  { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
  { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
  { name: 'AI Tools', icon: SparklesIcon, id: 'ai-content' },
  { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
  { name: 'CRM', icon: UsersIcon, id: 'crm' },
  { name: 'Facebook', icon: CogIcon, id: 'facebook' },
  { name: 'Profile', icon: UserIcon, id: 'profile' },
]

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('dashboard')
  const [user, setUser] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    total_properties: 0,
    active_listings: 0,
    total_leads: 0,
    total_users: 0,
    total_views: 0,
    monthly_leads: 0,
    revenue: '₹0'
  })
  const router = useRouter()

  useEffect(() => {
    const initAuth = async () => {
      await authManager.init()
      const state = authManager.getState()
      
      if (!state.isAuthenticated) {
        router.push('/login')
        return
      }

      if (!state.user?.onboardingCompleted) {
        router.push('/onboarding')
        return
      }

      setUser(state.user)
      setIsLoading(false)
      fetchStats()
    }

    initAuth()
  }, [router])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/stats')
      const data = await response.json()
      if (data.success) {
        setStats(data.stats)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return <DashboardStats stats={stats} />
      case 'property-form':
        return <PropertyForm onSuccess={fetchStats} />
      case 'ai-content':
        return <AIContentGenerator />
      case 'analytics':
        return <Analytics />
      case 'crm':
        return <CRM />
      case 'facebook':
        return <FacebookIntegration />
      case 'profile':
        return <ProfileSettings />
      default:
        return <DashboardStats stats={stats} />
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <HomeIcon className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-white">PropertyAI</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-white">
                <div className="w-8 h-8 bg-gray-600 rounded-full"></div>
                <span className="font-medium">{user?.firstName || 'Agent Name'}</span>
              </div>
              <button
                onClick={() => {
                  authManager.logout()
                  router.push('/login')
                }}
                className="text-white hover:text-gray-300 transition-colors"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <nav className="w-64 bg-white/10 backdrop-blur-lg border-r border-white/20 min-h-screen">
          <div className="p-4">
            <div className="space-y-2">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    activeSection === item.id
                      ? 'bg-white/20 text-white shadow-lg'
                      : 'text-gray-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </button>
              ))}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {renderSection()}
          </motion.div>
        </main>
      </div>
    </div>
  )
}
