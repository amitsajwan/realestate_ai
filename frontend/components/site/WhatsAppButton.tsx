import React from 'react'
import { BRAND_NAME } from '@/lib/brand'

/** Digits only, Indian 10-digit mobiles get the 91 country code. '' when it does not look like a phone number. */
export function waNumber(raw: string | null | undefined): string {
  const d = (raw || '').replace(/\D/g, '')
  if (d.length === 10 && /^[6-9]/.test(d)) return '91' + d
  return d.length >= 11 && d.length <= 15 ? d : ''
}

/** The prefilled first message. The backend reads `(ref <code>)` to route the chat to the right agent and home. */
export function waText(title?: string | null, code?: string | null): string {
  const what = (title || '').trim() || `a home on ${BRAND_NAME}`
  return `Hi, I am interested in ${what}${code ? ` (ref ${code})` : ''}`
}

export function waLink(number: string, title?: string | null, code?: string | null): string {
  return `https://wa.me/${number}?text=${encodeURIComponent(waText(title, code))}`
}

interface Props {
  title?: string | null
  code?: string | null
  /** The agent's own WhatsApp number: used only when his branding opts in with `show_whatsapp`. */
  agentNumber?: string | null
  showAgentNumber?: boolean
  className?: string
}

/**
 * "Chat on WhatsApp": opens WhatsApp with a prefilled message. The buyer starts the chat, so our replies are free (24-hour window).
 * Uses the platform number (NEXT_PUBLIC_WHATSAPP_NUMBER); an agent's own number only when his branding has show_whatsapp=true.
 * Renders nothing when no number is configured.
 */
export default function WhatsAppButton({ title, code, agentNumber, showAgentNumber, className }: Props) {
  const own = showAgentNumber ? waNumber(agentNumber) : ''
  const number = own || waNumber(process.env.NEXT_PUBLIC_WHATSAPP_NUMBER)
  if (!number) return null
  return (
    <a
      href={waLink(number, title, code)}
      target="_blank"
      rel="noopener noreferrer"
      className={
        className ||
        'flex min-h-[48px] items-center justify-center gap-2 rounded-xl border border-[#1f9d55] bg-white px-4 text-base font-semibold text-[#14713d] no-underline'
      }
    >
      <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z" />
      </svg>
      Chat on WhatsApp
    </a>
  )
}
