'use client'

import { PropertyContext } from '@/types/social_publishing'
import {
    BuildingLibraryIcon,
    BuildingOfficeIcon,
    BuildingStorefrontIcon,
    HomeIcon,
    MapPinIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import { useState } from 'react'

interface PropertySelectorMobileProps {
    properties: PropertyContext[]
    onPropertySelect: (property: PropertyContext) => void
}

const PROPERTY_TYPE_ICONS = {
    'Apartment': BuildingOfficeIcon,
    'House': HomeIcon,
    'Villa': BuildingLibraryIcon,
    'Commercial': BuildingStorefrontIcon,
    'default': HomeIcon
}

export default function PropertySelectorMobile({
    properties,
    onPropertySelect
}: PropertySelectorMobileProps) {

    const [searchQuery, setSearchQuery] = useState('')

    const filteredProperties = properties.filter(property =>
        property.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        property.location.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const getPropertyIcon = (propertyType: string) => {
        const IconComponent = PROPERTY_TYPE_ICONS[propertyType as keyof typeof PROPERTY_TYPE_ICONS] ||
            PROPERTY_TYPE_ICONS.default
        return IconComponent
    }

    const formatPrice = (price: number) => {
        if (price === 0) return 'Price on request'
        if (price >= 10000000) return `₹${(price / 10000000).toFixed(1)} Cr`
        if (price >= 100000) return `₹${(price / 100000).toFixed(1)} L`
        return `₹${price.toLocaleString()}`
    }

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Search Header */}
            <div className="bg-white px-4 py-4 border-b border-gray-200">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search properties..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* Properties List */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
                {filteredProperties.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64">
                        <HomeIcon className="w-16 h-16 text-gray-300 mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            {searchQuery ? 'No properties found' : 'No properties available'}
                        </h3>
                        <p className="text-gray-500 text-center">
                            {searchQuery
                                ? 'Try adjusting your search terms'
                                : 'Add properties to start creating social media content'
                            }
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filteredProperties.map((property, index) => {
                            const IconComponent = getPropertyIcon(property.propertyType)

                            return (
                                <motion.div
                                    key={property.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    onClick={() => onPropertySelect(property)}
                                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 active:scale-95 transition-transform cursor-pointer"
                                >
                                    {/* Property Header */}
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center space-x-3 flex-1">
                                            <div className="p-2 bg-blue-50 rounded-lg">
                                                <IconComponent className="w-6 h-6 text-blue-600" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="text-lg font-semibold text-gray-900 truncate">
                                                    {property.title}
                                                </h3>
                                                <div className="flex items-center space-x-1 mt-1">
                                                    <MapPinIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                                    <p className="text-sm text-gray-600 truncate">
                                                        {property.location}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Price */}
                                        <div className="text-right">
                                            <p className="text-lg font-bold text-gray-900">
                                                {formatPrice(property.price)}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Property Details */}
                                    <div className="grid grid-cols-3 gap-4 mb-3">
                                        <div className="text-center">
                                            <p className="text-2xl font-bold text-blue-600">{property.bedrooms}</p>
                                            <p className="text-xs text-gray-500 uppercase tracking-wide">Bedrooms</p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-2xl font-bold text-green-600">{property.bathrooms}</p>
                                            <p className="text-xs text-gray-500 uppercase tracking-wide">Bathrooms</p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-2xl font-bold text-purple-600">{property.areaSqft}</p>
                                            <p className="text-xs text-gray-500 uppercase tracking-wide">Sq Ft</p>
                                        </div>
                                    </div>

                                    {/* Property Type Badge */}
                                    <div className="flex items-center justify-between">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                            {property.propertyType}
                                        </span>

                                        {/* Selection Indicator */}
                                        <div className="flex items-center space-x-1 text-blue-600">
                                            <span className="text-sm font-medium">Select</span>
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </div>

                                    {/* Features Preview */}
                                    {property.features.length > 0 && (
                                        <div className="mt-3 pt-3 border-t border-gray-100">
                                            <div className="flex flex-wrap gap-1">
                                                {property.features.slice(0, 3).map((feature, idx) => (
                                                    <span
                                                        key={idx}
                                                        className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-50 text-blue-700"
                                                    >
                                                        {feature}
                                                    </span>
                                                ))}
                                                {property.features.length > 3 && (
                                                    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-600">
                                                        +{property.features.length - 3} more
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </motion.div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Bottom Info */}
            {filteredProperties.length > 0 && (
                <div className="bg-white border-t border-gray-200 px-4 py-3">
                    <p className="text-center text-sm text-gray-500">
                        {filteredProperties.length} propert{filteredProperties.length === 1 ? 'y' : 'ies'} found
                    </p>
                </div>
            )}
        </div>
    )
}
