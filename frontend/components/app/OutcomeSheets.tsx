'use client'
import React, { useEffect, useState } from 'react'
import { Btn, Chip, ErrorBox, inputCls } from '@/components/app/ui'
import { formatInr, formatPrice, parseInr } from '@/lib/app/format'
import { LOST_REASONS, outcomeSummary } from '@/lib/app/outcomes'
import { t } from '@/lib/app/strings'
import type { LeadOutcome, Listing, LostReason, OutcomeInput } from '@/lib/app/types'

/** A small bottom sheet: dim backdrop (tap to dismiss), Escape closes, content sits at the thumb. */
export function BottomSheet({
  title,
  onDismiss,
  children,
}: {
  title: string
  onDismiss: () => void
  children: React.ReactNode
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onDismiss()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onDismiss])
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <button type="button" aria-label={t('close')} onClick={onDismiss} className="absolute inset-0 bg-black/40" data-testid="sheet-backdrop" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative max-h-[90vh] w-full max-w-md space-y-4 overflow-y-auto rounded-t-3xl bg-white p-5 pb-8 shadow-xl"
      >
        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        {children}
      </div>
    </div>
  )
}

/** Stage Won: price and property, both optional. The price is pre-filled from the property and stays editable. */
export function DealClosedSheet({
  listings,
  defaultListingId,
  busy,
  error,
  onSave,
  onDismiss,
}: {
  listings: Listing[]
  defaultListingId?: string | null
  busy?: boolean
  error?: string | null
  onSave: (outcome: OutcomeInput | undefined) => void
  onDismiss: () => void
}) {
  const initial = listings.find((l) => l.id === defaultListingId) ?? null
  const [listingId, setListingId] = useState(initial?.id ?? '')
  const [price, setPrice] = useState(initial ? formatInr(initial.price_inr) : '')
  const [edited, setEdited] = useState(false)
  const [invalid, setInvalid] = useState(false)

  const parsed = price.trim() ? parseInr(price) : null

  function pickListing(id: string) {
    setListingId(id)
    // Follow the property's price until the agent types their own number.
    if (!edited) {
      const l = listings.find((x) => x.id === id)
      setPrice(l ? formatInr(l.price_inr) : '')
    }
  }

  function save() {
    const text = price.trim()
    const value = text ? parseInr(text) : null
    if (text && (value == null || value <= 0)) {
      setInvalid(true)
      return
    }
    const outcome: OutcomeInput = {}
    if (value) outcome.deal_price_inr = value
    if (listingId) outcome.listing_id = listingId
    onSave(Object.keys(outcome).length ? outcome : undefined)
  }

  return (
    <BottomSheet title={t('dealClosedTitle')} onDismiss={onDismiss}>
      <p className="text-sm text-gray-600">{t('dealClosedSub')}</p>
      <div>
        <label htmlFor="deal-price" className="mb-1 block text-sm font-medium text-gray-700">
          {t('dealPrice')}
        </label>
        <input
          id="deal-price"
          type="text"
          inputMode="text"
          autoComplete="off"
          className={inputCls}
          value={price}
          onChange={(e) => {
            setPrice(e.target.value)
            setEdited(true)
            setInvalid(false)
          }}
        />
        {invalid ? (
          <p role="alert" className="mt-1 text-xs text-red-600">{t('dealPriceInvalid')}</p>
        ) : (
          <p className="mt-1 text-xs text-gray-500" data-testid="deal-price-preview">
            {parsed && parsed > 0 ? `= ${formatPrice(parsed)}` : t('dealPriceHelp')}
          </p>
        )}
      </div>
      {listings.length > 0 && (
        <div>
          <label htmlFor="deal-listing" className="mb-1 block text-sm font-medium text-gray-700">
            {t('dealProperty')}
          </label>
          <select id="deal-listing" className={inputCls} value={listingId} onChange={(e) => pickListing(e.target.value)}>
            <option value="">{t('dealNoProperty')}</option>
            {listings.map((l) => (
              <option key={l.id} value={l.id}>
                {l.title || 'Untitled listing'}
              </option>
            ))}
          </select>
        </div>
      )}
      {error && <ErrorBox message={error} />}
      <Btn disabled={busy} onClick={save} className="!min-h-[56px] text-lg">
        {t('saveDeal')}
      </Btn>
    </BottomSheet>
  )
}

/** Stage Lost: tap a reason to save, or skip. */
export function LostReasonSheet({
  busy,
  error,
  onPick,
  onDismiss,
}: {
  busy?: boolean
  error?: string | null
  onPick: (outcome: OutcomeInput | undefined) => void
  onDismiss: () => void
}) {
  return (
    <BottomSheet title={t('lostTitle')} onDismiss={onDismiss}>
      <p className="text-sm text-gray-600">{t('lostSub')}</p>
      <div className="flex flex-wrap gap-2">
        {LOST_REASONS.map((r) => (
          <button
            key={r.key}
            type="button"
            disabled={busy}
            onClick={() => onPick({ lost_reason: r.key as LostReason })}
            className="min-h-[48px] rounded-full border border-gray-300 bg-white px-5 text-base font-semibold text-gray-800 active:bg-gray-100 disabled:opacity-50"
          >
            {t(r.label)}
          </button>
        ))}
      </div>
      {error && <ErrorBox message={error} />}
      <Btn variant="ghost" disabled={busy} onClick={() => onPick(undefined)}>
        {t('skip')}
      </Btn>
    </BottomSheet>
  )
}

/** After Won with a property: offer to mark that listing sold (or rented). We never change it without a Yes. */
export function MarkSoldPrompt({
  label,
  status,
  busy,
  error,
  onYes,
  onDismiss,
}: {
  label?: string | null
  status: 'sold' | 'rented'
  busy?: boolean
  error?: string | null
  onYes: () => void
  onDismiss: () => void
}) {
  const name = label || t('thisProperty')
  const title = `${t('markListingSoldQ')} ${name} ${status === 'rented' ? t('markListingAsRented') : t('markListingAsSold')}`
  return (
    <BottomSheet title={title} onDismiss={onDismiss}>
      <p className="text-sm text-gray-600">{t('markSuggestSub')}</p>
      {error && <ErrorBox message={error} />}
      <div className="grid grid-cols-2 gap-3">
        <Btn variant="secondary" disabled={busy} onClick={onDismiss}>
          {t('notNow')}
        </Btn>
        <Btn disabled={busy} onClick={onYes}>
          {t('yes')}
        </Btn>
      </div>
    </BottomSheet>
  )
}

/** Compact card on the lead detail: what happened, and a way to undo it. */
export function OutcomeSummary({
  outcome,
  listingTitle,
  busy,
  onReopen,
}: {
  outcome: LeadOutcome
  listingTitle?: string | null
  busy?: boolean
  onReopen: () => void
}) {
  const won = outcome.result === 'won'
  return (
    <section
      aria-label={won ? t('outcomeWon') : t('outcomeLost')}
      className={`flex items-center justify-between gap-3 rounded-2xl border p-4 ${won ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
      data-testid="outcome-summary"
    >
      <p className={`min-w-0 flex-1 font-semibold ${won ? 'text-green-900' : 'text-gray-800'}`}>{outcomeSummary(outcome, listingTitle)}</p>
      <Btn variant="secondary" block={false} disabled={busy} onClick={onReopen} className="!min-h-[48px] flex-none" title={t('reopenHint')}>
        {t('reopen')}
      </Btn>
    </section>
  )
}

/** Small Won/Lost badge for lead list cards. */
export function OutcomeBadge({ outcome }: { outcome?: LeadOutcome | null }) {
  if (!outcome) return null
  return outcome.result === 'won' ? <Chip tone="green">{t('outcomeWon')}</Chip> : <Chip tone="gray">{t('outcomeLost')}</Chip>
}
