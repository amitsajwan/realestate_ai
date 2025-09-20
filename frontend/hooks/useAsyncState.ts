import { useState, useCallback, useEffect, useRef } from 'react'

interface AsyncState<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  isSuccess: boolean
  isError: boolean
  isIdle: boolean
}

interface UseAsyncStateOptions<T> {
  initialData?: T
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
  retryCount?: number
  retryDelay?: number
}

export function useAsyncState<T>(
  asyncFunction: () => Promise<T>,
  options: UseAsyncStateOptions<T> = {}
) {
  const {
    initialData = null,
    onSuccess,
    onError,
    retryCount = 0,
    retryDelay = 1000
  } = options

  const [state, setState] = useState<AsyncState<T>>({
    data: initialData,
    isLoading: false,
    error: null,
    isSuccess: false,
    isError: false,
    isIdle: true
  })

  const isMounted = useRef(true)
  const retryTimeoutRef = useRef<NodeJS.Timeout>()
  const currentRetryCount = useRef(0)

  useEffect(() => {
    return () => {
      isMounted.current = false
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [])

  const execute = useCallback(async () => {
    if (!isMounted.current) return

    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      isError: false,
      isIdle: false
    }))

    try {
      const data = await asyncFunction()
      
      if (!isMounted.current) return

      setState({
        data,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        isIdle: false
      })

      onSuccess?.(data)
      currentRetryCount.current = 0
    } catch (error) {
      if (!isMounted.current) return

      const err = error instanceof Error ? error : new Error('Unknown error')
      
      setState({
        data: null,
        isLoading: false,
        error: err,
        isSuccess: false,
        isError: true,
        isIdle: false
      })

      onError?.(err)

      // Handle retry logic
      if (currentRetryCount.current < retryCount) {
        currentRetryCount.current++
        retryTimeoutRef.current = setTimeout(() => {
          execute()
        }, retryDelay * currentRetryCount.current)
      }
    }
  }, [asyncFunction, onSuccess, onError, retryCount, retryDelay])

  const reset = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
    currentRetryCount.current = 0
    setState({
      data: initialData,
      isLoading: false,
      error: null,
      isSuccess: false,
      isError: false,
      isIdle: true
    })
  }, [initialData])

  const setData = useCallback((data: T) => {
    setState(prev => ({
      ...prev,
      data,
      isSuccess: true,
      isError: false,
      error: null
    }))
  }, [])

  const setError = useCallback((error: Error) => {
    setState(prev => ({
      ...prev,
      error,
      isError: true,
      isSuccess: false,
      isLoading: false
    }))
  }, [])

  return {
    ...state,
    execute,
    reset,
    setData,
    setError
  }
}

// Specialized hook for form submissions
export function useFormSubmit<T, R>(
  submitFunction: (data: T) => Promise<R>,
  options: UseAsyncStateOptions<R> = {}
) {
  const [formData, setFormData] = useState<T | null>(null)
  
  const asyncState = useAsyncState(
    async () => {
      if (!formData) throw new Error('No form data provided')
      return submitFunction(formData)
    },
    options
  )

  const submit = useCallback(async (data: T) => {
    setFormData(data)
    return asyncState.execute()
  }, [asyncState])

  return {
    ...asyncState,
    submit
  }
}

// Hook for paginated data
interface PaginatedState<T> extends AsyncState<T[]> {
  currentPage: number
  totalPages: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

export function usePaginatedData<T>(
  fetchFunction: (page: number) => Promise<{ data: T[]; totalPages: number }>,
  options: UseAsyncStateOptions<T[]> = {}
) {
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const asyncState = useAsyncState(
    async () => {
      const result = await fetchFunction(currentPage)
      setTotalPages(result.totalPages)
      return result.data
    },
    {
      ...options,
      onSuccess: (data) => {
        options.onSuccess?.(data)
      }
    }
  )

  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }, [totalPages])

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1)
  }, [currentPage, goToPage])

  const previousPage = useCallback(() => {
    goToPage(currentPage - 1)
  }, [currentPage, goToPage])

  useEffect(() => {
    asyncState.execute()
  }, [currentPage])

  return {
    ...asyncState,
    currentPage,
    totalPages,
    hasNextPage: currentPage < totalPages,
    hasPreviousPage: currentPage > 1,
    goToPage,
    nextPage,
    previousPage
  }
}