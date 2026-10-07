'use client'
import Link from 'next/link'
import React from 'react'
import { ShareBar } from '@/components/app/ShareBar'
import { ErrorBox, LinkBtn, Spinner, TempChip } from '@/components/app/ui'
import { api } from '@/lib/app/client'
import { formatPrice, waDigits } from '@/lib/app/format'
import { withConfirmAction } from '@/lib/app/freshness'
import { dueLabel, sourceLabel } from '@/lib/app/leads'
import { actionHref } from '@/lib/app/marketing'
import { lostHint, resultsEmpty } from '@/lib/app/outcomes'
import { whatsappChatUrl } from '@/lib/app/share'
import { useSession } from '@/lib/app/session'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { BusinessToday as Today, RecommendedAction, RecommendedActionType, TodayFollowUp, TodayHotBuyer, TodayResults } from '@/lib/app/types'

export const TILE_LINKS = [
  { key: 'new_enquiries_24h', label: 'tileNew', href: '/studio/leads?tab=new' },
  { key: 'hot', label: 'tileHot', href: '/studio/leads?tab=all&hot=1' },
  { key: 'site_visits', label: 'tileVisits', href: '/studio/leads?tab=site_visit' },
  { key: 'follow_ups_due', label: 'tileFollowUps', href: '/studio/leads?tab=today' },
] as const

export function CountTiles({ counts }: { counts: Today['counts'] }) {
  return (
    <ul className="grid grid-cols-2 gap-3">
      {TILE_LINKS.map((tile) => (
        <li key={tile.key}>
          <Link href={tile.href} className="block min-h-[84px] rounded-2xl border border-gray-200 bg-white p-4 active:bg-gray-50">
            <p className="text-3xl font-bold text-gray-900">{counts[tile.key]}</p>
            <p className="text-sm text-gray-600">{t(tile.label)}</p>
          </Link>
        </li>
      ))}
    </ul>
  )
}

export function HotBuyerCard({ buyer }: { buyer: TodayHotBuyer }) {
  const firstName = buyer.name.split(' ')[0]
  return (
    <li className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <Link href={`/studio/leads/${buyer.id}`} className="block">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate font-semibold text-gray-900">{buyer.name}</p>
          <TempChip temperature={buyer.temperature} />
        </div>
        {buyer.requirement_line && <p className="mt-1 text-sm text-gray-700">{buyer.requirement_line}</p>}
        {buyer.top_match && (
          <p className="mt-1 text-xs text-gray-600">
            {t('topMatch')}: {buyer.top_match.title} <b className="text-green-700">{buyer.top_match.match_pct}%</b>
          </p>
        )}
      </Link>
      <div className="grid grid-cols-2 gap-3">
        <LinkBtn href={`tel:${buyer.phone}`} aria-label={`${t('call')} ${buyer.name}`}>
          {t('call')}
        </LinkBtn>
        <LinkBtn
          variant="whatsapp"
          href={whatsappChatUrl(waDigits(buyer.phone), `Hi ${firstName}, this is regarding your property enquiry.`)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`${t('whatsapp')} ${buyer.name}`}
        >
          {t('whatsapp')}
        </LinkBtn>
      </div>
    </li>
  )
}

export function FollowUpRow({ item }: { item: TodayFollowUp }) {
  return (
    <li>
      <Link href={`/studio/leads/${item.id}`} className="flex min-h-[64px] items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-4 active:bg-gray-50">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{item.name}</p>
          <p className="truncate text-sm text-gray-600">{item.reason}</p>
        </div>
        <span className={`flex-none rounded-full px-2.5 py-1 text-xs font-semibold ${item.overdue ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800'}`}>
          {dueLabel(item.due_at, item.overdue)}
        </span>
      </Link>
    </li>
  )
}

const ACTION_LABEL: Record<RecommendedActionType, Parameters<typeof t>[0]> = {
  call: 'actCall',
  follow_up: 'actFollowUp',
  send_property: 'actSendProperty',
  create_marketing: 'actCreateMarketing',
  confirm_listing: 'actConfirmListing',
}

export function ActionCard({ action }: { action: RecommendedAction }) {
  const href = actionHref(action)
  return (
    <li className="space-y-3 rounded-2xl border border-blue-200 bg-blue-50 p-4" data-testid={`action-${action.type}`}>
      <Link href={href} className="block">
        <p className="font-semibold text-gray-900">{action.title}</p>
        {action.detail && <p className="mt-0.5 text-sm text-gray-700">{action.detail}</p>}
      </Link>
      <LinkBtn href={href} aria-label={`${t(ACTION_LABEL[action.type])}: ${action.title}`}>
        {t(ACTION_LABEL[action.type])}
      </LinkBtn>
    </li>
  )
}

/** "AI recommends": what to do next, from the daily actions list. */
export function RecommendedActions({ actions }: { actions?: RecommendedAction[] }) {
  if (!actions || actions.length === 0) return null
  return (
    <section className="space-y-3" aria-label={t('aiRecommends')}>
      <h2 className="font-bold text-gray-900">{t('aiRecommends')}</h2>
      <ul className="space-y-3">
        {actions.map((a, i) => (
          <ActionCard key={`${a.type}-${a.lead_id ?? a.listing_id ?? i}`} action={a} />
        ))}
      </ul>
    </section>
  )
}

/** "This month": deals won and their value, best channel and why deals were lost. Hidden until there is something to show. */
export function ResultsCard({ results }: { results?: TodayResults }) {
  if (resultsEmpty(results) || !results) return null
  const hint = lostHint(results)
  return (
    <section aria-label={t('thisMonth')} className="space-y-3 rounded-2xl border border-green-200 bg-green-50 p-4" data-testid="results-card">
      <h2 className="font-bold text-gray-900">{t('thisMonth')}</h2>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-3xl font-bold text-gray-900" data-testid="deals-won">{results.deals_won}</p>
          <p className="text-sm text-gray-700">{t('dealsWon')}</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-gray-900" data-testid="deal-value">{results.deal_value_inr > 0 ? formatPrice(results.deal_value_inr) : '-'}</p>
          <p className="text-sm text-gray-700">{t('dealValue')}</p>
        </div>
      </div>
      {results.top_source && (
        <p className="text-sm font-semibold text-gray-800">
          {t('bestChannel')}: {sourceLabel(results.top_source)}
        </p>
      )}
      {hint && <p className="text-sm text-gray-700" data-testid="lost-hint">{hint}</p>}
    </section>
  )
}

function SiteCard({ siteUrl }: { siteUrl: string }) {
  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <h2 className="font-semibold">{t('mySite')}</h2>
      <a href={siteUrl} target="_blank" rel="noopener noreferrer" className="block break-all text-blue-700 underline">
        {siteUrl}
      </a>
      <ShareBar url={siteUrl} message="Namaste! Visit my property website:" />
    </section>
  )
}

/** /studio home: "Your business today". */
export function BusinessToday() {
  const { siteUrl, logout } = useSession(false)
  const state = useAsync(async () => {
    // Listings are only needed for "Listings that need your confirmation"; the home screen works without them.
    const listings = async () => {
      try {
        return await api.listListings()
      } catch {
        return []
      }
    }
    const [loaded, leads, mine] = await Promise.all([api.getToday(), api.listLeads().catch(() => []), listings()])
    const today = { ...loaded, actions: withConfirmAction(loaded.actions, mine) }
    const c = today.counts
    const hasLeads =
      leads.length > 0 || today.hot_buyers.length > 0 || today.follow_ups.length > 0 ||
      c.new_enquiries_24h + c.hot + c.site_visits + c.follow_ups_due + c.uncontacted > 0
    return { today, hasLeads }
  })
  const data = state.data
  const addBtn = (
    <LinkBtn href="/studio/listings/new" className="!min-h-[64px] text-lg">
      {t('addListing')}
    </LinkBtn>
  )
  const site = siteUrl ? <SiteCard siteUrl={siteUrl} /> : null

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('todayTitle')}</h1>
        <button type="button" onClick={logout} className="min-h-[44px] px-2 text-sm text-gray-500 underline">
          {t('logout')}
        </button>
      </div>

      {state.loading && !data && <Spinner />}
      {state.error && <ErrorBox message={state.error} onRetry={state.reload} />}

      {data && <RecommendedActions actions={data.today.actions} />}

      {data && !data.hasLeads && (
        <>
          <section className="rounded-2xl bg-blue-50 p-4">
            <h2 className="text-lg font-bold text-blue-900">{t('newAgentTitle')}</h2>
            <p className="mt-1 text-sm text-blue-900">{t('newAgentBody')}</p>
          </section>
          {site}
          {addBtn}
        </>
      )}

      {data && data.hasLeads && (
        <>
          <p className="text-lg font-semibold text-gray-900" data-testid="headline">
            {data.today.headline}
          </p>
          <CountTiles counts={data.today.counts} />
          <ResultsCard results={data.today.results} />

          <section className="space-y-3" aria-label={t('hotBuyers')}>
            <h2 className="font-bold text-gray-900">{t('hotBuyers')}</h2>
            {data.today.hot_buyers.length === 0 ? (
              <p className="text-sm text-gray-500">{t('noHotBuyers')}</p>
            ) : (
              <ul className="space-y-3">
                {data.today.hot_buyers.map((b) => (
                  <HotBuyerCard key={b.id} buyer={b} />
                ))}
              </ul>
            )}
          </section>

          {data.today.follow_ups.length > 0 && (
            <section className="space-y-3" aria-label={t('followUpsDue')}>
              <h2 className="font-bold text-gray-900">{t('followUpsDue')}</h2>
              <ul className="space-y-2">
                {data.today.follow_ups.map((f) => (
                  <FollowUpRow key={f.id} item={f} />
                ))}
              </ul>
            </section>
          )}

          {site}
          {addBtn}
        </>
      )}
    </div>
  )
}
