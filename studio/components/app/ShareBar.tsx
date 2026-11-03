'use client'
import React, { useState } from 'react'
import { copyText, whatsappShareUrl } from '@/lib/app/share'
import { t } from '@shared/strings'
import { Btn, LinkBtn } from './ui'

/** Big WhatsApp share button + copy link. `onShare` hears either one (home's setup list ticks "Share your website" with it). */
export function ShareBar({ url, message, onShare }: { url: string; message: string; onShare?: () => void }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="space-y-3">
      <LinkBtn variant="whatsapp" href={whatsappShareUrl(`${message} ${url}`)} target="_blank" rel="noopener noreferrer" onClick={onShare}>
        {t('shareWhatsapp')}
      </LinkBtn>
      <Btn
        variant="secondary"
        onClick={async () => {
          const ok = await copyText(url)
          setCopied(ok)
          if (ok) onShare?.()
          setTimeout(() => setCopied(false), 2000)
        }}
      >
        {copied ? t('copied') : t('copyLink')}
      </Btn>
    </div>
  )
}
