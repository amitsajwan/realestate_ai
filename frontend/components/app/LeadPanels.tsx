'use client'
import Link from 'next/link'
import React, { useEffect, useRef, useState } from 'react'
import { Btn, Chip, ErrorBox, LinkBtn, Spinner, inputCls } from '@/components/app/ui'
import { api, errorMessage } from '@/lib/app/client'
import { formatPrice, waDigits } from '@/lib/app/format'
import {
  NEXT_ACTION_LABEL,
  buildWhatsappUrl,
  dueLabel,
  followUpAt,
  requirementChips,
  requirementSourceNote,
} from '@/lib/app/leads'
import { whatsappChatUrl } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import type { DraftLanguage, FollowUpState, FollowupDraft, LeadDetail, LeadMatch, Requirement } from '@/lib/app/types'

/** AI summary + the one prominent next-step button. */
export function AiSummaryCard({
  lead,
  busy,
  onSchedule,
  onFollowUp,
}: {
  lead: LeadDetail
  busy?: boolean
  onSchedule: () => void
  onFollowUp: () => void
}) {
  const action = lead.next_action
  if (!lead.ai_summary && !action) return null
  const firstName = lead.name.split(' ')[0]
  let button: React.ReactNode = null
  if (action) {
    const label = t(NEXT_ACTION_LABEL[action.type])
    if (action.type === 'call') {
      button = <LinkBtn href={`tel:${lead.phone}`} className="!min-h-[60px] text-lg">{label}</LinkBtn>
    } else if (action.type === 'whatsapp') {
      button = (
        <LinkBtn
          variant="whatsapp"
          href={whatsappChatUrl(waDigits(lead.phone), `Hi ${firstName}, this is regarding your property enquiry.`)}
          target="_blank"
          rel="noopener noreferrer"
          className="!min-h-[60px] text-lg"
        >
          {label}
        </LinkBtn>
      )
    } else if (action.type === 'schedule_visit') {
      button = <Btn disabled={busy} onClick={onSchedule} className="!min-h-[60px] text-lg">{label}</Btn>
    } else {
      button = <Btn disabled={busy} onClick={onFollowUp} className="!min-h-[60px] text-lg">{label}</Btn>
    }
  }
  return (
    <section aria-label={t('aiSummary')} className="space-y-3 rounded-2xl border border-blue-200 bg-blue-50 p-4">
      <h2 className="text-sm font-bold uppercase tracking-wide text-blue-800">{t('aiSummary')}</h2>
      {lead.ai_summary && <p className="text-base text-gray-900">{lead.ai_summary}</p>}
      {action && (
        <div className="space-y-1">
          <p className="text-xs font-semibold text-blue-800">
            {t('nextStep')}: {action.reason}
          </p>
          {button}
        </div>
      )}
    </section>
  )
}

export function RequirementChips({ requirement }: { requirement?: Requirement | null }) {
  const chips = requirementChips(requirement)
  return (
    <section aria-label={t('whatTheyWant')} className="space-y-2">
      <h2 className="font-semibold">{t('whatTheyWant')}</h2>
      {chips.length === 0 ? (
        <p className="text-sm text-gray-500">{t('noRequirement')}</p>
      ) : (
        <>
          <ul className="flex flex-wrap gap-2">
            {chips.map((c, i) => (
              <li key={`${c}-${i}`}>
                <Chip tone="blue" className="!text-sm">{c}</Chip>
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-500" data-testid="req-source">{requirementSourceNote(requirement)}</p>
        </>
      )}
    </section>
  )
}

export function MatchesList({ matches }: { matches?: LeadMatch[] }) {
  return (
    <section aria-label={t('matchingProperties')} className="space-y-2">
      <h2 className="font-semibold">{t('matchingProperties')}</h2>
      {!matches || matches.length === 0 ? (
        <p className="text-sm text-gray-500">{t('noMatches')}</p>
      ) : (
        <ul className="space-y-2">
          {matches.map((m) => (
            <li key={m.listing_id}>
              <Link href={`/studio/listings/${m.listing_id}`} className="block rounded-2xl border border-gray-200 bg-white p-3 active:bg-gray-50">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate font-semibold text-gray-900">{m.title}</p>
                  <p className="flex-none text-sm font-semibold text-gray-700">{formatPrice(m.price_inr)}</p>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200" role="progressbar" aria-valuenow={m.match_pct} aria-valuemin={0} aria-valuemax={100} aria-label={`${m.match_pct}% ${t('matchPct')}`}>
                    <div className="h-full rounded-full bg-green-600" style={{ width: `${Math.max(0, Math.min(100, m.match_pct))}%` }} />
                  </div>
                  <span className="text-sm font-bold text-green-700">{m.match_pct}%</span>
                </div>
                {m.reasons.length > 0 && <p className="mt-1 text-xs text-gray-600">{m.reasons.join(' · ')}</p>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

const QUICK_DAYS = [
  { days: 1, label: 'fuTomorrow' },
  { days: 3, label: 'fu3Days' },
  { days: 7, label: 'fuNextWeek' },
] as const

export function FollowUpDue({
  followUp,
  busy,
  onSet,
}: {
  followUp?: FollowUpState
  busy?: boolean
  onSet: (iso: string) => void
}) {
  const due = followUp?.due_at
  return (
    <section aria-label={t('followUpDue')} className="space-y-2">
      <h2 className="font-semibold">{t('followUpDue')}</h2>
      <p className={`text-sm ${followUp?.overdue ? 'font-semibold text-red-700' : 'text-gray-700'}`} data-testid="followup-line">
        {due ? dueLabel(due, followUp!.overdue) : t('followUpNone')}
      </p>
      <div className="grid grid-cols-3 gap-2">
        {QUICK_DAYS.map((q) => (
          <Btn key={q.days} variant="secondary" disabled={busy} onClick={() => onSet(followUpAt(q.days))} className="!min-h-[48px] !px-2 text-sm">
            {t(q.label)}
          </Btn>
        ))}
      </div>
    </section>
  )
}

const LANGS: Array<{ key: DraftLanguage; label: 'langEn' | 'langHi' | 'langMr' }> = [
  { key: 'en', label: 'langEn' },
  { key: 'hi', label: 'langHi' },
  { key: 'mr', label: 'langMr' },
]

/** Draft follow-up: editable message, reasons, language toggle and a Send on WhatsApp button. The app never sends by itself. */
export function DraftPanel({ leadId, phone }: { leadId: string; phone: string }) {
  const [lang, setLang] = useState<DraftLanguage>('en')
  const [draft, setDraft] = useState<FollowupDraft | null>(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const seq = useRef(0)

  async function load(language: DraftLanguage) {
    const mine = ++seq.current
    setLoading(true)
    setError(null)
    try {
      const d = await api.createFollowupDraft(leadId, language)
      if (mine !== seq.current) return
      setDraft(d)
      setText(d.message)
    } catch (e) {
      if (mine === seq.current) setError(errorMessage(e))
    } finally {
      if (mine === seq.current) setLoading(false)
    }
  }

  useEffect(() => {
    load('en')
    return () => {
      seq.current++
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leadId])

  function pick(l: DraftLanguage) {
    setLang(l)
    load(l)
  }

  return (
    <section aria-label={t('draftFollowUp')} className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-semibold">{t('draftFollowUp')}</h2>
        <div className="flex gap-1" role="group" aria-label="Language">
          {LANGS.map((l) => (
            <button
              key={l.key}
              type="button"
              aria-pressed={lang === l.key}
              onClick={() => pick(l.key)}
              className={`min-h-[44px] min-w-[44px] rounded-full border px-3 text-sm font-semibold ${lang === l.key ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}
            >
              {t(l.label)}
            </button>
          ))}
        </div>
      </div>
      {loading && <Spinner label={t('drafting')} />}
      {error && <ErrorBox message={error} onRetry={() => load(lang)} />}
      {draft && !loading && (
        <>
          <label className="block text-sm font-medium text-gray-700" htmlFor="draft-text">
            {t('yourMessage')}
          </label>
          <textarea id="draft-text" className={`${inputCls} min-h-[140px] py-3`} value={text} onChange={(e) => setText(e.target.value)} />
          {draft.language !== lang && <p className="text-xs text-amber-800">{t('langFallback')}</p>}
          {draft.based_on.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600">{t('whySection')}</p>
              <ul className="list-disc pl-5 text-xs text-gray-600">
                {draft.based_on.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}
          <LinkBtn
            variant="whatsapp"
            href={buildWhatsappUrl(phone, text)}
            target="_blank"
            rel="noopener noreferrer"
            className="!min-h-[60px] text-lg"
          >
            {t('sendOnWhatsapp')}
          </LinkBtn>
          <p className="text-xs text-gray-500">{t('neverSends')}</p>
        </>
      )}
    </section>
  )
}
