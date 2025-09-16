/**
 * Authentication API
 * ==================
 * API calls for authentication operations
 */

import { AuthResponse, LoginRequest, RegisterRequest } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AuthAPI {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    /**
     * Register a new user
     */
    async register(userData: RegisterRequest): Promise<AuthResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Registration failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Login user
     */
    async login(credentials: LoginRequest): Promise<AuthResponse> {
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'http://localhost:3000'
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Login failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get current user info
     */
    async getCurrentUser(token: string): Promise<AuthResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Get user failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Update user data
     */
    async updateUser(userData: any, token: string): Promise<AuthResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/me`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Update user failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Logout user
     */
    async logout(token: string): Promise<void> {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            }
        });

        if (!response.ok) {
            console.warn('Logout request failed:', response.status);
        }
    }
}

export const authAPI = new AuthAPI();
