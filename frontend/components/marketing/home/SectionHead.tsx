import React from 'react'
import Link from 'next/link'
import { h2, moreLink } from './shared'

/** Heading, one-line lead and an optional "see all" link, as every home section starts. */
export default function SectionHead({ id, title, lead, more }: { id: string; title: string; lead: string; more?: { href: string; label: string } }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h2 id={id} className={h2}>{title}</h2>
        <p className="mt-2 text-slate-700">{lead}</p>
      </div>
      {more && <Link href={more.href} className={moreLink}>{more.label}</Link>}
    </div>
  )
}
