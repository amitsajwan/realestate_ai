import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import { debounce, throttle } from 'lodash'

// Hook for debounced state updates
export function useDebouncedState<T>(
  initialValue: T,
  delay: number = 300
) {
  const [value, setValue] = useState<T>(initialValue)
  const [debouncedValue, setDebouncedValue] = useState<T>(initialValue)

  const debouncedSetter = useMemo(
    () => debounce((newValue: T) => setDebouncedValue(newValue), delay),
    [delay]
  )

  useEffect(() => {
    debouncedSetter(value)
    return () => {
      debouncedSetter.cancel()
    }
  }, [value, debouncedSetter])

  return [debouncedValue, setValue] as const
}

// Hook for throttled callbacks
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 300
): T {
  const callbackRef = useRef(callback)
  callbackRef.current = callback

  return useMemo(
    () => throttle((...args) => callbackRef.current(...args), delay),
    [delay]
  ) as T
}

// Hook for memoized expensive computations
export function useComputedValue<T, D extends readonly unknown[]>(
  computeFn: () => T,
  deps: D
): T {
  const valueRef = useRef<T>()
  const depsRef = useRef<D>()

  if (!depsRef.current || !areDepsEqual(deps, depsRef.current)) {
    valueRef.current = computeFn()
    depsRef.current = deps
  }

  return valueRef.current as T
}

// Hook for optimized list filtering and sorting
interface UseOptimizedListOptions<T> {
  filterFn?: (item: T) => boolean
  sortFn?: (a: T, b: T) => number
  searchKeys?: (keyof T)[]
  searchTerm?: string
}

export function useOptimizedList<T>(
  items: T[],
  options: UseOptimizedListOptions<T> = {}
) {
  const { filterFn, sortFn, searchKeys = [], searchTerm = '' } = options

  const filteredItems = useMemo(() => {
    let result = [...items]

    // Apply search filter
    if (searchTerm && searchKeys.length > 0) {
      const lowerSearchTerm = searchTerm.toLowerCase()
      result = result.filter(item =>
        searchKeys.some(key => {
          const value = item[key]
          if (typeof value === 'string') {
            return value.toLowerCase().includes(lowerSearchTerm)
          }
          return false
        })
      )
    }

    // Apply custom filter
    if (filterFn) {
      result = result.filter(filterFn)
    }

    // Apply sorting
    if (sortFn) {
      result.sort(sortFn)
    }

    return result
  }, [items, filterFn, sortFn, searchKeys, searchTerm])

  const stats = useMemo(() => ({
    total: items.length,
    filtered: filteredItems.length,
    hasFilters: !!searchTerm || !!filterFn
  }), [items.length, filteredItems.length, searchTerm, filterFn])

  return {
    items: filteredItems,
    stats
  }
}

// Hook for lazy loading with intersection observer
export function useLazyLoad<T extends HTMLElement>(
  options: IntersectionObserverInit = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false)
  const targetRef = useRef<T>(null)

  useEffect(() => {
    const target = targetRef.current
    if (!target) return

    const observer = new IntersectionObserver(
      ([entry]) => setIsIntersecting(entry.isIntersecting),
      options
    )

    observer.observe(target)

    return () => observer.disconnect()
  }, [options.root, options.rootMargin, options.threshold])

  return { targetRef, isIntersecting }
}

// Hook for batch updates
export function useBatchUpdate<T>(
  updateFn: (items: T[]) => void,
  delay: number = 100
) {
  const batchRef = useRef<T[]>([])
  const timerRef = useRef<NodeJS.Timeout>()

  const processBatch = useCallback(() => {
    if (batchRef.current.length > 0) {
      updateFn(batchRef.current)
      batchRef.current = []
    }
  }, [updateFn])

  const batchedUpdate = useCallback((item: T) => {
    batchRef.current.push(item)

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    timerRef.current = setTimeout(processBatch, delay)
  }, [processBatch, delay])

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
      processBatch()
    }
  }, [processBatch])

  return batchedUpdate
}

// Helper function to compare dependencies
function areDepsEqual<T extends readonly unknown[]>(
  deps1: T,
  deps2: T
): boolean {
  if (deps1.length !== deps2.length) return false
  
  for (let i = 0; i < deps1.length; i++) {
    if (!Object.is(deps1[i], deps2[i])) return false
  }
  
  return true
}