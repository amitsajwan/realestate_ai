'use client'
import React, { useState } from 'react'
import { copyText, whatsappShareUrl } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import { Btn, LinkBtn } from './ui'

/** Big WhatsApp share button + copy link. */
export function ShareBar({ url, message }: { url: string; message: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="space-y-3">
      <LinkBtn variant="whatsapp" href={whatsappShareUrl(`${message} ${url}`)} target="_blank" rel="noopener noreferrer">
        {t('shareWhatsapp')}
      </LinkBtn>
      <Btn
        variant="secondary"
        onClick={async () => {
          setCopied(await copyText(url))
          setTimeout(() => setCopied(false), 2000)
        }}
      >
        {copied ? t('copied') : t('copyLink')}
      </Btn>
    </div>
  )
}
