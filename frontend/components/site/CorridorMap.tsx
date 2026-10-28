import React from 'react'
import Link from 'next/link'

/**
 * What is running and what is coming along the east Pune corridor (Nagar Road), drawn as a transit diagram for the home page's
 * hero (owner 2026-10-28: "show what is coming, metro, commercial spaces, corridor"). Drawn, not a picture: no photo of a line that
 * is not built exists, and a generated one would show a finished metro the site's own trackers say is years away.
 *
 * Every status here is the one the site already states (calendar/guides/upper-kharadi-metro-en.json, knowledge/areas.py and the
 * newsroom trackers): Line 2 runs to Ramwadi; Line 2B (Ramwadi to Wagholi/Vitthalwadi, 11 stations) was approved in June 2025 and
 * work began at Ramwadi in September 2026, its first phase to Tulja Bhavani; Line 4 (Kharadi to Khadakwasla) is approved. Change
 * them here when a tracker moves. The six-lane elevated road under the 2B viaduct (MSIDC, same pillars) and ITPP Kharadi (CapitaLand,
 * open since May 2023) were checked on 2026-10-29 (Punekar News, The Bridge Chronicle, capitaland.com); a pasted chatbot summary
 * the owner sent then had a wrong length for 2B and called the Ring Road's land "nearly acquired", so nothing here comes from it. It is a diagram, not a map to scale: the stations are evenly spaced.
 */
export const CORRIDOR_AS_OF = 'October 2026'

const RUN = '#2dd4bf'      // running: teal, like the trains
const BUILD = '#f0b440'    // work started: brand gold, solid
const APPROVED = '#f0b440' // approved: the same gold, dashed
const LINE4 = '#93c5fd'

// Line 2B in order, x along the diagram; the labelled ones alternate above and below the line so they never touch
const STATIONS: { name: string; x: number; label?: 'up' | 'down' }[] = [
  { name: 'Ramwadi', x: 96, label: 'down' },
  { name: 'Viman Nagar', x: 140 },
  { name: 'Somnath Nagar', x: 182 },
  { name: 'Kharadi Bypass', x: 224 },
  { name: 'Tulja Bhavani', x: 266, label: 'up' },
  { name: 'Ubale Nagar', x: 308 },
  { name: 'Upper Kharadi Road', x: 350, label: 'down' },
  { name: 'Wagheshwar Temple', x: 392 },
  { name: 'Wagholi', x: 434, label: 'up' },
  { name: 'Siddharth Nagar', x: 476 },
  { name: 'Bakori Phata', x: 518 },
  { name: 'Vitthalwadi', x: 560, label: 'down' },
]
const Y = 122
const PHASE1_END = 266

// what is coming, each with the stage it has reached and the page that follows it
const COMING: { name: string; status: string; href: string }[] = [
  { name: 'Metro Line 2B to Wagholi', status: 'Work started, Sep 2026', href: '/insights/metro-kharadi-wagholi-approved-not-running' },
  { name: 'Six-lane elevated road under the metro', status: 'Work started, Sep 2026', href: '/insights/metro-kharadi-wagholi-approved-not-running' },
  { name: 'Metro Line 4, Kharadi to Khadakwasla', status: 'Approved', href: '/insights/metro-kharadi-wagholi-approved-not-running' },
  { name: 'Ring Road, east arm', status: 'Land acquisition', href: '/news/track/pune-ring-road' },
  { name: 'HCMTR on Nagar Road', status: 'Land survey', href: '/news/track/hcmtr' },
]
// what is already there and draws people to the corridor
const OPEN: { kind: string; names: string }[] = [
  { kind: 'Offices', names: 'EON IT Park, World Trade Center, ITPP Kharadi (since 2023), Zensar' },
  { kind: 'Shopping', names: 'Phoenix Marketcity, Viman Nagar' },
  { kind: 'Airport', names: 'Pune Airport, Lohegaon' },
]

export default function CorridorMap() {
  return (
    <figure className="m-0 rounded-xl bg-white/[0.04] p-4 ring-1 ring-inset ring-white/15 sm:p-5" data-testid="corridor-map">
      <figcaption>
        <p className="font-semibold text-white">East Pune corridor: running and coming</p>
        <p className="text-sm text-white/65">Nagar Road, Ramwadi to Wagholi</p>
        <ul className="mt-2 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-xs text-white/70">
          <li className="flex items-center gap-1.5"><svg aria-hidden width="22" height="6"><line x1="1" y1="3" x2="21" y2="3" stroke={RUN} strokeWidth="4" strokeLinecap="round" /></svg>Running</li>
          <li className="flex items-center gap-1.5"><svg aria-hidden width="22" height="6"><line x1="1" y1="3" x2="21" y2="3" stroke={BUILD} strokeWidth="4" strokeLinecap="round" /></svg>Work started</li>
          <li className="flex items-center gap-1.5"><svg aria-hidden width="22" height="6"><line x1="1" y1="3" x2="21" y2="3" stroke={APPROVED} strokeWidth="3" strokeDasharray="4 4" /></svg>Approved, not started</li>
          <li className="flex items-center gap-1.5"><svg aria-hidden width="22" height="6"><line x1="1" y1="3" x2="21" y2="3" stroke="white" strokeOpacity="0.55" strokeWidth="2" strokeDasharray="3 3" /></svg>Elevated road</li>
        </ul>
      </figcaption>

      <svg viewBox="0 0 600 214" className="mt-3 block h-auto w-full" role="img" fontFamily="inherit"
        aria-label="Diagram: Metro Line 2 runs to Ramwadi. Line 2B, Ramwadi to Vitthalwadi through Kharadi, Upper Kharadi Road and Wagholi, is approved; work started in September 2026 on the first phase, to Tulja Bhavani. Line 4 from Kharadi to Khadakwasla is approved. A six-lane elevated road is planned under the Line 2B viaduct. Pune airport at Lohegaon and the EON IT Park, World Trade Center and ITPP offices sit along the line.">
        {/* Nagar Road under the line */}
        <line x1="20" y1={Y + 8} x2="584" y2={Y + 8} stroke="white" strokeOpacity="0.12" strokeWidth="14" strokeLinecap="round" />
        <text x="24" y={Y + 62} fontSize="13" fill="white" fillOpacity="0.45" letterSpacing="1.5">NAGAR ROAD</text>
        {/* the elevated road MSIDC builds under the 2B viaduct, on the same pillars: drawn just below the line, as far as Wagholi */}
        <line x1={STATIONS[0].x} y1={Y + 13} x2="434" y2={Y + 13} stroke="white" strokeOpacity="0.55" strokeWidth="2" strokeDasharray="3 3" />

        {/* the airport and the office parks, above the stations they sit near */}
        <g transform="translate(118 30)">
          <circle r="15" fill="white" fillOpacity="0.1" />
          <path d="M-7 1 L7 -4 L8 -2 L-1 2 L1 8 L-1 8 L-4 3 L-8 4 Z" fill="white" fillOpacity="0.85" />
          <text x="22" y="0" fontSize="17" fontWeight="600" fill="white">Pune Airport</text>
          <text x="22" y="18" fontSize="14" fill="white" fillOpacity="0.6">Lohegaon · open</text>
        </g>
        <line x1="140" y1="52" x2="140" y2={Y - 10} stroke="white" strokeOpacity="0.2" strokeDasharray="2 4" />
        <g transform="translate(330 30)">
          <rect x="-15" y="-15" width="30" height="30" rx="7" fill="white" fillOpacity="0.1" />
          <rect x="-8" y="-8" width="6" height="16" fill="white" fillOpacity="0.85" />
          <rect x="0" y="-4" width="6" height="12" fill="white" fillOpacity="0.85" />
          <text x="22" y="0" fontSize="17" fontWeight="600" fill="white">EON · WTC · ITPP</text>
          <text x="22" y="18" fontSize="14" fill="white" fillOpacity="0.6">Kharadi offices · open</text>
        </g>
        <line x1="224" y1="52" x2="224" y2={Y - 10} stroke="white" strokeOpacity="0.2" strokeDasharray="2 4" />

        {/* Line 2, running, comes in from the city; Line 2B carries on east */}
        <line x1="24" y1={Y} x2={STATIONS[0].x} y2={Y} stroke={RUN} strokeWidth="7" strokeLinecap="round" />
        <text x="22" y={Y - 16} fontSize="15" fill={RUN}>Line 2</text>
        <line x1={STATIONS[0].x} y1={Y} x2={PHASE1_END} y2={Y} stroke={BUILD} strokeWidth="7" />
        <line x1={PHASE1_END} y1={Y} x2={STATIONS[STATIONS.length - 1].x} y2={Y} stroke={APPROVED} strokeWidth="5" strokeDasharray="9 7" />

        {/* Line 4 leaves Kharadi south-west, towards Hadapsar and Khadakwasla */}
        <path d={`M 224 ${Y + 12} L 224 ${Y + 52} L 196 ${Y + 80}`} fill="none" stroke={LINE4} strokeWidth="4" strokeDasharray="7 6" />
        <text x="236" y={Y + 74} fontSize="15" fill={LINE4}>Line 4, Kharadi to Khadakwasla · approved</text>

        {STATIONS.map((s, i) => (
          <g key={s.name}>
            <circle cx={s.x} cy={Y} r={s.label ? 7 : 5} fill="#0f2340" stroke={i === 0 ? RUN : BUILD} strokeWidth="3" />
            {s.label && (
              <text x={s.x} y={s.label === 'up' ? Y - 18 : Y + 32} fontSize="17" fontWeight={s.name === 'Upper Kharadi Road' ? 700 : 500}
                fill="white" fillOpacity={s.name === 'Upper Kharadi Road' ? 1 : 0.85} textAnchor={i === STATIONS.length - 1 ? 'end' : 'middle'}>{s.name}</text>
            )}
          </g>
        ))}
      </svg>

      <p className="mt-2 text-xs leading-relaxed text-white/65">
        Line 2B (11 stations) was approved in June 2025; work began at Ramwadi in September 2026, and the first phase runs to Tulja Bhavani.
        No opening date is announced for Upper Kharadi Road or Wagholi.
      </p>
      <p className="mt-3 text-[11px] text-white/45">Diagram, not to scale. Status as of {CORRIDOR_AS_OF}: Maha-Metro, PIB, MSRDC, MSIDC and our trackers.</p>
    </figure>
  )
}

/** The corridor's other works and what is already open, under the hero: the hero card keeps to the diagram so it stays as tall
 *  as the promise beside it. */
export function CorridorStatus() {
  return (
    <section aria-labelledby="corridor-title" className="border-b border-slate-200 bg-slate-50 py-10 sm:py-12" data-testid="corridor-status">
      <div className="mx-auto max-w-5xl px-4">
        <h2 id="corridor-title" className="text-[1.375rem] font-semibold tracking-tight text-slate-900 sm:text-2xl">What is coming to east Pune</h2>
        <p className="mt-1 max-w-2xl text-slate-600">Each with the stage it has actually reached, as of {CORRIDOR_AS_OF}. Approved is not the same as running.</p>
        <div className="mt-6 grid gap-8 md:grid-cols-[1.4fr_1fr] md:gap-12">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Coming</h3>
            <ul className="mt-2 list-none border-t border-slate-200 p-0">
              {COMING.map((a) => (
                <li key={a.name} className="border-b border-slate-200">
                  <Link href={a.href} className="group flex min-h-[52px] items-center gap-3 py-3 no-underline">
                    <span className="min-w-0 flex-1 font-medium text-slate-900 underline-offset-4 group-hover:text-[#0f2340] group-hover:underline">{a.name}</span>
                    <span className="shrink-0 text-right text-sm text-slate-600">{a.status}</span>
                    <svg aria-hidden viewBox="0 0 20 20" className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-[#0f2340]">
                      <path d="M7.5 4.5 13 10l-5.5 5.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Already open</h3>
            <dl className="mt-2 border-t border-slate-200">
              {OPEN.map((o) => (
                <div key={o.kind} className="border-b border-slate-200 py-3">
                  <dt className="text-sm text-slate-500">{o.kind}</dt>
                  <dd className="m-0 font-medium text-slate-900">{o.names}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </section>
  )
}
