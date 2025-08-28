import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

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