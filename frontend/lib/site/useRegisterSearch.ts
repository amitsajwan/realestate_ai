'use client'

import { useEffect, useState } from 'react'
import { searchPlace, searchRegister } from './register'
import type { PlaceMatch, RegisterSearchHit } from './register'

/** Results as you type: searches the register 250 ms after the last key, drops answers to an older query. `done` is true once
 *  the current query (2+ characters) has an answer, so a page can tell "no match" from "still looking". `place` is the area page
 *  the search names ("2 bhk kharadi"), asked at the same time. */
export function useRegisterSearch(q: string, limit = 20): { hits: RegisterSearchHit[]; done: boolean; place: PlaceMatch | null } {
  const [hits, setHits] = useState<RegisterSearchHit[]>([])
  const [place, setPlace] = useState<PlaceMatch | null>(null)
  const [done, setDone] = useState(false)
  useEffect(() => {
    const t = q.trim()
    setDone(false)
    if (t.length < 2) { setHits([]); setPlace(null); return }
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      Promise.all([searchRegister(t, limit, ctrl.signal), searchPlace(t, ctrl.signal)]).then(([h, p]) => {
        if (!ctrl.signal.aborted) { setHits(h); setPlace(p); setDone(true) }
      })
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [q, limit])
  return { hits, done, place }
}
