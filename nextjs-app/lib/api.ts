// API service layer for PropertyAI backend integration
// Refactored to match actual backend endpoints

export interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Backend Property interface (matches backend schema)
export interface Property {
  id?: number
  user_id: string
  title: string
  type?: string
  bedrooms?: string
  price?: number
  price_unit?: string
  city?: string
  area?: string
  address?: string
  carpet_area?: number
  built_up_area?: number
  floor?: string
  furnishing?: string
  possession?: string
  amenities?: string[]
  description?: string
}

// Backend User Profile interface
export interface UserProfile {
  user_id: string
  name: string
  email: string
  phone?: string
  whatsapp?: string
  company?: string
  experience_years?: number
  specialization_areas?: string[]
  tagline?: string
  social_bio?: string
  about?: string
  address?: string
  city?: string
  state?: string
  pincode?: string
  languages?: string[]
  logo_url?: string
}

// Backend Auth interfaces
export interface UserRegistration {
  name: string
  email: string
  password: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface AuthResponse {
  success: boolean
  access_token?: string
  refresh_token?: string
  user_id?: string
  message?: string
  expires_in?: number
  onboarding_completed?: boolean
}

// Dashboard Stats (matches backend response)
export interface DashboardStats {
  total_properties: number
  active_listings: number
  total_leads: number
  total_users: number
  total_views: number
  monthly_leads: number
  revenue: string
}

// AI Suggestion (matches backend response)
export interface AISuggestion {
  title: string
  price: string
  description: string
  amenities: string
  highlights?: string[]
}

// Facebook interfaces
export interface FacebookPage {
  id: string
  name: string
  access_token: string
  category: string
}

export interface FacebookPost {
  id: string
  message: string
  created_time: string
  permalink_url: string
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public response?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

class APIService {
  private readonly baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  private token: string | null = null

  // Set auth token
  setToken(token: string) {
    this.token = token
  }

  // Clear auth token
  clearToken() {
    this.token = null
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    }

    // Add auth token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const config: RequestInit = {
      headers,
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new APIError(
          errorData.detail || `HTTP error! status: ${response.status}`,
          response.status,
          undefined,
          { data: errorData }
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

  // ===== AUTHENTICATION APIs (✅ Backend Available) =====
  
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.request<any>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    
    // Transform backend response to match frontend expectations
    const authResponse: AuthResponse = {
      success: !!response.access_token,
      access_token: response.access_token,
      user_id: response.user?.id,
      expires_in: 3600, // Default 1 hour
      onboarding_completed: response.onboarding_completed
    }
    
    if (authResponse.success && authResponse.access_token) {
      this.setToken(authResponse.access_token)
    }
    
    return authResponse
  }

  async register(userData: {
    name: string
    email: string
    password: string
  }): Promise<AuthResponse> {
    const response = await this.request<any>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
    
    // Transform backend response to match frontend expectations
    const authResponse: AuthResponse = {
      success: !!response.access_token,
      access_token: response.access_token,
      user_id: response.user?.id,
      expires_in: 3600 // Default 1 hour
    }
    
    if (authResponse.success && authResponse.access_token) {
      this.setToken(authResponse.access_token)
    }
    
    return authResponse
  }

  async getCurrentUser(): Promise<APIResponse<{ user: any }>> {
    return this.request<APIResponse<{ user: any }>>('/api/v1/auth/me')
  }

  // ===== DASHBOARD APIs (✅ Backend Available) =====
  
  async getDashboardStats(): Promise<APIResponse<DashboardStats>> {
    return this.request<APIResponse<DashboardStats>>('/api/v1/dashboard/stats')
  }

  // ===== PROPERTY APIs (✅ Backend Available) =====
  
  async createProperty(propertyData: Omit<Property, 'id'>): Promise<APIResponse<Property>> {
    return this.request<APIResponse<Property>>('/api/v1/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    })
  }

  async getUserProperties(userId: string): Promise<APIResponse<Property[]>> {
    return this.request<APIResponse<Property[]>>(`/v1/properties/user/${userId}`)
  }

  async deleteProperty(propertyId: number): Promise<APIResponse> {
    return this.request<APIResponse>(`/v1/properties/${propertyId}`, {
      method: 'DELETE',
    })
  }

  // ===== AI APIs (✅ Backend Available) =====
  
  async getAIPropertySuggestions(data: {
    property_type: string
    location: string
    budget: string
    requirements: string
  }): Promise<APIResponse<AISuggestion[]>> {
    return this.request<APIResponse<AISuggestion[]>>('/api/v1/property/ai_suggest', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ===== USER PROFILE APIs (✅ Backend Available) =====
  
  async createOrUpdateProfile(profileData: UserProfile): Promise<APIResponse<UserProfile>> {
    return this.request<APIResponse<UserProfile>>('/api/v1/user/profile', {
      method: 'POST',
      body: JSON.stringify(profileData),
    })
  }

  async getUserProfile(userId: string): Promise<APIResponse<UserProfile>> {
    return this.request<APIResponse<UserProfile>>(`/api/v1/user/profile/${userId}`)
  }

  async getDefaultUserProfile(): Promise<APIResponse<UserProfile>> {
    return this.request<APIResponse<UserProfile>>('/api/v1/user/profile/default_user')
  }

  // ===== FACEBOOK APIs (✅ Backend Available) =====
  
  async getFacebookOAuthUrl(): Promise<APIResponse<{ oauth_url: string; state: string }>> {
    return this.request<APIResponse<{ oauth_url: string; state: string }>>('/api/v1/facebook/oauth')
  }

  async handleFacebookCallback(code: string, state: string): Promise<APIResponse> {
    return this.request<APIResponse>(`/api/v1/facebook/callback?code=${code}&state=${state}`)
  }

  async getFacebookPages(): Promise<APIResponse<FacebookPage[]>> {
    return this.request<APIResponse<FacebookPage[]>>('/api/v1/facebook/pages')
  }

  async getFacebookPosts(): Promise<APIResponse<FacebookPost[]>> {
    return this.request<APIResponse<FacebookPost[]>>('/api/v1/facebook/posts')
  }

  async postToFacebook(data: { page_id: string; message: string }): Promise<APIResponse> {
    return this.request<APIResponse>('/api/v1/facebook/post', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getFacebookConfig(): Promise<APIResponse<{ connected: boolean; pages_count: number }>> {
    return this.request<APIResponse<{ connected: boolean; pages_count: number }>>('/api/v1/facebook/config')
  }

  // ===== LISTINGS APIs (✅ Backend Available) =====
  
  async generateListingPost(data: {
    property_details: any
    language: string
    style: string
  }): Promise<APIResponse<{ content: string; hashtags: string[] }>> {
    return this.request<APIResponse<{ content: string; hashtags: string[] }>>('/api/v1/listings/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ===== HEALTH CHECK (✅ Backend Available) =====
  
  async healthCheck(): Promise<APIResponse<{ status: string; database: string }>> {
    return this.request<APIResponse<{ status: string; database: string }>>('/health')
  }

  // ===== MOCK APIs (❌ Backend Not Available - Using Mock Data) =====
  
  // These endpoints don't exist in the backend, so we'll provide mock implementations
  // for development purposes. In production, these should be implemented in the backend.

  async getLeads(): Promise<APIResponse<any[]>> {
    // Mock implementation - backend doesn't have leads API
    return Promise.resolve({
      success: true,
      data: [
        {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com',
          phone: '+91 98765 43210',
          status: 'new',
          source: 'Website',
          notes: 'Interested in 2BHK apartment',
          createdAt: new Date().toISOString()
        }
      ]
    })
  }

  async createLead(leadData: any): Promise<APIResponse<any>> {
    // Mock implementation
    return Promise.resolve({
      success: true,
      data: { ...leadData, id: Date.now().toString(), createdAt: new Date().toISOString() }
    })
  }

  async updateLead(id: string, leadData: any): Promise<APIResponse<any>> {
    // Mock implementation
    return Promise.resolve({
      success: true,
      data: { ...leadData, id, updatedAt: new Date().toISOString() }
    })
  }

  async getAnalytics(period: 'week' | 'month' | 'year' = 'month'): Promise<APIResponse<any>> {
    // Mock implementation
    return Promise.resolve({
      success: true,
      data: {
        period,
        views: 1247,
        leads: 23,
        conversions: 8,
        revenue: '₹45,00,000'
      }
    })
  }

  async generateAIContent(prompt: string, style: string, tone: string): Promise<APIResponse<{ content: string }>> {
    // Mock implementation - backend doesn't have this specific endpoint
    return Promise.resolve({
      success: true,
      data: {
        content: `Generated content for: "${prompt}" in ${style} style with ${tone} tone.`
      }
    })
  }

  async uploadImage(file: File): Promise<APIResponse<{ url: string }>> {
    // Mock implementation - backend doesn't have file upload endpoint
    return Promise.resolve({
      success: true,
      data: {
        url: `https://example.com/uploads/${file.name}`
      }
    })
  }

  // ===== UTILITY METHODS =====
  
  async updateOnboarding(userId: string, step: number, data: any): Promise<APIResponse> {
    // Mock implementation - backend doesn't have onboarding endpoint
    // In a real implementation, this would update the user profile
    return this.createOrUpdateProfile({
      user_id: userId,
      name: data.firstName + ' ' + data.lastName,
      email: data.email || 'user@example.com',
      ...data
    })
  }
}

export const apiService = new APIService()
export { APIError }
