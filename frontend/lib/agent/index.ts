/**
 * Agent Module
 * ============
 * Centralized agent functionality
 */

// Export types
export type {
    Agent, AgentActivity, AgentBranding, AgentContactInfo, AgentCreate, AgentDashboard, AgentDashboardResponse, AgentDashboardStats, AgentFormData, AgentInquiriesResponse, AgentInquiry, AgentLanguagePreferences,
    AgentLanguagePreferencesResponse, AgentPerformanceMetrics, AgentPublicProfile,
    AgentPublicProfileResponse, AgentResponse, AgentSocialMedia, AgentsResponse, AgentStats, AgentTask, AgentUpdate, BrandingSuggestion
} from './types';

// Export API
export { agentAPI } from './api';

// Export manager
export { AgentManager, agentManager } from './manager';
export type { AgentResult, AgentState } from './manager';

