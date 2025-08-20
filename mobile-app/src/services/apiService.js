/**
 * API Service
 * Centralized API request handling with error management
 */

import axios from 'axios';
import config from '../config/config';

// Create axios instance with default config
const api = axios.create({
  baseURL: config.apiUrl,
  timeout: config.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * Set auth token for API requests
 * @param {string} token - JWT token
 */
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

/**
 * Handle API errors consistently
 * @param {Error} error - Axios error object
 * @returns {Object} Standardized error object
 */
const handleApiError = (error) => {
  // Network or connection error
  if (!error.response) {
    return {
      success: false,
      status: 0,
      message: 'Network error. Please check your internet connection.',
      error,
    };
  }

  // API error with response
  return {
    success: false,
    status: error.response.status,
    message: error.response?.data?.message || 'An error occurred',
    data: error.response?.data,
    error,
  };
};

/**
 * Wrapper for API requests with consistent error handling
 * @param {Function} apiCall - Axios request function
 * @returns {Promise} Promise resolving to standardized response
 */
const apiRequest = async (apiCall) => {
  try {
    const response = await apiCall();
    return {
      success: true,
      status: response.status,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error);
  }
};

// API service methods
const apiService = {
  // Auth endpoints
  auth: {
    login: (email, password) => apiRequest(() => 
      api.post('/auth/login', { email, password })
    ),
    register: (userData) => apiRequest(() => 
      api.post('/auth/register', userData)
    ),
    getProfile: () => apiRequest(() => 
      api.get('/auth/profile')
    ),
    updateProfile: (profileData) => apiRequest(() => 
      api.put('/auth/profile', profileData)
    ),
  },
  
  // Branding endpoints
  branding: {
    getBranding: () => apiRequest(() => 
      api.get('/branding')
    ),
    updateBranding: (brandingData) => apiRequest(() => 
      api.put('/branding', brandingData)
    ),
    resetBranding: () => apiRequest(() => 
      api.post('/branding/reset')
    ),
    uploadLogo: (logoFile) => {
      const formData = new FormData();
      formData.append('logo', logoFile);
      return apiRequest(() => 
        api.post('/branding/logo', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      );
    },
    uploadAgentPhoto: (photoFile) => {
      const formData = new FormData();
      formData.append('photo', photoFile);
      return apiRequest(() => 
        api.post('/branding/agent-photo', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      );
    }
  },
  
  // Properties endpoints
  properties: {
    getAll: (params) => apiRequest(() => 
      api.get('/properties', { params })
    ),
    getById: (id) => apiRequest(() => 
      api.get(`/properties/${id}`)
    ),
    create: (propertyData) => apiRequest(() => 
      api.post('/properties', propertyData)
    ),
    update: (id, propertyData) => apiRequest(() => 
      api.put(`/properties/${id}`, propertyData)
    ),
    delete: (id) => apiRequest(() => 
      api.delete(`/properties/${id}`)
    ),
  },
  
  // Leads endpoints
  leads: {
    getAll: (params) => apiRequest(() => 
      api.get('/leads', { params })
    ),
    getById: (id) => apiRequest(() => 
      api.get(`/leads/${id}`)
    ),
    create: (leadData) => apiRequest(() => 
      api.post('/leads', leadData)
    ),
    update: (id, leadData) => apiRequest(() => 
      api.put(`/leads/${id}`, leadData)
    ),
    delete: (id) => apiRequest(() => 
      api.delete(`/leads/${id}`)
    ),
  },
  
  // Clients endpoints
  clients: {
    getAll: (params) => apiRequest(() => 
      api.get('/clients', { params })
    ),
    getById: (id) => apiRequest(() => 
      api.get(`/clients/${id}`)
    ),
    create: (clientData) => apiRequest(() => 
      api.post('/clients', clientData)
    ),
    update: (id, clientData) => apiRequest(() => 
      api.put(`/clients/${id}`, clientData)
    ),
    delete: (id) => apiRequest(() => 
      api.delete(`/clients/${id}`)
    ),
  },
  
  // System endpoints
  system: {
    health: () => apiRequest(() => 
      api.get('/health')
    ),
  },
};

export default apiService;