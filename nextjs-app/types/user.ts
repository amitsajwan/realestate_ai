/**
 * Unified TypeScript interfaces for user-related data structures
 * Ensures consistency between frontend and backend data models
 */

// Base user interface matching backend User model
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
  onboardingCompleted: boolean;
  onboardingStep: number;
  companyName?: string;
  businessType?: string;
  targetAudience?: string;
  brandingPreferences?: BrandingPreferences;
}

// Branding preferences interface
export interface BrandingPreferences {
  primaryColor?: string;
  secondaryColor?: string;
  fontFamily?: string;
  logoUrl?: string;
  brandVoice?: 'professional' | 'friendly' | 'authoritative' | 'casual';
  designStyle?: 'modern' | 'classic' | 'minimalist' | 'bold';
}

// Authentication-related interfaces
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
}

// Onboarding-related interfaces
export interface OnboardingStepData {
  step: number;
  data: Record<string, any>;
  completed?: boolean;
}

export interface OnboardingUpdateRequest {
  step?: number;
  data?: Record<string, any>;
  completed?: boolean;
}

// Branding suggestion interfaces
export interface BrandingSuggestionRequest {
  companyName: string;
  businessType: string;
  targetAudience: string;
  additionalContext?: string;
}

export interface BrandingSuggestion {
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  brandVoice: 'professional' | 'friendly' | 'authoritative' | 'casual';
  designStyle: 'modern' | 'classic' | 'minimalist' | 'bold';
  reasoning: string;
  colorPalette: {
    primary: string;
    secondary: string;
    accent: string;
    neutral: string;
  };
  typography: {
    headings: string;
    body: string;
    accent: string;
  };
}

export interface BrandingSuggestionResponse {
  suggestions: BrandingSuggestion[];
  selectedIndex?: number;
}

// Form data interfaces for components
export interface LoginFormData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  confirmPassword?: string;
}

export interface OnboardingFormData {
  companyName: string;
  businessType: string;
  targetAudience: string;
  brandingPreferences?: Partial<BrandingPreferences>;
}

// Validation error interfaces
export interface ValidationErrors {
  [key: string]: string;
}

// API response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: ValidationErrors;
}

// Data transformation utilities
export class UserDataTransformer {
  /**
   * Transform backend user data to frontend format
   */
  static fromBackend(backendUser: any): User {
    return {
      id: backendUser._id || backendUser.id,
      email: backendUser.email,
      firstName: backendUser.first_name || backendUser.firstName,
      lastName: backendUser.last_name || backendUser.lastName,
      phone: backendUser.phone,
      isVerified: backendUser.is_verified || backendUser.isVerified || false,
      createdAt: backendUser.created_at || backendUser.createdAt,
      updatedAt: backendUser.updated_at || backendUser.updatedAt,
      onboardingCompleted: backendUser.onboarding_completed || backendUser.onboardingCompleted || false,
      onboardingStep: backendUser.onboarding_step || backendUser.onboardingStep || 0,
      companyName: backendUser.company_name || backendUser.companyName,
      businessType: backendUser.business_type || backendUser.businessType,
      targetAudience: backendUser.target_audience || backendUser.targetAudience,
      brandingPreferences: backendUser.branding_preferences || backendUser.brandingPreferences,
    };
  }

  /**
   * Transform frontend user data to backend format
   */
  static toBackend(frontendUser: Partial<User>): any {
    return {
      email: frontendUser.email,
      first_name: frontendUser.firstName,
      last_name: frontendUser.lastName,
      phone: frontendUser.phone,
      is_verified: frontendUser.isVerified,
      onboarding_completed: frontendUser.onboardingCompleted,
      onboarding_step: frontendUser.onboardingStep,
      company_name: frontendUser.companyName,
      business_type: frontendUser.businessType,
      target_audience: frontendUser.targetAudience,
      branding_preferences: frontendUser.brandingPreferences,
    };
  }

  /**
   * Transform onboarding data for backend submission
   */
  static transformOnboardingData(data: OnboardingFormData): any {
    return {
      company_name: data.companyName,
      business_type: data.businessType,
      target_audience: data.targetAudience,
      branding_preferences: data.brandingPreferences,
    };
  }
}

// Type guards for runtime type checking
export const isUser = (obj: any): obj is User => {
  return obj && 
    typeof obj.id === 'string' &&
    typeof obj.email === 'string' &&
    typeof obj.firstName === 'string' &&
    typeof obj.lastName === 'string' &&
    typeof obj.isVerified === 'boolean';
};

export const isBrandingSuggestion = (obj: any): obj is BrandingSuggestion => {
  return obj &&
    typeof obj.primaryColor === 'string' &&
    typeof obj.secondaryColor === 'string' &&
    typeof obj.fontFamily === 'string' &&
    typeof obj.brandVoice === 'string' &&
    typeof obj.designStyle === 'string';
};