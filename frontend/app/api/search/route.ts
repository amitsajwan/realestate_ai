import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url)
        const query = searchParams.get('q')

        if (!query) {
            return NextResponse.json({ results: [] })
        }

        // Mock search results - replace with actual API calls
        const mockResults = [
            {
                id: '1',
                title: 'Modern 3BHK Apartment in Downtown',
                description: 'Beautiful apartment with city views and modern amenities',
                type: 'property',
                href: '/properties/1',
                metadata: {
                    price: '₹75L',
                    location: 'Downtown Mumbai',
                    status: 'For Sale'
                }
            },
            {
                id: '2',
                title: 'Luxury Villa with Garden',
                description: 'Spacious villa with private garden and pool',
                type: 'property',
                href: '/properties/2',
                metadata: {
                    price: '₹1.2Cr',
                    location: 'Pune',
                    status: 'For Sale'
                }
            },
            {
                id: '3',
                title: 'Property Marketing Post',
                description: 'AI-generated marketing content for luxury properties',
                type: 'content',
                href: '/?section=property-marketing-hub',
                metadata: {
                    created_at: '2 days ago'
                }
            },
            {
                id: '4',
                title: 'Lead Analytics Dashboard',
                description: 'Comprehensive lead tracking and conversion metrics',
                type: 'analytics',
                href: '/?section=analytics',
                metadata: {
                    updated_at: '1 day ago'
                }
            },
            {
                id: '5',
                title: 'John Doe - Real Estate Agent',
                description: 'Experienced agent specializing in luxury properties',
                type: 'agent',
                href: '/agent/john-doe',
                metadata: {
                    location: 'Mumbai',
                    experience: '5+ years'
                }
            }
        ]

        // Simple search logic
        const filteredResults = mockResults.filter(item =>
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.description.toLowerCase().includes(query.toLowerCase())
        )

        return NextResponse.json({
            results: filteredResults,
            total: filteredResults.length,
            query
        })

    } catch (error) {
        console.error('Search API error:', error)
        return NextResponse.json(
            { error: 'Search failed' },
            { status: 500 }
        )
    }
}
