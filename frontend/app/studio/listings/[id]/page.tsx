'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import { FreshnessSection } from '@/components/app/FreshnessPrompt'
import { cleanInput } from '@/components/app/NewListingFlow'
import { PhotoPicker } from '@/components/app/PhotoPicker'
import { ListingPhotos } from '@/components/app/quality/ListingPhotos'
import { ReviewForm } from '@/components/app/ReviewForm'
import { ShareBar } from '@/components/app/ShareBar'
import { ConfirmSheet } from '@/components/app/list'
import { Btn, ErrorBox, LinkBtn, Spinner, StatusChip } from '@/components/app/ui'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { compressImage } from '@/lib/app/imageCompress'
import { qualityFields } from '@/lib/app/quality'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Listing, ListingInput, ListingStatus } from '@/lib/app/types'
import { FIELD_LABELS, missingFields } from '@/lib/app/validate'

/** Sold, rented and paused take the listing away from buyers: each asks first. */
const ASK: Partial<Record<ListingStatus, (title: string) => { title: string; body: string }>> = {
  sold: (title) => ({ title: `Mark ${title || 'this listing'} sold?`, body: 'Buyers stop seeing it and no more posts go out for it. You can make it live again later.' }),
  rented: (title) => ({ title: `Mark ${title || 'this listing'} rented?`, body: 'Buyers stop seeing it and no more posts go out for it. You can make it live again later.' }),
  paused: (title) => ({ title: `Pause ${title || 'this listing'}?`, body: 'Buyers cannot see it until you make it live again.' }),
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
  const { data, error, loading, setData } = useAsync(() => api.getListing(id), [id])
  const [form, setForm] = useState<ListingInput>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [newPhotos, setNewPhotos] = useState<File[]>([])
  const [asking, setAsking] = useState<{ status: ListingStatus; label: string } | null>(null)
  // How many posts the marketing run made, for the Marketing button (a nice-to-have: no count when it cannot be loaded).
  const campaign = useAsync(async () => {
    try {
      return (await api.getMarketingRun(id))?.posts?.length ?? 0
    } catch {
      return 0
    }
  }, [id])

  useEffect(() => {
    if (data) {
      const { id: _i, agent_id, status, created_at, updated_at, published_at, freshness_confirmed_at, freshness, days_since_confirmed, ...rest } = data
      setForm(rest)
    }
  }, [data])

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
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) setErrors(e.fields)
      setErr(e instanceof ApiError && e.missing.length ? `${t('required')}: ${e.missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e))
    } finally {
      setBusy(false)
      setConfirming(false)
    }
  }

  const listing = data

  async function addPhotos() {
    const uploaded = await api.uploadImages(await Promise.all(newPhotos.map((f) => compressImage(f))))
    const media = [...listing.media, ...uploaded.map((u, i) => ({ url: u.url, kind: 'image' as const, order: listing.media.length + i, ...qualityFields(u) }))]
    await run(() => api.updateListing(listing.id, { media }), 'Photos added. Open "Marketing" and refresh your post to use them.')
    setNewPhotos([])
  }
  const link = listingLink(getSiteUrl(), listing.id)
  const shareable = listing.status === 'live' || listing.status === 'under_offer'
  const { media: _media, ...editable } = form
  const missing = listing.status === 'draft' ? missingFields({ ...form, media: listing.media }) : []

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/listings" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="flex-1 truncate text-xl font-bold">{listing.title || 'Listing'}</h1>
        <StatusChip status={listing.status} transaction={listing.transaction} />
      </div>

      <FreshnessSection listings={[listing]} onUpdated={(l) => setData(l)} />

      {listing.status !== 'draft' && (
        <LinkBtn variant="secondary" href={`/studio/listings/${listing.id}/activity`}>{t('activity')}</LinkBtn>
      )}

      {shareable && (
        <section className="space-y-2 rounded-2xl border border-gray-200 bg-white p-4">
          <p className="break-all text-sm text-blue-700">{link}</p>
          <ShareBar url={link} message={`${listing.title}.`} />
        </section>
      )}

      {shareable && (
        <div className="space-y-2">
          <a href={`/studio/listings/${listing.id}/marketing`} data-testid="marketing-button"
            className="min-h-[56px] w-full items-center justify-center gap-2 rounded-xl bg-[#0f2340] px-5 text-base font-semibold text-white active:opacity-90 [display:flex]">
            {t('marketing')}
            {campaign.data ? <span className="rounded-full bg-[#f0b440] px-2 text-sm font-bold text-[#0f2340]">{campaign.data} {campaign.data === 1 ? 'post' : 'posts'}</span> : null}
          </a>
          <LinkBtn variant="secondary" href={`/studio/listings/${listing.id}/marketing#buyers`}>{t('buyersWhoMatch')}</LinkBtn>
        </div>
      )}

      <div className="space-y-2">
        {actionsFor(listing).map((a) =>
          a.status === 'publish' ? (
            confirming ? (
              <div key="c" className="space-y-2 rounded-xl border border-blue-200 bg-blue-50 p-3">
                <p className="text-center text-sm font-semibold">Post this listing to your website?</p>
                <Btn disabled={busy || missing.length > 0} onClick={() => run(() => api.publishListing(listing.id), t('posted'))}>{t('confirmPost')}</Btn>
                <Btn variant="ghost" onClick={() => setConfirming(false)}>{t('back')}</Btn>
              </div>
            ) : (
              <Btn key="p" disabled={busy} onClick={() => setConfirming(true)}>{a.label}</Btn>
            )
          ) : (
            <Btn key={a.label} variant={a.variant ?? 'primary'} disabled={busy} onClick={() => {
              const status = a.status as ListingStatus
              if (ASK[status]) setAsking({ status, label: a.label })
              else run(() => api.setListingStatus(listing.id, status), a.label)
            }}>
              {a.label}
            </Btn>
          ),
        )}
      </div>
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
      {msg && <p role="status" className="rounded-xl bg-green-50 p-3 text-center text-sm font-semibold text-green-800">{msg}</p>}
      {err && <ErrorBox message={err} />}

      <ListingPhotos media={listing.media} busy={busy}
        onToggle={(i, v) => run(() => api.updateListing(listing.id, { media: listing.media.map((m, j) => (j === i ? { ...m, use_enhanced: v } : m)) }),
          v ? 'Using the enhanced photo.' : 'Using your original photo.')} />

      <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label="Photos">
        <p className="font-semibold">Photos {listing.media.length === 0 && <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900">None yet</span>}</p>
        <PhotoPicker files={newPhotos} onChange={setNewPhotos} />
        {newPhotos.length > 0 && <Btn disabled={busy} onClick={addPhotos}>Add {newPhotos.length} photo{newPhotos.length > 1 ? 's' : ''}</Btn>}
      </section>

      <ReviewForm value={{ ...editable, media: listing.media }} onChange={({ media, ...rest }) => setForm(rest)} missing={missing} errors={errors} />
      <Btn disabled={busy} onClick={() => run(() => api.updateListing(listing.id, cleanInput(editable)), t('save'))}>{t('save')}</Btn>
    </div>
  )
}
