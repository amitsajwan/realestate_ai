import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import userEvent from '@testing-library/user-event'
import TeamManagement from '../../components/TeamManagement'

// Mock all dependencies
jest.mock('@/lib/crm-api', () => ({
  crmApi: {
    getTeams: jest.fn(),
    getTeam: jest.fn(),
    createTeam: jest.fn(),
    updateTeam: jest.fn(),
    deleteTeam: jest.fn(),
    inviteTeamMember: jest.fn(),
    acceptTeamInvitation: jest.fn(),
    removeTeamMember: jest.fn(),
    updateTeamMemberRole: jest.fn(),
  },
}))

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      email: 'admin@example.com',
      role: 'admin',
    },
  }),
}))

jest.mock('@heroicons/react/24/outline', () => ({
  __esModule: true,
  UsersIcon: (props: any) => <div data-testid="users-icon" {...props} />,
  PlusIcon: (props: any) => <div data-testid="plus-icon" {...props} />,
  UserPlusIcon: (props: any) => <div data-testid="user-plus-icon" {...props} />,
  PencilIcon: (props: any) => <div data-testid="pencil-icon" {...props} />,
  TrashIcon: (props: any) => <div data-testid="trash-icon" {...props} />,
  CheckCircleIcon: (props: any) => <div data-testid="check-circle-icon" {...props} />,
  XMarkIcon: (props: any) => <div data-testid="x-mark-icon" {...props} />,
  ExclamationTriangleIcon: (props: any) => <div data-testid="exclamation-icon" {...props} />,
  ArrowPathIcon: (props: any) => <div data-testid="arrow-path-icon" {...props} />,
  UserIcon: (props: any) => <div data-testid="user-icon" {...props} />,
  EnvelopeIcon: (props: any) => <div data-testid="envelope-icon" {...props} />,
  CalendarDaysIcon: (props: any) => <div data-testid="calendar-icon" {...props} />,
  ShieldCheckIcon: (props: any) => <div data-testid="shield-icon" {...props} />,
}))

import { crmApi } from '@/lib/crm-api'

const mockCrmApi = crmApi as jest.Mocked<typeof crmApi>

describe('Team Management Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the team management dashboard with header', async () => {
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-1',
              email: 'admin@example.com',
              role: 'admin',
              joined_at: '2024-01-01T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 1,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Team Management')).toBeInTheDocument()
        expect(screen.getByText('Manage your team members and their roles')).toBeInTheDocument()
      })
    })

    it('displays loading state initially', () => {
      mockCrmApi.getTeams.mockImplementation(() => new Promise(() => {}))

      render(<TeamManagement />)

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })

    it('displays error state when API fails', async () => {
      mockCrmApi.getTeams.mockRejectedValue(new Error('API Error'))

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })
  })

  describe('Team Display', () => {
    it('displays team statistics correctly', async () => {
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-1',
              email: 'admin@example.com',
              role: 'admin',
              joined_at: '2024-01-01T00:00:00Z',
              is_active: true,
              permissions: {},
            },
            {
              user_id: 'user-2',
              email: 'agent@example.com',
              role: 'agent',
              joined_at: '2024-01-02T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 2,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument() // Total Members
        expect(screen.getByText('2')).toBeInTheDocument() // Active Members
        expect(screen.getByText('1')).toBeInTheDocument() // Admins
      })
    })

    it('displays team members correctly', async () => {
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-1',
              email: 'admin@example.com',
              role: 'admin',
              joined_at: '2024-01-01T00:00:00Z',
              is_active: true,
              permissions: {},
            },
            {
              user_id: 'user-2',
              email: 'agent@example.com',
              role: 'agent',
              joined_at: '2024-01-02T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 2,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('admin@example.com')).toBeInTheDocument()
        expect(screen.getByText('agent@example.com')).toBeInTheDocument()
        expect(screen.getByText('ADMIN')).toBeInTheDocument()
        expect(screen.getByText('AGENT')).toBeInTheDocument()
      })
    })
  })

  describe('Team Invitation', () => {
    it('opens invite modal when invite button is clicked', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Sales Team')).toBeInTheDocument()
      })

      const inviteButton = screen.getByRole('button', { name: /invite member/i })
      await user.click(inviteButton)

      expect(screen.getByText('Invite Team Member')).toBeInTheDocument()
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument()
    })

    it('sends invitation successfully', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      const mockInvitation = {
        email: 'newmember@example.com',
        role: 'agent',
        invited_by: 'user-1',
        team_id: 'team-1',
        token: 'invitation-token',
        expires_at: '2024-01-08T00:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        status: 'pending',
      }

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)
      mockCrmApi.inviteTeamMember.mockResolvedValue(mockInvitation)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Sales Team')).toBeInTheDocument()
      })

      const inviteButton = screen.getByRole('button', { name: /invite member/i })
      await user.click(inviteButton)

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'newmember@example.com')

      const roleSelect = screen.getByLabelText(/role/i)
      await user.selectOptions(roleSelect, 'agent')

      const sendButton = screen.getByRole('button', { name: /send invitation/i })
      await user.click(sendButton)

      await waitFor(() => {
        expect(mockCrmApi.inviteTeamMember).toHaveBeenCalledWith('team-1', {
          email: 'newmember@example.com',
          role: 'agent',
        })
      })

      expect(screen.getByText(/invitation sent/i)).toBeInTheDocument()
    })

    it('closes invite modal when cancel is clicked', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Sales Team')).toBeInTheDocument()
      })

      const inviteButton = screen.getByRole('button', { name: /invite member/i })
      await user.click(inviteButton)

      expect(screen.getByText('Invite Team Member')).toBeInTheDocument()

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(screen.queryByText('Invite Team Member')).not.toBeInTheDocument()
    })
  })

  describe('Member Management', () => {
    it('changes member role successfully', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-2',
              email: 'agent@example.com',
              role: 'agent',
              joined_at: '2024-01-02T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 1,
        },
      ]

      const updatedMember = {
        user_id: 'user-2',
        email: 'agent@example.com',
        role: 'assistant',
        joined_at: '2024-01-02T00:00:00Z',
        is_active: true,
        permissions: {},
      }

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)
      mockCrmApi.updateTeamMemberRole.mockResolvedValue(updatedMember)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('agent@example.com')).toBeInTheDocument()
      })

      const roleSelect = screen.getByDisplayValue('AGENT')
      await user.selectOptions(roleSelect, 'assistant')

      await waitFor(() => {
        expect(mockCrmApi.updateTeamMemberRole).toHaveBeenCalledWith('team-1', 'user-2', 'assistant')
      })

      expect(screen.getByText(/member role updated/i)).toBeInTheDocument()
    })

    it('removes member successfully', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-2',
              email: 'agent@example.com',
              role: 'agent',
              joined_at: '2024-01-02T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 1,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)
      mockCrmApi.removeTeamMember.mockResolvedValue(undefined)

      // Mock window.confirm
      window.confirm = jest.fn(() => true)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('agent@example.com')).toBeInTheDocument()
      })

      const removeButton = screen.getByRole('button', { name: /remove/i })
      await user.click(removeButton)

      await waitFor(() => {
        expect(mockCrmApi.removeTeamMember).toHaveBeenCalledWith('team-1', 'user-2')
      })

      expect(screen.getByText(/member removed/i)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles invitation errors gracefully', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)
      mockCrmApi.inviteTeamMember.mockRejectedValue(new Error('Invitation failed'))

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Sales Team')).toBeInTheDocument()
      })

      const inviteButton = screen.getByRole('button', { name: /invite member/i })
      await user.click(inviteButton)

      const emailInput = screen.getByLabelText(/email address/i)
      await user.type(emailInput, 'newmember@example.com')

      const sendButton = screen.getByRole('button', { name: /send invitation/i })
      await user.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to send invitation/i)).toBeInTheDocument()
      })
    })

    it('handles role update errors gracefully', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [
            {
              user_id: 'user-2',
              email: 'agent@example.com',
              role: 'agent',
              joined_at: '2024-01-02T00:00:00Z',
              is_active: true,
              permissions: {},
            },
          ],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 1,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)
      mockCrmApi.updateTeamMemberRole.mockRejectedValue(new Error('Role update failed'))

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('agent@example.com')).toBeInTheDocument()
      })

      const roleSelect = screen.getByDisplayValue('AGENT')
      await user.selectOptions(roleSelect, 'assistant')

      await waitFor(() => {
        expect(screen.getByText(/failed to change member role/i)).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /invite member/i })).toBeInTheDocument()
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      const mockTeams = [
        {
          id: 'team-1',
          name: 'Sales Team',
          description: 'Main sales team',
          owner_id: 'user-1',
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          member_count: 0,
        },
      ]

      mockCrmApi.getTeams.mockResolvedValue(mockTeams)

      render(<TeamManagement />)

      await waitFor(() => {
        expect(screen.getByText('Sales Team')).toBeInTheDocument()
      })

      const inviteButton = screen.getByRole('button', { name: /invite member/i })
      inviteButton.focus()
      expect(document.activeElement).toBe(inviteButton)

      await user.keyboard('{Enter}')
      expect(screen.getByText('Invite Team Member')).toBeInTheDocument()
    })
  })
})