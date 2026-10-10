'use client'
import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import React, { useState } from 'react'
import { MarketingRunCard } from '@/components/app/MarketingRunCard'
import { Btn, ErrorBox, Spinner } from '@/components/app/ui'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { DraftLanguage } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'
import { FIELD_LABELS } from '@/lib/app/validate'

const LANGS: DraftLanguage[] = ['en', 'mr', 'hi']

/** `?start=1&lang=en|mr|hi` starts the run on arrival; a draft is posted and marketed from here in one tap. */
export default function ListingMarketingPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const params = useSearchParams()
  const asked = params?.get('lang') as DraftLanguage | null
  const urlStart: DraftLanguage | null = params?.get('start') === '1' ? (asked && LANGS.includes(asked) ? asked : 'en') : null
  const { data, error, loading, reload, setData } = useAsync(() => api.getListing(id), [id])
  const [autoStart, setAutoStart] = useState<DraftLanguage | null>(urlStart)
  const [posting, setPosting] = useState(false)
  const [postErr, setPostErr] = useState<{ message: string; missing: boolean } | null>(null)

  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? t('notFound')} onRetry={reload} />
  const live = data.status === 'live' || data.status === 'under_offer'

  const postAndMarket = async () => {
    setPosting(true)
    setPostErr(null)
    try {
      const l = await api.publishListing(id)
      setAutoStart(urlStart ?? 'en')
      setData(l)
    } catch (e) {
      const missing = e instanceof ApiError && e.missing.length > 0
      setPostErr({
        message: missing ? `${t('required')}: ${(e as ApiError).missing.map((m) => FIELD_LABELS[m] ?? m).join(', ')}` : errorMessage(e),
        missing,
      })
    } finally {
      setPosting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href={`/studio/listings/${id}`} className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold">{t('marketingTitle')}</h1>
          <p className="truncate text-sm text-gray-600">{data.title}</p>
        </div>
      </div>
      {live ? (
        <MarketingRunCard listingId={id} autoStart={autoStart}
          onAutoStarted={() => { setAutoStart(null); if (urlStart) router.replace(`/studio/listings/${id}/marketing`, { scroll: false }) }} />
      ) : data.status === 'draft' ? (
        <div className="space-y-2 rounded-xl bg-amber-50 p-3">
          <p className="text-sm text-amber-900">This property is not on your website yet. Post it and its marketing starts right away.</p>
          <Btn disabled={posting} onClick={postAndMarket}>{posting ? 'Posting…' : 'Post & market'}</Btn>
          {postErr && (
            <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <p>{postErr.message}</p>
              {postErr.missing && (
                <Link href={`/studio/listings/${id}`} className="mt-1 inline-flex min-h-[44px] items-center font-semibold underline">Fill them in</Link>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">This property is not live, so it cannot be marketed now.</p>
      )}
    </div>
  )
}
