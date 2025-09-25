'use client'

import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'

interface SearchResult {
    id: string
    title: string
    description: string
    type: 'property' | 'content' | 'agent' | 'post'
    href: string
    icon?: string
    metadata?: {
        price?: string
        location?: string
        status?: string
        created_at?: string
    }
}

interface GlobalSearchProps {
    className?: string
    placeholder?: string
}

export default function GlobalSearch({
    className = '',
    placeholder = "Search properties, content, agents..."
}: GlobalSearchProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [selectedIndex, setSelectedIndex] = useState(-1)

    const inputRef = useRef<HTMLInputElement>(null)
    const resultsRef = useRef<HTMLDivElement>(null)
    const router = useRouter()

    // Handle keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Cmd/Ctrl + K to open search
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                setIsOpen(true)
                setTimeout(() => inputRef.current?.focus(), 100)
            }

            // Escape to close
            if (e.key === 'Escape' && isOpen) {
                setIsOpen(false)
                setQuery('')
                setResults([])
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen])

    // Search function
    const performSearch = async (searchQuery: string) => {
        if (!searchQuery.trim()) {
            setResults([])
            return
        }

        setIsLoading(true)
        try {
            // Simulate API call - replace with actual API endpoints
            const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`)
            if (response.ok) {
                const data = await response.json()
                setResults(data.results || [])
            }
        } catch (error) {
            console.error('Search error:', error)
            // Fallback to mock data for demo
            setResults(getMockResults(searchQuery))
        } finally {
            setIsLoading(false)
        }
    }

    // Mock search results for demo
    const getMockResults = (searchQuery: string): SearchResult[] => {
        const mockProperties = [
            {
                id: '1',
                title: 'Modern 3BHK Apartment in Downtown',
                description: 'Beautiful apartment with city views',
                type: 'property' as const,
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
                description: 'Spacious villa with private garden',
                type: 'property' as const,
                href: '/properties/2',
                metadata: {
                    price: '₹1.2Cr',
                    location: 'Pune',
                    status: 'For Sale'
                }
            }
        ]

        const mockContent = [
            {
                id: '3',
                title: 'Property Marketing Post',
                description: 'AI-generated marketing content for luxury properties',
                type: 'content' as const,
                href: '/property-marketing-hub',
                metadata: {
                    created_at: '2 days ago'
                }
            }
        ]

        // Simple search logic
        const allItems = [...mockProperties, ...mockContent]
        return allItems.filter(item =>
            item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.description.toLowerCase().includes(searchQuery.toLowerCase())
        )
    }

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value
        setQuery(value)
        setSelectedIndex(-1)

        // Debounce search
        const timeoutId = setTimeout(() => {
            performSearch(value)
        }, 300)

        return () => clearTimeout(timeoutId)
    }

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) return

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault()
                setSelectedIndex(prev =>
                    prev < results.length - 1 ? prev + 1 : prev
                )
                break
            case 'ArrowUp':
                e.preventDefault()
                setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
                break
            case 'Enter':
                e.preventDefault()
                if (selectedIndex >= 0 && results[selectedIndex]) {
                    handleResultClick(results[selectedIndex])
                }
                break
        }
    }

    // Handle result click
    const handleResultClick = (result: SearchResult) => {
        router.push(result.href)
        setIsOpen(false)
        setQuery('')
        setResults([])
    }

    // Get result icon
    const getResultIcon = (type: string) => {
        switch (type) {
            case 'property':
                return '🏠'
            case 'content':
                return '📝'
            case 'agent':
                return '👤'
            case 'post':
                return '📄'
            default:
                return '📄'
        }
    }

    // Get result type label
    const getResultTypeLabel = (type: string) => {
        switch (type) {
            case 'property':
                return 'Property'
            case 'content':
                return 'Content'
            case 'agent':
                return 'Agent'
            case 'post':
                return 'Post'
            default:
                return 'Item'
        }
    }

    return (
        <div className={`relative ${className}`}>
            {/* Search Trigger Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-500" />
                <span className="hidden sm:block text-sm text-gray-500">Search...</span>
                <kbd className="hidden lg:block px-2 py-1 bg-gray-200 dark:bg-gray-600 rounded text-xs">
                    ⌘K
                </kbd>
            </button>

            {/* Search Modal */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
                        onClick={() => setIsOpen(false)}
                    >
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: -20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: -20 }}
                            className="absolute top-20 left-1/2 transform -translate-x-1/2 w-full max-w-2xl mx-4"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700">
                                {/* Search Input */}
                                <div className="flex items-center p-4 border-b border-gray-200 dark:border-gray-700">
                                    <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 mr-3" />
                                    <input
                                        ref={inputRef}
                                        type="text"
                                        value={query}
                                        onChange={handleInputChange}
                                        onKeyDown={handleKeyDown}
                                        placeholder={placeholder}
                                        className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-500 outline-none"
                                        autoComplete="off"
                                    />
                                    <button
                                        onClick={() => setIsOpen(false)}
                                        className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                    >
                                        <XMarkIcon className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Search Results */}
                                <div ref={resultsRef} className="max-h-96 overflow-y-auto">
                                    {isLoading ? (
                                        <div className="p-8 text-center">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                                            <p className="text-gray-500">Searching...</p>
                                        </div>
                                    ) : results.length > 0 ? (
                                        <div className="py-2">
                                            {results.map((result, index) => (
                                                <motion.button
                                                    key={result.id}
                                                    initial={{ opacity: 0, y: 10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ delay: index * 0.05 }}
                                                    onClick={() => handleResultClick(result)}
                                                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${index === selectedIndex ? 'bg-gray-50 dark:bg-gray-700' : ''
                                                        }`}
                                                >
                                                    <div className="flex items-start space-x-3">
                                                        <span className="text-lg flex-shrink-0">
                                                            {getResultIcon(result.type)}
                                                        </span>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center space-x-2 mb-1">
                                                                <h3 className="font-medium text-gray-900 dark:text-white truncate">
                                                                    {result.title}
                                                                </h3>
                                                                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-600 text-xs text-gray-600 dark:text-gray-300 rounded-full">
                                                                    {getResultTypeLabel(result.type)}
                                                                </span>
                                                            </div>
                                                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                                                {result.description}
                                                            </p>
                                                            {result.metadata && (
                                                                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                                                                    {result.metadata.price && (
                                                                        <span className="font-medium text-green-600">
                                                                            {result.metadata.price}
                                                                        </span>
                                                                    )}
                                                                    {result.metadata.location && (
                                                                        <span>📍 {result.metadata.location}</span>
                                                                    )}
                                                                    {result.metadata.status && (
                                                                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                                                                            {result.metadata.status}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </motion.button>
                                            ))}
                                        </div>
                                    ) : query ? (
                                        <div className="p-8 text-center">
                                            <p className="text-gray-500">No results found for "{query}"</p>
                                            <p className="text-sm text-gray-400 mt-1">
                                                Try searching for properties, content, or agents
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="p-8 text-center">
                                            <MagnifyingGlassIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                            <p className="text-gray-500 mb-2">Start typing to search</p>
                                            <p className="text-sm text-gray-400">
                                                Search across properties, content, agents, and more
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* Footer */}
                                <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600 rounded-b-xl">
                                    <div className="flex items-center justify-between text-xs text-gray-500">
                                        <div className="flex items-center space-x-4">
                                            <span>↑↓ Navigate</span>
                                            <span>↵ Select</span>
                                            <span>Esc Close</span>
                                        </div>
                                        <span>⌘K to search</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
