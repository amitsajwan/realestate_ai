'use client'
import Link from 'next/link'
import { useParams, useSearchParams } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import { AskAiPanel } from '@/components/app/AskAiPanel'
import { FreshnessSection } from '@/components/app/FreshnessPrompt'
import { ListingFacts } from '@/components/app/ListingFacts'
import { cleanInput } from '@/components/app/NewListingFlow'
import { PhotoPicker } from '@/components/app/PhotoPicker'
import { ListingPhotos } from '@/components/app/quality/ListingPhotos'
import { ReviewForm } from '@/components/app/ReviewForm'
import { SellingPoints } from '@/components/app/SellingPoints'
import { ShareBar } from '@/components/app/ShareBar'
import { SellersCard } from '@/components/app/SellersCard'
import { ConfirmSheet } from '@/components/app/list'
import { Btn, ErrorBox, Spinner, StatusChip, listingStatusWord } from '@/components/app/ui'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { formatPrice } from '@/lib/app/format'
import { compressImage } from '@/lib/app/imageCompress'
import { qualityFields } from '@/lib/app/quality'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { MAX_BROCHURE_MB, MAX_VIDEO_MB, uploadBrochure, uploadVideo } from '@/lib/app/video'
import { t } from '@shared/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Listing, ListingInput, ListingStatus, PerformanceItem } from '@/lib/app/types'
import { FIELD_LABELS, missingFields } from '@/lib/app/validate'

/** A marketing run still working on this listing (its worker steps; "asking" waits for the agent's answers). */
const ACTIVE_RUN: readonly string[] = ['queued', 'facts', 'asking', 'posts']

/**
 * One tab at a time (?tab=…). Overview opens first (2026-10-27): the photo, price and numbers, "still available?", and what to do
 * next (publish, market, share, sold/pause). It used to open on the edit form, with publish and sold on a fifth tab off the
 * screen. ?tab=status, from older links, lands on Overview; the marketing page links straight to files and facts.
 */
const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'details', label: 'Edit' },
  { id: 'files', label: 'Photos & files' },
  { id: 'facts', label: 'Checked facts' },
  { id: 'ai', label: 'Ask AI' },
] as const
type Tab = (typeof TABS)[number]['id']
const ALIASES: Record<string, Tab> = { status: 'overview' }

const SAVED_AGAIN = 'Saved. Start marketing again to use it in your posts.'

/** Sold, rented and paused take the listing away from buyers: each asks first. */
const ASK: Partial<Record<ListingStatus, (title: string) => { title: string; body: string }>> = {
  sold: (title) => ({ title: `Mark ${title || 'this listing'} sold?`, body: 'Buyers stop seeing it and no more posts go out for it. You can make it live again later.' }),
  rented: (title) => ({ title: `Mark ${title || 'this listing'} rented?`, body: 'Buyers stop seeing it and no more posts go out for it. You can make it live again later.' }),
  paused: (title) => ({ title: `Pause ${title || 'this listing'}?`, body: 'Buyers cannot see it until you make it live again.' }),
}

/** The editable part of a listing (the server's own fields left out, so a save never sends them back). */
function inputOf(l: Listing): ListingInput {
  const { id: _i, agent_id, status, created_at, updated_at, published_at, freshness_confirmed_at, freshness, days_since_confirmed, ...rest } = l
  return rest
}

function actionsFor(l: Listing): Array<{ label: string; status: ListingStatus | 'publish'; variant?: 'secondary' | 'danger' }> {
  const closed: ListingStatus = l.transaction === 'rent' ? 'rented' : 'sold'
  const closeLabel = l.transaction === 'rent' ? t('markRented') : t('markSold')
  switch (l.status) {
    case 'draft': return [{ label: t('publish'), status: 'publish' }]
    case 'live': return [
      { label: t('markUnderOffer'), status: 'under_offer', variant: 'secondary' },
      { label: closeLabel, status: closed, variant: 'secondary' },
      { label: t('pause'), status: 'paused', variant: 'danger' },
    ]
    case 'under_offer': return [
      { label: closeLabel, status: closed },
      { label: t('makeLive'), status: 'live', variant: 'secondary' },
      { label: t('pause'), status: 'paused', variant: 'danger' },
    ]
    case 'paused':
    case 'expired': return [{ label: t('makeLive'), status: 'live' }]
    default: return []
  }
}

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const asked = useSearchParams()?.get('tab') ?? ''
  const tab: Tab = TABS.some((x) => x.id === asked) ? (asked as Tab) : ALIASES[asked] ?? 'overview'
  const { data, error, loading, setData } = useAsync(() => api.getListing(id), [id])
  const [form, setForm] = useState<ListingInput>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [newPhotos, setNewPhotos] = useState<File[]>([])
  const [asking, setAsking] = useState<{ status: ListingStatus; label: string } | null>(null)
  const [deleting, setDeleting] = useState(false)
  // The marketing run: its post count for the Start marketing button, its facts and brochure claims for the facts tab,
  // and whether it is still working — while it is, status changes and file removals wait, so the posts are never made
  // for a listing that was just sold, paused or emptied.
  const campaign = useAsync(async () => {
    try {
      return await api.getMarketingRun(id)
    } catch {
      return null
    }
  }, [id])
  // This listing's numbers for the overview; a nice-to-have, so a failure shows none.
  const perf = useAsync<PerformanceItem | null>(
    () => Promise.resolve().then(() => api.getPerformance()).then((items) => items.find((p) => p.listing_id === id) ?? null, () => null), [id])
  const marketingActive = !!campaign.data && ACTIVE_RUN.includes(campaign.data.status)
  const postCount = campaign.data?.posts?.length ?? 0
  const saved = campaign.data ? t('savedMarketingPicksUp') : SAVED_AGAIN
  useEffect(() => {
    if (!marketingActive) return
    const timer = setTimeout(() => void campaign.reload(), 3000)
    return () => clearTimeout(timer)
  }, [marketingActive, campaign.data, campaign.reload])

  useEffect(() => {
    if (data) setForm(inputOf(data))
  }, [data])

  // The marketing run links to #selling-points: scroll there once the listing has loaded.
  const loaded = !!data
  useEffect(() => {
    if (loaded && window.location.hash === '#selling-points') document.getElementById('selling-points')?.scrollIntoView()
  }, [loaded, tab])

  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? 'Not found'} />

  async function run(fn: () => Promise<Listing>, okMsg: string) {
    setBusy(true)
    setErr(null)
    setErrors({})
    setMsg(null)
    try {
      setData(await fn())
      setMsg(okMsg)
      return true
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fields)
      setErr(e instanceof ApiError && e.missing.length ? `${t('required')}: ${e.missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e))
      return false
    } finally {
      setBusy(false)
      setConfirming(false)
    }
  }

  const listing = data

  async function addPhotos() {
    const uploaded = await api.uploadImages(await Promise.all(newPhotos.map((f) => compressImage(f))))
    const media = [...listing.media, ...uploaded.map((u, i) => ({ url: u.url, kind: 'image' as const, order: listing.media.length + i, ...qualityFields(u) }))]
    await run(() => api.updateListing(listing.id, { media }), saved)
    setNewPhotos([])
  }
  const videos = listing.media.filter((m) => m.kind === 'video')
  async function addVideo(file: File) {
    await run(async () => {
      const up = await uploadVideo(file)
      return api.updateListing(listing.id, { media: [...listing.media, { url: up.url, kind: 'video' as const, order: listing.media.length }] })
    }, saved)
  }
  function removeFile(url: string) {
    return run(() => api.updateListing(listing.id, { media: listing.media.filter((m) => m.url !== url) }), saved)
  }
  const brochures = listing.media.filter((m) => m.kind === 'document')
  async function addBrochure(file: File) {
    await run(async () => {
      const up = await uploadBrochure(file)
      return api.updateListing(listing.id, { media: [...listing.media, { url: up.url, kind: 'document' as const, order: listing.media.length }] })
    }, saved)
  }
  const link = listingLink(getSiteUrl(), listing.id)
  const shareable = listing.status === 'live' || listing.status === 'under_offer'
  // until the effect copies the listing into the form (one render), read the listing itself: no "add: title, price…" flash
  const values = Object.keys(form).length ? form : inputOf(listing)
  const { media: _media, ...editable } = values
  const missing = listing.status === 'draft' ? missingFields({ ...values, media: listing.media }) : []
  const needs = [
    ...missingFields({ ...values, media: listing.media }).map((m) => (FIELD_LABELS[m] ?? m).toLowerCase()),
    ...(listing.media.some((m) => m.kind === 'image') ? [] : ['photos']),
    ...(videos.length ? [] : ['video']),
    ...(brochures.length ? [] : ['brochure']),
  ].filter((x, i, all) => all.indexOf(x) === i)
  const tabHref = (x: Tab) => `/studio/listings/${listing.id}${x === 'overview' ? '' : `?tab=${x}`}`

  const cover = listing.media.find((m) => (m.kind ?? 'image') === 'image')?.url
  const facts = [
    listing.bhk ? `${listing.bhk} BHK` : '',
    listing.carpet_sqft ? `${listing.carpet_sqft} sq ft` : '',
    [listing.locality, listing.city].filter(Boolean).join(', '),
    listing.possession === 'ready' ? 'Ready to move' : listing.possession === 'under_construction' ? 'Under construction' : listing.possession ?? '',
  ].filter(Boolean)
  const p = perf.data

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/listings" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="flex-1 truncate text-xl font-bold">{listing.title || 'Listing'}</h1>
        <StatusChip status={listing.status} transaction={listing.transaction} />
      </div>

      <nav className="-mx-4 flex gap-1 overflow-x-auto border-b border-gray-200 px-2 [scrollbar-width:none]" aria-label="Listing sections">
        {TABS.map((x) => (
          <Link key={x.id} href={tabHref(x.id)} replace scroll={false} aria-current={tab === x.id ? 'page' : undefined}
            className={`flex min-h-[44px] shrink-0 items-center whitespace-nowrap border-b-2 px-3 text-sm font-semibold ${tab === x.id ? 'border-[#0f2340] text-[#0f2340]' : 'border-transparent text-gray-500'}`}>
            {x.label}
          </Link>
        ))}
      </nav>

      {msg && <p role="status" className="rounded-xl bg-green-50 p-3 text-center text-sm font-semibold text-green-800">{msg}</p>}
      {err && <ErrorBox message={err} />}

      {tab === 'overview' && (
        <>
          <FreshnessSection listings={[listing]} onUpdated={(l) => setData(l)} />

          <section aria-label="Summary" className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
            {cover ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={cover} alt="" className="aspect-[16/9] w-full bg-gray-100 object-cover" />
            ) : (
              <Link href={tabHref('files')} replace scroll={false}
                className="aspect-[16/9] w-full flex-col items-center justify-center gap-1 bg-gray-100 text-sm font-semibold text-[#0f2340] [display:flex]">
                <span aria-hidden className="text-3xl">📷</span>Add photos: listings with photos get far more enquiries
              </Link>
            )}
            <div className="space-y-1 p-4">
              <p className="text-2xl font-bold text-gray-900" data-testid="overview-price">{formatPrice(listing.price_inr, listing.transaction === 'rent') || 'No price yet'}</p>
              {facts.length > 0 && <p className="text-sm text-gray-700">{facts.join(' · ')}</p>}
              {p && (
                <ul className="mt-3 grid grid-cols-3 gap-2 border-t border-gray-100 pt-3 text-center" data-testid="overview-numbers">
                  {([[p.views, 'Views'], [p.enquiries, 'Enquiries'], [p.site_visits, 'Site visits']] as const).map(([n, label]) => (
                    <li key={label}>
                      <span className="block text-xl font-bold tabular-nums text-gray-900">{n}</span>
                      <span className="block text-xs text-gray-600">{label}</span>
                    </li>
                  ))}
                </ul>
              )}
              {listing.status !== 'draft' && (
                <Link href={`/studio/listings/${listing.id}/activity`} className="flex min-h-[44px] items-center text-sm font-semibold text-[#0f2340] underline decoration-[#f0b440] decoration-2 underline-offset-4">
                  {t('activity')}
                </Link>
              )}
            </div>
          </section>

          {listing.status === 'draft' && (
            <section aria-label="Publish" className="space-y-3 rounded-2xl border border-[#0f2340]/20 bg-white p-4">
              <h2 className="font-bold text-gray-900">Not on your website yet</h2>
              {missing.length > 0 ? (
                <>
                  <p className="text-sm text-gray-700" data-testid="readiness">To publish, add: <b>{missing.map((m) => (FIELD_LABELS[m] ?? m).toLowerCase()).join(', ')}</b>.</p>
                  <Link href={tabHref(missing.every((m) => m === 'media') ? 'files' : 'details')} replace scroll={false}
                    className="min-h-[52px] items-center justify-center rounded-xl bg-[#0f2340] px-5 text-base font-semibold text-white [display:flex]">
                    Fill in what is missing
                  </Link>
                </>
              ) : (
                <>
                  <p className="text-sm text-gray-700" data-testid="readiness">Everything needed is here. Publish it, then start marketing.</p>
                  <Btn disabled={busy} onClick={() => setConfirming(true)}>{t('publish')}</Btn>
                </>
              )}
            </section>
          )}

          {shareable && (
            <section aria-label="Get buyers" className="space-y-3">
              <p className="text-sm text-gray-700" data-testid="readiness">
                {needs.length ? <>Ready for marketing. <Link href={tabHref('files')} replace scroll={false} className="font-semibold text-[#0f2340] underline">Better with: {needs.join(', ')}</Link>.</> : 'Ready for marketing.'}
              </p>
              <a href={`/studio/listings/${listing.id}/marketing`} data-testid="marketing-button"
                className="min-h-[56px] w-full items-center justify-center gap-2 rounded-xl bg-[#0f2340] px-5 text-base font-semibold text-white active:opacity-90 [display:flex]">
                Start marketing
                {postCount > 0 && <span className="rounded-full bg-[#f0b440] px-2 text-sm font-bold text-[#0f2340]">{postCount} {postCount === 1 ? 'post' : 'posts'}</span>}
              </a>
              <ShareBar url={link} message={`${listing.title}.`} />
            </section>
          )}

          {actionsFor(listing).some((a) => a.status !== 'publish') && (
            <section aria-label="Status" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-4">
              <h2 className="font-bold text-gray-900">Status: {listingStatusWord(listing.status, listing.transaction).toLowerCase()}</h2>
              <p className="text-sm text-gray-600">Change it as the deal moves. Sold, rented and paused listings leave your website.</p>
              {marketingActive && (
                <p role="status" className="rounded-xl bg-blue-50 p-3 text-center text-sm font-semibold text-blue-900">
                  Marketing is in progress. Marking it sold, rented, paused or deleting it waits until the posts are ready.
                </p>
              )}
              <div className="grid grid-cols-1 gap-2">
                {actionsFor(listing).filter((a) => a.status !== 'publish').map((a) => (
                  <Btn key={a.label} variant={a.variant ?? 'primary'} disabled={busy || marketingActive} onClick={() => {
                    const status = a.status as ListingStatus
                    if (ASK[status]) setAsking({ status, label: a.label })
                    else run(() => api.setListingStatus(listing.id, status), a.label)
                  }}>
                    {a.label}
                  </Btn>
                ))}
              </div>
            </section>
          )}

          <button type="button" disabled={busy || marketingActive} onClick={() => setDeleting(true)}
            className="min-h-[48px] w-full rounded-xl text-sm font-semibold text-red-600 active:bg-red-50 disabled:text-gray-400">
            Delete listing
          </button>

          {confirming && (
            <ConfirmSheet title={`Publish ${listing.title || 'this listing'}?`} confirmLabel={t('publish')} busy={busy || missing.length > 0}
              onCancel={() => setConfirming(false)} onConfirm={() => run(() => api.publishListing(listing.id), t('posted'))}>
              <p>It goes on your website for buyers. Marketing is the next step, when you start it.</p>
            </ConfirmSheet>
          )}
          {asking && (
            <ConfirmSheet title={ASK[asking.status]!(listing.title).title} confirmLabel={asking.label} busy={busy}
              onCancel={() => setAsking(null)}
              onConfirm={async () => {
                const { status, label } = asking
                await run(() => api.setListingStatus(listing.id, status), label)
                setAsking(null)
              }}>
              <p>{ASK[asking.status]!(listing.title).body}</p>
            </ConfirmSheet>
          )}
          {deleting && (
            <ConfirmSheet title={`Delete ${listing.title || 'this listing'}?`} confirmLabel="Delete" busy={busy}
              onCancel={() => setDeleting(false)}
              onConfirm={async () => {
                setBusy(true)
                setErr(null)
                try {
                  await api.deleteListing(listing.id)
                  window.location.assign('/studio/listings')
                } catch (e) {
                  setErr(errorMessage(e))
                  setDeleting(false)
                  setBusy(false)
                }
              }}>
              <p>It comes off your website for good and its posts not yet out are cancelled. Posts already on Facebook and Instagram stay, and so do its leads. This cannot be undone.</p>
            </ConfirmSheet>
          )}
        </>
      )}

      {tab === 'details' && (
        <>
          <ReviewForm value={{ ...editable, media: listing.media }} onChange={({ media, ...rest }) => setForm(rest)} missing={missing} errors={errors} />
          {/* Save stays in reach on a long form, just above the tab bar */}
          <div className="sticky z-10 -mx-4 border-t border-gray-200 bg-gray-50/95 px-4 py-2 backdrop-blur" style={{ bottom: 'calc(60px + env(safe-area-inset-bottom, 0px))' }}>
            <Btn disabled={busy} onClick={() => run(() => api.updateListing(listing.id, cleanInput(editable)), 'Saved')}>{busy ? 'Saving…' : t('save')}</Btn>
          </div>
          {(form.selling_points?.length ?? 0) > 0 && (
            <>
              <SellingPoints points={form.selling_points ?? []} onChange={(selling_points) => setForm({ ...form, selling_points })} />
              <Btn variant="secondary" disabled={busy} onClick={() => run(() => api.updateListing(listing.id, { selling_points: form.selling_points }), saved)}>{t('spSave')}</Btn>
            </>
          )}
          <SellersCard listingId={listing.id} />
        </>
      )}
      {tab === 'files' && (
        <>
          <ListingPhotos media={listing.media} busy={busy}
            onToggle={(i, v) => run(() => api.updateListing(listing.id, { media: listing.media.map((m, j) => (j === i ? { ...m, use_enhanced: v } : m)) }), saved)} />

          <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Photos">
            <p className="font-semibold">Photos {listing.media.length === 0 && <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900">None yet</span>}</p>
            <PhotoPicker files={newPhotos} onChange={setNewPhotos} />
            {newPhotos.length > 0 && <Btn disabled={busy} onClick={addPhotos}>Add {newPhotos.length} photo{newPhotos.length > 1 ? 's' : ''}</Btn>}
          </section>

          <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Project files">
            <p className="font-semibold">Project files</p>
            <p className="text-sm text-gray-600">The builder&apos;s video and brochure, for this listing only. Buyers never see them as they are: Start marketing makes your reel from the video. The brochure is kept with the listing for your team; it is not read.</p>
            <p className="text-sm font-semibold text-gray-800">Video</p>
            <p className="text-sm text-gray-600">A site walkthrough (up to 3 minutes, {MAX_VIDEO_MB} MB). A phone-number strip along the bottom is removed and your logo is added.</p>
            {videos.map((v) => (
              <div key={v.url} className="space-y-2">
                <video src={v.url} controls preload="metadata" playsInline className="max-h-80 rounded-lg bg-black" />
                <Btn disabled={busy || marketingActive} onClick={() => removeFile(v.url)}>Remove video</Btn>
              </div>
            ))}
            {videos.length === 0 && (
              <label className="flex min-h-[44px] cursor-pointer items-center justify-center rounded-xl border border-dashed border-gray-300 p-3 text-sm font-semibold text-blue-700">
                {busy ? 'Uploading…' : 'Add a video'}
                <input type="file" accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm" className="sr-only" disabled={busy}
                  onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void addVideo(f) }} />
              </label>
            )}
            <p className="text-sm font-semibold text-gray-800">Brochure</p>
            <p className="text-sm text-gray-600">The builder&apos;s PDF (up to {MAX_BROCHURE_MB} MB).</p>
            {brochures.map((b) => (
              <div key={b.url} className="flex items-center justify-between gap-2">
                <a href={b.url} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center font-semibold text-blue-700 underline">Open brochure (PDF)</a>
                <Btn block={false} variant="secondary" disabled={busy || marketingActive} onClick={() => removeFile(b.url)}>Remove</Btn>
              </div>
            ))}
            {brochures.length === 0 && (
              <label className="flex min-h-[44px] cursor-pointer items-center justify-center rounded-xl border border-dashed border-gray-300 p-3 text-sm font-semibold text-blue-700">
                {busy ? 'Uploading…' : 'Add the brochure (PDF)'}
                <input type="file" accept="application/pdf,.pdf" className="sr-only" disabled={busy}
                  onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void addBrochure(f) }} />
              </label>
            )}
          </section>
        </>
      )}

      {tab === 'facts' && <ListingFacts listing={listing} run={campaign.data ?? null} />}

      {tab === 'ai' && <AskAiPanel listing={listing} onSaved={setData} />}

    </div>
  )
}
