'use client'
import Link from 'next/link'
import React from 'react'
import {
  activityIsEmpty,
  activityTime,
  axisLabels,
  chartScale,
  chartSummary,
  dayLabel,
  FEED_DOT,
  sourceRows,
} from '@/lib/app/activity'
import { api } from '@/lib/app/client'
import { formatPrice } from '@/lib/app/format'
import { sourceLabel } from '@/lib/app/leads'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import type { ActivityFeedItem, ListingActivity } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'
import { ShareBar } from './ShareBar'
import { ErrorBox, Spinner, StatusChip, TempChip } from './ui'

type Totals = ListingActivity['totals']

const PRIMARY: Array<[keyof Totals, Parameters<typeof t>[0]]> = [
  ['views', 'actViews'],
  ['unique_visitors', 'actVisitors'],
  ['enquiries', 'actEnquiries'],
  ['qualified', 'actQualified'],
  ['site_visits', 'actSiteVisits'],
  ['deals', 'actDeals'],
]
const SECONDARY: Array<[keyof Totals, Parameters<typeof t>[0]]> = [
  ['whatsapp_clicks', 'actWhatsappTaps'],
  ['call_clicks', 'actCalls'],
  ['shares', 'actShares'],
]

export function TotalsTiles({ totals }: { totals: Totals }) {
  return (
    <div className="space-y-2">
      <ul className="grid grid-cols-3 gap-2" data-testid="activity-totals">
        {PRIMARY.map(([key, label]) => (
          <li key={key} data-testid={`tile-${key}`} className="rounded-2xl border border-gray-200 bg-white p-3 text-center">
            <p className="text-2xl font-bold text-gray-900">{totals?.[key] ?? 0}</p>
            <p className="text-xs text-gray-600">{t(label)}</p>
          </li>
        ))}
      </ul>
      <ul className="grid grid-cols-3 gap-2" data-testid="activity-secondary">
        {SECONDARY.map(([key, label]) => (
          <li key={key} data-testid={`tile-${key}`} className="rounded-xl bg-gray-100 px-2 py-2 text-center">
            <p className="text-base font-bold text-gray-800">{totals?.[key] ?? 0}</p>
            <p className="text-[11px] text-gray-600">{t(label)}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

const W = 280
const H = 110
const PAD_TOP = 14

/** 14 bars (views) with a dot on days that had enquiries. Plain SVG, no library; the text summary is what screen readers get. */
export function ViewsChart({ daily }: { daily: ListingActivity['daily'] }) {
  const model = chartScale(daily)
  const n = model.bars.length
  const slot = n > 0 ? W / n : W
  const barW = Math.max(4, slot * 0.6)
  const plot = H - PAD_TOP
  const summary = chartSummary(daily)
  return (
    <figure className="space-y-2" data-testid="activity-chart">
      <figcaption className="flex items-baseline justify-between gap-2">
        <span className="font-bold text-gray-900">{t('actLast14')}</span>
        <span className="flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-blue-500" aria-hidden />
            {t('actChartViews')}
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-500" aria-hidden />
            {t('actChartEnquiries')}
          </span>
        </span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={summary} data-testid="chart-svg">
        <title>{summary}</title>
        <line x1="0" y1={H - 0.5} x2={W} y2={H - 0.5} stroke="#d1d5db" strokeWidth="1" />
        {model.bars.map((b, i) => {
          const h = b.views > 0 ? Math.max(3, b.height * plot) : 0
          const x = i * slot + (slot - barW) / 2
          const y = H - h
          return (
            <g key={b.date} data-testid="chart-bar" data-date={b.date} data-views={b.views} data-enquiries={b.enquiries}>
              <title>{`${dayLabel(b.date)}: ${b.views} views, ${b.enquiries} enquiries`}</title>
              {h > 0 && <rect x={x} y={y} width={barW} height={h} rx="2" fill="#3b82f6" />}
              {b.enquiries > 0 && <circle cx={x + barW / 2} cy={Math.max(6, y - 7)} r="5" fill="#f59e0b" stroke="#fff" strokeWidth="1.5" />}
            </g>
          )
        })}
      </svg>
      <div className="flex justify-between text-[11px] text-gray-500" aria-hidden data-testid="chart-axis">
        {axisLabels(daily).map((l, i) => (
          <span key={`${l}-${i}`}>{l}</span>
        ))}
      </div>
      <p className="text-sm text-gray-700" data-testid="chart-summary">{summary}</p>
    </figure>
  )
}

export function SourcesList({ bySource }: { bySource: ListingActivity['by_source'] }) {
  const rows = sourceRows(bySource)
  return (
    <section className="space-y-2" aria-label={t('actSources')}>
      <h2 className="font-bold text-gray-900">{t('actSources')}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-gray-500">{t('actSourcesEmpty')}</p>
      ) : (
        <ul className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
          {rows.map((r) => (
            <li key={r.key} data-testid={`source-${r.key}`}>
              <div className="flex items-baseline justify-between gap-2 text-sm">
                <span className="font-semibold text-gray-900">{r.label}</span>
                <span className="text-gray-600">
                  {r.views} {r.views === 1 ? t('actSourceView') : t('actSourceViews')} · {r.enquiries}{' '}
                  {r.enquiries === 1 ? t('actSourceEnquiry') : t('actSourceEnquiries')}
                </span>
              </div>
              <div className="mt-1 h-1.5 rounded-full bg-gray-100" aria-hidden>
                <div className="h-1.5 rounded-full bg-blue-400" style={{ width: `${Math.round(r.share * 100)}%` }} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export function PeopleList({ people }: { people: ListingActivity['people'] }) {
  return (
    <section className="space-y-2" aria-label={t('actPeople')}>
      <h2 className="font-bold text-gray-900">{t('actPeople')}</h2>
      {people.length === 0 ? (
        <p className="text-sm text-gray-500">{t('actPeopleEmpty')}</p>
      ) : (
        <ul className="space-y-2">
          {people.map((p) => (
            <li key={p.lead_id}>
              <Link
                href={`/studio/leads/${p.lead_id}`}
                className="flex min-h-[64px] items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50"
              >
                <div className="min-w-0">
                  <p className="truncate font-semibold text-gray-900">{p.name}</p>
                  {p.requirement_line && <p className="truncate text-sm text-gray-600">{p.requirement_line}</p>}
                  <p className="text-xs text-gray-500">{activityTime(p.last_activity_at)}</p>
                </div>
                <TempChip temperature={p.temperature} score={p.score} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function FeedRow({ item }: { item: ActivityFeedItem }) {
  const meta = [item.source ? sourceLabel(item.source) : '', activityTime(item.ts)].filter(Boolean).join(' · ')
  const body = (
    <>
      <span className={`mt-1.5 h-2.5 w-2.5 flex-none rounded-full ${FEED_DOT[item.type] ?? 'bg-gray-300'}`} aria-hidden />
      <span className="min-w-0 flex-1">
        <span className="block text-sm text-gray-900">{item.text}</span>
        <span className="block text-xs text-gray-500">{meta}</span>
      </span>
    </>
  )
  const cls = 'flex min-h-[48px] items-start gap-3 rounded-xl bg-white px-3 py-2'
  return (
    <li data-testid="feed-item" data-type={item.type}>
      {item.who.kind === 'lead' && item.who.lead_id ? (
        <Link href={`/studio/leads/${item.who.lead_id}`} className={`${cls} active:bg-gray-50`}>
          {body}
        </Link>
      ) : (
        <div className={cls}>{body}</div>
      )}
    </li>
  )
}

export function FeedList({ feed }: { feed: ListingActivity['feed'] }) {
  return (
    <section className="space-y-2" aria-label={t('actRecent')}>
      <h2 className="font-bold text-gray-900">{t('actRecent')}</h2>
      {feed.length === 0 ? (
        <p className="text-sm text-gray-500">{t('actRecentEmpty')}</p>
      ) : (
        <ul className="space-y-1 rounded-2xl border border-gray-200 bg-gray-50 p-1">
          {feed.map((f, i) => (
            <FeedRow key={`${f.ts}-${i}`} item={f} />
          ))}
        </ul>
      )}
    </section>
  )
}

/** Nothing has happened yet: say why and give the one thing to do, share the link. */
export function ActivityEmpty({ listingId, title }: { listingId: string; title: string }) {
  const siteUrl = getSiteUrl()
  return (
    <section className="space-y-3 rounded-2xl bg-blue-50 p-4" data-testid="activity-empty">
      <h2 className="text-lg font-bold text-blue-900">{t('actEmptyTitle')}</h2>
      <p className="text-sm text-blue-900">{t('actEmptyBody')}</p>
      {siteUrl && <ShareBar url={listingLink(siteUrl, listingId)} message={`${title}.`} />}
    </section>
  )
}

/** /studio/listings/[id]/activity: how this one listing is doing, who is interested, what just happened. */
export function ListingActivityView({ id }: { id: string }) {
  const { data, error, loading, reload } = useAsync(() => api.getListingActivity(id, 50), [id])
  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? t('activityLoadFailed')} onRetry={reload} />
  const { listing } = data
  const empty = activityIsEmpty(data)
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <Link href={`/studio/listings/${id}`} className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>
          ←
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-bold">{listing.title || t('activityTitle')}</h1>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="font-bold text-blue-700">{formatPrice(listing.price_inr) || '-'}</span>
            <StatusChip status={listing.status} />
          </div>
        </div>
      </div>

      {empty && <ActivityEmpty listingId={id} title={listing.title} />}
      <TotalsTiles totals={data.totals} />
      {!empty && <ViewsChart daily={data.daily} />}
      <SourcesList bySource={data.by_source} />
      <PeopleList people={data.people ?? []} />
      <FeedList feed={data.feed ?? []} />
    </div>
  )
}
