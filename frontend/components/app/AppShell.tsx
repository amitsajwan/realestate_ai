'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import React, { useCallback, useEffect, useState } from 'react'
import { isFixtureMode } from '@/lib/app/client'
import { contentApi } from '@/lib/app/content'
import { newsroomApi } from '@/lib/app/newsroom'
import { t, type StringKey } from '@/lib/app/strings'
import { useIsOwner } from './agents/useIsOwner'

interface Tab { href: string; label: StringKey; icon: string }

const HOME_TAB: Tab = { href: '/studio', label: 'home', icon: 'M3 11l9-8 9 8v9a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1z' }
const LISTINGS_TAB: Tab = { href: '/studio/listings', label: 'listings', icon: 'M4 6h16M4 12h16M4 18h16' }
const INTEREST_TAB: Tab = { href: '/studio/interest', label: 'interest', icon: 'M21 11.5a8.4 8.4 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.4 8.4 0 01-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.4 8.4 0 013.8-.9h.5a8.5 8.5 0 018 8v.5z' }
const NEWSROOM_TAB: Tab = { href: '/studio/newsroom', label: 'newsroom', icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h11a2 2 0 012 2v3h3v9a2 2 0 01-2 2zM7 8h7M7 12h7M7 16h4' }
const CONTENT_TAB: Tab = { href: '/studio/content', label: 'content', icon: 'M4 5h16v14H4zM4 15l4-4 4 4 3-3 5 5M9 9h.01' }
const LEADS_TAB: Tab = { href: '/studio/leads', label: 'leads', icon: 'M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 014-4h2a4 4 0 014 4v2zM12 7a3 3 0 11-6 0 3 3 0 016 0z' }
/** Owner only (the server answers 403 to anyone else, so these are simply not shown). */
const AGENTS_TAB: Tab = { href: '/studio/agents', label: 'agents', icon: 'M16 11a4 4 0 10-8 0 4 4 0 008 0zM4 21a8 8 0 0116 0M18 8l2 2 3-3' }
const ADMIN_TAB: Tab = { href: '/studio/admin', label: 'admin', icon: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4' }
const PROFILE_TAB: Tab = { href: '/studio/profile', label: 'profile', icon: 'M20 21a8 8 0 00-16 0M12 13a4 4 0 100-8 4 4 0 000 8z' }
const MORE_TAB: Tab = { href: '#more', label: 'more', icon: 'M5 12h.01M12 12h.01M19 12h.01' }

/** Everyone who is not the owner: the six tabs, unchanged. */
const AGENT_BAR: Tab[] = [HOME_TAB, LISTINGS_TAB, INTEREST_TAB, NEWSROOM_TAB, CONTENT_TAB, LEADS_TAB]
/**
 * The owner has nine places and a phone bar holds five (UX review, 2026-10-06): the four used daily, then More,
 * a bottom sheet with the rest.
 */
const OWNER_BAR: Tab[] = [HOME_TAB, CONTENT_TAB, NEWSROOM_TAB, LEADS_TAB]
const OWNER_MORE: Tab[] = [LISTINGS_TAB, INTEREST_TAB, AGENTS_TAB, ADMIN_TAB, PROFILE_TAB]

export function FixtureBanner() {
  const [on, setOn] = useState(false)
  useEffect(() => setOn(isFixtureMode()), [])
  if (!on) return null
  return <div className="bg-amber-100 px-3 py-1 text-center text-xs font-medium text-amber-900">{t('fixtureBanner')}</div>
}

// ---- badges --------------------------------------------------------------------------------------------------------------
type Badges = Partial<Record<string, number>>

/** Posts waiting for the owner's OK, one per slug (the Instagram and Facebook copies are one card on Content). */
export function countWaitingPosts(items: { slug: string; id: string; status: string }[]): number {
  return new Set(items.filter((i) => i.status === 'planned').map((i) => i.slug || i.id)).size
}

/**
 * Counts on the owner's tabs: Content = posts waiting for approval, Newsroom = drafts waiting for review.
 * Asked on load and again when the app comes back to the front; never blocks rendering; a failed call shows no badge.
 */
export function useNavBadges(enabled: boolean): Badges {
  const [badges, setBadges] = useState<Badges>({})
  useEffect(() => {
    if (!enabled) return
    let alive = true
    const put = (href: string, n: number | undefined) => { if (alive) setBadges((b) => ({ ...b, [href]: n })) }
    const load = () => {
      contentApi.getUpcoming().then((items) => put(CONTENT_TAB.href, countWaitingPosts(items)), () => put(CONTENT_TAB.href, undefined))
      newsroomApi.getStatus().then((s) => put(NEWSROOM_TAB.href, Number(s?.counts?.pending_review) || 0), () => put(NEWSROOM_TAB.href, undefined))
    }
    load()
    const onVisible = () => { if (document.visibilityState === 'visible') load() }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      alive = false
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [enabled])
  return enabled ? badges : {}
}

function Badge({ n }: { n?: number }) {
  if (!n || n <= 0) return null
  return (
    <span data-testid="nav-badge" aria-hidden
      className="absolute -right-3 -top-1.5 min-w-[20px] rounded-full bg-[#f0b440] px-1 text-center text-[11px] font-bold leading-[20px] tabular-nums text-[#0f2340] ring-2 ring-white">
      {n > 9 ? '9+' : n}
    </span>
  )
}

// ---- bar -----------------------------------------------------------------------------------------------------------------
function Icon({ d }: { d: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )
}

/** 12 px labels, 60 px targets, the active one navy with a bar on top. [display:flex]: styles/components.css redefines .flex. */
const itemCls = (on: boolean) =>
  `relative min-h-[60px] w-full flex-col items-center justify-center gap-1 text-xs font-semibold [display:flex] ${
    on ? 'text-[#0f2340] before:absolute before:inset-x-3 before:top-0 before:h-[3px] before:rounded-b-full before:bg-[#0f2340]' : 'text-gray-500'}`

function TabInner({ tab, badge }: { tab: Tab; badge?: number }) {
  return (
    <>
      <span className="relative"><Icon d={tab.icon} /><Badge n={badge} /></span>
      <span className="max-w-full truncate">{t(tab.label)}</span>
      {badge ? <span className="sr-only">{`, ${badge} waiting`}</span> : null}
    </>
  )
}

/** The rest of the owner's places as large rows in a bottom sheet (the ConfirmSheet look). */
function MoreSheet({ items, active, onClose }: { items: Tab[]; active: (href: string) => boolean; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="fixed inset-0 z-[60] items-end bg-black/50 [display:flex]" role="dialog" aria-modal="true" aria-label={t('more')} onClick={onClose}>
      <div className="mx-auto max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5" onClick={(e) => e.stopPropagation()}
        style={{ paddingBottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}>
        <div className="mb-2 items-center justify-between [display:flex]">
          <h2 className="text-lg font-bold text-gray-900">{t('more')}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="min-h-[48px] min-w-[48px] text-2xl text-gray-500">×</button>
        </div>
        <ul className="space-y-1">
          {items.map((it) => {
            const on = active(it.href)
            return (
              <li key={it.href}>
                <Link href={it.href} onClick={onClose} aria-current={on ? 'page' : undefined}
                  className={`min-h-[56px] items-center gap-4 rounded-2xl px-4 text-base font-semibold [display:flex] ${on ? 'bg-[#e7ebf2] text-[#0f2340]' : 'text-gray-900 active:bg-gray-100'}`}>
                  <Icon d={it.icon} />
                  <span className="flex-1">{t(it.label)}</span>
                  <span aria-hidden className="text-xl text-gray-400">›</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

/**
 * Full-screen phone shell. The root layout renders the legacy Navigation, so the shell is a fixed overlay
 * (z-50) that owns the whole viewport: scrollable content + bottom tab bar.
 * Owner: Home, Content, Newsroom, Leads, More. Everyone else: the six tabs.
 */
export function AppShell({ children, hideTabs = false }: { children: React.ReactNode; hideTabs?: boolean }) {
  const path = usePathname() || ''
  const owner = useIsOwner()
  const badges = useNavBadges(owner && !hideTabs)
  const [moreOpen, setMoreOpen] = useState(false)
  const closeMore = useCallback(() => setMoreOpen(false), [])
  useEffect(() => setMoreOpen(false), [path])
  const active = (href: string) => (href === '/studio' ? path === '/studio' : path === href || path.startsWith(href + '/'))
  const bar = owner ? OWNER_BAR : AGENT_BAR
  const moreActive = owner && OWNER_MORE.some((x) => active(x.href))
  return (
    <div data-surface="v2" className="fixed inset-0 z-50 flex flex-col bg-gray-50 text-gray-900">
      <FixtureBanner />
      {/* pb-28 leaves room for the tab bar; without tabs a sticky action bar must sit at the very bottom */}
      <main className={`mx-auto w-full max-w-md flex-1 overflow-y-auto px-4 pt-4 ${hideTabs ? 'pb-0' : 'pb-28'}`}>{children}</main>
      {!hideTabs && (
        <nav
          aria-label="Main"
          className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white"
          style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
        >
          <ul className="mx-auto max-w-md [display:flex]">
            {bar.map((tab) => (
              <li key={tab.href} className="min-w-0 flex-1">
                <Link href={tab.href} aria-current={active(tab.href) ? 'page' : undefined} className={itemCls(active(tab.href))}>
                  <TabInner tab={tab} badge={badges[tab.href]} />
                </Link>
              </li>
            ))}
            {owner && (
              <li className="min-w-0 flex-1">
                <button type="button" aria-haspopup="dialog" aria-expanded={moreOpen} aria-current={moreActive ? 'page' : undefined}
                  onClick={() => setMoreOpen(true)} className={itemCls(moreActive || moreOpen)}>
                  <TabInner tab={MORE_TAB} />
                </button>
              </li>
            )}
          </ul>
        </nav>
      )}
      {moreOpen && !hideTabs && <MoreSheet items={OWNER_MORE} active={active} onClose={closeMore} />}
    </div>
  )
}
