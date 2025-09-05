import axios from 'axios';

// Get API base URL with support for empty string (Docker/proxy setup)
const getAPIBaseURL = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  
  // If explicitly set to empty string, use relative paths (for Docker/nginx proxy)
  if (envUrl === '') {
    return '';
  }
  
  // If environment variable is set to a specific URL, use it
  if (envUrl) {
    return envUrl;
  }
  
  // Default behavior: detect environment
  // In browser context, check hostname to determine if we're in development
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    // In production/container, use relative paths through nginx proxy
    return '';
  }
  
  // Server-side: use relative paths by default (works with nginx proxy)
  return '';
};

const API_BASE_URL = getAPIBaseURL();

export const getOnboardingStep = async (userId: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/onboarding/${userId}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch onboarding step');
  }
};

export const saveOnboardingStep = async (userId: string, stepData: any) => {
  console.log('[saveOnboardingStep] Called with:', { userId, stepData });
  try {
    const response = await axios.post(`${API_BASE_URL}/onboarding/${userId}`, stepData);
    console.log('[saveOnboardingStep] Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('[saveOnboardingStep] Error:', error);
    throw new Error('Failed to save onboarding step');
  }
};

export const completeOnboarding = async (userId: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/onboarding/${userId}/complete`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to complete onboarding');
  }
};

export const validateOnboardingData = (step: number, data: any): boolean => {
  switch (step) {
    case 1:
      return data.firstName?.trim() && data.lastName?.trim();
    case 2:
      return data.company?.trim() && data.position?.trim();
    case 3:
      return data.aiStyle && data.aiTone;
    case 5:
      return data.termsAccepted && data.privacyAccepted;
    default:
      return true;
  }
};