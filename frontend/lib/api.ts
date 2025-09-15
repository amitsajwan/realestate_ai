// Simple API client for the multi-post management system
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

export const api = {
  // Enhanced Post Management API
  enhancedPosts: {
    create: async (postData: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(postData)
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    get: async (filters: any = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/?${params.toString()}`, {
        headers: getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    getById: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}`, {
        headers: getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    update: async (postId: string, updates: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates)
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    delete: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    publish: async (postId: string, channels: string[] = []) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}/publish`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ channels })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    schedule: async (postId: string, scheduledAt: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}/schedule`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ scheduled_at: scheduledAt })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    getAnalytics: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/${postId}/analytics`, {
        headers: getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }
  },

  // Enhanced Templates API
  enhancedTemplates: {
    create: async (templateData: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/templates/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(templateData)
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    },

    get: async (filters: any = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
      const response = await fetch(`${API_BASE_URL}/api/v1/enhanced-posts/posts/templates/?${params.toString()}`, {
        headers: getAuthHeaders()
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }
  },

  posts: {
    create: async (postData: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData)
      });
      return response.json();
    },

    get: async (filters: any = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, String(value));
          }
        }
      });
      const response = await fetch(`${API_BASE_URL}/api/v1/posts?${params.toString()}`);
      return response.json();
    },

    getById: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}`);
      return response.json();
    },

    update: async (postId: string, updates: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      return response.json();
    },

    delete: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}`, {
        method: 'DELETE'
      });
      return response.json();
    },

    publish: async (postId: string, channels: string[]) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channels })
      });
      return response.json();
    },

    getAnalytics: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/analytics`);
      return response.json();
    },

    generateAIContent: async (data: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/generate-ai-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return response.json();
    },

    unpublish: async (postId: string, channels: string[]) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/unpublish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channels })
      });
      return response.json();
    },

    getAiSuggestions: async (postId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/ai-suggestions`);
      return response.json();
    }
  },

  templates: {
    create: async (templateData: any) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(templateData)
      });
      return response.json();
    },

    get: async (filters: any = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
      const response = await fetch(`${API_BASE_URL}/api/v1/templates?${params.toString()}`);
      return response.json();
    }
  },

  properties: {
    get: async () => {
      const response = await fetch(`${API_BASE_URL}/api/v1/properties`);
      return response.json();
    }
  },

  getDashboardStats: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/stats`);
    return response.json();
  },

  getFacebookStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/facebook/status`);
    return response.json();
  },

  getFacebookLoginUrl: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/facebook/login`);
    return response.json();
  },

  getProperties: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties`);
    return response.json();
  },

  getPublishingStatus: async (propertyId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties/${propertyId}/publishing-status`);
    return response.json();
  },

  publishProperty: async (propertyId: string, publishData: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties/${propertyId}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(publishData)
    });
    return response.json();
  },

  unpublishProperty: async (propertyId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties/${propertyId}/unpublish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return response.json();
  },

  getBrandingSuggestions: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/branding/suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  getUserProfile: async (userId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/profile`);
    return response.json();
  },

  updateUserProfile: async (userId: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  deleteProperty: async (propertyId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties/${propertyId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  getAgentPublicProfile: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/profile`);
    return response.json();
  },

  updateAgentPublicProfile: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  getAgentPublicStats: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/public/stats`);
    return response.json();
  },

  getAgentProfile: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/agent/profile`);
    return response.json();
  },

  getAIPropertySuggestions: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties/ai-suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  uploadImages: async (formData: FormData) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/upload/images`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  },

  getCurrentUser: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: getAuthHeaders()
    });
    return response.json();
  },

  login: async (credentials: { email: string; password: string }) => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    return response.json();
  },

  register: async (userData: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },

  logout: async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: 'POST'
    });
    return response.json();
  },

  createProperty: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/properties`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};

export const apiService = api;