/**
 * Slug Utility Tests
 * ==================
 * Tests for slug generation and URL utilities
 */

import { generateAgentUrl, generatePropertyUrl, generateSlug, getAgentSlug } from '../slug'

describe('Slug Utilities', () => {
    describe('generateSlug', () => {
        it('should generate correct slug from agent name', () => {
            expect(generateSlug('Amit Sajwan')).toBe('amit-sajwan')
            expect(generateSlug('John Doe')).toBe('john-doe')
            expect(generateSlug('Jane Smith')).toBe('jane-smith')
        })

        it('should handle special characters correctly', () => {
            expect(generateSlug('Amit.Sajwan')).toBe('amit-sajwan')
            expect(generateSlug('Amit_Sajwan')).toBe('amit-sajwan')
            expect(generateSlug('Amit  Sajwan')).toBe('amit-sajwan') // Multiple spaces
        })

        it('should handle edge cases', () => {
            expect(generateSlug('')).toBe('')
            expect(generateSlug('   ')).toBe('')
            expect(generateSlug('Amit-Sajwan')).toBe('amit-sajwan')
        })
    })

    describe('getAgentSlug', () => {
        it('should use existing slug if available', () => {
            const agentData = { slug: 'amit-sajwan', agent_name: 'Amit Sajwan' }
            expect(getAgentSlug(agentData)).toBe('amit-sajwan')
        })

        it('should generate slug from agent_name if no slug', () => {
            const agentData = { agent_name: 'Amit Sajwan' }
            expect(getAgentSlug(agentData)).toBe('amit-sajwan')
        })

        it('should generate slug from full_name', () => {
            const agentData = { full_name: 'Amit Sajwan' }
            expect(getAgentSlug(agentData)).toBe('amit-sajwan')
        })

        it('should generate slug from first and last name', () => {
            const agentData = { first_name: 'Amit', last_name: 'Sajwan' }
            expect(getAgentSlug(agentData)).toBe('amit-sajwan')
        })

        it('should return default-agent for invalid data', () => {
            expect(getAgentSlug(null)).toBe('default-agent')
            expect(getAgentSlug({})).toBe('default-agent')
        })
    })

    describe('generatePropertyUrl', () => {
        it('should generate public property URL for published properties', () => {
            const url = generatePropertyUrl('68d4e0ae823db62f27689cf3', 'amit-sajwan', undefined, 'published')
            expect(url).toBe('http://localhost:3000/agent/amit-sajwan/properties/68d4e0ae823db62f27689cf3')
        })

        it('should generate dashboard URL for draft properties', () => {
            const url = generatePropertyUrl('68d4e0ae823db62f27689cf3', 'amit-sajwan', undefined, 'draft')
            expect(url).toBe('http://localhost:3000/?section=properties&property=68d4e0ae823db62f27689cf3')
        })

        it('should generate public property URL with custom base URL for published properties', () => {
            const url = generatePropertyUrl('68d4e0ae823db62f27689cf3', 'amit-sajwan', 'https://example.com', 'published')
            expect(url).toBe('https://example.com/agent/amit-sajwan/properties/68d4e0ae823db62f27689cf3')
        })

        it('should default to dashboard URL when status is not provided', () => {
            const url = generatePropertyUrl('68d4e0ae823db62f27689cf3', 'amit-sajwan')
            expect(url).toBe('http://localhost:3000/?section=properties&property=68d4e0ae823db62f27689cf3')
        })
    })

    describe('generateAgentUrl', () => {
        it('should generate correct agent URL', () => {
            const url = generateAgentUrl('amit-sajwan')
            expect(url).toBe('http://localhost:3000/agent/amit-sajwan')
        })

        it('should use custom base URL', () => {
            const url = generateAgentUrl('amit-sajwan', 'https://example.com')
            expect(url).toBe('https://example.com/agent/amit-sajwan')
        })
    })
})
