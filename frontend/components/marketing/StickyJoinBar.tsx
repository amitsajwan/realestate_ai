'use client'

import React, { useEffect, useState } from 'react'

/**
 * Phone-only bar with the join button (and WhatsApp when configured). It shows once the hero buttons (`watchId`) have scrolled
 * away and hides again while the invite form (`formId`) is on screen, so it never covers the form or the keyboard.
 */
export default function StickyJoinBar({ watchId, formId, label, whatsappUrl, whatsappLabel }: {
  watchId: string; formId: string; label: string; whatsappUrl?: string | null; whatsappLabel: string
}) {
  const [heroGone, setHeroGone] = useState(false)
  const [formSeen, setFormSeen] = useState(false)

  useEffect(() => {
    const hero = document.getElementById(watchId)
    const form = document.getElementById(formId)
    if (!hero || !form || typeof IntersectionObserver === 'undefined') return
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.target === hero) setHeroGone(!e.isIntersecting && e.boundingClientRect.top < 0)
        if (e.target === form) setFormSeen(e.isIntersecting)
      }
    })
    io.observe(hero)
    io.observe(form)
    return () => io.disconnect()
  }, [watchId, formId])

  const show = heroGone && !formSeen
  return (
    <div data-print="hide" aria-hidden={!show} data-testid="sticky-join"
      className={'fixed inset-x-0 bottom-0 z-30 border-t border-white/10 bg-[#0f2340] px-4 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] transition-transform duration-200 md:hidden '
        + (show ? 'translate-y-0' : 'pointer-events-none translate-y-full')}>
      <div className="flex gap-2">
        <a href={'#' + formId} tabIndex={show ? 0 : -1}
          className="flex min-h-[48px] flex-1 items-center justify-center rounded-xl bg-[#f0b440] px-4 text-base font-extrabold text-[#0f2340] no-underline">
          {label}
        </a>
        {whatsappUrl && (
          <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" tabIndex={show ? 0 : -1}
            className="flex min-h-[48px] items-center justify-center rounded-xl border-2 border-white/70 px-4 font-bold text-white no-underline">
            {whatsappLabel}<span className="sr-only"> (opens in a new tab)</span>
          </a>
        )}
      </div>
    </div>
  )
}
