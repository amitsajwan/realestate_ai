'use client'

import type { MarketingRun, RoomPiece } from '@/lib/app/types'

const ROLE_NAMES: Record<string, string> = {
  teaser: 'Teaser', brand: 'Brand', design: 'Design', homes: 'The homes', lifestyle: 'Lifestyle', location: 'Location',
  price: 'Price', trust: 'Trust', visit: 'Visit', story: 'Story',
}
const roleName = (r: string) => ROLE_NAMES[r] ?? r
const SEATS = ['Strategist', 'Copywriter', 'Art director', 'Film director', 'Reel creator', 'Creative director']

function Piece({ p, n }: { p: RoomPiece; n: number }) {
  return (
    <li className="flex gap-3">
      <span aria-hidden className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-bold text-white">{n}</span>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          {roleName(p.role)} · {p.format}{p.reel ? ' · reel' : ''}
        </p>
        <p className="font-semibold text-gray-900">{p.headline}</p>
        <p className="text-sm text-gray-600">{p.lines.join(' · ')}</p>
        {p.reel && <p className="mt-1 text-xs text-violet-700">Reel: “{p.reel.hook}” → {p.reel.payoff}</p>}
        {p.source && <p className="mt-1 text-xs text-gray-500">From the {p.source.by.toLowerCase()}’s pitch</p>}
      </div>
    </li>
  )
}

/** The creative room: the strategist's brief, the three pitches with the creative director's scores, and the campaign chosen.
 *  `onPick(n)` remakes the campaign from pitch n (1-based). */
export function CreativeRoom({ run, onPick }: { run: MarketingRun; onPick: (n: number) => void }) {
  const room = run.room
  const running = ['queued', 'facts', 'posts'].includes(run.status)
  if (!room) {
    if (run.step !== 'room') return null
    return (
      <div className="rounded-2xl border border-violet-200 bg-violet-50 p-4" role="status">
        <p className="font-bold text-violet-900">The creative room is meeting</p>
        <p className="mt-1 text-sm text-violet-800">
          {SEATS.join(', ')}: the brief, four pitches, a discussion, then one campaign merged from the best. A few minutes.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {SEATS.map((s) => <span key={s} className="animate-pulse rounded-full bg-white px-3 py-1 text-xs font-semibold text-violet-800">{s}</span>)}
        </div>
      </div>
    )
  }
  const b = room.brief
  const camp = room.campaign
  return (
    <div className="space-y-4 rounded-2xl border border-violet-200 bg-gradient-to-b from-violet-50 to-white p-4">
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-violet-700">Creative room</p>
        <h3 className="text-lg font-bold text-gray-900">{b.positioning || 'The brief'}</h3>
        {b.idea && <p className="mt-1 text-base italic text-gray-800">“{b.idea}”</p>}
      </div>

      {(b.buyers?.length ?? 0) > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Who buys it</p>
          <ul className="mt-1 flex list-none flex-wrap gap-2 p-0">
            {b.buyers!.map((x) => (
              <li key={x.who} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm">
                <span className="font-semibold text-gray-900">{x.who}</span>
                {x.why && <span className="text-gray-600"> · {x.why}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {(b.tone || (b.avoid?.length ?? 0) > 0) && (
        <p className="text-sm text-gray-700">
          {b.tone && <><span className="font-semibold">Tone:</span> {b.tone}. </>}
          {(b.avoid?.length ?? 0) > 0 && <><span className="font-semibold">Avoid:</span> {b.avoid!.join(', ')}.</>}
        </p>
      )}

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">The pitches</p>
        <ul className="mt-2 grid list-none gap-3 p-0 sm:grid-cols-2">
          {room.pitches.map((p, i) => {
            const chosen = room.chosen === i + 1
            return (
              <li key={p.name + i} className={`flex flex-col rounded-xl border bg-white p-3 ${chosen ? 'border-violet-600 ring-2 ring-violet-600' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-gray-500">{p.by}</span>
                  {typeof p.score === 'number' && p.score > 0 && (
                    <span className="rounded-full bg-gray-900 px-2 py-0.5 text-xs font-bold text-white">{p.score}/10</span>
                  )}
                </div>
                <p className="mt-1 font-bold text-gray-900">{p.name}</p>
                {p.idea && <p className="text-sm text-gray-700">{p.idea}</p>}
                <ul className="mt-2 list-disc space-y-0.5 pl-4 text-xs text-gray-600">
                  {p.pieces.map((x, j) => <li key={j}>{roleName(x.role)}: {x.headline}{x.reel ? ' 🎬' : ''}</li>)}
                </ul>
                {p.note && <p className="mt-2 text-xs italic text-gray-500">Director: {p.note}</p>}
                <div className="mt-auto pt-3">
                  {chosen ? (
                    <span className="inline-block rounded-full bg-violet-600 px-3 py-1 text-xs font-bold text-white">
                      {run.pick ? 'Your pick' : 'Director’s pick'}
                    </span>
                  ) : (
                    <button type="button" disabled={running} onClick={() => onPick(i + 1)}
                      className="min-h-[44px] w-full rounded-xl border border-violet-600 px-3 text-sm font-semibold text-violet-700 disabled:opacity-50">
                      Use this pitch
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      </div>

      {(room.discussion?.talk?.length ?? 0) > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">The discussion</p>
          <ul className="mt-2 list-none space-y-2 p-0">
            {room.discussion!.talk.map((x, i) => (
              <li key={i} className="rounded-xl border border-gray-200 bg-white p-3 text-sm">
                <p className="font-semibold text-gray-900">{x.seat}{x.builds_on ? ` on pitch ${x.builds_on}` : ''}</p>
                {x.build && <p className="text-gray-700">💡 {x.build}</p>}
                {x.concern && <p className="text-gray-500">⚠️ {x.concern}</p>}
              </li>
            ))}
          </ul>
          {(room.discussion!.best?.length ?? 0) > 0 && (
            <p className="mt-2 text-sm text-gray-700">
              <span className="font-semibold">Strongest ideas:</span> {room.discussion!.best.map((b) => b.idea).join(' · ')}
            </p>
          )}
        </div>
      )}

      {camp?.pieces?.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">The campaign, merged from the best, in posting order</p>
          <p className="text-base font-bold text-gray-900">{camp.name}</p>
          {camp.idea && <p className="text-sm text-gray-700">{camp.idea}</p>}
          {room.why && <p className="mt-1 text-xs italic text-gray-500">Why this one: {room.why}</p>}
          <ol className="mt-3 list-none space-y-3 p-0">
            {camp.pieces.map((p, i) => <Piece key={i} p={p} n={i + 1} />)}
          </ol>
          <p className="mt-3 text-xs text-gray-500">
            Every line was checked against {room.facts} facts; anything the facts don’t back was cut.
          </p>
        </div>
      )}
    </div>
  )
}
