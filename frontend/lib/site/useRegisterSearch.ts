'use client'

import { useEffect, useState } from 'react'
import { searchRegister } from './register'
import type { RegisterSearchHit } from './register'

/** Results as you type: searches the register 250 ms after the last key, drops answers to an older query. `done` is true once
 *  the current query (2+ characters) has an answer, so a page can tell "no match" from "still looking". */
export function useRegisterSearch(q: string, limit = 20): { hits: RegisterSearchHit[]; done: boolean } {
  const [hits, setHits] = useState<RegisterSearchHit[]>([])
  const [done, setDone] = useState(false)
  useEffect(() => {
    const t = q.trim()
    setDone(false)
    if (t.length < 2) { setHits([]); return }
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      searchRegister(t, limit, ctrl.signal).then((h) => { if (!ctrl.signal.aborted) { setHits(h); setDone(true) } })
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [q, limit])
  return { hits, done }
}
