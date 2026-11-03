import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import fs from 'fs'
import path from 'path'
import vm from 'vm'
import React from 'react'
import { studioManifest } from '@/lib/app/manifest'
import { keyBytes, phoneCard, type PhoneEnv } from '@/lib/app/phone'

jest.mock('@/lib/app/phone', () => {
  const actual = jest.requireActual('@/lib/app/phone')
  return {
    ...actual,
    getPushStatus: jest.fn(), alertsOn: jest.fn(), turnOnAlerts: jest.fn(), turnOffAlerts: jest.fn(), promptInstall: jest.fn(),
    hasInstallPrompt: jest.fn(), isStandalone: jest.fn(), isIos: jest.fn(), pushSupported: jest.fn(),
  }
})
// eslint-disable-next-line @typescript-eslint/no-require-imports
const phone = require('@/lib/app/phone') as Record<string, jest.Mock>
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { PhoneAppCard } = require('@/components/app/PhoneApp') as typeof import('@/components/app/PhoneApp')

const ENV: PhoneEnv = { standalone: false, canPrompt: false, ios: false, pushSupported: true, serverEnabled: true, permission: 'default', subscribed: false }

describe('what the phone card offers', () => {
  it('offers Install while Chrome can install it, and lead alerts while they are off', () => {
    expect(phoneCard({ ...ENV, canPrompt: true })).toEqual({ install: 'prompt', alerts: 'off', todo: true })
  })
  it('has nothing to do once Studio is installed and alerts are on', () => {
    expect(phoneCard({ ...ENV, standalone: true, subscribed: true, permission: 'granted' })).toEqual({ install: 'done', alerts: 'on', todo: false })
  })
  it('explains Add to Home Screen on iPhone, where alerts work only after it', () => {
    expect(phoneCard({ ...ENV, ios: true, pushSupported: false })).toEqual({ install: 'ios', alerts: 'after_install', todo: true })
    expect(phoneCard({ ...ENV, ios: true, standalone: true })).toEqual({ install: 'done', alerts: 'off', todo: true })
  })
  it('says alerts are blocked when the agent refused them, and offers no alerts until the server has its keys', () => {
    expect(phoneCard({ ...ENV, permission: 'denied' }).alerts).toBe('blocked')
    expect(phoneCard({ ...ENV, permission: 'denied', standalone: true }).todo).toBe(false)
    expect(phoneCard({ ...ENV, serverEnabled: false })).toEqual({ install: null, alerts: null, todo: false })
  })
})

describe('the manifest and the server key', () => {
  it('installs Studio on its own scope, opening on Studio home, with icons the site serves', () => {
    const m = studioManifest()
    expect(m.id).toBe('/studio')
    expect(m.scope).toBe('/studio')
    expect(m.start_url!.startsWith('/studio')).toBe(true)
    expect(m.display).toBe('standalone')
    for (const icon of m.icons!) expect(fs.existsSync(path.join(__dirname, '../../../frontend/public', icon.src))).toBe(true)
    for (const s of m.shortcuts!) expect(s.url.startsWith('/studio/')).toBe(true)
  })
  it('decodes the server key from base64url for pushManager.subscribe', () => {
    expect(Array.from(keyBytes('BAEC_-8'))).toEqual([4, 1, 2, 255, 239])
  })
})

describe('Studio on your phone card', () => {
  const ON = { enabled: true, public_key: 'BAEC', phones: 0 }
  beforeEach(() => {
    jest.clearAllMocks()
    window.localStorage.removeItem('app_phone_card_dismissed')
    phone.getPushStatus.mockResolvedValue(ON)
    phone.alertsOn.mockResolvedValue(false)
    phone.hasInstallPrompt.mockReturnValue(false)
    phone.isStandalone.mockReturnValue(false)
    phone.isIos.mockReturnValue(false)
    phone.pushSupported.mockReturnValue(true)
    Object.defineProperty(window, 'Notification', { value: { permission: 'default' }, configurable: true })
  })

  it('turns lead alerts on from Home and then says they are on', async () => {
    phone.turnOnAlerts.mockResolvedValue('granted')
    render(<PhoneAppCard place="home" />)
    fireEvent.click(await screen.findByTestId('phone-alerts-on'))
    await screen.findByTestId('phone-alerts-are-on')
    expect(phone.turnOnAlerts).toHaveBeenCalledWith(ON)
  })

  it('offers Install when Chrome can install it', async () => {
    phone.hasInstallPrompt.mockReturnValue(true)
    phone.promptInstall.mockResolvedValue(true)
    render(<PhoneAppCard place="home" />)
    fireEvent.click(await screen.findByTestId('phone-install'))
    await waitFor(() => expect(phone.promptInstall).toHaveBeenCalled())
  })

  it('tells iPhone users how to add Studio to the home screen', async () => {
    phone.isIos.mockReturnValue(true)
    phone.pushSupported.mockReturnValue(false)
    render(<PhoneAppCard place="home" />)
    expect(await screen.findByTestId('phone-install-ios')).toHaveTextContent('Add to Home Screen')
    expect(screen.getByText(/lead alerts work once Studio is on your home screen/)).toBeInTheDocument()
  })

  it('leaves Home once everything is done, or after Not now', async () => {
    phone.isStandalone.mockReturnValue(true)
    phone.alertsOn.mockResolvedValue(true)
    const { container, unmount } = render(<PhoneAppCard place="home" />)
    await act(async () => { await Promise.resolve() })
    expect(container).toBeEmptyDOMElement()
    unmount()
    phone.isStandalone.mockReturnValue(false)
    phone.alertsOn.mockResolvedValue(false)
    render(<PhoneAppCard place="home" />)
    fireEvent.click(await screen.findByText('Not now'))
    expect(screen.queryByTestId('phone-app-card')).toBeNull()
    expect(window.localStorage.getItem('app_phone_card_dismissed')).toBe('1')
  })

  it('lets the agent turn alerts off on My brand', async () => {
    phone.alertsOn.mockResolvedValue(true)
    phone.turnOffAlerts.mockResolvedValue(undefined)
    Object.defineProperty(window, 'Notification', { value: { permission: 'granted' }, configurable: true })
    render(<PhoneAppCard place="profile" />)
    fireEvent.click(await screen.findByTestId('phone-alerts-off'))
    await screen.findByTestId('phone-alerts-on')
    expect(phone.turnOffAlerts).toHaveBeenCalled()
  })

  it('shows what went wrong when alerts cannot be turned on', async () => {
    phone.turnOnAlerts.mockRejectedValue(new Error('This browser cannot show alerts.'))
    render(<PhoneAppCard place="home" />)
    fireEvent.click(await screen.findByTestId('phone-alerts-on'))
    expect(await screen.findByRole('alert')).toHaveTextContent('This browser cannot show alerts.')
  })

  it('shows nothing about alerts while the server has no keys (demo mode too)', async () => {
    phone.getPushStatus.mockResolvedValue({ enabled: false, public_key: null, phones: 0 })
    phone.isIos.mockReturnValue(true)
    render(<PhoneAppCard place="profile" />)
    await screen.findByTestId('phone-install-ios')
    expect(screen.queryByText(/lead alerts/i)).toBeNull()
  })
})

describe('the service worker (public/studio/sw.js)', () => {
  function loadWorker() {
    const handlers: Record<string, (e: unknown) => void> = {}
    const shown: Array<[string, Record<string, unknown>]> = []
    const opened: string[] = []
    const windows: Array<{ url: string; focus: jest.Mock; navigate: jest.Mock }> = []
    const self = {
      location: { origin: 'https://avasetu.in' },
      addEventListener: (type: string, f: (e: unknown) => void) => { handlers[type] = f },
      registration: { showNotification: async (title: string, opts: Record<string, unknown>) => { shown.push([title, opts]) } },
      clients: { matchAll: async () => windows, openWindow: async (u: string) => { opened.push(u) }, claim: async () => undefined },
      skipWaiting: () => undefined,
    }
    const code = fs.readFileSync(path.join(__dirname, '../../public/studio/sw.js'), 'utf8')
    vm.runInNewContext(code, { self, URL, Response: class { constructor(public body: string) {} }, fetch: () => Promise.reject(new Error('offline')) })
    const fire = async (type: string, event: Record<string, unknown>) => {
      let done: Promise<unknown> = Promise.resolve()
      handlers[type]({ ...event, waitUntil: (p: Promise<unknown>) => { done = p }, respondWith: (p: Promise<unknown>) => { done = p } })
      return done
    }
    return { fire, shown, opened, windows }
  }

  it('shows the alert the backend sent, grouped by its tag', async () => {
    const w = loadWorker()
    const payload = { title: 'New lead', body: 'Rohit enquired on your website', url: '/studio/leads/L9', tag: 'new_lead:L9' }
    await w.fire('push', { data: { json: () => payload } })
    expect(w.shown).toEqual([['New lead', expect.objectContaining({ body: 'Rohit enquired on your website', tag: 'new_lead:L9', renotify: true,
      data: { url: '/studio/leads/L9' } })]])
  })

  it('opens the lead on tap, in the open Studio window if there is one, and only ever a Studio page', async () => {
    const w = loadWorker()
    const notification = (url: string) => ({ close: jest.fn(), data: { url } })
    await w.fire('notificationclick', { notification: notification('/studio/leads/L9') })
    expect(w.opened).toEqual(['https://avasetu.in/studio/leads/L9'])
    await w.fire('notificationclick', { notification: notification('https://evil.example/') })
    expect(w.opened[1]).toBe('https://avasetu.in/studio')
    w.windows.push({ url: 'https://avasetu.in/studio/inbox', focus: jest.fn(), navigate: jest.fn() })
    await w.fire('notificationclick', { notification: notification('/studio/leads/L2') })
    expect(w.windows[0].focus).toHaveBeenCalled()
    expect(w.windows[0].navigate).toHaveBeenCalledWith('https://avasetu.in/studio/leads/L2')
    expect(w.opened).toHaveLength(2)
  })

  it('shows the offline note when a Studio page cannot load, and leaves other requests alone', async () => {
    const w = loadWorker()
    const page = (await w.fire('fetch', { request: { mode: 'navigate' } })) as { body: string }
    expect(page.body).toContain('No internet right now')
    expect(await w.fire('fetch', { request: { mode: 'cors' } })).toBeUndefined()
  })
})
