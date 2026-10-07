'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import { t } from '@/lib/app/strings'
import type { MarketingRun } from '@/lib/app/types'
import { Btn, ErrorBox } from './ui'

type Post = MarketingRun['posts'][number]

/** Edit one campaign post's caption, or ask for it again with a note. The run comes back updated (and planned calendar rows
 *  follow); approved rows never change. */
export function CampaignPostEditor({ listingId, post, onRun }: { listingId: string; post: Post; onRun: (r: MarketingRun) => void }) {
  const [caption, setCaption] = useState(post.caption)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState<'save' | 'redo' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [problems, setProblems] = useState<string[] | null>(null)
  const id = `cap-${post.angle}`

  const save = async () => {
    setBusy('save')
    setError(null)
    try {
      const r = await api.editRunPost(listingId, post.angle, caption)
      setProblems(r.problems)
      onRun(r.run)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  const redo = async () => {
    setBusy('redo')
    setError(null)
    setProblems(null)
    try {
      const r = await api.redoRunPost(listingId, post.angle, note)
      const fresh = r.posts.find((p) => p.angle === post.angle)
      if (fresh) setCaption(fresh.caption)
      setNote('')
      onRun(r)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="mt-2 space-y-2">
      <label htmlFor={id} className="block text-xs font-semibold text-gray-700">{t('editCaption')}</label>
      <textarea id={id} value={caption} onChange={(e) => setCaption(e.target.value)} rows={8}
        className="w-full rounded-lg border border-gray-300 p-2 text-xs" />
      <Btn variant="secondary" disabled={busy !== null || caption.trim() === '' || caption === post.caption} onClick={save}>
        {t('saveCaption')}
      </Btn>
      {problems && (problems.length === 0
        ? <p role="status" className="text-xs text-emerald-700">{t('saved')}</p>
        : <div role="status" className="rounded-lg bg-amber-50 p-2 text-xs text-amber-900">{t('checkWarnings')} {problems.join('; ')}</div>)}
      <label htmlFor={`note-${post.angle}`} className="block text-xs font-semibold text-gray-700">{t('improveNote')}</label>
      <input id={`note-${post.angle}`} value={note} onChange={(e) => setNote(e.target.value)} maxLength={300}
        placeholder={t('improveNotePlaceholder')} className="w-full rounded-lg border border-gray-300 p-2 text-xs" />
      <Btn variant="secondary" disabled={busy !== null || note.trim() === ''} onClick={redo}>
        {busy === 'redo' ? t('improving') : t('improve')}
      </Btn>
      {error && <ErrorBox message={error} />}
    </div>
  )
}
