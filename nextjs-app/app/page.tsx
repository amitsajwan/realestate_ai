'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  BuildingOfficeIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-purple-900 dark:to-slate-900">
      {/* Mobile-First Header */}
      <header className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-lg border-b border-gray-200 dark:border-white/20 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Mobile Menu Button */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
              >
                {isMobileMenuOpen ? (
                  <XMarkIcon className="w-6 h-6" />
                ) : (
                  <Bars3Icon className="w-6 h-6" />
                )}
              </button>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <HomeIcon className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  PropertyAI
                </h1>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center space-x-1">
              {navigation.slice(0, 4).map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeSection === item.id
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="hidden xl:block">{item.name}</span>
                </button>
              ))}
            </nav>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-3">
              <button className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors relative">
                <BellIcon className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center space-x-3">
                <div className="hidden sm:flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {(user?.firstName || 'A').charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {user?.firstName || 'Agent'}
                  </span>
                </div>
                <button
                  onClick={() => {
                    authManager.logout()
                    router.push('/login')
                  }}
                  className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:flex lg:flex-col lg:w-64 xl:w-72">
          <nav className="flex-1 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-r border-gray-200 dark:border-white/20">
            <div className="p-6">
              <div className="space-y-1">
                {navigation.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group hover-lift click-shrink ${
                      activeSection === item.id
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-[1.02] animate-scale-in'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white hover:transform hover:scale-[1.01]'
                    }`}
                  >
                    <item.icon className={`w-5 h-5 transition-transform group-hover:scale-110 hover-rotate ${
                      activeSection === item.id ? 'text-white' : ''
                    }`} />
                    <span className="font-medium">{item.name}</span>
                    {activeSection === item.id && (
                      <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </nav>
        </aside>

        {/* Mobile Navigation Overlay */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
                onClick={() => setIsMobileMenuOpen(false)}
              />
              <motion.nav
                initial={{ x: '-100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="lg:hidden fixed left-0 top-16 bottom-0 z-50 w-80 bg-white dark:bg-slate-900 shadow-2xl overflow-y-auto"
              >
                <div className="p-6">
                  <div className="space-y-2">
                    {navigation.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveSection(item.id)
                          setIsMobileMenuOpen(false)
                        }}
                        className={`w-full flex items-center space-x-4 px-4 py-4 rounded-xl text-left transition-all duration-200 ${
                          activeSection === item.id
                            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'
                        }`}
                      >
                        <item.icon className="w-6 h-6" />
                        <span className="font-medium text-lg">{item.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.nav>
            </>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="p-4 sm:p-6 lg:p-8">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="max-w-7xl mx-auto animate-fade-in"
            >
              {renderSection()}
            </motion.div>
          </div>
        </main>
      </div>
    </div>
  )
}
