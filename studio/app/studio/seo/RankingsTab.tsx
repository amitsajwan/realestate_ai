'use client'
import React, { useState } from 'react'
import { LinkOut, StatusPill } from '@/components/app/list'
import { ErrorBox, Spinner } from '@/components/app/ui'
import { timeAgo } from '@/lib/app/format'
import { errorMessage } from '@/lib/app/client'
import { getRankings, revertPage } from '@/lib/app/insights'
import type { AiVisits, BoardLeader, BoardRow, BoardStanding, PageCheck, PageContent, ProjectIndex, RankAction, RankTarget, Scoreboard, WeekNumbers } from '@/lib/app/insights'
import { useAsync } from '@/lib/app/useAsync'
import { getNotifications, markNotificationRead } from '@/lib/app/whatsapp'

// Insights → Rankings (docs/plan/rank-loop.md R9): the rank loop's numbers, fixes and results, read-only except "Undo".
const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://avasetu.in'
const FIX_LABEL: Record<string, string> = { title: 'Title from search', faq: 'Buyer questions', links: 'Link slot', refresh: 'Refresh facts',
  description: 'Search description', rival: 'Facts MagicBricks shows' }
// each number with what it counts, so the owner reads it the way the code counts it (owner 2026-11-06: "still not clear, what and why")
const WEEK_ROWS: [keyof WeekNumbers, string, string][] = [
  ['clicks', 'Clicks (28 days)', 'People who clicked one of our project pages in Google.'],
  ['impressions', 'Impressions (28 days)', 'Times a project page of ours was shown in Google results, clicked or not.'],
  ['page_one', 'Project pages on page one', 'Pages whose average Google place is 1-10, over every search they showed for, even one seen once.'],
  ['near_page_one', 'Pages near page one', 'Average place 8-20 and shown 20+ times: the pages a better page most often lifts. The doctor works these first.'],
  ['targeted', 'Pages with a target search', 'Pages given the one search they should win (the most-seen search in Search Console). Grows only as pages get seen.'],
]
const card = 'list-none rounded-2xl bg-white p-3'
const btn = 'min-h-[44px] rounded-xl border border-gray-300 px-3 text-sm font-semibold text-[#0f2340] active:bg-gray-100 disabled:text-gray-400'
const day = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '')
const pos = (p: number | null | undefined) => (p == null ? '-' : `#${Math.round(p * 10) / 10}`)

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-2xl bg-white p-4 text-sm text-gray-600">{children}</p>
}

/** Google position over the last readings: lower on the chart is better (position 1 at the top). */
function Trend({ t }: { t: RankTarget }) {
  const pts = t.history.filter((h) => h.position != null).map((h) => h.position as number)
  if (pts.length < 2) return null
  const max = Math.max(...pts, 10)
  const w = 120
  const h = 28
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${((i / (pts.length - 1)) * w).toFixed(1)},${((p / max) * h).toFixed(1)}`).join(' ')
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`position from ${pos(pts[0])} to ${pos(pts[pts.length - 1])}`}>
      <path d={d} fill="none" stroke="#0f2340" strokeWidth="1.5" />
    </svg>
  )
}

function ActionRow({ a, onDone }: { a: RankAction; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const undo = async () => {
    setBusy(true); setErr(null)
    try { await revertPage(a.path); onDone() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  const after = a.after28 ?? a.after14
  return (
    <li className={card}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 break-words font-semibold text-gray-900">{FIX_LABEL[a.fix] ?? a.fix} · <span className="font-normal">{a.path}</span></p>
        {a.gain != null && <StatusPill tone={a.gain > 0 ? 'ok' : a.gain < 0 ? 'bad' : 'muted'}>{a.gain > 0 ? '+' : ''}{a.gain} positions</StatusPill>}
      </div>
      <p className="text-xs text-gray-600">
        {day(a.at)}{a.phrase ? ` · "${a.phrase}"` : ''} · before {pos(a.before?.position)}, {a.before?.clicks ?? 0} clicks
        {after ? ` · after ${a.after28 ? 28 : 14} days ${pos(after.position)}, ${after.clicks} clicks` : ' · not measured yet'}
        {a.reverted ? ' · undone' : ''}
      </p>
      {a.new && <p className="mt-1 text-sm text-gray-800">Now: {a.new}</p>}
      {a.note && <p className="text-xs text-gray-500">{a.note}</p>}
      {(a.fix === 'title' || a.fix === 'description') && !a.reverted && (
        <button type="button" className={`${btn} mt-2`} disabled={busy} onClick={undo}>{busy ? 'Undoing…' : 'Undo on this page'}</button>
      )}
      {err && <p className="mt-1 text-sm text-red-700">{err}</p>}
    </li>
  )
}

const place = (p: number | null) => (p == null ? 'not top 10' : `#${p}`)

// the kinds of search the board counts (backend areastats.websearch); our own number and builder lookups are not counted
const KIND_LABEL: Record<string, [string, string]> = {
  area: ['Area searches', 'What buyers type for an area, e.g. "flats in Kharadi Pune". The searches that matter most.'],
  project: ['Project-name searches', 'A project name plus area, e.g. "Casa Saptak Lohegaon Pune". Easy to win: the name is on our page.'],
  target: ["Pages' own searches", "The search each page gets most in Search Console, checked on Google."],
  other: ['Other searches', ''],
}
const KIND_ORDER = ['area', 'target', 'project', 'other']

function BoardLine({ r }: { r: BoardRow }) {
  return (
    <li className="break-words text-xs text-gray-700">
      &quot;{r.query}&quot;: us {place(r.ours)}, MagicBricks {place(r.magicbricks)}, 99acres {place(r.acres99)}, Housing {place(r.housing)}
      {r.page && <> · <LinkOut href={SITE + r.page}>{r.page}</LinkOut></>}
    </li>
  )
}

function RowList({ title, hint, rows }: { title: string; hint: string; rows?: BoardRow[] }) {
  const [all, setAll] = useState(false)
  if (!rows?.length) return null
  return (
    <div className="mt-3">
      <p className="text-sm font-semibold text-gray-900">{title}</p>
      <p className="text-xs text-gray-600">{hint}</p>
      <ul className="mt-1 space-y-1 p-0">{(all ? rows : rows.slice(0, 5)).map((r) => <BoardLine key={r.query} r={r} />)}</ul>
      {rows.length > 5 && <button type="button" className={`${btn} mt-1`} onClick={() => setAll(!all)}>{all ? 'Show 5' : `Show all ${rows.length}`}</button>}
    </div>
  )
}

/** docs/plan/index-everything.md I6: our Google place against the big portals, from the searches we already run. Head to head
 * (both on the page) is the fair count; a search MagicBricks has no page for is a win that says little. */
function Board({ b }: { b: Scoreboard }) {
  const prev = b.history.length > 1 ? b.history[b.history.length - 2] : null
  const comparable = prev && !!prev.buyer_only === !!b.buyer_only   // weeks before 2026-11-06 counted our own lookups too
  const diff = comparable ? b.above_mb_when_shown - prev.above_mb_when_shown : null
  const kinds = KIND_ORDER.filter((k) => b.by_kind?.[k]?.searches)
  return (
    <div className={card} data-testid="board">
      <p className="font-semibold text-gray-900">Us against other sites on Google</p>
      <p className="text-xs text-gray-600">
        Buyer searches we ran on Google in the last 28 days{b.at ? `, counted ${timeAgo(b.at)}` : ''} (weekly). A sample of the
        searches we care about, not all of Google. Our own MahaRERA-number and builder-website lookups are not counted.
      </p>
      {b.leaders?.length ? <Leaders rows={b.leaders} areas={b.area_leaders ?? {}} us={b.us} areaUs={b.area_us ?? {}} /> : <p className="mt-2 text-sm text-gray-600">The next weekly count names every site above us.</p>}

      <p className="mt-3 text-sm font-semibold text-gray-900">Against MagicBricks, head to head</p>
      {b.both != null ? (
        <p className="text-lg font-semibold text-gray-900" data-testid="head-to-head">Above them in {b.above_mb_when_shown} of {b.both}
          {diff != null && <span className={`ml-1 text-xs ${diff >= 0 ? 'text-green-700' : 'text-red-700'}`}>{diff >= 0 ? '+' : ''}{diff}</span>}
        </p>
      ) : (
        <p className="text-lg font-semibold text-gray-900">Above them in {b.above_mb_when_shown} of the searches both show for</p>
      )}
      <p className="text-xs text-gray-600">
        Of {b.searches} searches, both sites showed in {b.both ?? '?'}: that is the fair fight. We showed in {b.ours} in all and
        MagicBricks in {b.magicbricks}; {b.above_mb - b.above_mb_when_shown} more showed us and not MagicBricks (mostly project
        names they have no page for).
      </p>

      {kinds.length > 0 && (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-700" data-testid="board-kinds">
            <thead className="text-gray-600"><tr><th className="py-1">Kind of search</th><th>Searches</th><th>We show</th><th>MB shows</th><th>Both</th><th>We are higher</th></tr></thead>
            <tbody>
              {kinds.map((k) => {
                const r = b.by_kind![k]
                return (
                  <tr key={k} className="border-t border-gray-100 align-top">
                    <td className="py-1 pr-2"><span className="font-medium">{(KIND_LABEL[k] ?? [k])[0]}</span><br /><span className="text-gray-500">{(KIND_LABEL[k] ?? ['', ''])[1]}</span></td>
                    <td>{r.searches}</td><td>{r.ours}</td><td>{r.magicbricks}</td><td>{r.both}</td><td>{r.ahead} of {r.both}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <RowList title="Where we beat MagicBricks" hint="Both on the page, ours higher. The link is the page of ours Google showed." rows={b.ahead_rows} />
      <RowList title="Where MagicBricks beats us" hint="Both on the page, theirs higher, closest first. Our page needs facts they do not show." rows={b.behind_rows} />
      <RowList title="Win next (MagicBricks just above us)" hint="They are at most 3 places above us, or in their top 3 while we are not on the page. The page doctor takes these first." rows={b.next} />
    </div>
  )
}

const leaderText = (t: BoardLeader) => `${t.site} ${t.above_us}`
const areaLabel = (k: string) => k.split('_').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ')

/** Who actually sits above us, read from the same results: the rival to study in each area is Google's pick, not ours
 * (docs/plan/rival-housiey-ravet.md: Housiey led Ravet and the MagicBricks board never named it). */
function Leaders({ rows, areas, us, areaUs }: { rows: BoardLeader[]; areas: Record<string, BoardLeader[]>; us?: BoardStanding | null; areaUs: Record<string, BoardStanding> }) {
  const byArea = Object.entries(areas).filter(([, ts]) => ts.some((t) => t.above_us))
  return (
    <div data-testid="board-leaders">
      {us && (
        <div className="mt-2" data-testid="board-us">
          <p className="text-sm font-semibold text-gray-900">Where we stand</p>
          <p className="text-lg font-semibold text-gray-900">We show in {us.shows} of {us.searches} searches</p>
          <p className="text-xs text-gray-600">Top 3 in {us.top3}, first in {us.first}. No. {us.place} of the {us.sites} sites seen, by searches shown in.</p>
        </div>
      )}
      <p className="mt-2 text-sm font-semibold text-gray-900">Above us most often</p>
      <p className="text-xs text-gray-600">Searches where the site showed above us, or showed and we did not.</p>
      <ul className="space-y-1 p-0">
        {rows.slice(0, 8).map((t) => (
          <li key={t.site} className="flex justify-between gap-2 text-xs text-gray-700">
            <span>{t.site}</span><span className="tabular-nums">above us in {t.above_us} of the {t.searches} it showed in · top 3 in {t.top3}</span>
          </li>
        ))}
      </ul>
      {byArea.length > 0 && (
        <ul className="mt-1 space-y-1 p-0">
          {byArea.map(([a, ts]) => (
            <li key={a} className="text-xs text-gray-700"><span className="font-medium">{areaLabel(a)}:</span> {areaUs[a] && `us ${areaUs[a].shows} of ${areaUs[a].searches}, top 3 in ${areaUs[a].top3}; `}{ts.filter((t) => t.above_us).map(leaderText).join(', ')}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

type AreaRow = { sitemap: string; listed: number; inspected: number; indexed: number }

// Search Console's reasons a page is not in Google, in plain words with what to do (owner 2026-11-06: "what and why").
// Matched on a lowercase part of Google's own wording, which uses curly quotes around 'noindex'.
const WHY_NOT_INDEXED: [string, string][] = [
  ['discovered', 'Google knows the address but has not read the page yet. Normal for a young site: it comes with time, better pages and Request indexing.'],
  ['noindex', "Google's last read found the page closed to search, from before it qualified (it is in the sitemap now, so it is open). Clears when Google reads it again. If the Monday site audit finds noindex on a sitemap page, that is a real fault."],
  ['unknown', 'Google has not come across the address yet. The sitemap brings it; Request indexing is faster.'],
  ['crawled', 'Google read the page and chose not to keep it: too thin, or too like another page. These are the ones to improve.'],
  ['redirect', 'The address now forwards to another page (towers merged into one project). Nothing to do.'],
  ['server error', 'Our server failed when Google came. Open the page: if it loads now, Google will retry.'],
  ['soft 404', 'Google thinks the page is empty or missing. Check it shows the project.'],
]
const whyNot = (state: string) => WHY_NOT_INDEXED.find(([k]) => state.toLowerCase().includes(k))?.[1]
const sitemapLabel = (s: string) => (s.startsWith('area-') ? s.slice(5).split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ') : s[0].toUpperCase() + s.slice(1))

/** Indexed share per child sitemap (seo/coverage.py), least indexed first: the area to send Request-indexing turns to. */
/** Project pages alone: how many Google has taken and why the others are not in, then what those pages hold. */
function ProjectPages({ index, content, at }: { index?: ProjectIndex | null; content?: PageContent; at: string | null }) {
  const reasons = Object.entries(index?.missing_by_state ?? {})
  return (
    <div className={card} data-testid="project-pages">
      <p className="font-semibold text-gray-900">Project pages in Google</p>
      <p className="text-xs text-gray-600">Project pages in our sitemap (the ones we ask Google to show), checked one by one with Google about once a week.</p>
      {!!index?.inspected && (
        <>
          <p className="text-sm text-gray-800">{index.indexed} of {index.inspected} checked are indexed ({Math.round((100 * index.indexed) / index.inspected)}%) · {index.listed} listed</p>
          {at && <p className="text-xs text-gray-600">Google&apos;s own answer, {timeAgo(at)}.</p>}
          {reasons.length > 0 && (
            <ul className="mt-1 space-y-1 p-0">
              {reasons.map(([state, n]) => (
                <li key={state} className="text-xs text-gray-700">
                  <div className="flex justify-between gap-2"><span className="font-medium">{state}</span><span className="tabular-nums">{n}</span></div>
                  {whyNot(state) && <p className="text-gray-500">{whyNot(state)}</p>}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      {!!content?.pages && (
        <>
          <p className="mt-2 text-sm font-medium text-gray-900">What the {content.pages} pages in search hold</p>
          <p className="text-xs text-gray-700">
            Prices {content.prices} · web facts {content.facts} · highlights {content.highlights} · photos {content.photos} · plans {content.plans}
          </p>
          <p className="text-xs text-gray-700">All five: {content.full} · written text, median {content.median_text} characters</p>
          <p className="text-xs text-gray-500">Prices: a price list we read. Web facts: facts checked on other sites. Highlights, photos and plans: the builder&apos;s or the brochure&apos;s. A page with all five answers a buyer best; photos and plans are the gap.</p>
        </>
      )}
    </div>
  )
}

function ByArea({ rows, at }: { rows: AreaRow[]; at: string | null }) {
  const [all, setAll] = useState(false)
  const shown = rows.filter((r) => r.inspected > 0)
  return (
    <div className={card}>
      <p className="font-semibold text-gray-900">Indexed by area</p>
      <p className="text-xs text-gray-600">Pages Google has indexed, of those we checked, per sitemap{at ? `, ${timeAgo(at)}` : ''}. Least indexed first.
        An area&apos;s row holds its project pages and its list pages; Core is the home page, guides and other site pages. A row of 1 or 2 pages says little.</p>
      <ul className="mt-1 space-y-1 p-0">
        {(all ? shown : shown.slice(0, 10)).map((r) => (
          <li key={r.sitemap} className="flex justify-between gap-2 text-xs text-gray-700">
            <span>{sitemapLabel(r.sitemap)}</span>
            <span className="tabular-nums">{r.indexed} of {r.inspected} checked ({Math.round((100 * r.indexed) / r.inspected)}%) · {r.listed} listed</span>
          </li>
        ))}
      </ul>
      {shown.length > 10 && <button type="button" className={`${btn} mt-2`} onClick={() => setAll(!all)}>{all ? 'Show 10' : `Show all ${shown.length}`}</button>}
    </div>
  )
}

const CHECK_KIND: Record<string, string> = {
  not_in_search: 'Not in search', record: 'Differs from the record', location: 'Place', wrong_project: 'Another project', number: 'Number', unsupported: 'Not in the sources', thin: 'Thin',
}

/** The daily page check (seo/review.py): finished pages against their sources. It only reports: nothing here changes a page. */
function PageChecks({ c }: { c: PageCheck }) {
  const [all, setAll] = useState(false)
  return (
    <div className={card}>
      <p className="font-semibold text-gray-900">Page check</p>
      <p className="text-xs text-gray-600">Up to 20 pages a day read live and compared with their sources. 7 days: {c.week} read, {c.week_flagged} with something to look at. Last run {c.at ? timeAgo(c.at) : 'not yet'}: {c.model} of {c.read} read by the model too.</p>
      <p className="text-xs text-gray-500">It only reports: nothing here changes a page or takes it out of search. &quot;Thin&quot; is stricter than the rule for search
        (under 60 words and at most one kind of own fact; search needs written text and one), so a thin page stays in until enrichment fills it or you fix it.
        A wrong number or another project&apos;s detail is worth fixing by hand.</p>
      {c.items.length === 0 ? <p className="mt-1 text-sm text-gray-600">Nothing to look at.</p> : (
        <ul className="mt-1 space-y-2 p-0">
          {(all ? c.items : c.items.slice(0, 10)).map((i) => (
            <li key={i.slug} className="break-words text-xs text-gray-700">
              {i.url ? <LinkOut href={i.url}>{i.name ?? i.slug}</LinkOut> : (i.name ?? i.slug)}
              <ul className="mt-0.5 space-y-0.5 p-0">
                {i.problems.map((p, n) => (
                  <li key={n}><span className="font-medium">{CHECK_KIND[p.kind] ?? p.kind}:</span> {p.detail}{p.quote ? ` ("${p.quote}")` : ''}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
      {c.items.length > 10 && <button type="button" className={`${btn} mt-2`} onClick={() => setAll(!all)}>{all ? 'Show 10' : `Show all ${c.items.length}`}</button>}
    </div>
  )
}

const AI_GROUP: Record<string, string> = {
  answer: 'Read to answer a question', referral: 'Visitors from an AI answer', search: 'Search crawlers', training: 'Training crawlers',
}

/** AI search (seo/aivisits.py): which assistants read our pages, which pages AI answers use, and visits they send us. */
function AiSearch({ a }: { a: AiVisits }) {
  return (
    <div className={card}>
      <p className="font-semibold text-gray-900">AI search</p>
      <p className="text-xs text-gray-600">From our request log, by user agent and referring site: 7 days, then {a.days} days. &quot;Read to answer&quot; is an assistant (ChatGPT, Perplexity, Claude) fetching a page while answering someone.</p>
      {a.agents.length === 0 ? <p className="mt-1 text-sm text-gray-600">Nothing yet: counting starts with the deploy.</p> : (
        <ul className="mt-1 space-y-1 p-0">
          {a.agents.map((r) => (
            <li key={r.group + r.agent} className="flex justify-between gap-2 text-xs text-gray-700">
              <span>{r.agent} · {AI_GROUP[r.group] ?? r.group}</span>
              <span className="tabular-nums">{r.week.toLocaleString('en-IN')} · {r.total.toLocaleString('en-IN')}</span>
            </li>
          ))}
        </ul>
      )}
      {[['Pages AI answers read', a.answer_pages], ['Pages people reached from AI answers', a.referral_pages]].map(([title, rows]) =>
        (rows as AiVisits['answer_pages']).length > 0 && (
          <div key={title as string} className="mt-2">
            <p className="text-xs font-semibold text-gray-800">{title as string}</p>
            <ul className="space-y-0.5 p-0">
              {(rows as AiVisits['answer_pages']).map((p) => <li key={p.path} className="break-words text-xs text-gray-700"><LinkOut href={SITE + p.path}>{p.path}</LinkOut> · {p.count}</li>)}
            </ul>
          </div>
        ))}
    </div>
  )
}

export default function RankingsTab() {
  const q = useAsync(() => getRankings(), [])
  React.useEffect(() => {   // opening the tab reads the weekly SEO note shown on Home
    getNotifications(true).then((n) => Promise.all(n.items.filter((x) => x.kind === 'seo_week').map((x) => markNotificationRead(x.id))), () => undefined)
  }, [])
  if (q.loading && !q.data) return <Spinner />
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />
  const d = q.data!
  const now = d.week.now
  const ago = d.week.week_ago
  return (
    <>
      <div className={card}>
        <p className="font-semibold text-gray-900">This week</p>
        {!now ? <p className="text-sm text-gray-600">No numbers yet: they start the day after Search Console is read.</p> : (
          <dl className="mt-1 grid grid-cols-2 gap-2 sm:grid-cols-5">
            {WEEK_ROWS.map(([k, label, hint]) => {
              const v = Number(now[k])
              const diff = ago ? v - Number(ago[k]) : null
              return (
                <div key={k}>
                  <dt className="text-xs text-gray-600">{label}</dt>
                  <dd className="text-lg font-semibold text-gray-900">{v.toLocaleString('en-IN')}
                    {diff != null && <span className={`ml-1 text-xs ${diff >= 0 ? 'text-green-700' : 'text-red-700'}`}>{diff >= 0 ? '+' : ''}{diff}</span>}
                  </dd>
                  {k === 'page_one' && now.page_one_listed != null && (
                    <dd className="text-xs font-medium text-gray-800" data-testid="page-one-listed">{now.page_one_listed.toLocaleString('en-IN')} of them are in search now{now.page_one_listed < v ? '; the rest are pages we took out, which Google shows until it reads them again' : ''}</dd>
                  )}
                  <dd className="text-xs text-gray-500">{hint}</dd>
                </div>
              )
            })}
          </dl>
        )}
      </div>

      {d.scoreboard?.at && <Board b={d.scoreboard} />}

      {(!!d.coverage?.projects?.inspected || !!d.coverage?.content?.pages) && <ProjectPages index={d.coverage.projects} content={d.coverage.content} at={d.coverage.at} />}

      {!!d.coverage?.by_sitemap.length && <ByArea rows={d.coverage.by_sitemap} at={d.coverage.at} />}

      {d.page_check && <PageChecks c={d.page_check} />}

      {d.ai && <AiSearch a={d.ai} />}

      <div className={card}>
        <p className="font-semibold text-gray-900">What works (page doctor)</p>
        <p className="text-xs text-gray-600">
          Positions gained 14 or 28 days after each fix. A fix with fewer than 5 results is tried first.
          {d.doctor.at ? ` Last round ${timeAgo(d.doctor.at)}.` : ''}
        </p>
        {d.doctor.results.length === 0 ? <p className="mt-1 text-sm text-gray-600">No fixes yet.</p> : (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-gray-600"><tr><th className="py-1">Fix</th><th>Tried</th><th>Measured</th><th>Median gain</th><th>Improved</th></tr></thead>
              <tbody>
                {d.doctor.results.map((r) => (
                  <tr key={r.fix} className="border-t border-gray-100">
                    <td className="py-1">{FIX_LABEL[r.fix] ?? r.fix}</td><td>{r.tried}</td><td>{r.measured}</td>
                    <td>{r.median_gain == null ? '-' : `${r.median_gain > 0 ? '+' : ''}${r.median_gain}`}</td>
                    <td>{r.improved_pct == null ? '-' : `${r.improved_pct}%`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {d.doctor.treated.length > 0 && (
          <ul className="mt-2 space-y-1 p-0 text-xs text-gray-700">
            {d.doctor.treated.map((t) => <li key={t.path} className="list-none break-words">{FIX_LABEL[t.fix] ?? t.fix}: {t.path} ({t.reason})</li>)}
          </ul>
        )}
      </div>

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Target searches ({d.targets.length})</p>
      {d.targets.length === 0 ? <Empty>No page has a target search yet (it needs Search Console data).</Empty> : (
        <ul className="space-y-2 p-0">
          {d.targets.map((t) => (
            <li key={t.path} className={card}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-gray-900">{t.name}</p>
                <Trend t={t} />
              </div>
              <p className="text-sm text-gray-700">&quot;{t.phrase}&quot; · {t.impressions ?? 0} impressions · {pos(t.position)} for it · page {pos(t.page_position)}, {t.clicks ?? 0} clicks</p>
              {t.checked_at && (
                <p className="text-xs text-gray-600">
                  Google {day(t.checked_at)}: {t.our_rank ? `we are #${t.our_rank}` : 'we are not in the top 10'}{t.above.length ? `; above us: ${t.above.join(', ')}` : ''}
                </p>
              )}
              {t.page_fix && <p className="text-xs text-gray-600">Last fix: {FIX_LABEL[t.page_fix] ?? t.page_fix}, {day(t.page_fix_at)}</p>}
              <LinkOut href={SITE + t.path} label={t.name}>Open page</LinkOut>
            </li>
          ))}
        </ul>
      )}

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Latest fixes</p>
      {d.actions.length === 0 ? <Empty>No fixes yet.</Empty> : (
        <ul className="space-y-2 p-0">{d.actions.map((a, i) => <ActionRow key={`${a.path}-${a.fix}-${i}`} a={a} onDone={q.reload} />)}</ul>
      )}

      <p className="px-1 pt-2 text-sm font-semibold text-gray-900">Searches with no page in the top 20 ({d.gaps.total})</p>
      {d.gaps.items.length === 0 ? <Empty>None yet (checked weekly).</Empty> : (
        <ul className="space-y-2 p-0">
          {d.gaps.items.map((g) => (
            <li key={g.phrase} className={card}>
              <p className="font-semibold text-gray-900">&quot;{g.phrase}&quot; · {g.source === 'searched'
                ? <>our Google search · {g.position == null ? 'we are not in the results' : pos(g.position)}</>
                : <>{g.impressions} impressions · {pos(g.position)}</>}{g.rising ? ' · rising' : ''}</p>
              <div className="text-xs text-gray-700">{g.page ? <>Our page for it: <LinkOut href={SITE + g.page}>{g.page}</LinkOut></> : g.action}</div>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
