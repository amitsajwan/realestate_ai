'use client'

import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { useMemo } from 'react'

interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ReactNode
  isActive?: boolean
}

interface BreadcrumbNavigationProps {
  className?: string
  showHome?: boolean
  customItems?: BreadcrumbItem[]
}

export default function BreadcrumbNavigation({
  className = '',
  showHome = true,
  customItems
}: BreadcrumbNavigationProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const breadcrumbs = useMemo(() => {
    if (customItems) {
      return customItems
    }

    const segments = pathname.split('/').filter(Boolean)
    const items: BreadcrumbItem[] = []

    // Add home if requested
    if (showHome) {
      items.push({
        label: 'Dashboard',
        href: '/',
        icon: <HomeIcon className="w-4 h-4" />
      })
    }

    // Build breadcrumbs from path segments
    let currentPath = ''
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const isLast = index === segments.length - 1

      // Skip certain segments
      if (segment === 'app' || segment === 'api') return

      // Handle special cases
      let label = segment
      let href = isLast ? undefined : currentPath

      // Handle dynamic routes
      if (segment.startsWith('[') && segment.endsWith(']')) {
        // Try to get meaningful label from search params or context
        const paramName = segment.slice(1, -1)
        const paramValue = searchParams.get(paramName)
        label = paramValue || segment
      }

      // Handle specific route labels
      switch (segment) {
        case 'agent':
          label = 'Agent Profile'
          break
        case 'properties':
          label = 'Properties'
          break
        case 'create':
          label = 'Create Property'
          break
        case 'contact':
          label = 'Contact'
          break
        case 'posts':
          label = 'Posts'
          break
        case 'analytics':
          label = 'Analytics'
          break
        case 'profile':
          label = 'Profile'
          break
        case 'login':
          label = 'Sign In'
          break
        case 'register':
          label = 'Sign Up'
          break
        case 'onboarding':
          label = 'Onboarding'
          break
        default:
          // Capitalize and clean up the label
          label = segment
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
      }

      items.push({
        label,
        href,
        isActive: isLast
      })
    })

    return items
  }, [pathname, searchParams, showHome, customItems])

  // Don't show breadcrumbs on root page or if only one item
  if (breadcrumbs.length <= 1) {
    return null
  }

  return (
    <nav
      className={`flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400 ${className}`}
      aria-label="Breadcrumb"
    >
      <ol className="flex items-center space-x-1">
        {breadcrumbs.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <ChevronRightIcon className="w-4 h-4 mx-2 text-gray-400" />
            )}

            {item.href ? (
              <Link
                href={item.href}
                className="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-200"
              >
                {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
                <span className="truncate max-w-[200px]">{item.label}</span>
              </Link>
            ) : (
              <span
                className={`flex items-center space-x-1 ${item.isActive
                    ? 'text-gray-900 dark:text-white font-medium'
                    : 'text-gray-500 dark:text-gray-400'
                  }`}
                aria-current={item.isActive ? 'page' : undefined}
              >
                {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
                <span className="truncate max-w-[200px]">{item.label}</span>
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}