'use client'
/** Picks the real API or the fixture API. `api` is what all screens import. */
import { ApiError, createApiClient } from './api'
import { createFixtureApi } from './fixtures'
import { clearSession, getToken } from './session'
import type { AppApi } from './types'

const FLAG = 'app_fixtures'

export function isFixtureMode(): boolean {
  if (process.env.NEXT_PUBLIC_APP_FIXTURES === '1') return true
  try {
    return typeof window !== 'undefined' && window.localStorage.getItem(FLAG) === '1'
  } catch {
    return false
  }
}

function enableFixtures() {
  try {
    window.localStorage.setItem(FLAG, '1')
  } catch {
    /* ignore */
  }
}

/** Dev-only: the login step failing with a network/proxy error means "no backend"; switch to the fake. */
function looksUnreachable(e: unknown): boolean {
  return e instanceof ApiError && [0, 500, 502, 503, 504].includes(e.status)
}

const real: AppApi = createApiClient({
  getToken,
  onUnauthorized: () => {
    clearSession()
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/join')) window.location.assign('/join')
  },
})
let fake: AppApi | null = null
const fixtures = () => (fake ??= createFixtureApi())

const methods = Object.keys(real) as Array<keyof AppApi>

export const api = Object.fromEntries(
  methods.map((m) => [
    m,
    async (...args: unknown[]) => {
      const call = (impl: AppApi) => (impl[m] as (...a: unknown[]) => Promise<unknown>)(...args)
      if (isFixtureMode()) return call(fixtures())
      try {
        return await call(real)
      } catch (e) {
        if (process.env.NODE_ENV === 'development' && m === 'requestOtp' && looksUnreachable(e)) {
          enableFixtures()
          return call(fixtures())
        }
        throw e
      }
    },
  ]),
) as unknown as AppApi

/** User-friendly message for any thrown error. */
export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  return e instanceof Error ? e.message : 'Something went wrong'
}
