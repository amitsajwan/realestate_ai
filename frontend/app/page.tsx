'use client'

import AdminPostsManagement from '@/components/AdminPostsManagement'
import BreadcrumbNavigation from '@/components/BreadcrumbNavigation'
import CRM from '@/components/CRM'
import DashboardCustomization from '@/components/DashboardCustomization'
import { DashboardStatsDisplay } from '@/components/DashboardStats'
import FacebookIntegration from '@/components/FacebookIntegration'
import MobileBottomNavigation from '@/components/MobileBottomNavigation'
import MobileFirstNavigation from '@/components/MobileFirstNavigation'
import MobilePropertyForm from '@/components/MobilePropertyForm'
import Properties from '@/components/Properties'
import PublishingWorkflowManager from '@/components/PublishingWorkflowManager'
import { Card, CardContent, CardHeader } from '@/components/UI'
import UnifiedPostingHub from '@/components/UnifiedPostingHub'
import { apiService } from '@/lib/api/centralized-client'
import { authManager } from '@/lib/auth'
import { User } from '@/lib/auth/types'
import { Property } from '@/lib/properties/types'
import { DashboardStats, DashboardWidget } from '@/types/dashboard'
import { UnifiedPostingMode } from '@/types/posting'
import {
  BuildingOfficeIcon,
  ChartBarIcon,
  CogIcon,
  GlobeAltIcon,
  HomeIcon,
  PlusIcon,
  SparklesIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
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
  { name: 'Property Marketing Hub', icon: SparklesIcon, id: 'property-marketing-hub', highlight: true },
  { name: 'Add Property', icon: PlusIcon, id: 'property-form' },
  { name: 'Analytics', icon: ChartBarIcon, id: 'analytics' },
  { name: 'CRM', icon: UsersIcon, id: 'crm' },
  { name: 'Team', icon: UsersIcon, id: 'team-management' },
  { name: 'Website', icon: GlobeAltIcon, id: 'public-website' },
  { name: 'Facebook', icon: CogIcon, id: 'facebook' }
]

export default function DashboardPage() {
  const router = useRouter()
  const [activeSection, setActiveSection] = useState('dashboard')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [showDashboardCustomization, setShowDashboardCustomization] = useState(false)
  const [properties, setProperties] = useState<Property[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [dashboardWidgets, setDashboardWidgets] = useState<DashboardWidget[]>([])
  const [showWorkflow, setShowWorkflow] = useState(false)
  const [workflowPropertyData, setWorkflowPropertyData] = useState<Property | null>(null)
  const [isAIContentModalOpen, setIsAIContentModalOpen] = useState(false)
  const [selectedPropertyForAI, setSelectedPropertyForAI] = useState<Property | null>(null)
  const [showUnifiedPosting, setShowUnifiedPosting] = useState(false)
  const [unifiedPostingMode, setUnifiedPostingMode] = useState<UnifiedPostingMode>('marketing-hub')
  const [unifiedPostingProperty, setUnifiedPostingProperty] = useState<Property | null>(null)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const initializeDashboard = async () => {
      try {
        const currentUser = await authManager.getCurrentUser()
        if (!currentUser) {
          router.push('/login')
          return
        }
        setUser(currentUser)
        await loadProperties()
        
        // Load saved dashboard widgets
        const savedWidgets = localStorage.getItem('dashboardWidgets')
        if (savedWidgets) {
          setDashboardWidgets(JSON.parse(savedWidgets))
        }
      } catch (error) {
        console.error('Failed to initialize dashboard:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initializeDashboard()
  }, [router])

  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    total_properties: 0,
    active_listings: 0,
    total_leads: 0,
    total_users: 0,
    total_views: 0,
    monthly_leads: 0,
    revenue: '$0'
  })

  const loadProperties = async () => {
    try {
      const [propertiesResponse, statsResponse] = await Promise.all([
        apiService.request<Property[]>('/api/properties', { method: 'GET' }),
        apiService.request<DashboardStats>('/api/stats/dashboard', { method: 'GET' })
      ])
      setProperties(propertiesResponse)
      
      // If the API call fails, we'll keep the default stats
      if (statsResponse) {
        setDashboardStats(statsResponse)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  const handleSectionChange = (section: string) => {
    setActiveSection(section)
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

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <DashboardStatsDisplay 
              stats={dashboardStats}
              onAddProperty={() => handleSectionChange('property-form')}
              onNavigateToAI={() => setIsAIContentModalOpen(true)}
              onNavigateToAnalytics={() => handleSectionChange('analytics')}
              onNavigateToSmartForm={() => handleSectionChange('property-form')}
              onNavigateToPosts={() => handleSectionChange('property-marketing-hub')}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {dashboardWidgets.map((widget) => (
                <Card key={widget.id}>
                  <CardHeader>
                    <h3 className="text-lg font-semibold">{widget.title}</h3>
                  </CardHeader>
                  <CardContent>
                    {widget.content}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )
      case 'properties':
        return (
          <Properties
            onPublishWorkflow={(property: Property) => {
              setWorkflowPropertyData(property)
              setShowWorkflow(true)
            }}
          />
        )
      case 'property-marketing-hub':
        return (
          <AdminPostsManagement
            onUnifiedPostClick={(property: Property) => {
              setUnifiedPostingMode('property-creation')
              setUnifiedPostingProperty(property)
              setShowUnifiedPosting(true)
            }}
            onCreatePost={() => {
              setUnifiedPostingMode('standalone')
              setShowUnifiedPosting(true)
            }}
          />
        )
      case 'facebook':
        return <FacebookIntegration />
      case 'public-website':
        return <PublicWebsiteManagement />
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
      default:
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold text-gray-900">Section under development</h2>
            <p className="text-gray-600 mt-2">This feature will be available soon.</p>
          </div>
        )
    }
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

        {/* Main Layout */}
        <div className="flex">
          {/* Desktop Sidebar */}
          <aside className="hidden lg:flex lg:flex-col lg:w-64 xl:w-72">
            <nav className="flex-1 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-r border-gray-200 dark:border-white/20">
              <div className="p-6">
                <div className="space-y-1">
                  {navigation.filter(item => item.id !== 'profile').map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleSectionChange(item.id)}
                      className={`relative w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 group hover-lift click-shrink ${
                        activeSection === item.id
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-[1.02] animate-scale-in'
                          : item.highlight
                            ? 'bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 text-purple-700 dark:bg-purple-900/20 dark:border-purple-700 dark:text-purple-300'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 hover:text-gray-900 dark:hover:text-white hover:transform hover:scale-[1.01]'
                      }`}
                    >
                      <item.icon className={`w-5 h-5 transition-transform group-hover:scale-110 hover-rotate ${
                        activeSection === item.id ? 'text-white' : ''
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
        propertyData={unifiedPostingProperty || undefined}
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