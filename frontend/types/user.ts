/**
 * Unified TypeScript interfaces for user-related data structures
 * Ensures consistency between frontend and backend data models
 */

import { logger } from '../lib/logger';

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

export interface RegisterData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  phone?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  first_name?: string;
  last_name?: string;
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
  firstName: string;
  lastName: string;
  phone?: string;
  confirmPassword: string;
}

export interface OnboardingFormData {
  firstName: string;
  lastName: string;
  phone: string;
  company: string;
  position: string;
  licenseNumber: string;
  aiStyle: string;
  aiTone: string;
  facebookPage: string;
  termsAccepted: boolean;
  privacyAccepted: boolean;
  profilePhoto: string;
  preferences: string[];
  brandingSuggestions: {
    tagline: string;
    about: string;
    colors: {
      primary: string;
      secondary: string;
      accent: string;
    };
  } | null;
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
    // Extract ID from MongoDB object if needed
    let userId = backendUser._id || backendUser.id;
    
    // Handle MongoDB ObjectId format if present
    if (typeof userId === 'object' && userId !== null) {
      if ('$oid' in userId) {
        userId = userId.$oid;
      }
    }
    
    logger.debug('[UserDataTransformer] Transforming backend user', {
      component: 'UserDataTransformer',
      action: 'user_transformation',
      metadata: {
        backendId: backendUser._id || backendUser.id,
        transformedId: userId
      }
    });
    
    return {
      id: userId,
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
      // Map frontend form fields to backend expected format
      first_name: data.firstName,
      last_name: data.lastName,
      phone: data.phone,
      company_name: data.company,
      position: data.position,
      license_number: data.licenseNumber,
      ai_style: data.aiStyle,
      ai_tone: data.aiTone,
      facebook_page: data.facebookPage,
      terms_accepted: data.termsAccepted,
      privacy_accepted: data.privacyAccepted,
      profile_photo: data.profilePhoto,
      preferences: data.preferences,
      branding_suggestions: data.brandingSuggestions
    };
  }
  
  /**
   * Transform register data for backend submission
   */
  static transformRegisterData(data: RegisterData): RegisterRequest {
    return {
      email: data.email,
      password: data.password,
      confirm_password: data.confirmPassword,
      first_name: data.firstName,
      last_name: data.lastName,
      phone: data.phone
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