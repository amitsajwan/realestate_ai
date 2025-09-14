'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
// import '@/styles/components/crm.css' // Temporarily disabled for tests
import { 
  UsersIcon, 
  PhoneIcon, 
  ChatBubbleLeftRightIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  StarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  MapPinIcon,
  ChevronDownIcon,
  XMarkIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { 
  StarIcon as StarSolidIcon,
  PhoneIcon as PhoneSolidIcon,
  ChatBubbleLeftRightIcon as ChatSolidIcon
} from '@heroicons/react/24/solid'
import { crmApi, Lead, LeadStats, LeadSearchFilters } from '@/lib/crm-api'

interface LeadActivity {
  id: string
  lead_id: string
  activity_type: string
  description: string
  performed_by: string
  timestamp: string
  metadata?: Record<string, any>
}

export default function CRM() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([])
  const [stats, setStats] = useState<LeadStats | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [urgencyFilter, setUrgencyFilter] = useState<string>('all')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [showLeadModal, setShowLeadModal] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  // Load data from API
  useEffect(() => {
    loadData()
  }, [currentPage, statusFilter, urgencyFilter, searchTerm])

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Load leads and stats in parallel
      const [leadsResult, statsData] = await Promise.all([
        loadLeads(),
        loadStats()
      ])

      setLeads(leadsResult.leads)
      setFilteredLeads(leadsResult.leads)
      setTotalPages(leadsResult.total_pages)
      setStats(statsData)

    } catch (err) {
      console.error('Error loading data:', err)
      setError(err instanceof Error ? err.message : 'Failed to load data')
      
      // Fallback to mock data if API fails
      loadMockData()
    } finally {
      setIsLoading(false)
    }
  }

  const loadLeads = async () => {
    const filters: LeadSearchFilters = {}
    
    if (statusFilter !== 'all') {
      filters.status = statusFilter
    }
    
    if (urgencyFilter !== 'all') {
      filters.urgency = urgencyFilter
    }
    
    if (searchTerm) {
      filters.search_term = searchTerm
    }

    return await crmApi.getLeads(filters, currentPage, 20)
  }

  const loadStats = async () => {
    return await crmApi.getLeadStats()
  }

  const loadMockData = () => {
    const mockLeads: Lead[] = [
      {
        id: '1',
        name: 'Rajesh Kumar',
        email: 'rajesh@email.com',
        phone: '+91 98765 43210',
        budget: 5000000,
        property_type_preference: '3 BHK Apartment',
        location_preference: 'Mumbai, Thane',
        timeline: '3 months',
        urgency: 'medium',
        source: 'website',
        status: 'new',
        score: 85,
        last_contact_date: '2024-01-15',
        created_at: '2024-01-15',
        updated_at: '2024-01-15',
        notes: 'Interested in properties near IT parks'
      },
      {
        id: '2',
        name: 'Priya Sharma',
        email: 'priya@email.com',
        phone: '+91 98765 43211',
        budget: 8000000,
        property_type_preference: 'Villa',
        location_preference: 'Pune, Hinjewadi',
        timeline: 'ASAP',
        urgency: 'high',
        source: 'referral',
        status: 'qualified',
        score: 92,
        last_contact_date: '2024-01-10',
        created_at: '2024-01-10',
        updated_at: '2024-01-10',
        notes: 'Ready to close deal quickly'
      },
      {
        id: '3',
        name: 'Amit Patel',
        email: 'amit@email.com',
        phone: '+91 98765 43212',
        budget: 3500000,
        property_type_preference: '2 BHK Apartment',
        location_preference: 'Ahmedabad',
        timeline: '6 months',
        urgency: 'low',
        source: 'social_media',
        status: 'contacted',
        score: 68,
        last_contact_date: '2024-01-08',
        created_at: '2024-01-08',
        updated_at: '2024-01-08',
        notes: 'First-time buyer, needs guidance'
      }
    ]

    setLeads(mockLeads)
    setFilteredLeads(mockLeads)
    
    // Mock stats
    setStats({
      total_leads: 3,
      new_leads: 1,
      contacted_leads: 1,
      qualified_leads: 1,
      converted_leads: 0,
      lost_leads: 0,
      conversion_rate: 0,
      average_deal_value: 0,
      total_pipeline_value: 16500000,
      leads_this_month: 3,
      leads_this_week: 2,
      leads_today: 0
    })
  }

  // Handle lead updates
  const handleLeadUpdate = async (leadId: string, updateData: Partial<Lead>) => {
    try {
      const updatedLead = await crmApi.updateLead(leadId, updateData)
      
      // Update local state
      setLeads(prev => prev.map(lead => lead.id === leadId ? updatedLead : lead))
      setFilteredLeads(prev => prev.map(lead => lead.id === leadId ? updatedLead : lead))
      
      // Reload stats
      const newStats = await crmApi.getLeadStats()
      setStats(newStats)
      
    } catch (err) {
      console.error('Error updating lead:', err)
      setError(err instanceof Error ? err.message : 'Failed to update lead')
    }
  }

  // Handle lead creation
  const handleCreateLead = async (leadData: Partial<Lead>) => {
    try {
      const newLead = await crmApi.createLead(leadData)
      
      // Add to local state
      setLeads(prev => [newLead, ...prev])
      setFilteredLeads(prev => [newLead, ...prev])
      
      // Reload stats
      const newStats = await crmApi.getLeadStats()
      setStats(newStats)
      
    } catch (err) {
      console.error('Error creating lead:', err)
      setError(err instanceof Error ? err.message : 'Failed to create lead')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'contacted': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'qualified': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'negotiating': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'converted': return 'bg-green-100 text-green-800 border-green-200'
      case 'lost': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'text-red-600'
      case 'medium': return 'text-yellow-600'
      case 'low': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading CRM data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button 
            onClick={loadData}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 mx-auto"
          >
            <ArrowPathIcon className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Modern Header */}
      <div className="glass-card">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
              <UsersIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white">CRM Dashboard</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Manage leads and customer relationships</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <button className="btn-primary flex items-center space-x-2">
              <PlusIcon className="w-4 h-4" />
              <span>Add Lead</span>
            </button>
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-outline flex items-center space-x-2 ${
                showFilters ? 'bg-blue-50 border-blue-300 text-blue-700' : ''
              }`}
            >
              <FunnelIcon className="w-4 h-4" />
              <span>Filters</span>
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="space-y-4 mb-6">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search leads by name, email, phone, or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            />
          </div>

          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Status</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="negotiating">Negotiating</option>
                    <option value="converted">Converted</option>
                    <option value="lost">Lost</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Urgency</label>
                  <select
                    value={urgencyFilter}
                    onChange={(e) => setUrgencyFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Urgency</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={() => {
                      setSearchTerm('')
                      setStatusFilter('all')
                      setUrgencyFilter('all')
                    }}
                    className="w-full px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
                  >
                    Clear Filters
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Enhanced Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="relative overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800/30"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-500 rounded-xl">
                  <UsersIcon className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.new_leads}</div>
                  <div className="text-sm text-blue-600/70 dark:text-blue-400/70">+{stats.leads_this_week} this week</div>
                </div>
              </div>
              <div className="text-sm font-medium text-blue-700 dark:text-blue-300">New Leads</div>
              <div className="absolute -bottom-2 -right-2 w-20 h-20 bg-blue-200/30 dark:bg-blue-700/20 rounded-full"></div>
            </motion.div>

            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="relative overflow-hidden bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-2xl p-6 border border-yellow-200 dark:border-yellow-800/30"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-yellow-500 rounded-xl">
                  <ClockIcon className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.contacted_leads + stats.qualified_leads}</div>
                  <div className="text-sm text-yellow-600/70 dark:text-yellow-400/70">In Progress</div>
                </div>
              </div>
              <div className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Active Leads</div>
              <div className="absolute -bottom-2 -right-2 w-20 h-20 bg-yellow-200/30 dark:bg-yellow-700/20 rounded-full"></div>
            </motion.div>

            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="relative overflow-hidden bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-2xl p-6 border border-green-200 dark:border-green-800/30"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-green-500 rounded-xl">
                  <StarSolidIcon className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.converted_leads}</div>
                  <div className="text-sm text-green-600/70 dark:text-green-400/70">{stats.conversion_rate}% rate</div>
                </div>
              </div>
              <div className="text-sm font-medium text-green-700 dark:text-green-300">Converted</div>
              <div className="absolute -bottom-2 -right-2 w-20 h-20 bg-green-200/30 dark:bg-green-700/20 rounded-full"></div>
            </motion.div>

            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="relative overflow-hidden bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800/30"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-purple-500 rounded-xl">
                  <CurrencyDollarIcon className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-purple-600 dark:text-purple-400">{formatCurrency(stats.total_pipeline_value / 10000000)}Cr</div>
                  <div className="text-sm text-purple-600/70 dark:text-purple-400/70">Pipeline Value</div>
                </div>
              </div>
              <div className="text-sm font-medium text-purple-700 dark:text-purple-300">Total Pipeline</div>
              <div className="absolute -bottom-2 -right-2 w-20 h-20 bg-purple-200/30 dark:bg-purple-700/20 rounded-full"></div>
            </motion.div>
          </div>
        )}

        {/* Modern Leads List */}
        <div className="glass-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-gray-800 dark:text-white">Leads Management</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {filteredLeads.length} of {leads.length} leads
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Sort by:</span>
              <select className="px-3 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option>Lead Score</option>
                <option>Date Created</option>
                <option>Last Contact</option>
                <option>Budget</option>
              </select>
            </div>
          </div>

          {filteredLeads.length === 0 ? (
            <div className="text-center py-12">
              <UsersIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No leads found</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                {searchTerm || statusFilter !== 'all' || urgencyFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Start by adding your first lead to the system'
                }
              </p>
              <button className="btn-primary">
                <PlusIcon className="w-4 h-4 mr-2" />
                Add First Lead
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredLeads.map((lead, index) => (
                <motion.div
                  key={lead.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-200 group"
                >
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    {/* Lead Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                            {lead.name.charAt(0)}
                          </div>
                          <div>
                            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">{lead.name}</h4>
                            <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                              <span className="flex items-center space-x-1">
                                <PhoneIcon className="w-4 h-4" />
                                <span>{lead.phone}</span>
                              </span>
                              <span className="flex items-center space-x-1">
                                <MapPinIcon className="w-4 h-4" />
                                <span>{lead.location_preference || 'Not specified'}</span>
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <div className="flex items-center space-x-1">
                            {[...Array(5)].map((_, i) => (
                              <StarSolidIcon 
                                key={i} 
                                className={`w-4 h-4 ${
                                  i < Math.floor(lead.score / 20) ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
                                }`} 
                              />
                            ))}
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400 ml-1">
                              {lead.score}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Budget</span>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{formatCurrency(lead.budget)}</p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Property Type</span>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{lead.property_type_preference || 'Not specified'}</p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Timeline</span>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{lead.timeline || 'Not specified'}</p>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Last Contact</span>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {lead.last_contact_date ? new Date(lead.last_contact_date).toLocaleDateString() : 'Never'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(lead.status)}`}>
                            {lead.status.charAt(0).toUpperCase() + lead.status.slice(1)}
                          </span>
                          <span className={`text-xs font-medium ${getUrgencyColor(lead.urgency)}`}>
                            {lead.urgency.toUpperCase()} PRIORITY
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {lead.source}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 lg:flex-col lg:space-x-0 lg:space-y-2">
                      <button 
                        onClick={() => {
                          setSelectedLead(lead)
                          setShowLeadModal(true)
                        }}
                        className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors duration-200"
                      >
                        <EyeIcon className="w-4 h-4" />
                        <span className="hidden sm:inline">View</span>
                      </button>
                      
                      <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors duration-200">
                        <PhoneSolidIcon className="w-4 h-4" />
                        <span className="hidden sm:inline">Call</span>
                      </button>
                      
                      <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors duration-200">
                        <ChatSolidIcon className="w-4 h-4" />
                        <span className="hidden sm:inline">Message</span>
                      </button>
                      
                      <button className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900/20 rounded-lg transition-colors duration-200">
                        <PencilIcon className="w-4 h-4" />
                        <span className="hidden sm:inline">Edit</span>
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Lead Detail Modal */}
      <AnimatePresence>
        {showLeadModal && selectedLead && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowLeadModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                    {selectedLead.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">{selectedLead.name}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Lead Details</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowLeadModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Lead Score */}
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Lead Score</h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="flex items-center space-x-1">
                        {[...Array(5)].map((_, i) => (
                          <StarSolidIcon 
                            key={i} 
                            className={`w-5 h-5 ${
                              i < Math.floor(selectedLead.score / 20) ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
                            }`} 
                          />
                        ))}
                      </div>
                      <span className="text-2xl font-bold text-gray-900 dark:text-white">{selectedLead.score}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(selectedLead.status)}`}>
                      {selectedLead.status.charAt(0).toUpperCase() + selectedLead.status.slice(1)}
                    </span>
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Contact Information</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <PhoneIcon className="w-5 h-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Phone</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{selectedLead.phone}</p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <ChatBubbleLeftRightIcon className="w-5 h-5 text-green-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{selectedLead.email}</p>
                    </div>
                  </div>
                </div>

                {/* Property Requirements */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Property Requirements</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <CurrencyDollarIcon className="w-5 h-5 text-green-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Budget</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{formatCurrency(selectedLead.budget)}</p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <MapPinIcon className="w-5 h-5 text-purple-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Location</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{selectedLead.location_preference || 'Not specified'}</p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <UsersIcon className="w-5 h-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Property Type</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{selectedLead.property_type_preference || 'Not specified'}</p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <ClockIcon className="w-5 h-5 text-orange-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Timeline</span>
                      </div>
                      <p className="text-gray-900 dark:text-white font-medium">{selectedLead.timeline}</p>
                    </div>
                  </div>
                </div>

                {/* Notes */}
                {selectedLead.notes && (
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notes</h4>
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <p className="text-gray-700 dark:text-gray-300">{selectedLead.notes}</p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button className="flex-1 btn-primary flex items-center justify-center space-x-2">
                    <PhoneSolidIcon className="w-5 h-5" />
                    <span>Call Lead</span>
                  </button>
                  <button className="flex-1 btn-outline flex items-center justify-center space-x-2">
                    <ChatSolidIcon className="w-5 h-5" />
                    <span>Send Message</span>
                  </button>
                  <button className="flex-1 btn-outline flex items-center justify-center space-x-2">
                    <PencilIcon className="w-5 h-5" />
                    <span>Edit Lead</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
