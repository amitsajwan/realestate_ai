'use client'
import React, { useEffect } from 'react'
import { t } from '@/lib/app/strings'
import { mmss, useRecorder } from '@/lib/app/useRecorder'
import { Btn } from './ui'

/** Big mic button: record / stop / timer / playback. Reports the recorded Blob (or null) upward. */
export function VoiceRecorder({ onChange }: { onChange: (b: Blob | null) => void }) {
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
