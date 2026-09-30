import React from 'react'

const HANDLE = /^[A-Za-z0-9._]{1,30}$/
const FB = /^https:\/\/www\.facebook\.com\/[A-Za-z0-9.\-_/]{1,120}$/

/** Instagram / Facebook links from the agent's profile. Values are re-validated before they become links. */
export default function SocialLinks({ instagram, facebook }: { instagram?: string; facebook?: string }) {
  const ig = instagram && HANDLE.test(instagram) ? `https://www.instagram.com/${instagram}` : null
  const fb = facebook && FB.test(facebook) ? facebook : null
  if (!ig && !fb) return null
  const cls = 'inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 text-sm font-semibold text-[var(--site-primary)] no-underline'
  return (
    <ul className="mt-3 flex list-none flex-wrap gap-2 p-0">
      {ig && <li><a href={ig} target="_blank" rel="noopener noreferrer" className={cls}>Instagram</a></li>}
      {fb && <li><a href={fb} target="_blank" rel="noopener noreferrer" className={cls}>Facebook</a></li>}
    </ul>
  )
}
