'use client'

import React, { useState } from 'react'
import { withParam } from '@/lib/site/links'
import { trackEvent } from '@/lib/site/tracking'

interface Props {
  agentSlug: string
  listingId?: string
  title: string
  className?: string
}

/** navigator.share with copy-link fallback. Shared URL gets ?src=share so the receiving visit is attributed. */
export default function ShareButton({ agentSlug, listingId, title, className = '' }: Props) {
  const [copied, setCopied] = useState(false)

  const onShare = async () => {
    const clean = window.location.href.split('#')[0].replace(/([?&])src=[^&]*&?/, '$1').replace(/[?&]$/, '')
    const url = withParam(clean, 'src', 'share')
    trackEvent('share', agentSlug, listingId)
    try {
      if (typeof navigator.share === 'function') {
        await navigator.share({ title, url })
        return
      }
    } catch {
      return // user cancelled
    }
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      window.prompt?.('Copy this link', url)
    }
  }

  return (
    <button type="button" onClick={onShare}
      className={'inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 font-semibold text-slate-800 ' + className}>
      <span aria-hidden="true">🔗</span>
      <span aria-live="polite">{copied ? 'Link copied' : 'Share'}</span>
    </button>
  )
}
