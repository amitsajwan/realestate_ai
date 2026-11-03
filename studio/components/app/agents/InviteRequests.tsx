'use client'
import React, { useState } from 'react'
import { adminApi } from '@/lib/app/admin'
import type { InviteRequest, InvitedRequest } from '@/lib/app/admin'
import { errorMessage } from '@/lib/app/client'
import { friendlyConciergeError } from '@/lib/app/concierge'
import { timeAgo } from '@/lib/app/format'
import { copyText } from '@/lib/app/share'
import { Btn, ErrorBox, LinkBtn, inputCls } from '../ui'

/** The brand's primary action (navy, like the header). */
export function NavyBtn(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" {...props} className="min-h-[52px] w-full rounded-xl bg-[#102340] px-5 text-base font-semibold text-white active:opacity-90 disabled:opacity-50" />
}

/** The code and WhatsApp message for an invited website request (shown once, like Add agent). */
export function CodeSheet({ result, onClose }: { result: InvitedRequest; onClose: () => void }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/50" role="dialog" aria-modal="true" aria-label="Send this to the agent">
      <div className="mx-auto max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5" style={{ paddingBottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Send this to {result.agent.name}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="min-h-[44px] min-w-[44px] text-2xl text-gray-500">×</button>
        </div>
        {result.code && result.whatsapp_message ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Agent created from the website request. This code is shown only now.</p>
            <p className="rounded-2xl bg-[#102340] py-4 text-center text-4xl font-bold tracking-[0.3em] text-[#F0B13B]" data-testid="invite-code">{result.code}</p>
            <label className="block text-sm font-medium text-gray-700" htmlFor="adm-msg">WhatsApp message</label>
            <textarea id="adm-msg" readOnly className={`${inputCls} min-h-[120px] py-3 text-sm`} value={result.whatsapp_message} />
            <Btn variant="secondary" onClick={async () => { setCopied(await copyText(result.whatsapp_message as string)); setTimeout(() => setCopied(false), 2000) }}>
              {copied ? 'Copied!' : 'Copy message'}
            </Btn>
            {result.whatsapp_url && <LinkBtn variant="whatsapp" href={result.whatsapp_url} target="_blank" rel="noopener noreferrer">Open WhatsApp</LinkBtn>}
          </div>
        ) : (
          <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            {result.agent.name} was already added, so no new code was made. Open him under Agents and use Make a new code if he needs one.
          </p>
        )}
        <Btn variant="ghost" onClick={onClose}>Done</Btn>
      </div>
    </div>
  )
}

export function InviteRow({ req, onInvited, onDismissed }: { req: InviteRequest; onInvited: (r: InvitedRequest) => void; onDismissed: () => void }) {
  const [busy, setBusy] = useState<'invite' | 'dismiss' | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function run(kind: 'invite' | 'dismiss') {
    setBusy(kind)
    setError(null)
    try {
      if (kind === 'invite') onInvited(await adminApi.invite(req.id))
      else {
        await adminApi.dismiss(req.id)
        onDismissed()
      }
    } catch (e) {
      setError(friendlyConciergeError(e) || errorMessage(e))
      setBusy(null)
    }
  }
  return (
    <li data-testid="invite-row" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
      <div>
        <p className="font-semibold text-gray-900">{req.name}</p>
        <p className="text-sm text-gray-600">{req.mobile}{req.city ? ` · ${req.city}` : ''}{req.created_at ? ` · asked ${timeAgo(req.created_at)}` : ''}</p>
        {req.message && <p className="mt-1 text-sm italic text-gray-700">&ldquo;{req.message}&rdquo;</p>}
      </div>
      {error && <ErrorBox message={error} />}
      {confirming ? (
        <div className="flex gap-2">
          <Btn variant="danger" onClick={() => run('dismiss')} disabled={!!busy}>{busy === 'dismiss' ? 'Dismissing...' : 'Yes, dismiss'}</Btn>
          <Btn variant="ghost" onClick={() => setConfirming(false)} disabled={!!busy}>Keep</Btn>
        </div>
      ) : (
        <div className="flex gap-2">
          <NavyBtn onClick={() => run('invite')} disabled={!!busy}>{busy === 'invite' ? 'Inviting...' : 'Invite'}</NavyBtn>
          <Btn variant="ghost" onClick={() => setConfirming(true)} disabled={!!busy}>Dismiss</Btn>
        </div>
      )}
    </li>
  )
}

