'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { freshnessOf, needingConfirmation } from '@/lib/app/freshness'
import { formatPrice } from '@/lib/app/format'
import { t } from '@/lib/app/strings'
import type { Listing, ListingStatus } from '@/lib/app/types'
import { Btn, ErrorBox } from './ui'

type Answer = 'confirm' | 'closed' | 'pause'

/** One card: "Is this still available?" (amber) or "Hidden from buyers until you confirm" (red), with three big answers. */
export function FreshnessCard({ listing, onUpdated }: { listing: Listing; onUpdated: (l: Listing, answer: Answer) => void }) {
  const [busy, setBusy] = useState<Answer | null>(null)
  const [error, setError] = useState<string | null>(null)
  const hidden = freshnessOf(listing) === 'hidden'
  const rent = listing.transaction === 'rent'
  const days = listing.days_since_confirmed

  async function answer(kind: Answer) {
    setBusy(kind)
    setError(null)
    try {
      const closed: ListingStatus = rent ? 'rented' : 'sold'
      const updated =
        kind === 'confirm'
          ? await api.confirmAvailable(listing.id)
          : await api.setListingStatus(listing.id, kind === 'closed' ? closed : 'paused')
      onUpdated(updated, kind)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <li
      data-testid={`freshness-${listing.id}`}
      data-state={hidden ? 'hidden' : 'confirm'}
      className={`space-y-3 rounded-2xl border p-4 ${hidden ? 'border-red-300 bg-red-50' : 'border-amber-300 bg-amber-50'}`}
    >
      <div>
        <h3 className={`text-lg font-bold ${hidden ? 'text-red-800' : 'text-amber-900'}`}>
          {hidden ? t('freshHiddenTitle') : t('freshAskTitle')}
        </h3>
        <p className="mt-1 font-semibold text-gray-900">
          {listing.title}
          {listing.price_inr ? ` · ${formatPrice(listing.price_inr, rent)}` : ''}
        </p>
        <p className="mt-1 text-sm text-gray-700">
          {hidden ? t('freshHiddenBody') : t('freshAskBody')}
          {days != null ? ` ${t('freshConfirmedDays')} ${days} ${t('freshDaysAgo')}.` : ''}
        </p>
      </div>
      <div className="space-y-2">
        <Btn disabled={busy !== null} onClick={() => answer('confirm')}>
          {t('freshYes')}
        </Btn>
        <div className="grid grid-cols-2 gap-2">
          <Btn variant="secondary" disabled={busy !== null} onClick={() => answer('closed')}>
            {rent ? t('freshRented') : t('freshSold')}
          </Btn>
          <Btn variant="danger" disabled={busy !== null} onClick={() => answer('pause')}>
            {t('freshPause')}
          </Btn>
        </div>
      </div>
      {error && <ErrorBox message={error} />}
    </li>
  )
}

const DONE: Record<Answer, (rent: boolean) => string> = {
  confirm: () => t('freshThanks'),
  closed: (rent) => (rent ? t('freshRentedDone') : t('freshSoldDone')),
  pause: () => t('freshPausedDone'),
}

/**
 * Every listing that needs an answer, hidden ones first. Renders nothing when all is fresh.
 * `onUpdated` gets the listing the server returned so the screen can swap it in (the card then disappears).
 */
export function FreshnessSection({ listings, onUpdated }: { listings: Listing[]; onUpdated: (l: Listing) => void }) {
  const [notice, setNotice] = useState<string | null>(null)
  const need = needingConfirmation(listings)
  if (need.length === 0 && !notice) return null
  return (
    <section id="confirm" aria-label={t('freshSectionLabel')} className="space-y-3">
      {notice && (
        <p role="status" className="rounded-xl bg-green-50 p-3 text-center text-sm font-semibold text-green-800">
          {notice}
        </p>
      )}
      {need.length > 0 && (
        <ul className="space-y-3">
          {need.map((l) => (
            <FreshnessCard
              key={l.id}
              listing={l}
              onUpdated={(updated, kind) => {
                setNotice(`${updated.title || l.title}: ${DONE[kind](updated.transaction === 'rent')}`)
                onUpdated(updated)
              }}
            />
          ))}
        </ul>
      )}
    </section>
  )
}
