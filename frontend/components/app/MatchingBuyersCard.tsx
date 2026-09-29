'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { api } from '@/lib/app/client'
import { buyerDraftUrl } from '@/lib/app/marketing'
import { t } from '@/lib/app/strings'
import type { MatchingBuyer } from '@/lib/app/types'
import { useAsync } from '@/lib/app/useAsync'
import { ErrorBox, LinkBtn, Spinner, TempChip, inputCls } from './ui'

export function BuyerRow({ buyer }: { buyer: MatchingBuyer }) {
  const [message, setMessage] = useState(buyer.draft.message)
  const [open, setOpen] = useState(false)
  const boxId = `draft-${buyer.lead_id}`
  return (
    <li className="space-y-3 rounded-xl border border-gray-200 p-3" data-testid={`buyer-${buyer.lead_id}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <Link href={`/studio/leads/${buyer.lead_id}`} className="block truncate font-semibold text-gray-900">
            {buyer.name}
          </Link>
          {buyer.requirement_line && <p className="text-sm text-gray-700">{buyer.requirement_line}</p>}
        </div>
        <div className="flex flex-none flex-col items-end gap-1">
          <span className="rounded-full bg-green-100 px-2.5 py-1 text-xs font-bold text-green-800">
            {buyer.match_pct}% {t('matchPct')}
          </span>
          <TempChip temperature={buyer.temperature} />
        </div>
      </div>
      {buyer.reasons.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label="Why it matches">
          {buyer.reasons.map((r) => (
            <li key={r} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
              {r}
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        aria-expanded={open}
        aria-controls={boxId}
        onClick={() => setOpen((v) => !v)}
        className="min-h-[44px] text-sm font-semibold text-blue-700 underline"
      >
        {open ? t('hideMessage') : t('editMessage')}
      </button>
      {open && (
        <textarea
          id={boxId}
          aria-label={`${t('yourMessage')} - ${buyer.name}`}
          className={`${inputCls} min-h-[120px] py-3`}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
      )}
      <LinkBtn
        variant="whatsapp"
        href={buyerDraftUrl(buyer, message)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`${t('sendOnWhatsapp')} - ${buyer.name}`}
      >
        {t('sendOnWhatsapp')}
      </LinkBtn>
    </li>
  )
}

/** Presentational part, so it can be tested without the API. */
export function MatchingBuyersList({ buyers }: { buyers: MatchingBuyer[] }) {
  return (
    <>
      <h2 className="text-lg font-bold text-gray-900">
        {buyers.length} {t('buyersMatchOne')}
      </h2>
      {buyers.length === 0 ? (
        <p className="text-sm text-gray-600">{t('noBuyersMatch')}</p>
      ) : (
        <ul className="space-y-3">
          {buyers.map((b) => (
            <BuyerRow key={b.lead_id} buyer={b} />
          ))}
        </ul>
      )}
      <p className="text-xs text-gray-500">{t('neverSendsShort')}</p>
    </>
  )
}

/** "N of your buyers match this property": each row has an editable WhatsApp draft. Nothing is sent for the agent. */
export function MatchingBuyersCard({ listingId }: { listingId: string }) {
  const state = useAsync(() => api.getMatchingLeads(listingId), [listingId])
  return (
    <section id="buyers" className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label={t('buyersWhoMatch')}>
      {state.loading && !state.data && <Spinner />}
      {state.error && (
        <>
          <ErrorBox message={`${t('buyersLoadFailed')} ${state.error}`} onRetry={state.reload} />
          <p className="text-xs text-gray-500">{t('neverSendsShort')}</p>
        </>
      )}
      {state.data && <MatchingBuyersList buyers={state.data.buyers} />}
    </section>
  )
}
