'use client'
import { useEffect, useState } from 'react'
import { isFixtureMode } from '@/lib/app/client'
import { conciergeApi } from '@/lib/app/concierge'

let known: boolean | null = null
const KEY = 'app_is_owner'

/** Demo mode is the owner, unless localStorage app_fixture_agent=1 asks to see Studio as an agent sees it. */
function fixtureAsAgent(): boolean {
  try {
    return window.localStorage.getItem('app_fixture_agent') === '1'
  } catch {
    return false
  }
}

/** The answer from earlier in this browser session: without it the owner's tab bar first drew as an agent's, then jumped. */
function remembered(): boolean | null {
  try {
    const v = typeof window === 'undefined' ? null : window.sessionStorage.getItem(KEY)
    return v === '1' ? true : v === '0' ? false : null
  } catch {
    return null
  }
}

function remember(v: boolean) {
  try {
    window.sessionStorage.setItem(KEY, v ? '1' : '0')
  } catch {
    /* storage blocked: asked again on the next page load */
  }
}

/**
 * True when the signed-in user may use the concierge (the server decides: 403 for everyone else). Asked once per page load; the
 * last answer in this browser session is used meanwhile, so screens draw right the first time.
 */
export function useIsOwner(): boolean {
  const [owner, setOwner] = useState<boolean>(known === true)
  useEffect(() => {
    if (isFixtureMode()) return setOwner(!fixtureAsAgent())
    if (known !== null) return setOwner(known)
    const before = remembered()
    if (before !== null) setOwner(before)
    let alive = true
    conciergeApi.list().then(() => (known = true), () => (known = false)).then(() => {
      remember(known === true)
      if (alive) setOwner(known === true)
    })
    return () => {
      alive = false
    }
  }, [])
  return owner
}
