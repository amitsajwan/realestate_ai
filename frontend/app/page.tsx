'use client'

import AdminPostsManagement from '@/components/AdminPostsManagement'
import BreadcrumbNavigation from '@/components/BreadcrumbNavigation'
import CRM from '@/components/CRM'
import DashboardCustomization from '@/components/DashboardCustomization'
import { DashboardStats } from '@/components/DashboardStats'
import FacebookIntegration from '@/components/FacebookIntegration'
import GlobalSearch from '@/components/GlobalSearch'
import MobileBottomNavigation from '@/components/MobileBottomNavigation'
import MobileFirstNavigation from '@/components/MobileFirstNavigation'
import { MobileNavigation } from '@/components/MobileNavigation'
import MobilePropertyForm from '@/components/MobilePropertyForm'
import ProfileSettings from '@/components/ProfileSettings'
import Properties from '@/components/Properties'
import PublishingWorkflowManager from '@/components/PublishingWorkflowManager'
import { Button, Card, CardContent, CardHeader } from '@/components/UI'
import UnifiedPostingHub from '@/components/UnifiedPostingHub'
import { apiService } from '@/lib/api/centralized-client'
import { authManager } from '@/lib/auth'
import {
  AdjustmentsHorizontalIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  BellIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  CogIcon,
  GlobeAltIcon,
  HomeIcon,
  PlusIcon,
  SparklesIcon,
  UserIcon,
  UsersIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { lazy, Suspense, useEffect, useState } from 'react'

// Lazy load heavy components
const AIContentGeneratorModal = lazy(() => import('@/components/AIContentGeneratorModal'))
const Analytics = lazy(() => import('@/components/Analytics'))
const PublicWebsiteManagement = lazy(() => import('@/components/PublicWebsiteManagement'))
const TeamManagement = lazy(() => import('@/components/TeamManagement'))
const UXDemo = lazy(() => import('@/components/UXDemo'))

interface NavigationItem {
  name: string
  icon: any
  id: string
  highlight?: boolean
  badge?: string
  position?: 'bottom'
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', icon: HomeIcon, id: 'dashboard' },
  { name: 'Properties', icon: BuildingOfficeIcon, id: 'properties' },
  { name: 'Property Marketing Hub', icon: BuildingOfficeIcon, id: 'property-marketing-hub', highlight: true },
  { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
  { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
  { name: 'CRM', icon: UsersIcon, id: 'crm' },
  { name: 'Team Management', icon: UsersIcon, id: 'team-management' },
  { name: 'Public Website', icon: GlobeAltIcon, id: 'public-website' },
  { name: 'Facebook', icon: CogIcon, id: 'facebook' },
  { name: 'Profile', icon: UserIcon, id: 'profile' },
  // Moved to bottom as utility
  { name: 'UX Demo', icon: SparklesIcon, id: 'ux-demo', position: 'bottom' },
]

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('property-marketing-hub')
  const [user, setUser] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [properties, setProperties] = useState<any[]>([])
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [selectedPropertyForContent, setSelectedPropertyForContent] = useState<string | undefined>(undefined)
  const [showWorkflow, setShowWorkflow] = useState(false)
  const [workflowPropertyData, setWorkflowPropertyData] = useState<any>(null)
  const [isAIContentModalOpen, setIsAIContentModalOpen] = useState(false)
  const [selectedPropertyForAI, setSelectedPropertyForAI] = useState<any>(null)
  const [showDashboardCustomization, setShowDashboardCustomization] = useState(false)
  const [dashboardWidgets, setDashboardWidgets] = useState<any[]>([])
  const [showUnifiedPosting, setShowUnifiedPosting] = useState(false)
  const [unifiedPostingMode, setUnifiedPostingMode] = useState<'quick-post' | 'standalone' | 'marketing-hub' | 'property-creation'>('quick-post')
  const [unifiedPostingProperty, setUnifiedPostingProperty] = useState<any>(null)
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
      console.debug('[DashboardPage] Checking authentication...')
      if (typeof window !== 'undefined') {
        console.debug('[DashboardPage] Current URL:', window.location.href)
        console.debug('[DashboardPage] URL params:', Object.fromEntries(new URLSearchParams(window.location.search).entries()))

        // Handle URL section parameter
        const urlParams = new URLSearchParams(window.location.search)
        const sectionParam = urlParams.get('section')
        if (sectionParam) {
          console.debug('[DashboardPage] Setting active section from URL:', sectionParam)
          setActiveSection(sectionParam)
        }
      }

      try {
        console.log('[DashboardPage] Initializing authentication...')
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
          setIsLoading(false)
          router.push('/login')
          return
        }

        if (!state.user?.onboarding_completed) {
          console.log('[DashboardPage] Onboarding not completed, redirecting to onboarding')
          setIsLoading(false)
          router.push('/onboarding')
          return
        }

        console.log('[DashboardPage] User authenticated and onboarded, loading dashboard data')
        setUser(state.user)
        setIsLoading(false)

        // Wait a moment to ensure token is fully propagated before making API calls
        await new Promise(resolve => setTimeout(resolve, 150))

        fetchStats()
        loadProperties()
      } catch (error) {
        console.error('[DashboardPage] Auth initialization failed:', error)
        setIsLoading(false)
        router.push('/login')
      }
    }

    // Add timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      if (isLoading) {
        console.warn('[DashboardPage] Loading timeout, redirecting to login')
        setIsLoading(false)
        router.push('/login')
      }
    }, 3000) // 3 second timeout

    initAuth()

    // Subscribe to auth state changes to handle logout
    const unsubscribe = authManager.subscribe((state) => {
      console.debug('[DashboardPage] Auth state changed:', {
        isAuthenticated: state.isAuthenticated,
        hasUser: !!state.user
      })

      if (!state.isAuthenticated) {
        console.info('[DashboardPage] User logged out, redirecting to login')
        router.push('/login')
      }
    })

    return () => {
      clearTimeout(timeout)
      unsubscribe()
    }
  }, [router, isLoading])

  const fetchStats = async () => {
    try {
      const response = await apiService.getDashboardStats()
      if (response.success && response.data) {
        setStats(response.data)
      }
    } catch (error) {
      console.error('[DashboardPage] Error fetching stats:', error)
    }
  }

  const loadProperties = async () => {
    try {
      console.log('[DashboardPage] Fetching properties from API...')
      const response = await apiService.getProperties()
      console.log('[DashboardPage] API response:', response)

      // Handle both direct array response and wrapped response
      const propertiesData = Array.isArray(response) ? response : (response as any)?.data || []

      if (propertiesData && propertiesData.length > 0) {
        // Transform the API response to match the expected format
        const transformedProperties = propertiesData.map((property: any) => ({
          id: property.id,
          title: property.title,
          price: property.price,
          status: property.status === 'active' ? 'for-sale' : property.status,
          type: property.property_type,
          bedrooms: property.bedrooms,
          bathrooms: property.bathrooms,
          area: property.area_sqft,
          address: property.location,
          date_added: property.created_at ? (() => {
            try {
              let cleanDateString = property.created_at;
              if (cleanDateString.includes('.') && !cleanDateString.endsWith('Z') && !cleanDateString.includes('+') && !cleanDateString.includes('-', 10)) {
                const parts = cleanDateString.split('.');
                if (parts.length === 2) {
                  const microseconds = parts[1].substring(0, 6);
                  cleanDateString = parts[0] + '.' + microseconds + 'Z';
                }
              }
              return new Date(cleanDateString).toISOString().split('T')[0];
            } catch {
              return new Date().toISOString().split('T')[0];
            }
          })() : new Date().toISOString().split('T')[0],
          description: property.description,
          images: property.images || [],
          image: property.images?.[0] || null
        }))
        setProperties(transformedProperties)
        console.log('[DashboardPage] Properties loaded:', transformedProperties.length)
        console.log('[DashboardPage] Properties state updated:', transformedProperties)
      } else {
        console.log('[DashboardPage] No properties found, using empty array')
        setProperties([])
      }
    } catch (error) {
      console.error('[DashboardPage] Error fetching properties:', error)
      // Fallback to empty array on error
      setProperties([])
    }
  }

  // Removed testThemePersistence function to prevent theme initialization loops

  const handleGenerateContent = (propertyId: string) => {
    // Find the property data
    const property = properties.find(p => p.id === propertyId)
    if (property) {
      setUnifiedPostingProperty(property)
      setUnifiedPostingMode('quick-post')
      setShowUnifiedPosting(true)
    }
  }

  const handleSectionChange = (section: string) => {
    setActiveSection(section)
    // Clear selected property when navigating away from marketing hub
    if (section !== 'property-marketing-hub') {
      setSelectedPropertyForContent(undefined)
    }
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'property-marketing-hub':
        // Use admin interface for posts management
        return <AdminPostsManagement
          onCreatePost={() => {
            setUnifiedPostingProperty(null)
            setUnifiedPostingMode('standalone')
            setShowUnifiedPosting(true)
          }}
        />
      case 'properties':
        return <Properties
          onAddProperty={() => setActiveSection('property-form')}
          properties={properties}
          setProperties={setProperties}
          onRefresh={loadProperties}
          onGenerateContent={handleGenerateContent}
        />
      case 'posts':
        // Legacy alias -> redirect to Marketing Hub
        return <AdminPostsManagement
          onCreatePost={() => {
            setUnifiedPostingProperty(null)
            setUnifiedPostingMode('standalone')
            setShowUnifiedPosting(true)
          }}
        />
      case 'property-form':
        return (
          <MobilePropertyForm
            onSuccess={() => {
              console.log('[DashboardPage] Property form completed successfully')
              setActiveSection('properties')
              loadProperties()
            }}
          />
        )
      case 'ai-content':
        return (
          <div className="text-center py-16">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <SparklesIcon className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Content Generator</h2>
              <p className="text-gray-600 mb-8">Create compelling content for your properties using AI</p>
              <button
                onClick={() => {
                  setUnifiedPostingMode('standalone')
                  setShowUnifiedPosting(true)
                }}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 flex items-center space-x-2 mx-auto"
              >
                <SparklesIcon className="w-5 h-5" />
                <span>Start Creating Content</span>
              </button>
            </div>
          </div>
        )
      case 'analytics':
        return (
          <Suspense fallback={
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          }>
            <Analytics properties={properties} />
          </Suspense>
        )
      case 'crm':
        return <CRM />
      case 'team-management':
        return (
          <Suspense fallback={
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          }>
            <TeamManagement />
          </Suspense>
        )
      case 'ux-demo':
        return (
          <Suspense fallback={
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          }>
            <UXDemo />
          </Suspense>
        )
      case 'facebook':
        return <FacebookIntegration />
      case 'profile':
        return <ProfileSettings />
      case 'public-website':
        return (
          <Suspense fallback={
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          }>
            <PublicWebsiteManagement />
          </Suspense>
        )
      default:
        return (
          <div className="space-y-8">
            <DashboardStats
              stats={stats}
              onAddProperty={() => setActiveSection('property-form')}
              onNavigateToAI={() => {
                setUnifiedPostingMode('standalone')
                setShowUnifiedPosting(true)
              }}
              onNavigateToAnalytics={() => setActiveSection('analytics')}
              onNavigateToSmartForm={() => setActiveSection('property-form')}
              onNavigateToPosts={() => {
                setUnifiedPostingMode('marketing-hub')
                setShowUnifiedPosting(true)
              }}
            />


            {/* Recent Properties Preview */}
            <Card className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">Recent Properties</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setActiveSection('properties')}
                    className="text-brand-primary hover:text-brand-primary-hover"
                  >
                    View All →
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {properties.slice(0, 3).map((property, index) => (
                    <motion.div
                      key={property.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gray-50 rounded-xl p-4 hover:shadow-md transition-all duration-200 cursor-pointer hover:bg-gray-100"
                      onClick={() => setActiveSection('properties')}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-gray-900 truncate">{property.title}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${property.status === 'for-sale'
                          ? 'bg-emerald-100 text-emerald-700'
                          : property.status === 'for-rent'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-100 text-gray-700'
                          }`}>
                          {property.status === 'for-sale' ? 'For Sale' : property.status === 'for-rent' ? 'For Rent' : property.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <span className="font-semibold text-gray-900">₹{property.price.toLocaleString()}</span>
                        <span>{property.bedrooms} bed • {property.bathrooms} bath</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
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
          <p className="text-gray-300 text-sm mt-2">Initializing authentication...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="page-transition">
        {/* Mobile-First Navigation */}
        <MobileFirstNavigation
          activeSection={activeSection}
          onSectionChange={handleSectionChange}
          user={user}
          properties={properties}
          onShowDashboardCustomization={() => setShowDashboardCustomization(true)}
          onShowAIContentModal={() => setIsAIContentModalOpen(true)}
        />

        {/* Content Area removed to prevent extra vertical whitespace */}

        {/* Desktop Header (hidden on mobile) */}
        <header className="hidden md:block sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-lg border-b border-gray-200 dark:border-white/20 shadow-sm">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16 min-h-[64px]">
              {/* Logo and Mobile Menu Button */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="lg:hidden p-3 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors min-h-[48px] min-w-[48px] flex items-center justify-center"
                  aria-label="Toggle mobile menu"
                  title="Toggle mobile menu"
                >
                  {isMobileMenuOpen ? (
                    <XMarkIcon className="w-6 h-6" />
                  ) : (
                    <Bars3Icon className="w-6 h-6" />
                  )}
                </button>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg">
                    <HomeIcon className="w-6 h-6 text-white" />
                  </div>
                  <h1 className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
                    PropertyAI
                  </h1>
                </div>
              </div>

              {/* Desktop Navigation */}
              <nav id="navigation" className="hidden lg:flex items-center space-x-1">
                {navigation.slice(0, 5).map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleSectionChange(item.id)}
                    className={`relative flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${activeSection === item.id
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white'
                      }`}
                    title={`Navigate to ${item.name}`}
                    aria-label={`Navigate to ${item.name}`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="hidden xl:block">{item.name}</span>
                  </button>
                ))}
              </nav>

              {/* Right Side Actions */}
              <div className="flex items-center space-x-3">
                {/* Global Search */}
                <GlobalSearch className="hidden md:block" />

                {/* Dashboard Customization Button */}
                <button
                  onClick={() => setShowDashboardCustomization(true)}
                  className="hidden lg:flex items-center space-x-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  title="Customize Dashboard"
                  aria-label="Customize Dashboard"
                >
                  <AdjustmentsHorizontalIcon className="w-4 h-4" />
                  <span className="text-sm font-medium hidden xl:block">Customize</span>
                </button>

                {/* Create Post Button - Desktop */}
                {properties.length > 0 && (
                  <button
                    onClick={() => setIsAIContentModalOpen(true)}
                    className="hidden sm:flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                    title="Create Post"
                    aria-label="Create Post"
                  >
                    <SparklesIcon className="w-4 h-4" />
                    <span className="text-sm font-medium">Create Post</span>
                  </button>
                )}
                {/* Create Post Button - Mobile */}
                {properties.length > 0 && (
                  <button
                    onClick={() => setIsAIContentModalOpen(true)}
                    className="sm:hidden p-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
                    title="Create Post"
                  >
                    <SparklesIcon className="w-5 h-5" />
                  </button>
                )}
                <button
                  className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors relative"
                  title="Notifications"
                  aria-label="Notifications"
                >
                  <BellIcon className="w-5 h-5" />
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
                </button>
                <div className="flex items-center space-x-3">
                  <div className="hidden sm:flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {(user?.first_name || 'A').charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {user?.first_name || 'Agent'}
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
            <nav id="navigation" className="flex-1 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-r border-gray-200 dark:border-white/20">
              <div className="p-6">
                <div className="space-y-1">
                  {navigation.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleSectionChange(item.id)}
                      className={`relative w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group hover-lift click-shrink ${activeSection === item.id
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-[1.02] animate-scale-in'
                        : item.highlight
                          ? 'bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 text-purple-700 dark:bg-purple-900/20 dark:border-purple-700 dark:text-purple-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white hover:transform hover:scale-[1.01]'
                        }`}
                    >
                      <item.icon className={`w-5 h-5 transition-transform group-hover:scale-110 hover-rotate ${activeSection === item.id ? 'text-white' : ''
                        }`} />
                      <span className="font-medium">{item.name}</span>
                      {item.badge && (
                        <span className="ml-auto px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                          {item.badge}
                        </span>
                      )}
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
                  className="lg:hidden fixed left-0 top-16 bottom-0 z-50 w-80 max-w-[85vw] bg-white dark:bg-slate-900 shadow-2xl overflow-y-auto"
                >
                  <div className="p-6">
                    <div className="space-y-2">
                      {navigation.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            handleSectionChange(item.id)
                            setIsMobileMenuOpen(false)
                          }}
                          className={`relative w-full flex items-center space-x-4 px-4 py-4 rounded-xl text-left transition-all duration-200 ${activeSection === item.id
                            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                            : item.highlight
                              ? 'bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 text-purple-700 dark:bg-purple-900/20 dark:border-purple-700 dark:text-purple-300'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'
                            }`}
                        >
                          <item.icon className="w-6 h-6" />
                          <span className="font-medium text-lg">{item.name}</span>
                          {item.badge && (
                            <span className="ml-auto px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.nav>
              </>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <main id="main-content" className="flex-1 min-h-screen bg-gray-50 pb-20 lg:pb-0">
            <div className="p-4 sm:p-6 lg:p-8">
              {/* Breadcrumb Navigation */}
              <BreadcrumbNavigation className="mb-6" />

              <motion.div
                key={activeSection}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className="container mx-auto animate-fade-in"
              >
                {renderSection()}
              </motion.div>
            </div>
          </main>

          {/* Mobile Navigation */}
          <MobileNavigation
            activeSection={activeSection}
            onSectionChange={handleSectionChange}
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
          />

          {/* Mobile Bottom Navigation */}
          <MobileBottomNavigation
            activeSection={activeSection}
            onSectionChange={handleSectionChange}
            className="lg:hidden"
          />
        </div>
      </div>

      {/* Property-to-Post Workflow */}
      <PublishingWorkflowManager
        propertyData={workflowPropertyData}
        isOpen={showWorkflow}
        onClose={() => {
          setShowWorkflow(false)
          setWorkflowPropertyData(null)
        }}
        onComplete={() => {
          setShowWorkflow(false)
          setWorkflowPropertyData(null)
          setActiveSection('properties')
          loadProperties()
        }}
      />

      {/* Unified Posting Hub */}
      <UnifiedPostingHub
        mode={unifiedPostingMode}
        propertyData={unifiedPostingProperty}
        isOpen={showUnifiedPosting}
        onClose={() => {
          setShowUnifiedPosting(false)
          setUnifiedPostingProperty(null)
        }}
        onContentGenerated={(content) => {
          console.log('Content generated:', content)
        }}
        onPublish={(content, language) => {
          console.log('Content published:', content, language)
          setShowUnifiedPosting(false)
          setUnifiedPostingProperty(null)
          // Refresh properties to show updated content
          loadProperties()
        }}
        preselectedLanguage="en"
        preselectedPlatforms={['website', 'facebook', 'instagram']}
      />

      {/* AI Content Generator Modal */}
      <Suspense fallback={
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      }>
        <AIContentGeneratorModal
          isOpen={isAIContentModalOpen}
          onClose={() => {
            setIsAIContentModalOpen(false)
            setSelectedPropertyForAI(null)
          }}
          propertyData={selectedPropertyForAI}
        />
      </Suspense>

      {/* Dashboard Customization Modal */}
      <DashboardCustomization
        isOpen={showDashboardCustomization}
        onClose={() => setShowDashboardCustomization(false)}
        onSave={(widgets) => {
          setDashboardWidgets(widgets)
          // Save to localStorage or API
          localStorage.setItem('dashboardWidgets', JSON.stringify(widgets))
        }}
        currentWidgets={dashboardWidgets}
      />
    </div>
  )
}
