'use client'
import { useEffect, useState } from 'react'
import { isFixtureMode } from '@/lib/app/client'
import { conciergeApi } from '@/lib/app/concierge'

let known: boolean | null = null

/** True when the signed-in user may use the concierge (the server decides: 403 for everyone else). Asked once per page load. */
export function useIsOwner(): boolean {
  const [owner, setOwner] = useState<boolean>(known === true)
  useEffect(() => {
    if (isFixtureMode()) return setOwner(true)
    if (known !== null) return setOwner(known)
    let alive = true
    conciergeApi.list().then(() => (known = true), () => (known = false)).then(() => alive && setOwner(known === true))
    return () => {
      alive = false
    }
  }, [])
  return owner
}
