import React from 'react'
import { hasContact, type MarketingConfig } from '@/lib/marketing/config'
import { CONTACT_UNSET } from '@/lib/marketing/strings'

/** Contact details from env. Shows only what is configured; never invents an address or number. */
export default function ContactLines({ cfg }: { cfg: MarketingConfig }) {
  if (!hasContact(cfg)) return <p className="text-slate-700">{CONTACT_UNSET}</p>
  return (
    <ul className="space-y-1 text-slate-800">
      <li><span className="font-medium">{cfg.businessName}</span></li>
      {cfg.email && (
        <li>Email: <a href={'mailto:' + cfg.email} className="font-medium text-[#0f2340] underline">{cfg.email}</a></li>
      )}
      {cfg.whatsappUrl && (
        <li>WhatsApp: <a href={cfg.whatsappUrl} className="font-medium text-[#0f2340] underline" rel="noopener noreferrer">{cfg.whatsappDisplay}</a></li>
      )}
    </ul>
  )
}
