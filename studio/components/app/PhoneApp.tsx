'use client'
import React from 'react'
import { Btn } from '@/components/app/ui'
import {
  alertsOn, cardDismissed, captureInstallPrompt, dismissCard, getPushStatus, hasInstallPrompt, isIos, isStandalone, onInstallChange,
  phoneCard, promptInstall, pushSupported, registerWorker, syncAlerts, turnOffAlerts, turnOnAlerts,
  type Permission, type PhoneCard, type PushStatus,
} from '@/lib/app/phone'

/** Runs once as Studio opens (StudioGate): keeps Chrome's install prompt, registers the alerts' service worker, and re-links this
 *  phone's alerts to whoever is signed in. Shows nothing. */
export function PhoneAppSetup() {
  React.useEffect(() => {
    captureInstallPrompt()
    void registerWorker().then(() => syncAlerts())
  }, [])
  return null
}

const OFF: PushStatus = { enabled: false, public_key: null, phones: 0 }

function usePhoneCard() {
  const [status, setStatus] = React.useState<PushStatus | null>(null)
  const [subscribed, setSubscribed] = React.useState(false)
  const [, redraw] = React.useReducer((n: number) => n + 1, 0)
  React.useEffect(() => {
    let live = true
    void (async () => {
      const s = await getPushStatus().catch(() => OFF)
      const on = await alertsOn(s).catch(() => false)
      if (live) {
        setStatus(s)
        setSubscribed(on)
      }
    })()
    const stop = onInstallChange(redraw)
    return () => { live = false; stop() }
  }, [])
  const card: PhoneCard | null = status && phoneCard({
    standalone: isStandalone(), canPrompt: hasInstallPrompt(), ios: isIos(), pushSupported: pushSupported(),
    serverEnabled: status.enabled, permission: pushSupported() ? (Notification.permission as Permission) : 'default',
    subscribed,
  })
  return { card, status, setSubscribed, redraw }
}

/**
 * "Studio on your phone": install it and turn on lead alerts. On Home it shows while one of the two is still to do, until the
 * agent taps Not now; on My brand it always shows, with the way to turn alerts off.
 */
export function PhoneAppCard({ place }: { place: 'home' | 'profile' }) {
  const { card, status, setSubscribed, redraw } = usePhoneCard()
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [hidden, setHidden] = React.useState(false)
  // once the agent used the card it stays, to show how it went (alerts on, or why not), even with nothing left to do
  const [used, setUsed] = React.useState(false)
  React.useEffect(() => { if (place === 'home') setHidden(cardDismissed()) }, [place])

  if (!card || hidden) return null
  if (place === 'home' && !card.todo && !used) return null
  if (!card.install && !card.alerts) return null

  const run = async (f: () => Promise<void>) => {
    setBusy(true)
    setUsed(true)
    setError(null)
    try {
      await f()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
      redraw()
    }
  }
  const install = () => run(async () => { await promptInstall() })
  const alertsOnNow = () => run(async () => {
    const permission = await turnOnAlerts(status!)
    setSubscribed(permission === 'granted')
  })
  const alertsOff = () => run(async () => {
    await turnOffAlerts()
    setSubscribed(false)
  })

  return (
    <section aria-label="Studio on your phone" data-testid="phone-app-card" className="space-y-3 rounded-2xl border border-[#0f2340]/15 bg-white p-4">
      <h2 className="font-bold text-gray-900">Studio on your phone</h2>

      {card.install === 'prompt' && (
        <div className="space-y-2">
          <p className="text-sm text-gray-700">Put Studio on your home screen. It opens like an app, without the browser bar.</p>
          <Btn onClick={install} disabled={busy} data-testid="phone-install">Install Studio</Btn>
        </div>
      )}
      {card.install === 'ios' && (
        <p className="text-sm text-gray-700" data-testid="phone-install-ios">
          On iPhone: in Safari, tap the Share button <span aria-hidden>⬆︎</span>, then <b>Add to Home Screen</b>.
        </p>
      )}
      {card.install === 'done' && place === 'profile' && <p className="text-sm text-green-800">✓ Studio is on this phone&apos;s home screen.</p>}

      {card.alerts === 'off' && (
        <div className="space-y-2">
          <p className="text-sm text-gray-700">Lead alerts: your phone rings when a buyer enquires, replies or is waiting for you.</p>
          <Btn variant={card.install === 'prompt' ? 'secondary' : 'primary'} onClick={alertsOnNow} disabled={busy} data-testid="phone-alerts-on">
            Turn on lead alerts
          </Btn>
        </div>
      )}
      {card.alerts === 'on' && (
        <div className="space-y-2">
          <p className="text-sm text-green-800" data-testid="phone-alerts-are-on">✓ Lead alerts are on for this phone.</p>
          {place === 'profile' && <Btn variant="secondary" onClick={alertsOff} disabled={busy} data-testid="phone-alerts-off">Turn off alerts</Btn>}
        </div>
      )}
      {card.alerts === 'blocked' && (
        <p className="text-sm text-gray-700">Alerts are blocked for Studio in this browser. Allow notifications for this site in the browser&apos;s site settings, then open Studio again.</p>
      )}
      {card.alerts === 'after_install' && <p className="text-sm text-gray-700">On iPhone, lead alerts work once Studio is on your home screen.</p>}

      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {place === 'home' && (
        <button type="button" onClick={() => { dismissCard(); setHidden(true) }} className="min-h-[44px] text-sm font-semibold text-gray-600 underline">
          Not now
        </button>
      )}
    </section>
  )
}
