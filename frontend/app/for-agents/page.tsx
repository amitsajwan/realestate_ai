import React from 'react'
import Link from 'next/link'
import type { Metadata } from 'next'
import { Baloo_2, Hind } from 'next/font/google'
import MarketingShell from '@/components/marketing/MarketingShell'
import { siteLinks, FOR_AGENTS_PATH, INVITE_PATH } from '@/components/marketing/siteLinks'
import { getMarketingConfig } from '@/lib/marketing/config'
import { pageMetadata } from '@/lib/marketing/seo'
import { BRAND_NAME, LOGO, TAGLINE, demoAgentPath, siteUrl } from '@/lib/brand'
import InviteQr from './InviteQr'
import { FOR_AGENTS as C } from './content'

const baloo = Baloo_2({ subsets: ['latin'], weight: ['800'], display: 'swap' })
const hind = Hind({ subsets: ['devanagari', 'latin'], weight: ['500', '600'], display: 'swap' })

export const metadata: Metadata = pageMetadata(getMarketingConfig(), {
  title: C.metaTitle,
  description: C.metaDescription,
  path: FOR_AGENTS_PATH,
})

const wrap = 'mx-auto max-w-5xl px-4'
const h2 = 'text-2xl font-extrabold tracking-tight text-[#0f2340] sm:text-3xl print:text-[15pt]'
const section = 'py-10 sm:py-14 print:py-[3.5mm]'
const short = (url: string) => url.replace(/^https?:\/\//, '').replace(/\/$/, '')

/* Print: A4, two pages, no header/footer/chat, every link printed as its address.
   The app's global print sheet (styles/components.css) makes every background transparent and all text black. Inside this
   brochure we restore colour inheritance and re-apply the brand colours that the Tailwind classes in the markup use, so the
   PDF keeps navy, gold and cream. Keep these maps in step with the classes below. */
const esc = (cls: string) => cls.replace(/[^a-zA-Z0-9_-]/g, (c) => '\\' + c)
const PRINT_BG: Record<string, string> = {
  'bg-[#0f2340]': '#0f2340', 'fa-navy': '#102340', 'bg-[#f0b440]': '#f0b440', 'bg-[#fbf6ea]': '#fbf6ea', 'bg-white': '#fff',
  'bg-[#fbf1d8]': '#fbf1d8', 'bg-[#e6f4f1]': '#e6f4f1', 'bg-white/15': 'rgba(255,255,255,.15)', 'bg-white/[0.06]': 'rgba(255,255,255,.07)',
}
const PRINT_TEXT: Record<string, string> = {
  'text-white': '#fff', 'text-[#f0b440]': '#f0b440', 'text-[#0f2340]': '#0f2340', 'text-slate-100': '#f1f5f9', 'text-slate-200': '#e2e8f0',
  'text-slate-600': '#475569', 'text-slate-700': '#334155', 'text-slate-800': '#1e293b', 'text-[#8a6410]': '#8a6410',
  'text-[#0b3f3a]': '#0b3f3a', 'text-[#0f766e]': '#0f766e',
}
const PRINT_BORDER: Record<string, string> = {
  'border-[#ead9ae]': '#ead9ae', 'border-slate-200': '#e2e8f0', 'border-[#f0b440]': '#f0b440', 'border-white/15': 'rgba(255,255,255,.15)',
}
const rules = (m: Record<string, string>, prop: string) =>
  Object.entries(m).map(([cls, v]) => `  .fa-root .${esc(cls)} { ${prop}: ${v} !important; }`).join('\n')
const PRINT_CSS = `
@media print {
  @page { size: A4; margin: 10mm 11mm; }
  html { font-size: 10.5px !important; }
  html, body, #main-content, [data-surface] { background: #fff !important; min-height: 0 !important; }
  [data-print="hide"], #navigation, [data-testid="chat-widget"] { display: none !important; }
  .fa-root { color: #0f172a !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .fa-root * { color: inherit !important; }
  .fa-root a { text-decoration: none !important; }
  .fa-page2 { break-before: page; }
  .fa-keep { break-inside: avoid; }
${rules(PRINT_BG, 'background-color')}
${rules(PRINT_TEXT, 'color')}
${rules(PRINT_BORDER, 'border-color')}
}
`

function Check({ className = '' }: { className?: string }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" className={'shrink-0 ' + className} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
  )
}

const GET_ICONS = [
  // page, megaphone, inbox, chart
  'M4 5h16v14H4zM4 9h16M8 13h5M8 16h8',
  'M4 10v4h3l6 4V6L7 10H4zM17 9a4 4 0 010 6',
  'M4 13l2-8h12l2 8v6H4zM4 13h5l1 2h4l1-2h5',
  'M5 19V11M10 19V6M15 19v-6M20 19V9',
]

export default function ForAgentsPage() {
  const s = siteLinks()
  const site = siteUrl()
  const inviteUrl = site + INVITE_PATH
  const live = [
    { label: 'A demo agent page', note: 'What your page looks like (fictional agent, sample homes)', href: demoAgentPath(), url: site + demoAgentPath() },
    { label: `${BRAND_NAME} on Instagram`, note: 'Designed posts and reels', href: s.instagram.href, url: s.instagram.href, external: true },
    { label: 'Latest homes and posts', note: 'The tap-to-show-interest hub', href: '/go', url: site + '/go' },
    { label: 'Pune property news', note: 'Plain-language news, with sources', href: '/news', url: site + '/news' },
  ]
  return (
    <MarketingShell>
      <style dangerouslySetInnerHTML={{ __html: PRINT_CSS }} />
      <article className="fa-root" aria-labelledby="fa-title">
        {/* Hero */}
        <header className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] text-white fa-navy print:bg-none">
          <div className={wrap + ' grid items-center gap-8 py-10 sm:py-14 md:grid-cols-[1.35fr_1fr] print:!grid-cols-[1.5fr_1fr] print:gap-[6mm] print:py-[7mm]'}>
            <div>
              <p className="flex items-center gap-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={LOGO.mark} alt="" width={44} height={44} className="h-11 w-11" />
                <span className="leading-none">
                  <span className={baloo.className + ' block text-[1.9rem] font-extrabold leading-none tracking-tight text-white'}>{BRAND_NAME}</span>
                  <span className="mt-1 block text-sm font-medium text-[#f0b440]">{TAGLINE}</span>
                </span>
              </p>
              <p className="mt-6 flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-wide text-[#f0b440]">
                <span>{C.eyebrow}</span>
                <span className="rounded-full bg-[#f0b440] px-2.5 py-0.5 text-[#0f2340]">{C.pilot}</span>
              </p>
              <h1 id="fa-title" className="mt-3 text-[1.9rem] font-extrabold leading-[1.15] tracking-tight sm:text-[2.6rem] print:text-[20pt]">{C.title}</h1>
              <p className="mt-4 text-base leading-relaxed text-slate-100 sm:text-lg">{C.lead}</p>
              <div className="mt-6 flex flex-wrap gap-3 print:hidden">
                <Link href={INVITE_PATH} className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:w-auto">{C.cta.button}</Link>
                <Link href={demoAgentPath()} className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-white/70 px-6 text-lg font-bold text-white no-underline hover:bg-white/10 sm:w-auto">{C.cta.demo}</Link>
              </div>
            </div>
            <div className="rounded-2xl border border-white/15 bg-white/[0.06] p-5 print:p-[4mm]">
              <p className="text-xs font-bold uppercase tracking-wide text-[#f0b440]">In your language</p>
              <ul className="mt-3 space-y-3 p-0">
                {C.summaries.map((x) => (
                  <li key={x.lang} lang={x.lang} className={hind.className + ' list-none text-[1.05rem] font-medium leading-relaxed text-white'}>
                    <span className="mr-2 rounded bg-white/15 px-1.5 py-0.5 text-xs font-semibold text-[#f0b440]">{x.label}</span>
                    {x.text}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </header>

        {/* The agent's problem */}
        <section aria-labelledby="fa-problem" className={'bg-[#fbf6ea] ' + section}>
          <div className={wrap}>
            <h2 id="fa-problem" className={h2}>{C.problem.heading}</h2>
            <ul className="mt-5 grid gap-3 p-0 md:grid-cols-3 print:mt-[3mm] print:!grid-cols-3 print:gap-[3mm]">
              {C.problem.items.map((p) => (
                <li key={p.title} className="fa-keep list-none rounded-2xl border border-[#ead9ae] bg-white p-5 print:p-[3.5mm]">
                  <h3 className="text-lg font-bold text-[#0f2340]">{p.title}</h3>
                  <p className="mt-1.5 leading-relaxed text-slate-700">{p.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Create -> Attract -> Qualify -> Close */}
        <section id="how" aria-labelledby="fa-steps" className={section}>
          <div className={wrap}>
            <h2 id="fa-steps" className={h2}>{C.steps.heading}</h2>
            <ol className="mt-5 grid gap-3 p-0 sm:grid-cols-2 lg:grid-cols-4 print:mt-[3mm] print:!grid-cols-4 print:gap-[3mm]">
              {C.steps.items.map((st, i) => (
                <li key={st.key} className="fa-keep list-none rounded-2xl bg-[#0f2340] p-5 text-white print:p-[3.5mm]">
                  <p className="flex items-center gap-3 text-sm font-bold uppercase tracking-wide text-[#f0b440]">
                    <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-[#f0b440] text-base font-extrabold text-[#0f2340]">{i + 1}</span>
                    {st.label}
                  </p>
                  <h3 className="mt-3 text-lg font-bold leading-snug">{st.title}</h3>
                  <p className="mt-1.5 leading-relaxed text-slate-100">{st.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* What you get */}
        <section aria-labelledby="fa-gets" className={'fa-page2 bg-slate-50 print:bg-white ' + section}>
          <div className={wrap}>
            <h2 id="fa-gets" className={h2}>{C.gets.heading}</h2>
            <ul className="mt-5 grid gap-3 p-0 sm:grid-cols-2 print:mt-[3mm] print:!grid-cols-2 print:gap-[3mm]">
              {C.gets.items.map((g, i) => (
                <li key={g.title} className="fa-keep flex list-none gap-4 rounded-2xl border border-slate-200 bg-white p-5 print:p-[3.5mm]">
                  <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#fbf1d8] text-[#0f2340]">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={GET_ICONS[i]} /></svg>
                  </span>
                  <span>
                    <h3 className="text-lg font-bold text-[#0f2340]">{g.title}</h3>
                    <p className="mt-1 leading-relaxed text-slate-700">{g.body}</p>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Cost, what is coming, trust */}
        <section aria-label="Cost, what is coming and trust" className={section}>
          <div className={wrap + ' grid gap-4 md:grid-cols-3 print:!grid-cols-3 print:gap-[3mm]'}>
            <div className="fa-keep rounded-2xl border-2 border-[#f0b440] bg-[#fbf6ea] p-5 print:p-[3.5mm]">
              <h2 id="fa-cost" className="text-sm font-bold uppercase tracking-wide text-[#8a6410]">{C.cost.heading}</h2>
              <p className="mt-2 text-2xl font-extrabold text-[#0f2340]">{C.cost.title}</p>
              <p className="mt-2 leading-relaxed text-slate-800">{C.cost.body}</p>
            </div>
            <div className="fa-keep rounded-2xl border border-slate-200 bg-white p-5 print:p-[3.5mm]">
              <h2 id="fa-coming" className="text-sm font-bold uppercase tracking-wide text-slate-600">{C.coming.heading}</h2>
              <ul className="mt-2 space-y-2 p-0">
                {C.coming.items.map((t) => (
                  <li key={t} className="flex list-none gap-2 leading-relaxed text-slate-800"><span aria-hidden="true" className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[#f0b440]" />{t}</li>
                ))}
              </ul>
              <p className="mt-2 text-sm text-slate-600">{C.coming.note}</p>
            </div>
            <div className="fa-keep rounded-2xl bg-[#e6f4f1] p-5 text-[#0b3f3a] print:p-[3.5mm]">
              <h2 id="fa-trust" className="text-sm font-bold uppercase tracking-wide">{C.trust.heading}</h2>
              <ul className="mt-2 space-y-2 p-0">
                {C.trust.items.map((t) => (
                  <li key={t} className="flex list-none gap-2 leading-relaxed"><Check className="mt-0.5 text-[#0f766e]" />{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* See it live */}
        <section aria-labelledby="fa-live" className={'bg-[#fbf6ea] ' + section}>
          <div className={wrap}>
            <h2 id="fa-live" className={h2}>{C.live.heading}</h2>
            <p className="mt-1 text-slate-700">{C.live.lead}</p>
            <ul className="mt-4 grid gap-3 p-0 sm:grid-cols-2 print:mt-[2.5mm] print:!grid-cols-2 print:gap-[2.5mm]">
              {live.map((l) => (
                <li key={l.label} className="fa-keep list-none">
                  <a href={l.href} {...(l.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                    className="flex h-full min-h-[64px] flex-col justify-center rounded-2xl border border-[#ead9ae] bg-white px-5 py-3 no-underline hover:border-[#0f2340] print:min-h-0 print:px-[3.5mm] print:py-[2.5mm]">
                    <span className="font-bold text-[#0f2340]">{l.label}{l.external && <span className="sr-only"> (opens in a new tab)</span>}</span>
                    <span className="text-sm text-slate-600">{l.note}</span>
                    <span className="mt-1 break-all text-sm font-semibold text-[#8a6410]">{short(l.url)}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Call to action + QR */}
        <section id="invite" aria-labelledby="fa-cta" className="bg-gradient-to-b from-[#0f2340] to-[#183a5d] py-10 text-white sm:py-14 fa-navy print:bg-none print:py-[5mm]">
          <div className={wrap + ' grid items-center gap-8 md:grid-cols-[1.4fr_1fr] print:!grid-cols-[1.6fr_1fr] print:gap-[6mm]'}>
            <div>
              <h2 id="fa-cta" className="text-2xl font-extrabold sm:text-3xl print:text-[15pt]">{C.cta.heading}</h2>
              <p className="mt-3 text-lg leading-relaxed text-slate-100">{C.cta.body}</p>
              <p data-testid="print-invite" className="mt-[3mm] hidden text-lg text-white print:block">
                Open <strong className="text-[#f0b440]">{short(inviteUrl)}</strong> or scan the code.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 print:hidden">
                <Link href={INVITE_PATH}
                  className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-[#f0b440] px-7 text-lg font-extrabold text-[#0f2340] no-underline hover:bg-[#f5c75e] sm:w-auto">
                  {C.cta.button}
                </Link>
                <Link href={demoAgentPath()} className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-white/70 px-6 text-lg font-bold text-white no-underline hover:bg-white/10 sm:w-auto print:hidden">
                  {C.cta.demo}
                </Link>
              </div>
            </div>
            <figure className="mx-auto w-full max-w-[15rem] rounded-2xl bg-white p-4 text-center text-[#0f2340] print:max-w-[45mm] print:p-[3mm]">
              <InviteQr value={inviteUrl} label={`QR code: ${short(inviteUrl)}`} className="mx-auto block h-auto w-full" />
              <figcaption className="mt-2 text-sm font-bold">{C.cta.qr}</figcaption>
              <p className="text-[11px] leading-snug text-slate-600 [overflow-wrap:anywhere]">{short(site)}<wbr />{INVITE_PATH}</p>
            </figure>
          </div>
        </section>
      </article>
    </MarketingShell>
  )
}
