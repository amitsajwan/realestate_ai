import React from 'react'
import Link from 'next/link'
import { CONTACT, socialLinks } from '@/lib/marketing/social'
import { PATHS } from '@/lib/marketing/strings'
import SocialStrip from '@/components/site/SocialStrip'

/**
 * Footer contact block. Contact is the website, the Facebook Page and Instagram: no phone, email or personal name.
 * tone = the footer background it sits on.
 */
export default function ContactBlock({ tone = 'light' }: { tone?: 'light' | 'dark' }) {
  const { facebook, instagram } = socialLinks()
  const dark = tone === 'dark'
  const a = dark ? 'font-semibold text-white underline underline-offset-4' : 'font-semibold text-[#0f2340] underline underline-offset-4'
  return (
    <div data-testid="contact-block">
      <h2 className={'text-sm font-semibold uppercase tracking-wide ' + (dark ? 'text-[var(--site-accent)]' : 'text-slate-600')}>{CONTACT.heading}</h2>
      <p className={'mt-2 max-w-md ' + (dark ? 'text-slate-200' : 'text-slate-800')}>
        {CONTACT.before}
        <Link href={PATHS.invite} className={a}>{CONTACT.invite}</Link>
        {CONTACT.middle}
        <a href={facebook} target="_blank" rel="noopener noreferrer" className={a}>{CONTACT.facebook}</a>
        {CONTACT.and}
        <a href={instagram} target="_blank" rel="noopener noreferrer" className={a}>{CONTACT.instagram}</a>
        {CONTACT.after}
      </p>
      <SocialStrip tone={tone} className="mt-3" />
    </div>
  )
}
