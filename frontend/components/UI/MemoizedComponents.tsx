'use client'

import React, { memo, useMemo } from 'react'
import { motion } from 'framer-motion'

// Memoized Navigation Item
interface NavItemProps {
  href: string
  label: string
  isActive?: boolean
  onClick?: () => void
  className?: string
}

export const NavItem = memo<NavItemProps>(({ 
  href, 
  label, 
  isActive = false, 
  onClick,
  className = '' 
}) => {
  return (
    <a 
      href={href}
      onClick={onClick}
      className={`${className} ${isActive ? 'font-bold' : ''}`}
    >
      {label}
    </a>
  )
})

NavItem.displayName = 'NavItem'

// Memoized Stat Card
interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>
  value: number | string
  label: string
  trend?: number
  className?: string
}

export const StatCard = memo<StatCardProps>(({ 
  icon: Icon, 
  value, 
  label, 
  trend,
  className = '' 
}) => {
  const trendColor = useMemo(() => {
    if (!trend) return ''
    return trend > 0 ? 'text-green-600' : 'text-red-600'
  }, [trend])

  const formattedValue = useMemo(() => {
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
    return value
  }, [value])

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between">
        <Icon className="w-8 h-8 text-gray-400" />
        {trend && (
          <span className={`text-sm font-medium ${trendColor}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{formattedValue}</p>
        <p className="text-sm text-gray-500 mt-1">{label}</p>
      </div>
    </div>
  )
})

StatCard.displayName = 'StatCard'

// Memoized Property Card
interface PropertyCardProps {
  property: {
    id: string
    title: string
    location: string
    price: number
    bedrooms: number
    bathrooms: number
    area: number
    image?: string
  }
  onClick?: (id: string) => void
  className?: string
}

export const PropertyCard = memo<PropertyCardProps>(({ 
  property, 
  onClick,
  className = '' 
}) => {
  const formattedPrice = useMemo(() => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(property.price)
  }, [property.price])

  const handleClick = () => {
    onClick?.(property.id)
  }

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`bg-white rounded-lg shadow-md overflow-hidden cursor-pointer ${className}`}
      onClick={handleClick}
    >
      {property.image ? (
        <img 
          src={property.image} 
          alt={property.title}
          className="w-full h-48 object-cover"
        />
      ) : (
        <div className="w-full h-48 bg-gray-200" />
      )}
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">
          {property.title}
        </h3>
        <p className="text-sm text-gray-600 mb-3">{property.location}</p>
        
        <div className="flex justify-between items-center mb-3">
          <span className="text-2xl font-bold text-blue-600">
            {formattedPrice}
          </span>
        </div>
        
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <span>{property.bedrooms} beds</span>
          <span>•</span>
          <span>{property.bathrooms} baths</span>
          <span>•</span>
          <span>{property.area} sqft</span>
        </div>
      </div>
    </motion.div>
  )
})

PropertyCard.displayName = 'PropertyCard'

// Memoized Filter Button
interface FilterButtonProps {
  label: string
  isActive: boolean
  onClick: () => void
  count?: number
  className?: string
}

export const FilterButton = memo<FilterButtonProps>(({ 
  label, 
  isActive, 
  onClick, 
  count,
  className = '' 
}) => {
  return (
    <button
      onClick={onClick}
      className={`
        px-4 py-2 rounded-full text-sm font-medium transition-colors
        ${isActive 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }
        ${className}
      `}
    >
      {label}
      {count !== undefined && (
        <span className="ml-1">({count})</span>
      )}
    </button>
  )
})

FilterButton.displayName = 'FilterButton'

// Memoized List with virtualization support
interface VirtualListProps<T> {
  items: T[]
  renderItem: (item: T, index: number) => React.ReactNode
  itemHeight: number
  containerHeight: number
  className?: string
}

export function VirtualList<T>({ 
  items, 
  renderItem, 
  itemHeight, 
  containerHeight,
  className = '' 
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = React.useState(0)

  const visibleItems = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight)
    const endIndex = Math.min(
      items.length - 1,
      Math.floor((scrollTop + containerHeight) / itemHeight)
    )

    return items.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      originalIndex: startIndex + index
    }))
  }, [items, scrollTop, itemHeight, containerHeight])

  const totalHeight = items.length * itemHeight

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }

  return (
    <div
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map(({ item, originalIndex }) => (
          <div
            key={originalIndex}
            style={{
              position: 'absolute',
              top: originalIndex * itemHeight,
              height: itemHeight,
              width: '100%'
            }}
          >
            {renderItem(item, originalIndex)}
          </div>
        ))}
      </div>
    </div>
  )
}