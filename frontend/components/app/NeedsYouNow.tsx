'use client'
import Link from 'next/link'
import React from 'react'
import { useIsOwner } from '@/components/app/agents/useIsOwner'
import { countWaitingPosts } from '@/components/app/AppShell'
import { api } from '@/lib/app/client'
import { contentApi } from '@/lib/app/content'
import { inboxApi } from '@/lib/app/inbox'
import { getNotifications } from '@/lib/app/whatsapp'

/**
 * Top of Studio home (2026-10-17, replaced the alert badges): "what needs you now", one row per kind of waiting thing, each opening
 * that list already filtered. Every source is optional: one that fails is left out, never an error on the home screen.
 */
export const PASSED_KIND = 'buyer_passed'
export const INVITE_KIND = 'invite_request'
export const TRIAL_KIND = 'trial_claimed'
export const SEO_KIND = 'seo_week'

export interface NeedsRow { key: string; href: string; n: number; one: string; many: string }

/** The weekly report's to-dos that are jobs (its 'answer' is the Inbox row already): they show here, not on the This week card. */
export interface WeekTodos { followup: number; photos: number; freshness: number; firstListing: boolean }

export function needsRows(c: { inbox: number; passed: number; calls: number; posts: number; invites: number; trials: number; seo?: number }, w?: WeekTodos): NeedsRow[] {
  return [
    { key: 'passed', href: '/studio/inbox', n: c.passed, one: 'buyer was passed to you', many: 'buyers were passed to you' },
    { key: 'inbox', href: '/studio/inbox?tab=needs', n: c.inbox, one: 'chat or comment waiting for an answer', many: 'chats and comments waiting for an answer' },
    { key: 'calls', href: '/studio/leads?tab=today', n: c.calls, one: 'buyer to call today', many: 'buyers to call today' },
    { key: 'uncontacted', href: '/studio/leads?tab=new', n: w?.followup ?? 0, one: 'enquiry not contacted for over a day', many: 'enquiries not contacted for over a day' },
    { key: 'first', href: '/studio/listings/new', n: w?.firstListing ? 1 : 0, one: 'first listing to post: it takes a minute', many: '' },
    { key: 'freshness', href: '/studio/listings', n: w?.freshness ?? 0, one: 'listing to confirm as still available', many: 'listings to confirm as still available' },
    { key: 'photos', href: '/studio/listings', n: w?.photos ?? 0, one: 'live listing without photos', many: 'live listings without photos' },
    { key: 'posts', href: '/studio/content', n: c.posts, one: 'post waiting for your OK', many: 'posts waiting for your OK' },
    { key: 'invites', href: '/studio/admin', n: c.invites, one: 'request to join', many: 'requests to join' },
    { key: 'trials', href: '/studio/agents?tab=signedup', n: c.trials, one: 'agent took the free trial', many: 'agents took the free trial' },
    { key: 'seo', href: '/studio/newsroom/insights?tab=rankings', n: Math.min(c.seo ?? 0, 1), one: 'SEO week to read, with pages to ask Google for', many: '' },
  ].filter((r) => r.n > 0)
}

const zero = () => 0

export function NeedsYouNow() {
  const owner = useIsOwner()
  const [rows, setRows] = React.useState<NeedsRow[] | null>(null)
  React.useEffect(() => {
    let live = true
    const unread = getNotifications(true).then((n) => n.items, () => [])
    Promise.all([
      inboxApi.threads().then((ts) => ts.filter((t) => t.needs_you).length, zero),
      unread,
      api.getToday().then((d) => d?.follow_ups?.length ?? 0, zero),
      owner ? contentApi.getUpcoming().then(countWaitingPosts, zero) : Promise.resolve(0),
      Promise.resolve().then(() => api.getWeeklyReport()).then((r) => r.todo, () => []),
    ]).then(([inbox, items, calls, posts, todo]) => {
      const left = (k: string) => todo.find((x) => x.kind === k)
      const week: WeekTodos = { followup: left('followup')?.count ?? 0, photos: left('photos')?.count ?? 0, freshness: left('freshness')?.count ?? 0, firstListing: !!left('post') }
      const kind = (k: string) => items.filter((x) => x.kind === k).length
      if (live) setRows(needsRows({ inbox, passed: kind(PASSED_KIND), calls, posts, invites: kind(INVITE_KIND), trials: kind(TRIAL_KIND), seo: kind(SEO_KIND) }, week))
    })
    return () => {
      live = false
    }
  }, [owner])
  if (!rows) return null
  return (
    <section aria-label="Needs you now" className="rounded-2xl border border-amber-300 bg-amber-50 p-3">
      <h2 className="px-1 pb-1 font-bold text-amber-950">{rows.length ? 'Needs you now' : 'All caught up'}</h2>
      {rows.length === 0 ? (
        <p className="px-1 text-sm text-amber-900">Nothing is waiting for you right now.</p>
      ) : (
        <ul className="divide-y divide-amber-200">
          {rows.map((r) => (
            <li key={r.key}>
              <Link href={r.href} data-testid={`needs-${r.key}`} className="flex min-h-[52px] items-center gap-3 px-1 font-semibold text-amber-950">
                <span className="inline-flex h-7 min-w-[28px] items-center justify-center rounded-full bg-amber-600 px-2 text-sm text-white tabular-nums">{r.n}</span>
                <span className="flex-1">{r.n === 1 ? r.one : r.many}</span>
                <span aria-hidden>&rsaquo;</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default NeedsYouNow
