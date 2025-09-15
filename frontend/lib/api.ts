// Simple API client for the multi-post management system
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
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
  }
};