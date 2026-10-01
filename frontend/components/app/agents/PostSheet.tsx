'use client'
import React, { useEffect, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { CHANNEL_LABEL, conciergeApi, firstName, friendlyConciergeError } from '@/lib/app/concierge'
import type { Captions, PostChannel, PostResult } from '@/lib/app/concierge'
import { Btn, ErrorBox, Spinner } from '../ui'
import { BRAND_NAME } from '@/lib/brand'

const ORDER: PostChannel[] = ['facebook_page', 'instagram']

/**
 * Shows the exact captions first (with 'Listed by' and his interest link), then posts on the Avasetu Page and
 * Instagram after the owner approves on the agent's behalf. Needs the agent's recorded consent.
 */
export function PostSheet({ agentId, agentName, listingId, listingTitle, consentGiven, onClose }: {
  agentId: string
  agentName: string
  listingId: string
  listingTitle: string
  consentGiven: boolean
  onClose: () => void
}) {
  const [captions, setCaptions] = useState<Captions | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState<PostResult[] | null>(null)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        let c: Captions
        try {
          c = await conciergeApi.captions(agentId, listingId)
        } catch (e) {
          if (e instanceof ApiError && e.status === 409 && /pack/i.test(e.detail)) {
            await conciergeApi.makePack(agentId, listingId) // the post text and images come from the marketing pack
            c = await conciergeApi.captions(agentId, listingId)
          } else throw e
        }
        if (alive) setCaptions(c)
      } catch (e) {
        if (alive) setError(friendlyConciergeError(e))
      }
    })()
    return () => {
      alive = false
    }
  }, [agentId, listingId])

  async function post() {
    setBusy(true)
    setError(null)
    try {
      setResults(await conciergeApi.post(agentId, listingId))
    } catch (e) {
      setError(friendlyConciergeError(e))
    } finally {
      setBusy(false)
    }
  }

  const dry = results?.some((r) => r.status === 'dry_run')
  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/50" role="dialog" aria-modal="true" aria-label={`Post to ${BRAND_NAME}`}>
      <div className="mx-auto max-h-[92vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-5" style={{ paddingBottom: 'calc(1.25rem + env(safe-area-inset-bottom, 0px))' }}>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Post to {BRAND_NAME}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="min-h-[44px] min-w-[44px] text-2xl text-gray-500">×</button>
        </div>
        <p className="mb-3 text-sm text-gray-600">{listingTitle}. This goes on the {BRAND_NAME} pages, not {firstName(agentName)}&apos;s own accounts. Buyers who tap the link reach {firstName(agentName)}.</p>

        {!captions && !error && <Spinner label="Preparing the post..." />}
        {captions && (
          <div className="space-y-3">
            {ORDER.filter((c) => captions[c]).map((c) => (
              <section key={c} className="rounded-2xl border border-gray-200 bg-gray-50 p-3" data-testid={`caption-${c}`}>
                <h3 className="text-sm font-semibold text-blue-900">{CHANNEL_LABEL[c]}</h3>
                <p className="mt-1 whitespace-pre-wrap break-words text-sm text-gray-800">{captions[c]?.text}</p>
              </section>
            ))}
          </div>
        )}
        {error && <div className="mt-3"><ErrorBox message={error} /></div>}

        {results ? (
          <div className="mt-3 space-y-2">
            <ul className="space-y-1 text-sm">
              {results.map((r) => (
                <li key={r.channel} className={r.status === 'failed' ? 'text-red-700' : 'text-green-700'}>
                  {CHANNEL_LABEL[r.channel]}: {r.status === 'failed' ? `failed. ${r.error ?? ''}` : r.status === 'dry_run' ? 'checked (test mode, nothing was published)' : 'posted'}
                </li>
              ))}
            </ul>
            {dry && <p className="text-xs text-gray-500">Test mode is on, so nothing went out. Posting for real is switched on in the server settings.</p>}
            <Btn onClick={onClose}>Done</Btn>
          </div>
        ) : (
          <div className="mt-4 space-y-2">
            {!consentGiven && <p role="alert" className="rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-900">Record {firstName(agentName)}&apos;s consent first (on his page). Posting is blocked until then.</p>}
            <Btn onClick={post} disabled={!captions || !consentGiven || busy}>{busy ? 'Posting...' : `Approve and post for ${firstName(agentName)}`}</Btn>
            <Btn variant="ghost" onClick={onClose}>Cancel</Btn>
          </div>
        )}
      </div>
    </div>
  )
}
