/**
 * CRM API Service
 * ===============
 * Service for communicating with the advanced CRM backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Lead {
  id: string
  name: string
  email: string
  phone: string
  budget: number
  property_type_preference?: string
  location_preference?: string
  timeline?: string
  urgency: 'low' | 'medium' | 'high' | 'urgent'
  source: 'website' | 'referral' | 'social_media' | 'advertisement' | 'cold_call' | 'walk_in' | 'other'
  status: 'new' | 'contacted' | 'qualified' | 'negotiating' | 'converted' | 'lost' | 'archived'
  score: number
  notes?: string
  assigned_agent_id?: string
  team_id?: string
  created_at: string
  updated_at: string
  last_contact_date?: string
  next_follow_up?: string
  conversion_value?: number
  conversion_date?: string
  activities?: LeadActivity[]
}

export interface LeadActivity {
  id: string
  lead_id: string
  activity_type: string
  description: string
  performed_by: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface LeadStats {
  total_leads: number
  new_leads: number
  contacted_leads: number
  qualified_leads: number
  converted_leads: number
  lost_leads: number
  conversion_rate: number
  average_deal_value: number
  total_pipeline_value: number
  leads_this_month: number
  leads_this_week: number
  leads_today: number
}

export interface LeadSearchFilters {
  status?: string
  urgency?: string
  source?: string
  assigned_agent_id?: string
  team_id?: string
  min_budget?: number
  max_budget?: number
  min_score?: number
  max_score?: number
  date_from?: string
  date_to?: string
  search_term?: string
}

export interface LeadSearchResult {
  leads: Lead[]
  total: number
  page: number
  per_page: number
  total_pages: number
  filters_applied: LeadSearchFilters
}

export interface Team {
  id: string
  name: string
  description?: string
  industry?: string
  size?: string
  website?: string
  phone?: string
  address?: string
  timezone: string
  owner_id: string
  status: 'active' | 'inactive' | 'suspended' | 'pending'
  members: TeamMember[]
  member_count: number
  created_at: string
  updated_at: string
  settings: Record<string, any>
}

export interface TeamMember {
  user_id: string
  email: string
  first_name: string
  last_name: string
  role: 'super_admin' | 'admin' | 'agent' | 'assistant' | 'viewer'
  permissions: string[]
  joined_at: string
  last_active?: string
  is_active: boolean
  invited_by?: string
}

export interface AnalyticsMetric {
  name: string
  value: number
  type: 'count' | 'sum' | 'average' | 'percentage' | 'ratio' | 'growth_rate'
  unit?: string
  change_percentage?: number
  change_direction?: 'up' | 'down' | 'neutral'
  previous_value?: number
  target_value?: number
  description?: string
}

export interface DashboardMetrics {
  overview_metrics: AnalyticsMetric[]
  property_analytics: any
  lead_analytics: any
  team_analytics?: any
  market_analytics?: any
  revenue_analytics?: any
  generated_at: string
  period: string
  date_range: {
    start: string
    end: string
  }
}

class CRMApiService {
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/crm`
    this.token = this.getToken()
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  private getHeaders(): HeadersInit {
    // Refresh token on each request to ensure it's current
    this.token = this.getToken()

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      if (response.status === 401) {
        // Token might be expired or invalid
        console.warn('[CRM API] 401 Unauthorized - token may be expired or invalid')
        // Clear the stored token
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token')
        }
        this.token = null
        throw new Error('Authentication failed. Please log in again.')
      }

      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Lead Management
  async createLead(leadData: Partial<Lead>): Promise<Lead> {
    const response = await fetch(`${this.baseUrl}/leads`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(leadData),
    })

    return this.handleResponse<Lead>(response)
  }

  async getLeads(filters: LeadSearchFilters = {}, page = 1, perPage = 20): Promise<LeadSearchResult> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== undefined && value !== null)
      ),
    })

    const response = await fetch(`${this.baseUrl}/leads?${params}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<LeadSearchResult>(response)
  }

  async getLead(leadId: string): Promise<Lead> {
    const response = await fetch(`${this.baseUrl}/leads/${leadId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<Lead>(response)
  }

  async updateLead(leadId: string, updateData: Partial<Lead>): Promise<Lead> {
    const response = await fetch(`${this.baseUrl}/leads/${leadId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(updateData),
    })

    return this.handleResponse<Lead>(response)
  }

  async getLeadStats(): Promise<LeadStats> {
    const response = await fetch(`${this.baseUrl}/leads/stats`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<LeadStats>(response)
  }

  // Analytics
  async getDashboardMetrics(period = 'this_month', startDate?: string, endDate?: string): Promise<DashboardMetrics> {
    const params = new URLSearchParams({
      period,
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate }),
    })

    const response = await fetch(`${this.baseUrl}/analytics/dashboard?${params}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<DashboardMetrics>(response)
  }

  // Team Management
  async createTeam(teamData: Partial<Team>): Promise<Team> {
    const response = await fetch(`${this.baseUrl}/teams`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(teamData),
    })

    return this.handleResponse<Team>(response)
  }

  async getTeam(teamId: string): Promise<Team> {
    const response = await fetch(`${this.baseUrl}/teams/${teamId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<Team>(response)
  }

  async updateTeam(teamId: string, updateData: Partial<Team>): Promise<Team> {
    const response = await fetch(`${this.baseUrl}/teams/${teamId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(updateData),
    })

    return this.handleResponse<Team>(response)
  }

  async inviteMember(teamId: string, invitation: {
    email: string
    role: string
    permissions: string[]
    message?: string
  }): Promise<any> {
    const response = await fetch(`${this.baseUrl}/teams/${teamId}/invite`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(invitation),
    })

    return this.handleResponse<any>(response)
  }

  async acceptInvitation(invitationToken: string): Promise<Team> {
    const response = await fetch(`${this.baseUrl}/teams/invitations/${invitationToken}/accept`, {
      method: 'POST',
      headers: this.getHeaders(),
    })

    return this.handleResponse<Team>(response)
  }

  async removeMember(teamId: string, memberId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${this.baseUrl}/teams/${teamId}/members/${memberId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })

    return this.handleResponse<{ success: boolean }>(response)
  }

  async getTeamStats(teamId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/teams/${teamId}/stats`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<any>(response)
  }

  async getAuditLogs(teamId: string, limit = 100, offset = 0): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    })

    const response = await fetch(`${this.baseUrl}/teams/${teamId}/audit-logs?${params}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<any[]>(response)
  }
}

// Export singleton instance
export const crmApi = new CRMApiService()
export default crmApi