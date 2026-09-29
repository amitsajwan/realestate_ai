'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { errorMessage } from './client'

/** Run an async loader on mount (and on reload()); tracks loading/error. Ignores results after unmount. */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const alive = useRef(true)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const r = await loaderRef.current()
      if (alive.current) setData(r)
    } catch (e) {
      if (alive.current) setError(errorMessage(e))
    } finally {
      if (alive.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    alive.current = true
    reload()
    return () => {
      alive.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, loading, reload, setData }
}
