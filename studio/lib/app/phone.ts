'use client'
/**
 * Studio on the agent's phone (owner, 2026-11-03): installed from the browser (no app store) and ringing when a buyer is waiting.
 *
 * - Install: Chrome on Android offers it through `beforeinstallprompt`, which we keep until the agent taps Install. iPhone has no
 *   such prompt: Safari's Share > Add to Home Screen, which we explain.
 * - Alerts: Web Push. The server's key comes from GET /notifications/push; the browser's subscription goes to
 *   PUT /notifications/push/subscription (backend app/modules/notifications/push.py). On iPhone, push exists only for Studio
 *   added to the home screen (iOS 16.4 and later).
 * - The service worker that shows the alerts is public/studio/sw.js, registered with scope /studio.
 *
 * The rule for what the card offers (`phoneCard`) is pure and tested without a browser; the rest touches browser APIs.
 */
import { API_BASE_URL } from '@shared/config/api'
import { getToken } from '@shared/session'
import { isFixtureMode } from './client'

export const SW_URL = '/studio/sw.js'
export const SW_SCOPE = '/studio'
const DISMISSED_KEY = 'app_phone_card_dismissed'

export type Permission = 'default' | 'granted' | 'denied'

export interface PhoneEnv {
  /** Studio is open as the installed app (home screen), not in a browser tab. */
  standalone: boolean
  /** Chrome handed us its install prompt. */
  canPrompt: boolean
  ios: boolean
  /** This browser can do Web Push here (on iPhone: only once Studio is on the home screen). */
  pushSupported: boolean
  /** The server has its keys (VAPID) set. */
  serverEnabled: boolean
  permission: Permission
  /** This phone's alerts are on (a subscription the server knows). */
  subscribed: boolean
}

export interface PhoneCard {
  install: 'prompt' | 'ios' | 'done' | null
  alerts: 'off' | 'on' | 'blocked' | 'after_install' | null
  /** Something on the card is still to do: Home shows the card only then. */
  todo: boolean
}

export function phoneCard(e: PhoneEnv): PhoneCard {
  const install = e.standalone ? 'done' : e.canPrompt ? 'prompt' : e.ios ? 'ios' : null
  let alerts: PhoneCard['alerts'] = null
  if (e.serverEnabled) {
    if (e.pushSupported) alerts = e.permission === 'denied' ? 'blocked' : e.subscribed ? 'on' : 'off'
    else if (e.ios && !e.standalone) alerts = 'after_install'
  }
  return { install, alerts, todo: install === 'prompt' || install === 'ios' || alerts === 'off' }
}

/** The server key as pushManager.subscribe wants it. */
export function keyBytes(base64url: string): Uint8Array {
  const b64 = (base64url + '='.repeat((4 - (base64url.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(b64)
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

function sameKey(a: ArrayBuffer | null | undefined, b: Uint8Array): boolean {
  if (!a) return false
  const x = new Uint8Array(a)
  return x.length === b.length && x.every((v, i) => v === b[i])
}

// ---- install -----------------------------------------------------------------------------------------------------------------

interface InstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let installPrompt: InstallPromptEvent | null = null
const listeners = new Set<() => void>()
let capturing = false

/** Keep Chrome's install prompt for the Install button (Chrome fires it once, early, so this runs as Studio opens). */
export function captureInstallPrompt(): void {
  if (capturing || typeof window === 'undefined') return
  capturing = true
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()   // our button asks, at a moment the agent chooses
    installPrompt = e as InstallPromptEvent
    listeners.forEach((f) => f())
  })
  window.addEventListener('appinstalled', () => {
    installPrompt = null
    listeners.forEach((f) => f())
  })
}

export function hasInstallPrompt(): boolean {
  return installPrompt !== null
}

export function onInstallChange(f: () => void): () => void {
  listeners.add(f)
  return () => { listeners.delete(f) }
}

export async function promptInstall(): Promise<boolean> {
  const p = installPrompt
  if (!p) return false
  installPrompt = null
  await p.prompt()
  const { outcome } = await p.userChoice
  listeners.forEach((f) => f())
  return outcome === 'accepted'
}

export function isStandalone(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia?.('(display-mode: standalone)').matches || (navigator as Navigator & { standalone?: boolean }).standalone === true
}

export function isIos(): boolean {
  if (typeof navigator === 'undefined') return false
  // iPadOS asks for desktop sites and says "Macintosh"; a touch screen gives it away
  return /iPhone|iPad|iPod/.test(navigator.userAgent) || (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1)
}

export function pushSupported(): boolean {
  return typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

export function cardDismissed(): boolean {
  try {
    return window.localStorage.getItem(DISMISSED_KEY) === '1'
  } catch {
    return false
  }
}

export function dismissCard(): void {
  try {
    window.localStorage.setItem(DISMISSED_KEY, '1')
  } catch {
    /* storage blocked: the card shows again next time, which is harmless */
  }
}

/** Register the service worker (production only: in development a worker would keep serving old pages). */
export async function registerWorker(): Promise<ServiceWorkerRegistration | null> {
  if (process.env.NODE_ENV !== 'production' || typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return null
  try {
    // updateViaCache none: the browser always fetches sw.js afresh, so a deploy reaches every phone
    return await navigator.serviceWorker.register(SW_URL, { scope: SW_SCOPE, updateViaCache: 'none' })
  } catch {
    return null   // Studio works without it, only without alerts and the offline page
  }
}

// ---- alerts (Web Push) ---------------------------------------------------------------------------------------------------------

export interface PushStatus {
  enabled: boolean
  public_key: string | null
  phones: number
}

type FetchImpl = typeof fetch

async function call<T>(path: string, method = 'GET', body?: unknown, token: string | null = getToken(), fetchImpl: FetchImpl = fetch): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetchImpl(`${API_BASE_URL}/api/v1/notifications${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error((data as { detail?: string }).detail || `Request failed (${res.status})`)
  return data as T
}

export async function getPushStatus(fetchImpl?: FetchImpl): Promise<PushStatus> {
  if (isFixtureMode()) return { enabled: false, public_key: null, phones: 0 }
  return call<PushStatus>('/push', 'GET', undefined, getToken(), fetchImpl)
}

async function readySubscription(): Promise<{ reg: ServiceWorkerRegistration; sub: PushSubscription | null } | null> {
  const reg = (await navigator.serviceWorker.getRegistration(SW_SCOPE)) || (await registerWorker())
  if (!reg) return null
  return { reg, sub: await reg.pushManager.getSubscription() }
}

/** Ask the phone for permission (needs the agent's tap) and turn alerts on. Returns the permission the agent gave. */
export async function turnOnAlerts(status: PushStatus): Promise<Permission> {
  if (!status.enabled || !status.public_key) throw new Error('Phone alerts are not set up on the server yet')
  const permission = (await Notification.requestPermission()) as Permission
  if (permission !== 'granted') return permission
  const ready = await readySubscription()
  if (!ready) throw new Error('This browser cannot show alerts. Open Studio in Chrome, or on iPhone add it to your home screen first.')
  const key = keyBytes(status.public_key)
  let sub = ready.sub
  if (sub && !sameKey(sub.options.applicationServerKey, key)) {
    await sub.unsubscribe()
    sub = null
  }
  sub = sub || (await ready.reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key as BufferSource }))
  await call('/push/subscription', 'PUT', sub.toJSON())
  return permission
}

/** Turn this phone's alerts off: the server forgets it and the browser drops the subscription. */
export async function turnOffAlerts(token: string | null = getToken()): Promise<void> {
  const ready = pushSupported() ? await readySubscription() : null
  const sub = ready?.sub
  if (!sub) return
  try {
    await call('/push/subscription', 'DELETE', { endpoint: sub.endpoint }, token)
  } finally {
    await sub.unsubscribe().catch(() => false)
  }
}

/** Whether this phone's alerts are on: a subscription with the server's current key. */
export async function alertsOn(status: PushStatus): Promise<boolean> {
  if (!status.enabled || !status.public_key || !pushSupported() || Notification.permission !== 'granted') return false
  const ready = await readySubscription()
  return !!ready?.sub && sameKey(ready.sub.options.applicationServerKey, keyBytes(status.public_key))
}

/**
 * As Studio opens: a phone that had alerts on tells the server again. That links it to whoever is signed in now, and after the
 * server's key changed it subscribes afresh, so alerts keep working without the agent doing anything.
 */
export async function syncAlerts(): Promise<void> {
  if (isFixtureMode() || !pushSupported() || Notification.permission !== 'granted' || !getToken()) return
  try {
    const status = await getPushStatus()
    const ready = await readySubscription()
    if (!status.enabled || !ready?.sub) return
    await turnOnAlerts(status)   // permission is already granted: no question is shown
  } catch {
    /* the card shows alerts as off, and the agent can turn them on again */
  }
}
