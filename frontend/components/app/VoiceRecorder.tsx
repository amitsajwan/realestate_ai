'use client'
import React, { useEffect } from 'react'
import { t } from '@/lib/app/strings'
import { mmss, useRecorder } from '@/lib/app/useRecorder'
import { Btn } from './ui'

/** Voice is a Premium feature: unless NEXT_PUBLIC_VOICE_ENABLED=true it is shown, greyed out and labelled Premium. */
export const VOICE_ENABLED = process.env.NEXT_PUBLIC_VOICE_ENABLED === 'true'

export function VoiceRecorder({ onChange }: { onChange: (b: Blob | null) => void }) {
  return VOICE_ENABLED ? <LiveVoiceRecorder onChange={onChange} /> : <PremiumVoiceTeaser />
}

function PremiumVoiceTeaser() {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-4" data-testid="voice-premium">
      <div className="relative">
        <button type="button" disabled aria-disabled="true" aria-label={`${t('voicePremium')} (${t('voicePremiumBadge')})`}
          className="flex h-24 w-24 cursor-not-allowed items-center justify-center rounded-full bg-gray-300 text-4xl text-white opacity-70">
          <span aria-hidden>🎤</span>
        </button>
        <span className="absolute -right-3 -top-2 rounded-full bg-amber-400 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-gray-900 shadow">{t('voicePremiumBadge')}</span>
      </div>
      <p className="text-sm font-semibold text-gray-700">{t('voicePremium')}</p>
      <p className="text-center text-xs text-gray-500">{t('voicePremiumSub')}</p>
    </div>
  )
}

/** Big mic button: record / stop / timer / playback. Reports the recorded Blob (or null) upward. */
function LiveVoiceRecorder({ onChange }: { onChange: (b: Blob | null) => void }) {
  const rec = useRecorder()

  useEffect(() => {
    onChange(rec.state === 'done' ? rec.blob : null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rec.state, rec.blob])

  const recording = rec.state === 'recording'
  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        onClick={recording ? rec.stop : rec.start}
        aria-label={recording ? t('stopRecording') : t('speak')}
        className={`flex h-24 w-24 items-center justify-center rounded-full text-4xl text-white shadow-lg ${recording ? 'animate-pulse bg-red-600' : 'bg-blue-600 active:bg-blue-700'}`}
      >
        {recording ? '■' : '🎤'}
      </button>
      <p className="text-sm font-medium text-gray-600" aria-live="polite">
        {recording ? `${t('recording')} ${mmss(rec.seconds)} - ${t('stopRecording')}` : rec.state === 'done' ? mmss(rec.seconds) : t('speak')}
      </p>
      {rec.state === 'done' && rec.url && (
        <div className="w-full space-y-2">
          <audio controls src={rec.url} className="w-full" />
          <Btn variant="ghost" onClick={rec.reset}>{t('reRecord')}</Btn>
        </div>
      )}
      {rec.error && (
        <p role="alert" className="rounded-xl bg-amber-50 p-3 text-center text-sm text-amber-800">
          {rec.error === 'unsupported' ? t('micUnsupported') : rec.error === 'denied' ? t('micDenied') : 'Could not start the microphone. You can type instead.'}
        </p>
      )}
    </div>
  )
}
