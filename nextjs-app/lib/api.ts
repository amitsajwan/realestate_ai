// API service layer for PropertyAI backend integration

export interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface Property {
  id: string
  title: string
  price: string
  address: string
  bedrooms: string
  bathrooms: string
  area: string
  description: string
  amenities: string
  status: 'draft' | 'published' | 'sold'
  images: string[]
  createdAt: string
  updatedAt: string
}

export interface DashboardStats {
  total_properties: number
  active_listings: number
  total_leads: number
  total_users: number
  total_views: number
  monthly_leads: number
  revenue: string
}

export interface Lead {
  id: string
  name: string
  email: string
  phone: string
  property_id?: string
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost'
  source: string
  notes: string
  createdAt: string
}

export interface AISuggestion {
  title: string
  price: string
  description: string
  amenities: string
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

class APIService {
  private baseURL = '/api'

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new APIError(
          `HTTP error! status: ${response.status}`,
          response.status
        )
      }

      const data = await response.json()
      return data
    } catch (error) {
      if (error instanceof APIError) {
        throw error
      }
      throw new APIError(
        'Network error occurred',
        0,
        'NETWORK_ERROR'
      )
    }
  }

  // Authentication APIs
  async login(email: string, password: string) {
    return this.request<APIResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(userData: {
    email: string
    password: string
    firstName: string
    lastName: string
    phone?: string
  }) {
    return this.request<APIResponse>('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async updateOnboarding(userId: string, step: number, data: any) {
    return this.request<APIResponse>('/v1/auth/onboarding', {
      method: 'PUT',
      body: JSON.stringify({ userId, step, data }),
    })
  }

  // Dashboard APIs
  async getDashboardStats(): Promise<APIResponse<DashboardStats>> {
    return this.request<APIResponse<DashboardStats>>('/v1/dashboard/stats')
  }

  // Property APIs
  async getProperties(): Promise<APIResponse<Property[]>> {
    return this.request<APIResponse<Property[]>>('/v1/properties')
  }

  async createProperty(propertyData: Omit<Property, 'id' | 'createdAt' | 'updatedAt'>): Promise<APIResponse<Property>> {
    return this.request<APIResponse<Property>>('/v1/properties', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    })
  }

  async updateProperty(id: string, propertyData: Partial<Property>): Promise<APIResponse<Property>> {
    return this.request<APIResponse<Property>>(`/v1/properties/${id}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData),
    })
  }

  async deleteProperty(id: string): Promise<APIResponse> {
    return this.request<APIResponse>(`/v1/properties/${id}`, {
      method: 'DELETE',
    })
  }

  // AI APIs
  async getAIPropertySuggestions(data: {
    property_type: string
    location: string
    budget: string
    requirements: string
  }): Promise<APIResponse<AISuggestion[]>> {
    return this.request<APIResponse<AISuggestion[]>>('/v1/property/ai_suggest', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateAIContent(prompt: string, style: string, tone: string): Promise<APIResponse<{ content: string }>> {
    return this.request<APIResponse<{ content: string }>>('/v1/ai/generate-content', {
      method: 'POST',
      body: JSON.stringify({ prompt, style, tone }),
    })
  }

  // Lead/CRM APIs
  async getLeads(): Promise<APIResponse<Lead[]>> {
    return this.request<APIResponse<Lead[]>>('/v1/leads')
  }

  async createLead(leadData: Omit<Lead, 'id' | 'createdAt'>): Promise<APIResponse<Lead>> {
    return this.request<APIResponse<Lead>>('/v1/leads', {
      method: 'POST',
      body: JSON.stringify(leadData),
    })
  }

  async updateLead(id: string, leadData: Partial<Lead>): Promise<APIResponse<Lead>> {
    return this.request<APIResponse<Lead>>(`/v1/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(leadData),
    })
  }

  // Analytics APIs
  async getAnalytics(period: 'week' | 'month' | 'year' = 'month'): Promise<APIResponse<any>> {
    return this.request<APIResponse<any>>(`/v1/analytics?period=${period}`)
  }

  // Facebook Integration APIs
  async connectFacebook(code: string): Promise<APIResponse> {
    return this.request<APIResponse>('/v1/facebook/connect', {
      method: 'POST',
      body: JSON.stringify({ code }),
    })
  }

  async getFacebookPages(): Promise<APIResponse<any[]>> {
    return this.request<APIResponse<any[]>>('/v1/facebook/pages')
  }

  async postToFacebook(pageId: string, content: string): Promise<APIResponse> {
    return this.request<APIResponse>('/v1/facebook/post', {
      method: 'POST',
      body: JSON.stringify({ pageId, content }),
    })
  }

  // File Upload APIs
  async uploadImage(file: File): Promise<APIResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('file', file)

    return this.request<APIResponse<{ url: string }>>('/v1/upload/image', {
      method: 'POST',
      headers: {
        // Don't set Content-Type for FormData
      },
      body: formData,
    })
  }

  // Health Check
  async healthCheck(): Promise<APIResponse<{ status: string; database: string }>> {
    return this.request<APIResponse<{ status: string; database: string }>>('/health')
  }
}

export const apiService = new APIService()
export { APIError }
