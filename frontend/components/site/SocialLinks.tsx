import React from 'react'
import type { AgentBranding } from '@/lib/site/types'

const HANDLE = /^[A-Za-z0-9._]{1,30}$/
const FB = /^https:\/\/www\.facebook\.com\/[A-Za-z0-9.\-_/]{1,120}$/
const YT = /^https:\/\/www\.youtube\.com\/@[A-Za-z0-9._-]{1,60}\/?$/
const LI = /^https:\/\/www\.linkedin\.com\/(?:company|in)\/[A-Za-z0-9_-]{1,100}\/?$/
const X = /^https:\/\/x\.com\/[A-Za-z0-9_]{1,15}\/?$/

export interface SocialLink { key: 'instagram' | 'facebook' | 'youtube' | 'linkedin' | 'x'; label: string; href: string }

/** The agent's social pages as links. Each value is re-validated before it becomes a link; anything else is dropped. */
export function agentSocialLinks(social?: AgentBranding['social']): SocialLink[] {
  const s = social || {}
  const out: SocialLink[] = []
  if (s.instagram && HANDLE.test(s.instagram)) out.push({ key: 'instagram', label: 'Instagram', href: `https://www.instagram.com/${s.instagram}` })
  if (s.facebook && FB.test(s.facebook)) out.push({ key: 'facebook', label: 'Facebook', href: s.facebook })
  if (s.youtube && YT.test(s.youtube)) out.push({ key: 'youtube', label: 'YouTube', href: s.youtube })
  if (s.linkedin && LI.test(s.linkedin)) out.push({ key: 'linkedin', label: 'LinkedIn', href: s.linkedin })
  if (s.x && X.test(s.x)) out.push({ key: 'x', label: 'X', href: s.x })
  return out
}

const ICONS: Record<SocialLink['key'], string> = {
  instagram: 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zM17.3 5.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4zM12 2c-2.7 0-3 0-4.1.1C4.4 2.3 2.3 4.4 2.1 7.9 2 9 2 9.3 2 12s0 3 .1 4.1c.2 3.5 2.3 5.6 5.8 5.8 1.1.1 1.4.1 4.1.1s3 0 4.1-.1c3.5-.2 5.6-2.3 5.8-5.8.1-1.1.1-1.4.1-4.1s0-3-.1-4.1c-.2-3.5-2.3-5.6-5.8-5.8C15 2 14.7 2 12 2zm0 1.8c2.7 0 3 0 4 .1 2.6.1 3.9 1.4 4 4 .1 1 .1 1.3.1 4s0 3-.1 4c-.1 2.6-1.4 3.9-4 4-1 .1-1.3.1-4 .1s-3 0-4-.1c-2.6-.1-3.9-1.4-4-4-.1-1-.1-1.3-.1-4s0-3 .1-4c.1-2.6 1.4-3.9 4-4 1-.1 1.3-.1 4-.1z',
  facebook: 'M14 8h3V4h-3c-2.8 0-4.5 1.8-4.5 4.6V11H7v4h2.5v7h4v-7H16l.5-4h-3V8.8c0-.5.3-.8.5-.8z',
  youtube: 'M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8zM9.7 15V9l5.8 3-5.8 3z',
  linkedin: 'M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.5h4V21H3zM9.5 9.5h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5.2c0-1.2 0-2.9-1.8-2.9s-2 1.4-2 2.8V21h-4z',
  x: 'M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.2-8.3L2 3h6.4l4.4 5.8zm-1.1 16.2h1.7L7.4 4.7H5.6z',
}

/** Round icon links for the agent's footer (dark background). */
export function SocialIcons({ links }: { links: SocialLink[] }) {
  if (!links.length) return null
  return (
    <ul className="flex list-none flex-wrap gap-2 p-0" aria-label="Follow us">
      {links.map((l) => (
        <li key={l.key}>
          <a href={l.href} target="_blank" rel="noopener noreferrer" aria-label={l.label}
            className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white no-underline hover:bg-white/20">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><path d={ICONS[l.key]} /></svg>
          </a>
        </li>
      ))}
    </ul>
  )
}

/** Social links from the agent's profile as labelled pills (About section). */
export default function SocialLinks({ social }: { social?: AgentBranding['social'] }) {
  const links = agentSocialLinks(social)
  if (!links.length) return null
  const cls = 'inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[var(--site-primary)] no-underline'
  return (
    <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
      {links.map((l) => <li key={l.key}><a href={l.href} target="_blank" rel="noopener noreferrer" className={cls}>{l.label}</a></li>)}
    </ul>
  )
}
