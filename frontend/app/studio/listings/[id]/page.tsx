'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import { cleanInput } from '@/components/app/NewListingFlow'
import { ReviewForm } from '@/components/app/ReviewForm'
import { ShareBar } from '@/components/app/ShareBar'
import { Btn, ErrorBox, LinkBtn, Spinner, StatusChip } from '@/components/app/ui'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { getSiteUrl } from '@/lib/app/session'
import { listingLink } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Listing, ListingInput, ListingStatus } from '@/lib/app/types'
import { FIELD_LABELS, missingFields } from '@/lib/app/validate'

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

  useEffect(() => {
    if (data) {
      const { id: _i, agent_id, status, created_at, updated_at, published_at, freshness_confirmed_at, ...rest } = data
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
  const link = listingLink(getSiteUrl(), listing.id)
  const shareable = listing.status === 'live' || listing.status === 'under_offer'
  const { media: _media, ...editable } = form
  const missing = listing.status === 'draft' ? missingFields({ ...form, media: listing.media }) : []

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/listings" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="flex-1 truncate text-xl font-bold">{listing.title || 'Listing'}</h1>
        <StatusChip status={listing.status} />
      </div>

      {shareable && (
        <section className="space-y-2 rounded-2xl border border-gray-200 bg-white p-4">
          <p className="break-all text-sm text-blue-700">{link}</p>
          <ShareBar url={link} message={`${listing.title}.`} />
        </section>
      )}

      {shareable && (
        <div className="grid grid-cols-2 gap-3">
          <LinkBtn variant="secondary" href={`/studio/listings/${listing.id}/marketing`}>{t('marketing')}</LinkBtn>
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
            <Btn key={a.label} variant={a.variant ?? 'primary'} disabled={busy} onClick={() => run(() => api.setListingStatus(listing.id, a.status as ListingStatus), a.label)}>
              {a.label}
            </Btn>
          ),
        )}
      </div>
      {msg && <p role="status" className="rounded-xl bg-green-50 p-3 text-center text-sm font-semibold text-green-800">{msg}</p>}
      {err && <ErrorBox message={err} />}

      {listing.media.length > 0 && (
        <div className="flex gap-2 overflow-x-auto">
          {listing.media.map((m) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={m.url} src={m.url} alt="" className="h-28 w-40 flex-none rounded-xl object-cover" />
          ))}
        </div>
      )}

      <ReviewForm value={{ ...editable, media: listing.media }} onChange={({ media, ...rest }) => setForm(rest)} missing={missing} errors={errors} />
      <Btn disabled={busy} onClick={() => run(() => api.updateListing(listing.id, cleanInput(editable)), t('save'))}>{t('save')}</Btn>
    </div>
  )
}
