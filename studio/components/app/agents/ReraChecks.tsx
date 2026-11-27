'use client'
import React, { useState } from 'react'
import { adminApi } from '@/lib/app/admin'
import type { AgentCheck, AgentCheckStatus } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import { MAHARERA_URL } from '@shared/site/theme'
import { Btn, inputCls } from '../ui'

const LABEL: Record<AgentCheckStatus, string> = { pending: 'To check', verified: 'MahaRERA verified', rejected: 'Did not match' }
const TONE: Record<AgentCheckStatus, string> = {
  pending: 'bg-amber-100 text-amber-900', verified: 'bg-green-100 text-green-900', rejected: 'bg-red-100 text-red-800',
}

/**
 * Studio > Agents > MahaRERA check (owner only; docs/plan/agent-network.md step 1). Each agent's MahaRERA agent number, to look up
 * on the register by hand: paste the agent's register page and mark it verified, or say why it did not match. Only verified agents
 * see the lead board, and their page shows the "MahaRERA verified" badge. A number the agent changes comes back here to check.
 */
export function ReraChecks({ items, onChange }: { items: AgentCheck[]; onChange: () => void }) {
  if (items.length === 0) return <p className="rounded-2xl bg-white p-6 text-center text-gray-600">No agents yet.</p>
  return (
    <>
      <p className="text-sm text-gray-600">
        Look each number up on the <a href={MAHARERA_URL} target="_blank" rel="noopener noreferrer" className="font-semibold text-blue-700 underline">MahaRERA register</a>,
        then record what it says. Only verified agents see the lead board.
      </p>
      <ul className="space-y-2">{items.map((c) => <CheckRow key={c.agent_id} c={c} onChange={onChange} />)}</ul>
    </>
  )
}

function CheckRow({ c, onChange }: { c: AgentCheck; onChange: () => void }) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState(c.register_url ?? '')
  const [note, setNote] = useState(c.note ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save(status: AgentCheckStatus) {
    setBusy(true)
    setError(null)
    try {
      await adminApi.setAgentCheck(c.agent_id, { status, register_url: url.trim() || null, note: note.trim() || null })
      setOpen(false)
      onChange()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li data-testid="rera-check-row" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{c.name}</p>
          <p className="text-sm text-gray-700">{c.rera_agent_no ? `MahaRERA ${c.rera_agent_no}` : 'No MahaRERA number given yet'}</p>
          {c.number_changed && <p className="text-xs font-semibold text-amber-800">Changed the number since the last check</p>}
          {c.checked_at && <p className="text-xs text-gray-500">Checked {timeAgo(c.checked_at)}{c.note ? ` · ${c.note}` : ''}</p>}
          {c.register_url && c.status === 'verified' && (
            <a href={c.register_url} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold text-blue-700 underline">Register page</a>
          )}
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${TONE[c.status]}`}>{LABEL[c.status]}</span>
      </div>
      {c.rera_agent_no && !open && (
        <Btn variant="secondary" onClick={() => setOpen(true)}>{c.status === 'pending' ? 'Record the check' : 'Change'}</Btn>
      )}
      {open && (
        <div className="space-y-2">
          <label className="block space-y-1 text-sm font-semibold text-gray-800">
            <span>The agent&apos;s page on the MahaRERA register</span>
            <input className={inputCls} inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://maharerait.maharashtra.gov.in/agent/view/..." />
          </label>
          <label className="block space-y-1 text-sm font-semibold text-gray-800">
            <span>Note (optional, only you see it)</span>
            <input className={inputCls} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Name matches, registration valid to 2028" />
          </label>
          {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
          <div className="grid grid-cols-2 gap-2">
            <Btn disabled={busy} onClick={() => save('verified')}>Verified</Btn>
            <Btn variant="secondary" disabled={busy} onClick={() => save('rejected')}>Did not match</Btn>
          </div>
          {c.status !== 'pending' && (
            <button type="button" disabled={busy} onClick={() => save('pending')} className="min-h-[44px] w-full text-sm font-semibold text-gray-600">Undo the check</button>
          )}
          <button type="button" onClick={() => setOpen(false)} className="min-h-[44px] w-full text-sm font-semibold text-gray-600">Cancel</button>
        </div>
      )}
    </li>
  )
}
