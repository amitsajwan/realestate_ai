import React from 'react'
import Link from 'next/link'
import type { MarketingConfig } from '@/lib/marketing/config'
import { LEGAL_LAST_UPDATED, LEGAL_LAST_UPDATED_ISO, LEGAL_NOTICE, NAV, PATHS, type LegalDoc } from '@/lib/marketing/strings'
import ContactLines from './ContactLines'
import MarketingShell from './MarketingShell'

/** Shared layout for /privacy, /terms and /data-deletion. */
export default function LegalPage({ doc, cfg }: { doc: LegalDoc; cfg: MarketingConfig }) {
  return (
    <MarketingShell>
      <article className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{doc.title}</h1>
        <p className="mt-2 text-sm text-slate-600">
          Last updated: <time dateTime={LEGAL_LAST_UPDATED_ISO}>{LEGAL_LAST_UPDATED}</time>
        </p>
        <p className="mt-5 text-lg leading-relaxed text-slate-800">{doc.intro}</p>
        <p className="mt-3 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">{LEGAL_NOTICE}</p>

        <nav aria-label="On this page" className="mt-8 rounded-xl border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-900">On this page</p>
          <ol className="mt-2 columns-1 gap-6 text-sm sm:columns-2">
            {doc.sections.map((s) => (
              <li key={s.id} className="break-inside-avoid">
                <a href={'#' + s.id} className="inline-flex min-h-[36px] items-center text-[#0f2340] underline underline-offset-2">{s.heading}</a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="mt-10 space-y-10">
          {doc.sections.map((s) => (
            <section key={s.id} id={s.id} aria-labelledby={s.id + '-h'} className="scroll-mt-20">
              <h2 id={s.id + '-h'} className="text-xl font-semibold text-slate-900">{s.heading}</h2>
              {s.paragraphs?.map((p, i) => (
                <p key={i} className="mt-3 leading-relaxed text-slate-800">{p}</p>
              ))}
              {s.bullets && (
                <ul className="mt-3 list-disc space-y-2 pl-6 leading-relaxed text-slate-800">
                  {s.bullets.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              )}
              {s.contact && <div className="mt-3"><ContactLines cfg={cfg} /></div>}
            </section>
          ))}
        </div>

        <nav aria-label="Related pages" className="mt-12 border-t border-slate-200 pt-6 text-sm">
          <ul className="flex flex-wrap gap-x-6">
            {NAV.legal.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{l.label}</Link>
              </li>
            ))}
            <li>
              <Link href={PATHS.invite} className="flex min-h-[44px] items-center text-[#0f2340] underline underline-offset-2">{NAV.requestInvite}</Link>
            </li>
          </ul>
        </nav>
      </article>
    </MarketingShell>
  )
}
