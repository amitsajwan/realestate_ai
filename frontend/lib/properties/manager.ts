/**
 * Properties Manager
 * ==================
 * Centralized state management for properties
 */

import { logger } from '../logger';
import { propertiesAPI } from './api';
import { AIPropertySuggestion, Property, PropertyCreate, PropertyUpdate } from './types';

export interface PropertiesState {
    properties: Property[];
    currentProperty: Property | null;
    isLoading: boolean;
    error: string | null;
    totalCount: number;
}

export interface PropertiesResult {
    success: boolean;
    data?: Property | Property[];
    error?: string;
}

export class PropertiesManager {
    private state: PropertiesState = {
        properties: [],
        currentProperty: null,
        isLoading: false,
        error: null,
        totalCount: 0
    };

    private subscribers: Set<(state: PropertiesState) => void> = new Set();

    /**
     * Get current state
     */
    getState(): PropertiesState {
        return { ...this.state };
    }

    /**
     * Subscribe to state changes
     */
    subscribe(callback: (state: PropertiesState) => void): () => void {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }

    /**
     * Update state and notify subscribers
     */
    private setState(newState: Partial<PropertiesState>): void {
        this.state = { ...this.state, ...newState };
        this.subscribers.forEach(callback => callback(this.state));
    }

    /**
     * Load all properties
     */
    async loadProperties(skip: number = 0, limit: number = 100): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.getProperties(skip, limit);

            if (response.success && response.data) {
                this.setState({
                    properties: response.data,
                    totalCount: response.total || response.data.length,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load properties');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Load properties error', {
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
     * Load a specific property
     */
    async loadProperty(propertyId: string): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.getProperty(propertyId);

            if (response.success && response.data) {
                this.setState({
                    currentProperty: response.data,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to load property');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Load property error', {
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
     * Create a new property
     */
    async createProperty(propertyData: PropertyCreate): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.createProperty(propertyData);

            if (response.success && response.data) {
                // Add to properties list
                const currentState = this.getState();
                this.setState({
                    properties: [response.data!, ...currentState.properties],
                    totalCount: currentState.totalCount + 1,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to create property');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Create property error', {
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
     * Update an existing property
     */
    async updateProperty(propertyId: string, propertyData: PropertyUpdate): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.updateProperty(propertyId, propertyData);

            if (response.success && response.data) {
                // Update in properties list
                const currentState = this.getState();
                this.setState({
                    properties: currentState.properties.map((p: Property) =>
                        p.id === propertyId ? response.data! : p
                    ),
                    currentProperty: currentState.currentProperty?.id === propertyId ? response.data! : currentState.currentProperty,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to update property');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Update property error', {
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
     * Delete a property
     */
    async deleteProperty(propertyId: string): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.deleteProperty(propertyId);

            if (response.success) {
                // Remove from properties list
                const currentState = this.getState();
                this.setState({
                    properties: currentState.properties.filter((p: Property) => p.id !== propertyId),
                    totalCount: currentState.totalCount - 1,
                    currentProperty: currentState.currentProperty?.id === propertyId ? null : currentState.currentProperty,
                    isLoading: false,
                    error: null
                });
                return { success: true };
            } else {
                throw new Error(response.error || 'Failed to delete property');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Delete property error', {
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
     * Get AI suggestions for a property
     */
    async getAIPropertySuggestions(propertyId: string, data: any): Promise<{ success: boolean; data?: AIPropertySuggestion; error?: string }> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.getAIPropertySuggestions(propertyId, data);

            this.setState({ isLoading: false, error: null });
            return response;
        } catch (error) {
            logger.error('[PropertiesManager] Get AI suggestions error', {
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
     * Search properties
     */
    async searchProperties(query: string, filters?: any): Promise<PropertiesResult> {
        try {
            this.setState({ isLoading: true, error: null });

            const response = await propertiesAPI.searchProperties(query, filters);

            if (response.success && response.data) {
                this.setState({
                    properties: response.data,
                    totalCount: response.total || response.data.length,
                    isLoading: false,
                    error: null
                });
                return { success: true, data: response.data };
            } else {
                throw new Error(response.error || 'Failed to search properties');
            }
        } catch (error) {
            logger.error('[PropertiesManager] Search properties error', {
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
     * Clear current property
     */
    clearCurrentProperty(): void {
        this.setState({ currentProperty: null });
    }

    /**
     * Clear error
     */
    clearError(): void {
        this.setState({ error: null });
    }
}

export const propertiesManager = new PropertiesManager();
