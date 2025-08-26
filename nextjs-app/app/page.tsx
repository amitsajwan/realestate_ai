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
  ArrowRightOnRectangleIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline'
import { authManager } from '@/lib/auth'
import { apiService } from '@/lib/api'
import DashboardStats from '@/components/DashboardStats'
import PropertyForm from '@/components/PropertyForm'
import Properties from '@/components/Properties'
import AIContentGenerator from '@/components/AIContentGenerator'
import Analytics from '@/components/Analytics'
import CRM from '@/components/CRM'
import FacebookIntegration from '@/components/FacebookIntegration'
import ProfileSettings from '@/components/ProfileSettings'
import { loadBrandTheme, applyBrandTheme } from '@/lib/theme'

const navigation = [
  { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
  { name: 'Properties', icon: BuildingOfficeIcon, id: 'properties' },
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
  const [properties, setProperties] = useState<any[]>([])
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
      console.log('[DashboardPage] Checking authentication...')
      console.log('[DashboardPage] Current URL:', window.location.href)
      console.log('[DashboardPage] URL params:', Object.fromEntries(new URLSearchParams(window.location.search).entries()))
      
      await authManager.init()
      const state = authManager.getState()
      
      console.log('[DashboardPage] Auth state after init:', {
        isAuthenticated: state.isAuthenticated,
        hasUser: !!state.user,
        user: state.user,
        isLoading: state.isLoading
      })
      
      if (!state.isAuthenticated) {
        console.log('[DashboardPage] Not authenticated, redirecting to login')
        router.push('/login')
        return
      }

      if (!state.user?.onboardingCompleted) {
        console.log('[DashboardPage] Onboarding not completed, redirecting to onboarding')
        router.push('/onboarding')
        return
      }

      console.log('[DashboardPage] User authenticated and onboarded, loading dashboard data')
      setUser(state.user)
      setIsLoading(false)
      fetchStats()
      loadMockProperties()
    }

    initAuth()
  }, [router])

  const fetchStats = async () => {
    try {
      const response = await apiService.getDashboardStats()
      if (response.success && response.data) {
        setStats(response.data)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const loadMockProperties = () => {
    const mockData = [
      {
        id: '1',
        title: 'Modern Downtown Condo',
        price: 450000,
        status: 'for-sale',
        type: 'Condo',
        bedrooms: 2,
        bathrooms: 2,
        area: 1200,
        address: '123 Main St, Downtown',
        dateAdded: '2024-01-15',
        description: 'Beautiful modern condo with city views'
      },
      {
        id: '2',
        title: 'Luxury Villa',
        price: 850000,
        status: 'sold',
        type: 'House',
        bedrooms: 4,
        bathrooms: 3,
        area: 2500,
        address: '456 Oak Ave, Suburbs',
        dateAdded: '2024-01-10',
        description: 'Spacious luxury villa with garden'
      },
      {
        id: '3',
        title: 'Suburban House',
        price: 320000,
        status: 'for-rent',
        type: 'House',
        bedrooms: 3,
        bathrooms: 2,
        area: 1800,
        address: '789 Pine St, Suburbs',
        dateAdded: '2024-01-20',
        description: 'Family-friendly suburban home'
      },
      {
        id: '4',
        title: 'City Apartment',
        price: 280000,
        status: 'for-sale',
        type: 'Apartment',
        bedrooms: 1,
        bathrooms: 1,
        area: 800,
        address: '321 Elm St, City Center',
        dateAdded: '2024-01-25',
        description: 'Cozy apartment in the heart of the city'
      },
      {
        id: '5',
        title: 'Waterfront Townhouse',
        price: 620000,
        status: 'for-sale',
        type: 'Townhouse',
        bedrooms: 3,
        bathrooms: 2,
        area: 1600,
        address: '555 Lake Dr, Waterfront',
        dateAdded: '2024-01-30',
        description: 'Beautiful townhouse with lake views'
      }
    ]
    setProperties(mockData)
  }

  const testThemePersistence = () => {
    console.log('Testing theme persistence...');
    const savedTheme = loadBrandTheme();
    console.log('Saved theme:', savedTheme);
    
    if (savedTheme) {
      console.log('Applying saved theme:', savedTheme);
      applyBrandTheme(savedTheme, false);
    } else {
      console.log('No saved theme found, applying test theme');
      const testTheme = {
        primary: '#007bff',
        secondary: '#6c757d', 
        accent: '#28a745'
      };
      applyBrandTheme(testTheme, true);
    }
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'properties':
        return <Properties onAddProperty={() => setActiveSection('property-form')} properties={properties} setProperties={setProperties} />
      case 'property-form':
        return <PropertyForm />
      case 'ai-content':
        return <AIContentGenerator />
      case 'analytics':
        return <Analytics properties={properties} />
      case 'crm':
        return <CRM />
      case 'facebook':
        return <FacebookIntegration />
      case 'profile':
        return <ProfileSettings />
      default:
        return (
          <div>
            <DashboardStats stats={stats} />
            <div className="mt-4 p-4 bg-yellow-100 border border-yellow-300 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Theme Debug Tools</h3>
              <button
                onClick={testThemePersistence}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
              >
                Test Theme Persistence
              </button>
            </div>
          </div>
        )
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
