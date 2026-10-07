'use client'
import React, { useState } from 'react'
import { errorMessage } from '@/lib/app/client'
import { conciergeApi, friendlyConciergeError } from '@/lib/app/concierge'
import type { CreatedAgent } from '@/lib/app/concierge'
import { normalizePhone } from '@/lib/app/format'
import { copyText } from '@/lib/app/share'
import { Btn, ErrorBox, Field, LinkBtn, inputCls } from '../ui'

/** Bottom sheet: name, mobile, label. Then the 6-digit code and the WhatsApp message to send (shown once). */
export function AddAgentSheet({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('')
  const [mobile, setMobile] = useState('')
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CreatedAgent | null>(null)
  const [copied, setCopied] = useState(false)

  const phone = normalizePhone(mobile)
  const valid = name.trim().length >= 2 && !!phone

  async function submit(reissue = false) {
    if (!valid) return
    setBusy(true)
    setError(null)
    try {
      const r = await conciergeApi.create({ name: name.trim(), mobile: phone as string, label: label.trim(), reissue })
      setResult(r)
      onCreated()
    } catch (e) {
      setError(friendlyConciergeError(e) || errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/50" role="dialog" aria-modal="true" aria-label="Add agent">
      <div className="mx-auto max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5" style={{ paddingBottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">{result ? 'Send this to the agent' : 'Add agent'}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="min-h-[44px] min-w-[44px] text-2xl text-gray-500">×</button>
        </div>

        {!result ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">We set up his login and website now. You can fill in his logo, listings and details after.</p>
            <Field label="His name" htmlFor="ag-name">
              <input id="ag-name" className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="Rahul Sharma" autoComplete="off" />
            </Field>
            <Field label="His mobile number" htmlFor="ag-mobile" error={mobile && !phone ? 'Enter a valid 10-digit mobile' : undefined}>
              <input id="ag-mobile" className={inputCls} inputMode="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="98765 43210" autoComplete="off" />
            </Field>
            <Field label="Label for you (optional)" htmlFor="ag-label">
              <input id="ag-label" className={inputCls} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Rahul, Baner" autoComplete="off" />
            </Field>
            {error && <ErrorBox message={error} />}
            <Btn onClick={() => submit(false)} disabled={!valid || busy}>{busy ? 'Setting up...' : 'Create agent'}</Btn>
          </div>
        ) : result.code && result.whatsapp_message ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">{result.reissued ? 'A new code was made. The old code no longer works.' : 'Agent created.'} This code is shown only now.</p>
            <p className="rounded-2xl bg-blue-900 py-4 text-center text-4xl font-bold tracking-[0.3em] text-amber-400" data-testid="invite-code">{result.code}</p>
            <label className="block text-sm font-medium text-gray-700" htmlFor="ag-msg">WhatsApp message</label>
            <textarea id="ag-msg" readOnly className={`${inputCls} min-h-[120px] py-3 text-sm`} value={result.whatsapp_message} />
            <Btn variant="secondary" onClick={async () => { setCopied(await copyText(result.whatsapp_message as string)); setTimeout(() => setCopied(false), 2000) }}>
              {copied ? 'Copied!' : 'Copy message'}
            </Btn>
            {result.whatsapp_url && <LinkBtn variant="whatsapp" href={result.whatsapp_url} target="_blank" rel="noopener noreferrer">Open WhatsApp</LinkBtn>}
            <Btn variant="ghost" onClick={onClose}>Done</Btn>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">{result.agent.name} is already added. Codes are stored scrambled, so the old one cannot be shown again.</p>
            {error && <ErrorBox message={error} />}
            <Btn onClick={() => submit(true)} disabled={busy}>Make a new code</Btn>
            <p className="text-xs text-gray-500">A new code stops the old one from working.</p>
            <Btn variant="ghost" onClick={onClose}>Close</Btn>
          </div>
        )}
      </div>
    </div>
  )
}
