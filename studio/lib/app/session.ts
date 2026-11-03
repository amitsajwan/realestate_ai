'use client'
/** Token in localStorage (all access wrapped in try/catch, in shared/session.ts) and a tiny useSession hook. */
import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { clearSession, getPhone, getSiteUrl, getToken } from '@shared/session'

export * from '@shared/session'

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
    // a Studio link sent on WhatsApp (the lead board) opens again after signing in
    const here = typeof window === 'undefined' ? '' : window.location.pathname
    if (require && !token) router.replace(here.startsWith('/studio/') ? `/join?next=${encodeURIComponent(here)}` : '/join')
  }, [require, router])

  const logout = useCallback(() => {
    clearSession()
    router.replace('/join')
  }, [router])

  return { ...state, logout }
}

/** Where to go after signing in: the Studio page in ?next=, else Studio home. Only a /studio path is followed. */
export function nextAfterLogin(search: string = typeof window === 'undefined' ? '' : window.location.search): string {
  const next = new URLSearchParams(search).get('next') || ''
  return /^\/studio(\/[\w-]+)*$/.test(next) ? next : '/studio'
}
