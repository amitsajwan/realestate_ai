'use client'

import React, { useState } from 'react'
import { trackEvent } from '@/lib/site/tracking'

/** The page carries the number reversed, so its digits never appear in the HTML or the page data a search engine reads. */
export const hidePhone = (digits: string): string => digits.split('').reverse().join('')

/**
 * An agent's number on their own site, kept out of search (owner 2026-10-31: House Deal's pages may show it, but searching the
 * number must not find it). It shows only after a tap, which a crawler never makes, and data-nosnippet keeps it out of results
 * even if one did. `code` is hidePhone("91XXXXXXXXXX").
 */
export default function HiddenPhone({ code, agentSlug, className }: { code: string; agentSlug: string; className?: string }) {
  const [shown, setShown] = useState(false)
  const n = hidePhone(code)
  if (!/^91[6-9]\d{9}$/.test(n)) return null
  if (!shown) {
    return (
      <button type="button" onClick={() => setShown(true)} className={'inline-flex min-h-[44px] items-center underline underline-offset-2 ' + (className ?? '')}>
        Show phone number
      </button>
    )
  }
  return (
    <span data-nosnippet="">
      <a href={'tel:+' + n} onClick={() => trackEvent('call_click', agentSlug)} className={'inline-flex min-h-[44px] items-center ' + (className ?? '')}>
        {'+91 ' + n.slice(2, 7) + ' ' + n.slice(7)}
      </a>
    </span>
  )
}
