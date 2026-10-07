'use client'
import Link from 'next/link'
import React, { useState } from 'react'
import { AiSummaryCard, DraftPanel, FollowUpDue, MatchesList, RequirementChips } from '@/components/app/LeadPanels'
import { DealClosedSheet, LostReasonSheet, MarkSoldPrompt, OutcomeSummary } from '@/components/app/OutcomeSheets'
import { Btn, ErrorBox, LinkBtn, STAGES, Spinner, TempChip, inputCls } from '@/components/app/ui'
import { api, errorMessage } from '@/lib/app/client'
import { displayPhone, timeAgo, waDigits } from '@/lib/app/format'
import { eventLabel } from '@/lib/app/leads'
import { dealListings } from '@/lib/app/outcomes'
import { whatsappChatUrl } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { LeadDetail, LeadPatch, Listing, OutcomeInput, Stage } from '@/lib/app/types'

type Sheet = 'won' | 'lost' | null

export function LeadDetailView({ id }: { id: string }) {
  const { data, error, loading, setData } = useAsync(async () => {
    const [lead, listings] = await Promise.all([api.getLead(id), api.listListings().catch(() => [] as Listing[])])
    return { lead, listings, titles: Object.fromEntries(listings.map((l) => [l.id, l.title])) as Record<string, string> }
  }, [id])
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [showDraft, setShowDraft] = useState(false)
  const [sheet, setSheet] = useState<Sheet>(null)
  const [suggest, setSuggest] = useState<NonNullable<LeadDetail['suggest_listing_status']> | null>(null)

  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? t('notFound')} />
  const { lead, titles, listings } = data

  /** Returns the updated lead, or null when the request failed (the message is in `err`). */
  async function patch(p: LeadPatch, clearNote = false): Promise<LeadDetail | null> {
    setBusy(true)
    setErr(null)
    try {
      const updated = await api.updateLead(id, p)
      setData({ ...data!, lead: updated })
      if (clearNote) setNote('')
      return updated
    } catch (e) {
      setErr(errorMessage(e))
      return null
    } finally {
      setBusy(false)
    }
  }
  const update = (stage: Stage) => patch({ stage })
  // A note alone never touches the stage (and so never touches a stored deal outcome).
  const addNote = () => patch({ note: note.trim() }, true)

  function chooseStage(s: Stage) {
    if (s === lead.stage) return
    setErr(null)
    // Won and Lost ask one quick question first; nothing changes until the sheet is saved.
    if (s === 'won' || s === 'lost') setSheet(s)
    else update(s)
  }

  function closeSheets() {
    setSheet(null)
    setSuggest(null)
    setErr(null)
  }

  async function saveOutcome(stage: 'won' | 'lost', outcome: OutcomeInput | undefined) {
    const updated = await patch({ stage, ...(outcome ? { outcome } : {}) })
    if (!updated) return
    setSheet(null)
    const s = updated.suggest_listing_status
    // Nothing to ask when the listing is already in that state.
    if (s && listings.find((l) => l.id === s.listing_id)?.status !== s.status) setSuggest(s)
  }

  async function markListing() {
    if (!suggest) return
    setBusy(true)
    setErr(null)
    try {
      const l = await api.setListingStatus(suggest.listing_id, suggest.status)
      setData({ ...data!, listings: data!.listings.map((x) => (x.id === l.id ? l : x)) })
      setSuggest(null)
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const firstName = lead.name.split(' ')[0]
  return (
    <div className="space-y-4 pb-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/leads" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="flex-1 truncate text-xl font-bold">{lead.name}</h1>
        <TempChip temperature={lead.temperature} score={lead.score} />
      </div>
      <p className="text-gray-600">{displayPhone(lead.phone)}</p>

      {lead.outcome && (lead.stage === 'won' || lead.stage === 'lost') && (
        <OutcomeSummary
          outcome={lead.outcome}
          listingTitle={lead.outcome.listing_id ? titles[lead.outcome.listing_id] : null}
          busy={busy}
          onReopen={() => update('contacted')}
        />
      )}

      <AiSummaryCard
        lead={lead}
        busy={busy}
        onSchedule={() => update('site_visit')}
        onFollowUp={() => setShowDraft(true)}
      />

      {lead.message && <p className="rounded-xl bg-white p-3 text-gray-800">“{lead.message}”</p>}

      <div className="grid grid-cols-2 gap-3">
        <LinkBtn href={`tel:${lead.phone}`}>📞 {t('call')}</LinkBtn>
        <LinkBtn variant="whatsapp" href={whatsappChatUrl(waDigits(lead.phone), `Hi ${firstName}, this is regarding your property enquiry.`)} target="_blank" rel="noopener noreferrer">
          {t('whatsapp')}
        </LinkBtn>
      </div>

      <RequirementChips requirement={lead.requirement} />
      <MatchesList matches={lead.matches} />
      <FollowUpDue followUp={lead.follow_up} busy={busy} onSet={(iso) => patch({ follow_up_at: iso })} />

      {showDraft ? (
        <DraftPanel leadId={lead.id} phone={lead.phone} />
      ) : (
        <Btn variant="secondary" onClick={() => setShowDraft(true)}>{t('draftFollowUp')}</Btn>
      )}

      <section>
        <h2 className="mb-2 font-semibold">{t('stage')}</h2>
        <div className="flex flex-wrap gap-2">
          {STAGES.map((s) => (
            <button
              key={s.key}
              type="button"
              aria-pressed={lead.stage === s.key}
              disabled={busy}
              onClick={() => chooseStage(s.key)}
              className={`min-h-[44px] rounded-full border px-4 text-sm font-semibold ${lead.stage === s.key ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-300 bg-white text-gray-700'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">{t('addNote')}</h2>
        <textarea aria-label={t('addNote')} className={`${inputCls} min-h-[80px] py-3`} placeholder={t('notePlaceholder')} value={note} onChange={(e) => setNote(e.target.value)} />
        <Btn variant="secondary" disabled={busy || !note.trim()} onClick={addNote}>{t('save')}</Btn>
        {err && !sheet && !suggest && <ErrorBox message={err} />}
      </section>

      {lead.notes.length > 0 && (
        <section>
          <h2 className="mb-2 font-semibold">{t('notes')}</h2>
          <ul className="space-y-2">
            {[...lead.notes].reverse().map((n, i) => (
              <li key={i} className="rounded-xl bg-white p-3 text-sm">
                <p>{n.text}</p>
                <p className="text-xs text-gray-500">{timeAgo(n.ts)}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="mb-2 font-semibold">{t('timeline')}</h2>
        <ol className="space-y-2 border-l-2 border-blue-200 pl-4">
          {[...lead.timeline].reverse().map((ev, i) => (
            <li key={i} className="text-sm text-gray-800">{eventLabel(ev, ev.listing_id ? titles[ev.listing_id] : null)}</li>
          ))}
        </ol>
      </section>

      {sheet === 'won' && (
        <DealClosedSheet
          listings={dealListings(listings, lead.first_listing_id)}
          defaultListingId={lead.first_listing_id}
          busy={busy}
          error={err}
          onSave={(o) => saveOutcome('won', o)}
          onDismiss={closeSheets}
        />
      )}
      {sheet === 'lost' && (
        <LostReasonSheet busy={busy} error={err} onPick={(o) => saveOutcome('lost', o)} onDismiss={closeSheets} />
      )}
      {suggest && (
        <MarkSoldPrompt
          label={titles[suggest.listing_id]}
          status={suggest.status}
          busy={busy}
          error={err}
          onYes={markListing}
          onDismiss={closeSheets}
        />
      )}
    </div>
  )
}
