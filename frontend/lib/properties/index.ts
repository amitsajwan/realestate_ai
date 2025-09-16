/**
 * Properties Module
 * =================
 * Centralized properties functionality
 */

// Export types
export type {
    AIPropertySuggestion, MarketInsight, PropertiesResponse, Property, PropertyAnalytics, PropertyCreate, PropertyFormData,
    PropertyResponse, PropertyUpdate, PublishingRequest,
    PublishingStatusResponse
} from './types';

export { PropertyStatus, PublishingStatus } from './types';

// Export API
export { propertiesAPI } from './api';

// Export manager
export { PropertiesManager, propertiesManager } from './manager';
export type { PropertiesResult, PropertiesState } from './manager';

