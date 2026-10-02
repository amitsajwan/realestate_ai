'use client'
import React, { useEffect, useState } from 'react'
import { ApiError } from '@/lib/app/api'
import { CHANNEL_LABEL, conciergeApi, firstName, friendlyConciergeError } from '@/lib/app/concierge'
import type { Captions, PostChannel, PostResult } from '@/lib/app/concierge'
import { REEL_LANGS, reelsApi } from '@/lib/app/reels'
import type { ReelJob, ReelLang, ReelPost } from '@/lib/app/reels'
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

  // A finished listing reel can go out as an Instagram / Facebook Reel instead (same consent, same 'Listed by' caption).
  const [reels, setReels] = useState<ReelJob[]>([])
  const [reelLang, setReelLang] = useState<ReelLang | null>(null)
  const [reelBusy, setReelBusy] = useState(false)
  const [reelResults, setReelResults] = useState<ReelPost[] | null>(null)
  useEffect(() => {
    let alive = true
    reelsApi.forAgentListing(agentId, listingId).latest().then((jobs) => {
      const done = Object.values(jobs).filter((j): j is ReelJob => !!j && j.status === 'done')
      if (alive) {
        setReels(done)
        setReelLang(done[0]?.lang ?? null)
      }
    }).catch(() => { /* no reel: the option simply does not show */ })
    return () => {
      alive = false
    }
  }, [agentId, listingId])

  async function postReel() {
    if (!reelLang) return
    setReelBusy(true)
    setError(null)
    try {
      setReelResults(await reelsApi.postReel(agentId, listingId, reelLang))
    } catch (e) {
      setError(friendlyConciergeError(e))
    } finally {
      setReelBusy(false)
    }
  }

  const dry = results?.some((r) => r.status === 'dry_run') || reelResults?.some((r) => r.status === 'dry_run')
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

        {reels.length > 0 && (
          <section className="mt-4 space-y-2 rounded-2xl border border-gray-200 p-3" aria-label="Post the reel" data-testid="post-reel">
            <h3 className="text-sm font-semibold text-gray-900">Or post the finished reel as an Instagram and Facebook Reel</h3>
            {reels.length > 1 && (
              <div role="radiogroup" aria-label="Reel language" className="flex gap-2">
                {reels.map((j) => (
                  <button key={j.lang} type="button" role="radio" aria-checked={reelLang === j.lang} onClick={() => setReelLang(j.lang)}
                    className={`min-h-[44px] flex-1 rounded-xl border text-sm font-semibold ${reelLang === j.lang ? 'border-blue-600 bg-blue-50 text-blue-900' : 'border-gray-300 text-gray-700'}`}>
                    {REEL_LANGS.find((l) => l.code === j.lang)?.label ?? j.lang}
                  </button>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500">The caption carries the same &lsquo;Listed by&rsquo; line as the post above.</p>
            {reelResults ? (
              <ul className="space-y-1 text-sm" data-testid="reel-results">
                {reelResults.map((r) => (
                  <li key={r.channel} className={r.status === 'failed' ? 'text-red-700' : 'text-green-700'}>
                    {CHANNEL_LABEL[r.channel]}: {r.status === 'failed' ? `failed. ${r.error ?? ''}` : r.status === 'dry_run' ? 'checked (test mode, nothing was published)' : r.status === 'already_posted' ? 'already posted' : 'reel posted'}
                  </li>
                ))}
              </ul>
            ) : (
              <Btn variant="secondary" onClick={postReel} disabled={!consentGiven || reelBusy || !reelLang}>
                {reelBusy ? 'Posting the reel...' : `Post the reel for ${firstName(agentName)}`}
              </Btn>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
