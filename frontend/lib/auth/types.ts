/**
 * Authentication Types
 * ===================
 * Centralized type definitions for the auth module
 */

export interface User {
    id: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    is_verified: boolean;
    firstName: string | null;
    lastName: string | null;
    phone: string | null;
    company: string | null;
    onboardingCompleted: boolean;
    onboardingStep: number;
    created_at: string;
    updated_at: string;
}

export interface AuthState {
    isAuthenticated: boolean;
    user: User | null;
    token: string | null;
    refreshToken: string | null;
    isLoading: boolean;
    error: string | null;
}

export interface AuthResult {
    success: boolean;
    user?: User;
    error?: string;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
    firstName?: string;
    lastName?: string;
    phone?: string;
    company?: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    phone?: string;
    company?: string;
}

export interface AuthResponse {
    user?: User;
    accessToken?: string;
    access_token?: string;
    token_type?: string;
    refreshToken?: string;
    // Direct user properties (for /me endpoint)
    id?: string;
    email?: string;
    is_active?: boolean;
    is_superuser?: boolean;
    is_verified?: boolean;
    first_name?: string | null;
    last_name?: string | null;
    phone?: string | null;
    company?: string | null;
    onboarding_completed?: boolean;
    onboarding_step?: number;
    onboardingCompleted?: boolean;
    onboardingStep?: number;
    created_at?: string;
    updated_at?: string;
}

export interface LoginFormData {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    phone: string;
    confirmPassword: string;
}

export interface ValidationErrors {
    [key: string]: string;
}

export interface BrandingSuggestion {
    tagline: string;
    about: string;
    primary_color: string;
    secondary_color: string;
    font_family: string;
    logo_style: string;
    colorPalette: {
        primary: string;
        secondary: string;
        accent: string;
    };
}
