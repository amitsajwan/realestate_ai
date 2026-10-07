import React from 'react'
import { showDirectContact, telLink, whatsappLink } from '@/lib/site/links'
import TrackedLink from './TrackedLink'

interface Props {
  agentSlug: string
  phone?: string | null
  waMessage: string
  listingId?: string
  size?: 'lg' | 'md'
  className?: string
}

const base = 'inline-flex min-h-[48px] flex-1 items-center justify-center gap-2 rounded-xl px-5 font-semibold no-underline transition active:scale-95'

/** Big WhatsApp + Call buttons. Renders nothing for a number that is not a valid Indian mobile. */
export default function ContactButtons({ agentSlug, phone, waMessage, listingId, size = 'lg', className = '' }: Props) {
  if (!showDirectContact()) return null
  const wa = whatsappLink(phone, waMessage)
  const tel = telLink(phone)
  if (!wa && !tel) return null
  const pad = size === 'lg' ? 'text-lg min-h-[56px]' : 'text-base'
  return (
    <div className={'flex w-full gap-3 ' + className}>
      {wa && (
        <TrackedLink href={wa} event="whatsapp_click" agentSlug={agentSlug} listingId={listingId} target="_blank" rel="noopener noreferrer"
          className={base + ' ' + pad + ' bg-[#25D366] text-[#053b1a]'} aria-label="Chat on WhatsApp">
          <span aria-hidden="true">💬</span> WhatsApp
        </TrackedLink>
      )}
      {tel && (
        <TrackedLink href={tel} event="call_click" agentSlug={agentSlug} listingId={listingId}
          className={base + ' ' + pad + ' border-2 border-[var(--site-primary)] bg-white text-[var(--site-primary)]'} aria-label="Call the agent">
          <span aria-hidden="true">📞</span> Call
        </TrackedLink>
      )}
    </div>
  )
}
