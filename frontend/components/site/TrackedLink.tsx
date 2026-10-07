'use client'

import React from 'react'
import { trackEvent, type SiteEventType } from '@/lib/site/tracking'

interface Props extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'onClick'> {
  href: string
  event: SiteEventType
  agentSlug: string
  listingId?: string
}

/** Anchor that reports a click event (whatsapp_click / call_click) without delaying navigation. */
export default function TrackedLink({ event, agentSlug, listingId, children, ...rest }: Props) {
  return (
    <a {...rest} onClick={() => trackEvent(event, agentSlug, listingId)}>
      {children}
    </a>
  )
}
