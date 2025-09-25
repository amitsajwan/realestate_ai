/**
 * Unified Authentication Service
 * =============================
 * Frontend authentication service for the unified identity system.
 * 
 * Features:
 * - Token-based authentication
 * - Automatic token refresh
 * - User-agent mapping
 * - Consistent error handling
 */

interface User {
    _id: string;
    email: string;
    username?: string;
    is_active: boolean;
    created_at: string;
}

interface AgentProfile {
    id: string;
    user_id: string;
    username: string;
    email: string;
    phone?: string;
    bio?: string;
    tagline?: string;
    profile_image_url?: string;
    slug: string;
    created_at?: string;
    updated_at?: string;
}

interface UserAgentMapping {
    user: User;
    agent_profile: AgentProfile | null;
    has_agent_profile: boolean;
}

interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}

class UnifiedAuthService {
    private baseUrl: string;
    private tokenKey = 'unified_auth_token';
    private userKey = 'unified_auth_user';

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }

    /**
     * Login with email and password
     */
    async login(email: string, password: string): Promise<AuthResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data: AuthResponse = await response.json();

            // Store token and user data
            this.setToken(data.access_token);
            this.setUser(data.user);

            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    /**
     * Register new user
     */
    async register(email: string, password: string, username?: string): Promise<AuthResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password,
                    username: username || email.split('@')[0]
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            const data: AuthResponse = await response.json();

            // Store token and user data
            this.setToken(data.access_token);
            this.setUser(data.user);

            return data;
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    /**
     * Logout user
     */
    async logout(): Promise<void> {
        try {
            const token = this.getToken();
            if (token) {
                await fetch(`${this.baseUrl}/api/v1/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage regardless of API call success
            this.clearAuth();
        }
    }

    /**
     * Get current user
     */
    async getCurrentUser(): Promise<User | null> {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/mapping`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.clearAuth();
                    return null;
                }
                throw new Error('Failed to get current user');
            }

            const data: UserAgentMapping = await response.json();
            return data.user;
        } catch (error) {
            console.error('Get current user error:', error);
            this.clearAuth();
            return null;
        }
    }

    /**
     * Get current agent profile
     */
    async getCurrentAgentProfile(): Promise<AgentProfile | null> {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/profile`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 404) {
                    return null; // No agent profile exists
                }
                if (response.status === 401) {
                    this.clearAuth();
                    return null;
                }
                throw new Error('Failed to get agent profile');
            }

            const data: AgentProfile = await response.json();
            return data;
        } catch (error) {
            console.error('Get agent profile error:', error);
            return null;
        }
    }

    /**
     * Get complete user-agent mapping
     */
    async getUserAgentMapping(): Promise<UserAgentMapping | null> {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/mapping`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.clearAuth();
                    return null;
                }
                throw new Error('Failed to get user-agent mapping');
            }

            const data: UserAgentMapping = await response.json();
            return data;
        } catch (error) {
            console.error('Get user-agent mapping error:', error);
            this.clearAuth();
            return null;
        }
    }

    /**
     * Create agent profile
     */
    async createAgentProfile(profileData: Partial<AgentProfile>): Promise<AgentProfile> {
        try {
            const token = this.getToken();
            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(profileData),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create agent profile');
            }

            const data: AgentProfile = await response.json();
            return data;
        } catch (error) {
            console.error('Create agent profile error:', error);
            throw error;
        }
    }

    /**
     * Update agent profile
     */
    async updateAgentProfile(profileData: Partial<AgentProfile>): Promise<AgentProfile> {
        try {
            const token = this.getToken();
            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(profileData),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update agent profile');
            }

            const data: AgentProfile = await response.json();
            return data;
        } catch (error) {
            console.error('Update agent profile error:', error);
            throw error;
        }
    }

    /**
     * Get agent by slug (public access)
     */
    async getAgentBySlug(slug: string): Promise<AgentProfile | null> {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/agent/public/${slug}`);

            if (!response.ok) {
                if (response.status === 404) {
                    return null;
                }
                throw new Error('Failed to get agent by slug');
            }

            const data: AgentProfile = await response.json();
            return data;
        } catch (error) {
            console.error('Get agent by slug error:', error);
            return null;
        }
    }

    /**
     * Get agent slug for current user
     */
    async getAgentSlug(): Promise<string | null> {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await fetch(`${this.baseUrl}/api/v1/agent/slug`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 404) {
                    return null; // No agent profile exists
                }
                if (response.status === 401) {
                    this.clearAuth();
                    return null;
                }
                throw new Error('Failed to get agent slug');
            }

            const data = await response.json();
            return data.slug;
        } catch (error) {
            console.error('Get agent slug error:', error);
            return null;
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return !!this.getToken();
    }

    /**
     * Get stored token
     */
    getToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem(this.tokenKey);
    }

    /**
     * Set token in storage
     */
    private setToken(token: string): void {
        if (typeof window === 'undefined') return;
        localStorage.setItem(this.tokenKey, token);
    }

    /**
     * Get stored user
     */
    getUser(): User | null {
        if (typeof window === 'undefined') return null;
        const userStr = localStorage.getItem(this.userKey);
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * Set user in storage
     */
    private setUser(user: User): void {
        if (typeof window === 'undefined') return;
        localStorage.setItem(this.userKey, JSON.stringify(user));
    }

    /**
     * Clear authentication data
     */
    private clearAuth(): void {
        if (typeof window === 'undefined') return;
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
    }

    /**
     * Get authorization header
     */
    getAuthHeader(): { Authorization: string } | {} {
        const token = this.getToken();
        return token ? { Authorization: `Bearer ${token}` } : {};
    }

    /**
     * Make authenticated API request
     */
    async authenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
        const token = this.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers,
        };

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            this.clearAuth();
            throw new Error('Authentication expired');
        }

        return response;
    }
}

// Export singleton instance
export const unifiedAuthService = new UnifiedAuthService();
export default unifiedAuthService;
