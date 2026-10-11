'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { brochureApi, brochureFileError, friendlyBrochureError, pendingFacts } from './brochure'
import type { BrochureApi, BrochureKit, FactState, FactValue, RegistrationAnswer } from './brochure'

export type UploadPhase = 'idle' | 'uploading' | 'reading'

/**
 * The brochure kit of one listing: load it, upload a PDF (with progress), and confirm, fix or drop each fact.
 * Fact taps are optimistic: the card changes at once, the server's kit replaces it, and a refusal puts the old state back.
 */
export function useBrochure(listingId: string, client: BrochureApi = brochureApi) {
  const [kit, setKit] = useState<BrochureKit | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [progress, setProgress] = useState(0)
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const alive = useRef(true)
  const kitRef = useRef<BrochureKit | null>(null)
  kitRef.current = kit
  const clientRef = useRef(client)
  clientRef.current = client

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const k = await clientRef.current.get(listingId)
      if (alive.current) setKit(k)
    } catch (e) {
      if (alive.current) setError(friendlyBrochureError(e))
    } finally {
      if (alive.current) setLoading(false)
    }
  }, [listingId])

  useEffect(() => {
    void reload()
  }, [reload])

  const upload = useCallback(
    async (file: File): Promise<boolean> => {
      const bad = brochureFileError(file)
      if (bad) {
        setError(bad)
        return false
      }
      setError(null)
      setProgress(0)
      setPhase('uploading')
      try {
        const k = await clientRef.current.upload(listingId, file, (f) => {
          if (!alive.current) return
          setProgress(f)
          if (f >= 1) setPhase('reading') // bytes are up; the server is reading the pages
        })
        if (alive.current) setKit(k)
        return true
      } catch (e) {
        if (alive.current) setError(friendlyBrochureError(e))
        return false
      } finally {
        if (alive.current) setPhase('idle')
      }
    },
    [listingId],
  )

  const patchLocal = (factId: string, state: FactState, value?: FactValue) =>
    setKit((k) =>
      k
        ? { ...k, facts: k.facts.map((f) => (f.id === factId ? { ...f, state, ...(value !== undefined ? { value, edited: true } : {}) } : f)) }
        : k,
    )

  const setFact = useCallback(
    async (factId: string, state: FactState, value?: FactValue): Promise<boolean> => {
      const before = kitRef.current?.facts.find((f) => f.id === factId)
      if (!before) return false
      setError(null)
      setSaving((s) => ({ ...s, [factId]: true }))
      patchLocal(factId, state, value)
      try {
        const k = await clientRef.current.setFact(listingId, factId, state, value)
        if (alive.current) setKit(k)
        return true
      } catch (e) {
        if (alive.current) {
          setKit((k) => (k ? { ...k, facts: k.facts.map((f) => (f.id === factId ? before : f)) } : k))
          setError(friendlyBrochureError(e))
        }
        return false
      } finally {
        if (alive.current) setSaving((s) => ({ ...s, [factId]: false }))
      }
    },
    [listingId],
  )

  /** Use or don't use one plan, map or render; optimistic like a fact (saving key `img:<id>`). */
  const setImage = useCallback(
    async (imageId: string, state: FactState): Promise<boolean> => {
      const before = kitRef.current?.images?.find((i) => i.id === imageId)
      if (!before) return false
      const key = `img:${imageId}`
      const put = (s: FactState) =>
        setKit((k) => (k ? { ...k, images: (k.images ?? []).map((i) => (i.id === imageId ? { ...i, state: s } : i)) } : k))
      setError(null)
      setSaving((s) => ({ ...s, [key]: true }))
      put(state)
      try {
        const k = await clientRef.current.setImage(listingId, imageId, state)
        if (alive.current) setKit(k)
        return true
      } catch (e) {
        if (alive.current) {
          put(before.state)
          setError(friendlyBrochureError(e))
        }
        return false
      } finally {
        if (alive.current) setSaving((s) => ({ ...s, [key]: false }))
      }
    },
    [listingId],
  )

  /** Confirms every fact still pending, one request each, stopping at the first refusal. */
  const confirmAll = useCallback(async (): Promise<boolean> => {
    for (const f of pendingFacts(kitRef.current)) {
      if (!(await setFact(f.id, 'confirmed'))) return false
    }
    return true
  }, [setFact])

  const setRegistration = useCallback(
    async (answer: RegistrationAnswer): Promise<boolean> => {
      setError(null)
      setSaving((s) => ({ ...s, registration: true }))
      try {
        const k = await clientRef.current.setRegistration(listingId, answer)
        if (alive.current) setKit(k)
        return true
      } catch (e) {
        if (alive.current) setError(friendlyBrochureError(e))
        return false
      } finally {
        if (alive.current) setSaving((s) => ({ ...s, registration: false }))
      }
    },
    [listingId],
  )

  return { kit, loading, error, phase, progress, saving, reload, upload, setFact, setImage, confirmAll, setRegistration, clearError: () => setError(null) }
}
