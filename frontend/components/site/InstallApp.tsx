'use client'

import React, { useEffect, useState } from 'react'

interface InstallEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

/** "Add to home screen": the browser's own install button where it offers one (Android Chrome), the Share-menu hint on iPhone
 *  Safari, nothing once it runs as the installed app. The manifest (app/manifest.ts) opens the installed app on /check. */
export default function InstallApp() {
  const [ev, setEv] = useState<InstallEvent | null>(null)
  const [ios, setIos] = useState(false)
  const [installed, setInstalled] = useState(true)

  useEffect(() => {
    const standalone = window.matchMedia?.('(display-mode: standalone)').matches || (navigator as unknown as { standalone?: boolean }).standalone === true
    setInstalled(!!standalone)
    setIos(/iphone|ipad|ipod/i.test(navigator.userAgent) && !/crios|fxios/i.test(navigator.userAgent))
    const onPrompt = (e: Event) => { e.preventDefault(); setEv(e as InstallEvent) }
    const onInstalled = () => { setInstalled(true); setEv(null) }
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => { window.removeEventListener('beforeinstallprompt', onPrompt); window.removeEventListener('appinstalled', onInstalled) }
  }, [])

  if (installed || (!ev && !ios)) return null
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200" data-testid="install-app">
      <p className="min-w-0 flex-1 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">Keep the checker on your phone.</span>{' '}
        {ev ? 'It opens like an app, with your projects one tap away.' : <>Tap <span className="font-semibold">Share</span>, then <span className="font-semibold">Add to Home Screen</span>.</>}
      </p>
      {ev && (
        <button type="button" onClick={async () => { await ev.prompt(); await ev.userChoice; setEv(null) }}
          className="min-h-[44px] rounded-full bg-[#0f2340] px-5 font-semibold text-white">Add to home screen</button>
      )}
    </div>
  )
}
