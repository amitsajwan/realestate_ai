'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { errorMessage } from './client'

/** Run an async loader on mount (and on reload()); tracks loading/error. Ignores results after unmount, and the answer of
 *  any call that a later one has replaced: the owner picking an agent before their own listings came back saw their own. */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const alive = useRef(true)
  const latest = useRef(0)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const reload = useCallback(async () => {
    const call = ++latest.current
    const current = () => alive.current && call === latest.current
    setLoading(true)
    setError(null)
    try {
      const r = await loaderRef.current()
      if (current()) setData(r)
    } catch (e) {
      if (current()) setError(errorMessage(e))
    } finally {
      if (current()) setLoading(false)
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
