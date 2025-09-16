/**
 * Agent Manager
 * =============
 * Centralized state management for agent functionality
 */

import { logger } from '../logger';
import { agentAPI } from './api';
import {
    Agent,
    AgentCreate,
    AgentDashboard,
    AgentInquiry,
    AgentLanguagePreferences,
    AgentUpdate,
    BrandingSuggestion
} from './types';

export interface AgentState {
    agent: Agent | null;
    dashboard: AgentDashboard | null;
    inquiries: AgentInquiry[];
    languagePreferences: AgentLanguagePreferences | null;
    isLoading: boolean;
    error: string | null;
}

export interface AgentResult {
    success: boolean;
    data?: Agent | AgentDashboard | AgentInquiry[] | AgentLanguagePreferences | BrandingSuggestion;
    error?: string;
}

export class AgentManager {
    private state: AgentState = {
        agent: null,
        dashboard: null,
        inquiries: [],
        languagePreferences: null,
        isLoading: false,
        error: null
    };

    private subscribers: Set<(state: AgentState) => void> = new Set();

    /**
     * Get current state
     */
    getState(): AgentState {
        return { ...this.state };
    }

    /**
     * Subscribe to state changes
     */
    subscribe(callback: (state: AgentState) => void): () => void {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }

    /**
     * Update state and notify subscribers
     */
    private setState(newState: Partial<AgentState>): void {
        this.state = { ...this.state, ...newState };
        this.subscribers.forEach(callback => callback(this.state));
    }

    /**
     * Load agent profile
     */
    async loadAgentProfile(): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.getAgentProfile();

            if (response.success && response.data) {
                this.setState({
                    agent: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load agent profile');
            }
        } catch (error) {
            logger.error('[AgentManager] Load agent profile error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Create agent profile
     */
    async createAgentProfile(agentData: AgentCreate): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.createAgentProfile(agentData);

            if (response.success && response.data) {
                this.setState({
                    agent: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to create agent profile');
            }
        } catch (error) {
            logger.error('[AgentManager] Create agent profile error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Update agent profile
     */
    async updateAgentProfile(agentData: AgentUpdate): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.updateAgentProfile(agentData);

            if (response.success && response.data) {
                this.setState({
                    agent: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to update agent profile');
            }
        } catch (error) {
            logger.error('[AgentManager] Update agent profile error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Load agent dashboard
     */
    async loadAgentDashboard(): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.getAgentDashboard();

            if (response.success && response.data) {
                this.setState({
                    dashboard: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load agent dashboard');
            }
        } catch (error) {
            logger.error('[AgentManager] Load agent dashboard error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Load agent inquiries
     */
    async loadAgentInquiries(skip: number = 0, limit: number = 100): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.getAgentInquiries(skip, limit);

            if (response.success && response.data) {
                this.setState({
                    inquiries: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load agent inquiries');
            }
        } catch (error) {
            logger.error('[AgentManager] Load agent inquiries error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Load agent language preferences
     */
    async loadAgentLanguagePreferences(): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.getAgentLanguagePreferences();

            if (response.success && response.data) {
                this.setState({
                    languagePreferences: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load agent language preferences');
            }
        } catch (error) {
            logger.error('[AgentManager] Load agent language preferences error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Update agent language preferences
     */
    async updateAgentLanguagePreferences(preferences: Partial<AgentLanguagePreferences>): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.updateAgentLanguagePreferences(preferences);

            if (response.success && response.data) {
                this.setState({
                    languagePreferences: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to update agent language preferences');
            }
        } catch (error) {
            logger.error('[AgentManager] Update agent language preferences error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Get branding suggestions
     */
    async getBrandingSuggestions(agentData: any): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.getBrandingSuggestions(agentData);

            this.setState({ isLoading: false, error: null });
            return response;
        } catch (error) {
            logger.error('[AgentManager] Get branding suggestions error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Complete agent onboarding
     */
    async completeAgentOnboarding(onboardingData: any): Promise<AgentResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await agentAPI.completeAgentOnboarding(onboardingData);

            if (response.success && response.data) {
                this.setState({
                    agent: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to complete agent onboarding');
            }
        } catch (error) {
            logger.error('[AgentManager] Complete agent onboarding error', {
                errorDetails: error instanceof Error ? error.message : String(error)
            });
            this.setState({
                isLoading: false,
                error: error instanceof Error ? error.message : String(error)
            });
            return { success: false, error: error instanceof Error ? error.message : String(error) };
        }
    }

    /**
     * Clear error
     */
    clearError(): void {
        this.setState({ error: null });
    }

    /**
     * Reset state
     */
    reset(): void {
        this.setState({
            agent: null,
            dashboard: null,
            inquiries: [],
            languagePreferences: null,
            isLoading: false,
            error: null
        });
    }
}

export const agentManager = new AgentManager();
