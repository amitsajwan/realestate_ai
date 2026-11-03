/** The Studio login in localStorage (all access wrapped in try/catch). Shared because the public site also asks whether the
 *  visitor is a signed-in agent (lib/site/tracking.ts), so its own visits are not counted. Studio's hook is in lib/app/session.ts. */

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
  try {
    window.sessionStorage.removeItem('app_is_owner')   // useIsOwner's remembered answer belongs to this login
  } catch {
    /* ignore */
  }
}
