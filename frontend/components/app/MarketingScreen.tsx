'use client'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { DraftLanguage, MarketingPack } from '@/lib/app/types'
import { MarketingPackView } from './MarketingPackView'
import { MarketingRunCard } from './MarketingRunCard'
import { MatchingBuyersCard } from './MatchingBuyersCard'
import { Btn, ErrorBox } from './ui'

const LANGS: Array<{ key: DraftLanguage; label: 'langEn' | 'langHi' | 'langMr' }> = [
  { key: 'en', label: 'langEn' },
  { key: 'hi', label: 'langHi' },
  { key: 'mr', label: 'langMr' },
]

function PackSkeleton() {
  return (
    <div role="status" aria-label={t('creatingMarketing')} className="space-y-3" data-testid="pack-skeleton">
      <p className="text-center text-sm font-semibold text-gray-600">{t('creatingMarketing')}</p>
      {[0, 1, 2].map((i) => (
        <div key={i} className="animate-pulse space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
          <div className="h-5 w-1/3 rounded bg-gray-200" />
          <div className="aspect-square w-full rounded-xl bg-gray-100" />
          <div className="h-4 w-full rounded bg-gray-100" />
          <div className="h-4 w-2/3 rounded bg-gray-100" />
        </div>
      ))}
    </div>
  )
}

/**
 * Marketing pack + "buyers who match" for one live listing. Never blocks: a failure only shows a friendly retry.
 * autoCreate = generate straight away (right after posting); otherwise open the saved pack and create one if none exists.
 */
export function MarketingScreen({ listingId, autoCreate = false }: { listingId: string; autoCreate?: boolean }) {
  const [pack, setPack] = useState<MarketingPack | null>(null)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requested, setRequested] = useState<DraftLanguage>('en')
  const started = useRef(false)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const generate = useCallback(
    async (language?: DraftLanguage) => {
      setBusy(true)
      setError(null)
      if (language) setRequested(language)
      try {
        const p = await api.createMarketingPack(listingId, language)
        if (alive.current) setPack(p)
      } catch (e) {
        if (alive.current) setError(errorMessage(e))
      } finally {
        if (alive.current) setBusy(false)
      }
    },
    [listingId],
  )

  const open = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const p = await api.getMarketingPack(listingId)
      if (alive.current) {
        setPack(p)
        setRequested(p.language)
        setBusy(false)
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return generate()
      if (alive.current) {
        setError(errorMessage(e))
        setBusy(false)
      }
    }
  }, [listingId, generate])

  useEffect(() => {
    if (started.current) return
    started.current = true
    void (autoCreate ? generate() : open())
  }, [autoCreate, generate, open])

  const fellBack = !!pack && !busy && pack.language !== requested

  return (
    <div className="space-y-4">
      <MarketingRunCard listingId={listingId} />
      <div className="flex items-center gap-2" role="group" aria-label={t('packLanguage')}>
        <span className="text-sm text-gray-600">{t('packLanguage')}</span>
        {LANGS.map((l) => (
          <button
            key={l.key}
            type="button"
            aria-pressed={requested === l.key}
            disabled={busy}
            onClick={() => generate(l.key)}
            className={`min-h-[44px] min-w-[52px] rounded-full border px-3 text-sm font-semibold ${
              requested === l.key ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'
            } disabled:opacity-60`}
          >
            {t(l.label)}
          </button>
        ))}
      </div>

      {busy && <PackSkeleton />}
      {!busy && error && (
        <div className="space-y-2">
          <ErrorBox message={t('marketingFailed')} />
          <Btn onClick={() => generate(pack ? requested : undefined)}>{t('tryAgain')}</Btn>
        </div>
      )}
      {fellBack && <p role="status" className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{t('packLangFallback')}</p>}
      {!busy && pack && <MarketingPackView pack={pack} />}

      <MatchingBuyersCard listingId={listingId} />
    </div>
  )
}
