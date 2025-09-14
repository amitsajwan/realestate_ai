'use client'

import { apiService } from '@/lib/api'
import {
  BuildingOfficeIcon,
  ChartBarIcon,
  CheckCircleIcon,
  EnvelopeIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  GlobeAltIcon,
  PencilIcon,
  PhoneIcon
} from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

interface AgentPublicProfile {
  id: string
  agent_name: string
  slug: string
  bio: string
  photo: string
  phone: string
  email: string
  office_address: string
  specialties: string[]
  experience: string
  languages: string[]
  is_active: boolean
  is_public: boolean
  view_count: number
  contact_count: number
  created_at: string
  updated_at: string
}

interface PublicWebsiteStats {
  total_views: number
  total_contacts: number
  properties_count: number
  recent_inquiries: number
}

export default function PublicWebsiteManagement() {
  const [profile, setProfile] = useState<AgentPublicProfile | null>(null)
  const [stats, setStats] = useState<PublicWebsiteStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    agent_name: '',
    bio: '',
    phone: '',
    email: '',
    office_address: '',
    specialties: [] as string[],
    experience: '',
    languages: [] as string[],
    is_public: true
  })

  useEffect(() => {
    loadPublicProfile()
    loadStats()
  }, [])


  const loadPublicProfile = async () => {
    try {
      setIsLoading(true)
      const response = await apiService.getAgentPublicProfile()
      if (response.success) {
        const data = response.data

        // Map API data to frontend format
        const mappedProfile = {
          agent_name: `${data.first_name || ''} ${data.last_name || ''}`.trim() || '',
          bio: data.professional_bio || '',
          phone: data.phone || '',
          email: data.email || '',
          office_address: data.office_address || '',
          specialties: data.specialization_areas ? data.specialization_areas.split(',').map(s => s.trim()) : [],
          experience: data.experience || '',
          languages: data.languages || [],
          is_public: data.is_public || false
        }

        setProfile(mappedProfile) // Set the mapped data as profile
        setEditForm(mappedProfile) // Also set as edit form
      } else {
        console.error('Failed to load public profile:', response)
        toast.error('Failed to load public profile')
      }
    } catch (error) {
      console.error('Error loading public profile:', error)
      toast.error('Failed to load public profile')
    } finally {
      setIsLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await apiService.getAgentPublicStats()
      if (response.success) {
        const data = response.data
        console.log('Public stats data:', data) // Debug log
        setStats(data)
      } else {
        console.error('Failed to load stats:', response)
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleSaveProfile = async () => {
    try {
      const response = await apiService.updateAgentPublicProfile(editForm)

      if (response.success) {
        toast.success('Public profile updated successfully!')
        setIsEditing(false)
        loadPublicProfile()
      } else {
        throw new Error('Failed to update profile')
      }
    } catch (error) {
      toast.error('Failed to update public profile')
    }
  }

  const handleSpecialtyChange = (specialty: string, checked: boolean) => {
    if (checked) {
      setEditForm(prev => ({
        ...prev,
        specialties: [...prev.specialties, specialty]
      }))
    } else {
      setEditForm(prev => ({
        ...prev,
        specialties: prev.specialties.filter(s => s !== specialty)
      }))
    }
  }

  const handleLanguageChange = (language: string, checked: boolean) => {
    if (checked) {
      setEditForm(prev => ({
        ...prev,
        languages: [...prev.languages, language]
      }))
    } else {
      setEditForm(prev => ({
        ...prev,
        languages: prev.languages.filter(l => l !== language)
      }))
    }
  }

  const getPublicWebsiteUrl = () => {
    if (profile?.slug) {
      return `${window.location.origin}/agent/${profile.slug}`
    }
    return null
  }


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" data-testid="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Public Website Management</h2>
          <p className="text-gray-600 mt-1">Manage your public agent website and profile</p>
        </div>
        <div className="flex items-center space-x-3">
          {profile?.is_public && getPublicWebsiteUrl() && (
            <a
              href={getPublicWebsiteUrl() || undefined}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <EyeIcon className="w-4 h-4 mr-2" />
              View Public Site
            </a>
          )}
          <button
            onClick={() => {
              if (!isEditing && profile) {
                // When entering edit mode, populate form with current profile data
                setEditForm({
                  agent_name: profile.agent_name || '',
                  bio: profile.bio || '',
                  phone: profile.phone || '',
                  email: profile.email || '',
                  office_address: profile.office_address || '',
                  specialties: profile.specialties || [],
                  experience: profile.experience || '',
                  languages: profile.languages || [],
                  is_public: profile.is_public || false
                })
              }
              setIsEditing(!isEditing)
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <PencilIcon className="w-4 h-4 mr-2" />
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </button>
        </div>
      </div>


      {/* Status Banner */}
      <div className={`p-4 rounded-lg ${profile?.is_public ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
        <div className="flex items-center">
          {profile?.is_public ? (
            <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
          ) : (
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 mr-2" />
          )}
          <div>
            <h3 className={`font-medium ${profile?.is_public ? 'text-green-800' : 'text-yellow-800'}`}>
              {profile?.is_public ? 'Public Website Active' : 'Public Website Inactive'}
            </h3>
            <p className={`text-sm ${profile?.is_public ? 'text-green-600' : 'text-yellow-600'}`}>
              {profile?.is_public
                ? 'Your public website is live and visible to visitors'
                : 'Your public website is not visible to visitors. Enable it to start receiving leads.'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <EyeIcon className="w-8 h-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Views</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_views}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <EnvelopeIcon className="w-8 h-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Contacts</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_contacts}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <ChartBarIcon className="w-8 h-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Public Properties</p>
                <p className="text-2xl font-bold text-gray-900">{stats.properties_count}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center">
              <PhoneIcon className="w-8 h-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Recent Inquiries</p>
                <p className="text-2xl font-bold text-gray-900">{stats.recent_inquiries}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Profile Form */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Public Profile Settings</h3>
          <p className="text-gray-600 mt-1">Configure how your profile appears on your public website</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Public Status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium text-gray-900">Public Website Status</h4>
              <p className="text-sm text-gray-600">Make your website visible to the public</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isEditing ? editForm.is_public : (profile?.is_public || editForm.is_public || false)}
                onChange={(e) => setEditForm(prev => ({ ...prev, is_public: e.target.checked }))}
                className="sr-only peer"
                disabled={!isEditing}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Agent Name *
              </label>
              <input
                key={`agent_name_${profile?.agent_name || 'empty'}`}
                type="text"
                value={isEditing ? editForm.agent_name : (profile?.agent_name || '')}
                onChange={(e) => setEditForm(prev => ({ ...prev, agent_name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your professional name"
                readOnly={!isEditing}
              />
              {/* Debug info */}
              <div className="text-xs text-gray-500 mt-1">
                Debug: profile={JSON.stringify(profile)}, editForm={JSON.stringify(editForm)}, isEditing={isEditing}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                key={`email_${profile?.email || 'empty'}`}
                type="email"
                value={isEditing ? editForm.email : (profile?.email || '')}
                onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="your.email@example.com"
                readOnly={!isEditing}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <input
                key={`phone_${profile?.phone || 'empty'}`}
                type="tel"
                value={isEditing ? editForm.phone : (profile?.phone || '')}
                onChange={(e) => setEditForm(prev => ({ ...prev, phone: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="+1 (555) 123-4567"
                readOnly={!isEditing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Office Address
              </label>
              <input
                type="text"
                value={isEditing ? editForm.office_address : (profile?.office_address || '')}
                onChange={(e) => setEditForm(prev => ({ ...prev, office_address: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="123 Main St, City, State"
                readOnly={!isEditing}
              />
            </div>
          </div>

          {/* Bio */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Professional Bio
            </label>
            <textarea
              rows={4}
              value={isEditing ? editForm.bio : (profile?.bio || '')}
              onChange={(e) => setEditForm(prev => ({ ...prev, bio: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Tell visitors about your experience, specialties, and what makes you unique..."
              readOnly={!isEditing}
            />
          </div>

          {/* Experience */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Experience
            </label>
            <input
              type="text"
              value={isEditing ? editForm.experience : (profile?.experience || '')}
              onChange={(e) => setEditForm(prev => ({ ...prev, experience: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., 10+ years in real estate, Certified Realtor"
              readOnly={!isEditing}
            />
          </div>

          {/* Specialties */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Specialties
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {['Residential', 'Commercial', 'Luxury', 'Investment', 'First-time Buyers', 'Relocation'].map((specialty) => (
                <label key={specialty} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isEditing ? editForm.specialties.includes(specialty) : (profile?.specialties?.includes(specialty) || editForm.specialties.includes(specialty) || false)}
                    onChange={(e) => handleSpecialtyChange(specialty, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    disabled={!isEditing}
                  />
                  <span className="ml-2 text-sm text-gray-700">{specialty}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Languages */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Languages
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {['English', 'Spanish', 'French', 'Mandarin', 'Hindi', 'Arabic'].map((language) => (
                <label key={language} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isEditing ? editForm.languages.includes(language) : (profile?.languages?.includes(language) || editForm.languages.includes(language) || false)}
                    onChange={(e) => handleLanguageChange(language, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    disabled={!isEditing}
                  />
                  <span className="ml-2 text-sm text-gray-700">{language}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Save Button */}
          {isEditing && (
            <div className="flex justify-end pt-6 border-t border-gray-200">
              <button
                onClick={handleSaveProfile}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/properties"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <BuildingOfficeIcon className="w-6 h-6 text-blue-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">Manage Properties</h4>
                <p className="text-sm text-gray-600">Add or edit public properties</p>
              </div>
            </a>
            <a
              href="/crm"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <EnvelopeIcon className="w-6 h-6 text-green-500 mr-3" />
              <div>
                <h4 className="font-medium text-gray-900">View Inquiries</h4>
                <p className="text-sm text-gray-600">Check contact form submissions</p>
              </div>
            </a>
            {getPublicWebsiteUrl() && (
              <a
                href={getPublicWebsiteUrl() || undefined}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <GlobeAltIcon className="w-6 h-6 text-purple-500 mr-3" />
                <div>
                  <h4 className="font-medium text-gray-900">Preview Website</h4>
                  <p className="text-sm text-gray-600">See how visitors see your site</p>
                </div>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}