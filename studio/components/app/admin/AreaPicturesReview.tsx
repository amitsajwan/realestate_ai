'use client'
import React, { useState } from 'react'
import { areaPicturesApi } from '@/lib/app/areaPictures'
import type { AreaPictureItem } from '@/lib/app/areaPictures'
import { errorMessage } from '@/lib/app/client'
import { useAsync } from '@/lib/app/useAsync'
import { LOCALITIES } from '@shared/marketing/localities'
import { Btn, ErrorBox, inputCls, Spinner } from '../ui'

const STATUS_WORD: Record<AreaPictureItem['status'], string> = {
  pending: 'Waiting for you', live: 'Live on the guide', refused: 'Refused', superseded: 'Replaced by a retake',
}
const STATUS_TONE: Record<AreaPictureItem['status'], string> = {
  pending: 'bg-amber-100 text-amber-900', live: 'bg-green-100 text-green-900', refused: 'bg-red-100 text-red-900',
  superseded: 'bg-gray-200 text-gray-700',
}

function PictureCard({ p, busy, onDecide }: { p: AreaPictureItem; busy: boolean; onDecide: (id: string, live: boolean) => void }) {
  return (
    <li data-testid="area-picture" data-status={p.status} className="min-w-0 rounded-xl border border-gray-200 bg-white p-2">
      {/* eslint-disable-next-line @next/next/no-img-element -- our own uploaded copy, not a Next-optimisable remote image */}
      <img src={p.url} alt={`${p.area} from above, ${p.captured_on}`} className="h-28 w-full rounded-lg bg-gray-100 object-cover" />
      <p className="mt-1 text-sm font-semibold text-gray-900">{p.year}<span className="font-normal text-gray-500"> · {p.captured_on}</span></p>
      <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_TONE[p.status]}`}>{STATUS_WORD[p.status]}</span>
      {p.judged ? (
        <p className={`mt-1 text-xs ${p.judged.ok ? 'text-green-700' : 'text-amber-700'}`}>
          The judge: {p.judged.ok ? 'usable' : 'doubtful'}{p.judged.reason ? ` — ${p.judged.reason}` : ''}
        </p>
      ) : (
        <p className="mt-1 text-xs text-gray-500">The judge could not answer: the code checks alone kept it.</p>
      )}
      {typeof p.cloud_pct === 'number' && <p className="text-xs text-gray-500">Measured cloud: {p.cloud_pct}%</p>}
      {(p.status === 'pending') && (
        <div className="mt-2 grid grid-cols-2 gap-2">
          <Btn onClick={() => onDecide(p.id, true)} disabled={busy} data-testid="area-picture-approve">Approve</Btn>
          <Btn variant="secondary" onClick={() => onDecide(p.id, false)} disabled={busy} data-testid="area-picture-refuse">Refuse</Btn>
        </div>
      )}
    </li>
  )
}

/** Studio > Admin > Pictures from above (backend areastats.pictures, docs/plan/area-pictures.md step 3): the area's
 *  Sentinel-2 pictures side by side with the AI judge's notes. While untrusted, every new picture waits here; approving
 *  one lets later pictures that pass the code checks and the judge go live by themselves. */
export function AreaPicturesReview() {
  const [area, setArea] = useState(LOCALITIES[0]?.key ?? 'kharadi')
  const { data, error, loading, reload } = useAsync(() => areaPicturesApi.list(area), [area])
  const [busy, setBusy] = useState(false)
  const [actError, setActError] = useState<string | null>(null)
  const items = data?.items ?? []

  async function decide(id: string, live: boolean) {
    setBusy(true)
    setActError(null)
    try {
      await areaPicturesApi.decide(id, live)
      reload()
    } catch (e) {
      setActError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div data-testid="area-pictures">
      <p className="text-sm text-gray-600">
        {data && !data.trusted
          ? 'Every new picture waits for you. Approve one good pair and later pictures that pass the code checks and the AI judge go live by themselves.'
          : 'Pictures that pass the code checks and the AI judge go live by themselves; anything the judge doubts still waits here.'}
      </p>
      <label className="mt-2 block text-sm font-semibold text-gray-800">Area
        <select className={inputCls} value={area} onChange={(e) => setArea(e.target.value)} data-testid="area-pictures-area">
          {LOCALITIES.map((l) => <option key={l.key} value={l.key}>{l.name}</option>)}
        </select>
      </label>
      {actError && <div className="mt-2"><ErrorBox message={actError} /></div>}
      {loading && !data ? <Spinner /> : error && !data ? <ErrorBox message={errorMessage(error)} onRetry={reload} /> : (
        items.length === 0 ? (
          <p className="mt-3 rounded-xl bg-gray-50 px-3 py-2 text-sm text-gray-600" data-testid="area-pictures-empty">No pictures of this area yet.</p>
        ) : (
          <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {items.map((p) => <PictureCard key={p.id} p={p} busy={busy} onDecide={decide} />)}
          </ul>
        )
      )}
    </div>
  )
}
