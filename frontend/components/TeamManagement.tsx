'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  UsersIcon,
  PlusIcon,
  UserPlusIcon,
  CogIcon,
  ShieldCheckIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { crmApi, Team, TeamMember, LeadStats } from '@/lib/crm-api'

interface TeamManagementProps {
  teamId?: string
}

export default function TeamManagement({ teamId }: TeamManagementProps) {
  const [team, setTeam] = useState<Team | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showMemberModal, setShowMemberModal] = useState(false)
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)
  const [inviteData, setInviteData] = useState({
    email: '',
    role: 'agent' as const,
    message: ''
  })

  useEffect(() => {
    if (teamId) {
      loadTeam()
    }
  }, [teamId])

  const loadTeam = async () => {
    if (!teamId) return
    
    try {
      setIsLoading(true)
      setError(null)
      
      const teamData = await crmApi.getTeam(teamId)
      setTeam(teamData)
      
    } catch (err) {
      console.error('Error loading team:', err)
      setError(err instanceof Error ? err.message : 'Failed to load team')
    } finally {
      setIsLoading(false)
    }
  }

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!teamId) return

    try {
      await crmApi.inviteMember(teamId, inviteData)
      setShowInviteModal(false)
      setInviteData({ email: '', role: 'agent', message: '' })
      loadTeam() // Reload team data
      
    } catch (err) {
      console.error('Error inviting member:', err)
      setError(err instanceof Error ? err.message : 'Failed to invite member')
    }
  }

  const handleRemoveMember = async (memberId: string) => {
    if (!teamId) return

    try {
      await crmApi.removeMember(teamId, memberId)
      loadTeam() // Reload team data
      
    } catch (err) {
      console.error('Error removing member:', err)
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'super_admin': return 'bg-red-100 text-red-800 border-red-200'
      case 'admin': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'agent': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'assistant': return 'bg-green-100 text-green-800 border-green-200'
      case 'viewer': return 'bg-gray-100 text-gray-800 border-gray-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'super_admin': return ShieldCheckIcon
      case 'admin': return CogIcon
      case 'agent': return UsersIcon
      case 'assistant': return UserPlusIcon
      case 'viewer': return EyeIcon
      default: return UsersIcon
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading team data...</p>
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
            onClick={loadTeam}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 mx-auto"
          >
            <ArrowPathIcon className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  if (!team) {
    return (
      <div className="text-center py-12">
        <UsersIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Team Found</h3>
        <p className="text-gray-500 dark:text-gray-400">Create a team to start collaborating with your colleagues.</p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Team Management</h1>
          <p className="text-gray-300">{team.name} • {team.member_count} members</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <UserPlusIcon className="w-5 h-5" />
          <span>Invite Member</span>
        </button>
      </div>

      {/* Team Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-500 rounded-xl">
              <UsersIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{team.member_count}</p>
              <p className="text-gray-300 text-sm">Total Members</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-500 rounded-xl">
              <CheckIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {team.members.filter(m => m.is_active).length}
              </p>
              <p className="text-gray-300 text-sm">Active Members</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-500 rounded-xl">
              <ShieldCheckIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {team.members.filter(m => m.role === 'admin' || m.role === 'super_admin').length}
              </p>
              <p className="text-gray-300 text-sm">Administrators</p>
            </div>
          </div>
        </div>
      </div>

      {/* Team Members */}
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-semibold text-white mb-6">Team Members</h2>
        
        <div className="space-y-4">
          {team.members.map((member, index) => {
            const RoleIcon = getRoleIcon(member.role)
            
            return (
              <motion.div
                key={member.user_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {member.first_name.charAt(0)}{member.last_name.charAt(0)}
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {member.first_name} {member.last_name}
                    </h3>
                    <p className="text-gray-300 text-sm">{member.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getRoleColor(member.role)}`}>
                        <RoleIcon className="w-3 h-3 inline mr-1" />
                        {member.role.replace('_', ' ').toUpperCase()}
                      </span>
                      {member.is_active ? (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 border border-green-200">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 border border-gray-200">
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setSelectedMember(member)
                      setShowMemberModal(true)
                    }}
                    className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => handleRemoveMember(member.user_id)}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Invite Member Modal */}
      <AnimatePresence>
        {showInviteModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowInviteModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Invite Team Member</h3>
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleInviteMember} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={inviteData.email}
                    onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="colleague@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Role
                  </label>
                  <select
                    value={inviteData.role}
                    onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="agent">Agent</option>
                    <option value="assistant">Assistant</option>
                    <option value="admin">Admin</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Message (Optional)
                  </label>
                  <textarea
                    value={inviteData.message}
                    onChange={(e) => setInviteData(prev => ({ ...prev, message: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Welcome to our team!"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowInviteModal(false)}
                    className="flex-1 px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Send Invitation
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}