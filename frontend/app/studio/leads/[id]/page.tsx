'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React, { useState } from 'react'
import { Btn, ErrorBox, LinkBtn, STAGES, Spinner, TempChip, inputCls } from '@/components/app/ui'
import { api, errorMessage } from '@/lib/app/client'
import { displayPhone, timeAgo, waDigits } from '@/lib/app/format'
import { eventLabel } from '@/lib/app/leads'
import { whatsappChatUrl } from '@/lib/app/share'
import { t } from '@/lib/app/strings'
import { useAsync } from '@/lib/app/useAsync'
import type { Stage } from '@/lib/app/types'

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, error, loading, setData } = useAsync(async () => {
    const [lead, listings] = await Promise.all([api.getLead(id), api.listListings().catch(() => [])])
    return { lead, titles: Object.fromEntries(listings.map((l) => [l.id, l.title])) as Record<string, string> }
  }, [id])
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  if (loading && !data) return <Spinner />
  if (error || !data) return <ErrorBox message={error ?? 'Not found'} />
  const { lead, titles } = data

  async function update(stage: Stage, withNote?: string) {
    setBusy(true)
    setErr(null)
    try {
      const lead = await api.updateLead(id, stage, withNote?.trim() || undefined)
      setData({ ...data!, lead })
      if (withNote) setNote('')
    } catch (e) {
      setErr(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const firstName = lead.name.split(' ')[0]
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Link href="/studio/leads" className="flex min-h-[44px] min-w-[44px] items-center text-xl" aria-label={t('back')}>←</Link>
        <h1 className="flex-1 truncate text-xl font-bold">{lead.name}</h1>
        <TempChip temperature={lead.temperature} score={lead.score} />
      </div>
      <p className="text-gray-600">{displayPhone(lead.phone)}</p>
      {lead.message && <p className="rounded-xl bg-white p-3 text-gray-800">“{lead.message}”</p>}

      <div className="grid grid-cols-2 gap-3">
        <LinkBtn href={`tel:${lead.phone}`}>📞 {t('call')}</LinkBtn>
        <LinkBtn variant="whatsapp" href={whatsappChatUrl(waDigits(lead.phone), `Hi ${firstName}, this is regarding your property enquiry.`)} target="_blank" rel="noopener noreferrer">
          {t('whatsapp')}
        </LinkBtn>
      </div>

      <section>
        <h2 className="mb-2 font-semibold">Stage</h2>
        <div className="flex flex-wrap gap-2">
          {STAGES.map((s) => (
            <button
              key={s.key}
              type="button"
              aria-pressed={lead.stage === s.key}
              disabled={busy}
              onClick={() => lead.stage !== s.key && update(s.key)}
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
        <Btn variant="secondary" disabled={busy || !note.trim()} onClick={() => update(lead.stage, note)}>{t('save')}</Btn>
        {err && <ErrorBox message={err} />}
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
    </div>
  )
}
