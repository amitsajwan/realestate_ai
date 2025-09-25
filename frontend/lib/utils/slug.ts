/**
 * Slug Utility Functions
 * =====================
 * Centralized slug generation and validation utilities
 * Ensures consistency across the application
 */

/**
 * Generate a URL-safe slug from a string
 * Uses the same logic as the backend for consistency
 */
export function generateSlug(text: string): string {
    if (!text) return ''

    return text
        .toLowerCase()
        .replace(/\s+/g, '-')      // Replace spaces with hyphens
        .replace(/\./g, '-')       // Replace dots with hyphens
        .replace(/_/g, '-')        // Replace underscores with hyphens
        .replace(/[^a-z0-9-]/g, '') // Remove any other special characters
        .replace(/-+/g, '-')       // Replace multiple hyphens with single hyphen
        .replace(/^-|-$/g, '')     // Remove leading/trailing hyphens
}

/**
 * Validate if a slug is properly formatted
 */
export function isValidSlug(slug: string): boolean {
    if (!slug) return false

    // Check if slug contains only lowercase letters, numbers, and hyphens
    const slugRegex = /^[a-z0-9-]+$/
    return slugRegex.test(slug) && !slug.startsWith('-') && !slug.endsWith('-')
}

/**
 * Get agent slug from various data sources
 * Prioritizes existing slug, falls back to generating from name
 */
export function getAgentSlug(agentData: any): string {
    if (!agentData) return 'default-agent'

    // Use existing slug if available
    if (agentData.slug && isValidSlug(agentData.slug)) {
        return agentData.slug
    }

    // Generate from agent name
    if (agentData.agent_name) {
        return generateSlug(agentData.agent_name)
    }

    // Generate from full name
    if (agentData.full_name) {
        return generateSlug(agentData.full_name)
    }

    // Generate from first and last name
    if (agentData.first_name || agentData.last_name) {
        const fullName = `${agentData.first_name || ''} ${agentData.last_name || ''}`.trim()
        if (fullName) {
            return generateSlug(fullName)
        }
    }

    return 'default-agent'
}

/**
 * Generate property URL for public sharing
 * Uses agent-based URL format for consistency
 * Only generates public URLs for published properties
 */
export function generatePropertyUrl(propertyId: string, agentSlug: string, baseUrl?: string, propertyStatus?: string): string {
    const origin = baseUrl || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000')

    // Only generate public URLs for published properties
    if (propertyStatus === 'published') {
        return `${origin}/agent/${agentSlug}/properties/${propertyId}`
    }

    // For draft properties, return dashboard URL instead
    return `${origin}/?section=properties&property=${propertyId}`
}

/**
 * Generate agent public URL
 */
export function generateAgentUrl(agentSlug: string, baseUrl?: string): string {
    const origin = baseUrl || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000')
    return `${origin}/agent/${agentSlug}`
}
