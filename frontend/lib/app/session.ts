'use client'
/** Token in localStorage (all access wrapped in try/catch) and a tiny useSession hook. */
import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

const TOKEN_KEY = 'app_token'
const SITE_KEY = 'app_site_url'
const PHONE_KEY = 'app_phone'

function read(key: string): string | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage.getItem(key)
  } catch {
    return null
  }
}
function write(key: string, value: string | null) {
  try {
    if (typeof window === 'undefined') return
    if (value === null) window.localStorage.removeItem(key)
    else window.localStorage.setItem(key, value)
  } catch {
    /* storage blocked: session lasts only for this page view */
  }
}

export const getToken = () => read(TOKEN_KEY)
export const getSiteUrl = () => read(SITE_KEY)
export const getPhone = () => read(PHONE_KEY)

export function saveSession(s: { token: string; siteUrl?: string | null; phone?: string }) {
  write(TOKEN_KEY, s.token)
  if (s.siteUrl !== undefined) write(SITE_KEY, s.siteUrl)
  if (s.phone) write(PHONE_KEY, s.phone)
}

export function saveSiteUrl(url: string) {
  write(SITE_KEY, url)
}

export function clearSession() {
  write(TOKEN_KEY, null)
  write(SITE_KEY, null)
}

export interface Session {
  ready: boolean
  token: string | null
  siteUrl: string | null
  phone: string | null
  logout: () => void
}

/** With `require` (default) the hook redirects to /join when there is no token. */
export function useSession(require = true): Session {
  const router = useRouter()
  const [state, setState] = useState<{ ready: boolean; token: string | null; siteUrl: string | null; phone: string | null }>({
    ready: false,
    token: null,
    siteUrl: null,
    phone: null,
  })

  useEffect(() => {
    const token = getToken()
    setState({ ready: true, token, siteUrl: getSiteUrl(), phone: getPhone() })
    if (require && !token) router.replace('/join')
  }, [require, router])

  const logout = useCallback(() => {
    clearSession()
    router.replace('/join')
  }, [router])

  return { ...state, logout }
}
