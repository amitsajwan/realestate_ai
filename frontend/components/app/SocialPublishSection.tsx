'use client'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/lib/app/client'
import { timeAgo } from '@/lib/app/format'
import {
  channelLabel,
  doneChannels,
  friendlyPublishError,
  publishRequestError,
  SOCIAL_CHANNELS,
  statusLabel,
  statusTone,
} from '@/lib/app/social'
import { t } from '@/lib/app/strings'
import type { MarketingPack, Publication, SocialChannel, SocialStatus } from '@/lib/app/types'
import { Btn, Chip, ErrorBox } from './ui'

const checkboxCls = 'h-6 w-6 flex-none rounded border-gray-300 accent-blue-600'

function ResultRow({ p, onRetry, retrying }: { p: Publication; onRetry?: () => void; retrying?: boolean }) {
  return (
    <li className="space-y-2 rounded-xl border border-gray-200 bg-white p-3" data-testid={`pub-${p.id}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-gray-900">{channelLabel(p.channel)}</span>
        <Chip tone={statusTone(p.status)}>{statusLabel(p.status)}</Chip>
      </div>
      {p.permalink && (
        <a href={p.permalink} target="_blank" rel="noopener noreferrer" className="inline-block min-h-[44px] py-2 text-sm font-semibold text-blue-700 underline">
          {t('socialViewPost')}
        </a>
      )}
      {p.status === 'failed' && (
        <div className="space-y-2">
          <p className="text-sm text-red-700">{friendlyPublishError(p.error)}</p>
          {p.error && (
            <p className="break-words text-xs text-gray-500">
              {t('socialDetails')}: {p.error}
            </p>
          )}
          {onRetry && (
            <Btn variant="secondary" onClick={onRetry} disabled={retrying}>
              {retrying ? t('socialPosting') : t('tryAgain')}
            </Btn>
          )}
        </div>
      )}
    </li>
  )
}

/**
 * "Post to Avasetu": posts the marketing pack to the brand Facebook Page and Instagram.
 * Nothing is ever sent until the agent taps the approve button with a channel and the consent ticked.
 */
export function SocialPublishSection({ pack }: { pack: MarketingPack }) {
  const listingId = pack.listing_id
  const [status, setStatus] = useState<SocialStatus | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState<Publication[]>([])
  const [selected, setSelected] = useState<SocialChannel[]>([])
  const [forced, setForced] = useState<SocialChannel[]>([])
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [retryingId, setRetryingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<Publication[]>([])
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  const refreshHistory = useCallback(async () => {
    try {
      const items = await api.listPublications(listingId)
      if (alive.current) setHistory(items)
    } catch {
      /* history is a nice-to-have */
    }
  }, [listingId])

  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    try {
      const s = await api.getSocialStatus()
      if (alive.current) setStatus(s)
    } catch {
      if (alive.current) setLoadFailed(true)
    }
    await refreshHistory()
    if (alive.current) setLoading(false)
  }, [refreshHistory])

  useEffect(() => {
    void load()
  }, [load])

  const done = doneChannels(history, pack.version)
  const isConfigured = (c: SocialChannel) => !!status?.channels?.[c]
  const isLocked = (c: SocialChannel) => done.has(c) && !forced.includes(c)
  const canPick = (c: SocialChannel) => isConfigured(c) && !isLocked(c)
  const picked = selected.filter(canPick)
  const dry = !!status?.dry_run
  const canPost = !busy && consent && picked.length > 0

  const toggle = (c: SocialChannel) =>
    setSelected((cur) => (cur.includes(c) ? cur.filter((x) => x !== c) : [...cur, c]))

  const postAgain = (c: SocialChannel) => {
    setForced((cur) => (cur.includes(c) ? cur : [...cur, c]))
    setSelected((cur) => (cur.includes(c) ? cur : [...cur, c]))
  }

  async function post() {
    if (!canPost) return
    setBusy(true)
    setError(null)
    try {
      const created = await api.publishToSocial(listingId, {
        channels: picked,
        approve: true,
        consent: true,
        force: picked.some((c) => forced.includes(c)),
      })
      if (!alive.current) return
      setResults(created)
      setSelected([])
      setForced([])
      setConsent(false)
      await refreshHistory()
    } catch (e) {
      if (alive.current) setError(publishRequestError(e))
    } finally {
      if (alive.current) setBusy(false)
    }
  }

  async function retry(p: Publication) {
    setRetryingId(p.id)
    setError(null)
    try {
      const updated = await api.retryPublication(p.id)
      if (!alive.current) return
      setResults((cur) => cur.map((r) => (r.id === updated.id ? updated : r)))
      await refreshHistory()
    } catch (e) {
      if (alive.current) setError(publishRequestError(e))
    } finally {
      if (alive.current) setRetryingId(null)
    }
  }

  const resultIds = new Set(results.map((r) => r.id))
  const earlier = history.filter((h) => !resultIds.has(h.id))

  return (
    <section className="space-y-3 rounded-2xl border border-gray-200 bg-white p-4" aria-label={t('socialTitle')} data-testid="social-section">
      <h2 className="text-lg font-bold text-gray-900">{t('socialTitle')}</h2>
      <p className="text-sm text-gray-600">{t('socialExplain')}</p>

      {dry && (
        <p className="rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-900" data-testid="social-test-banner">
          {t('socialTestBanner')}
        </p>
      )}

      {loading && !status && <p className="text-sm text-gray-500">{t('loading')}</p>}
      {!loading && loadFailed && <ErrorBox message={t('socialLoadFailed')} onRetry={() => void load()} />}

      {status && (
        <>
          <ul className="space-y-2" aria-label={t('socialTitle')}>
            {SOCIAL_CHANNELS.map((c) => {
              const configured = isConfigured(c)
              const locked = isLocked(c)
              const label = channelLabel(c)
              return (
                <li key={c} className="flex min-h-[52px] items-center justify-between gap-3 rounded-xl border border-gray-200 px-3">
                  <label className="flex min-h-[52px] flex-1 items-center gap-3 text-base font-semibold text-gray-900">
                    <input
                      type="checkbox"
                      className={checkboxCls}
                      checked={picked.includes(c)}
                      disabled={!canPick(c)}
                      onChange={() => toggle(c)}
                    />
                    <span className={configured && !locked ? '' : 'text-gray-400'}>{label}</span>
                  </label>
                  {!configured && <Chip>{t('socialNotSetUp')}</Chip>}
                  {configured && locked && (
                    <div className="flex items-center gap-2">
                      <Chip tone="green">{t('socialDone')}</Chip>
                      <Btn variant="secondary" block={false} className="min-h-[44px] px-3 text-sm" aria-label={`${t('socialPostAgain')} ${label}`} onClick={() => postAgain(c)}>
                        {t('socialPostAgain')}
                      </Btn>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>

          <label className="flex items-start gap-3 rounded-xl bg-gray-50 p-3 text-sm text-gray-900">
            <input type="checkbox" className={`${checkboxCls} mt-0.5`} checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            <span>{t('socialConsent')}</span>
          </label>

          <Btn onClick={() => void post()} disabled={!canPost}>
            {busy ? t('socialPosting') : dry ? t('socialApproveTest') : t('socialApprove')}
          </Btn>
        </>
      )}

      {error && <ErrorBox message={error} />}

      {results.length > 0 && (
        <div className="space-y-2" data-testid="social-results">
          <h3 className="text-sm font-semibold text-gray-700">{t('socialResults')}</h3>
          <ul className="space-y-2">
            {results.map((p) => (
              <ResultRow key={p.id} p={p} onRetry={() => void retry(p)} retrying={retryingId === p.id} />
            ))}
          </ul>
        </div>
      )}

      <div className="space-y-2 border-t border-gray-100 pt-3" data-testid="social-history">
        <h3 className="text-sm font-semibold text-gray-700">{t('socialHistory')}</h3>
        {earlier.length === 0 ? (
          results.length === 0 && !loading && <p className="text-sm text-gray-500">{t('socialHistoryEmpty')}</p>
        ) : (
          <ul className="space-y-2">
            {earlier.map((p) => (
              <li key={p.id} className="space-y-1 rounded-xl bg-gray-50 p-3 text-sm" data-testid={`history-${p.id}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-gray-900">{channelLabel(p.channel)}</span>
                  <Chip tone={statusTone(p.status)}>{statusLabel(p.status)}</Chip>
                </div>
                <p className="text-xs text-gray-500">
                  {timeAgo(p.created_at)} · {t('socialVersion')} {p.pack_version}
                </p>
                {p.permalink && (
                  <a href={p.permalink} target="_blank" rel="noopener noreferrer" className="inline-block text-sm font-semibold text-blue-700 underline">
                    {t('socialViewPost')}
                  </a>
                )}
                {p.status === 'failed' && <p className="text-xs text-red-700">{friendlyPublishError(p.error)}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
