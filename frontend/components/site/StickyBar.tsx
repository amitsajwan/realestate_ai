import React from 'react'
import { telLink, whatsappLink } from '@/lib/site/links'
import TrackedLink from './TrackedLink'

interface Props {
  agentSlug: string
  phone?: string | null
  waMessage: string
  listingId?: string
}

/** Mobile-only fixed bottom bar: WhatsApp / Call / Enquire. Page wrapper adds bottom padding (SiteShell bottomPad). */
export default function StickyBar({ agentSlug, phone, waMessage, listingId }: Props) {
  const wa = whatsappLink(phone, waMessage)
  const tel = telLink(phone)
  const item = 'flex min-h-[48px] flex-1 items-center justify-center rounded-lg text-sm font-bold no-underline'
  return (
    <nav aria-label="Contact the agent"
      className="fixed inset-x-0 bottom-0 z-40 flex gap-2 border-t border-slate-200 bg-white px-3 pt-2 shadow-[0_-4px_12px_rgba(0,0,0,0.08)] md:hidden"
      style={{ paddingBottom: 'calc(0.5rem + env(safe-area-inset-bottom, 0px))' }}>
      {wa && (
        <TrackedLink href={wa} event="whatsapp_click" agentSlug={agentSlug} listingId={listingId} target="_blank" rel="noopener noreferrer"
          className={item + ' bg-[#25D366] text-[#053b1a]'}>WhatsApp</TrackedLink>
      )}
      {tel && (
        <TrackedLink href={tel} event="call_click" agentSlug={agentSlug} listingId={listingId}
          className={item + ' border-2 border-[var(--site-primary)] text-[var(--site-primary)]'}>Call</TrackedLink>
      )}
      <a href="#enquire" className={item + ' bg-[var(--site-primary)] text-[var(--site-on-primary)]'}>Enquire</a>
    </nav>
  )
}
