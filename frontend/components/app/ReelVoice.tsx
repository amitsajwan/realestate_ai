'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import type { MarketingRun, MarketingReel, VoiceChoice, VoiceGender, VoiceLanguage } from '@/lib/app/types'

const GENDERS: { key: VoiceGender; label: string }[] = [
  { key: 'female', label: 'Female' },
  { key: 'male', label: 'Male' },
]

/** One reel's voice-over, the last step: pick Hinglish, English or Marathi (each shows how the reel opens) and a female or
 *  male voice; the server makes it in the background, the run's poll shows it when done. */
export function ReelVoice({ listingId, reel, choices, onRun }: {
  listingId: string
  reel: MarketingReel
  choices: VoiceChoice[]
  onRun: (r: MarketingRun) => void
}) {
  const key = reel.kind === 'ad' ? reel.angle || '' : reel.kind
  const [open, setOpen] = useState(false)
  const [language, setLanguage] = useState<VoiceLanguage>(reel.voice_language || 'hinglish')
  const [gender, setGender] = useState<VoiceGender>(reel.voice_gender || 'female')
  const [error, setError] = useState<string | null>(null)
  const busy = reel.voice_state === 'queued' || reel.voice_state === 'making'
  const voiced = reel.voice === 'spoken'
  const label = (l?: VoiceLanguage) => choices.find((c) => c.key === l)?.label || l

  const ask = async () => {
    setError(null)
    try {
      onRun(await api.voiceReel(listingId, key, language, gender))
      setOpen(false)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (busy) return <p className="mt-1 text-xs text-gray-600">Adding the voice…</p>
  return (
    <div className="mt-1 space-y-1">
      {voiced && !open && (
        <p className="text-xs text-gray-600">Voice: {label(reel.voice_language)}, {reel.voice_gender}</p>
      )}
      {reel.voice_state === 'failed' && reel.voice_error && <p className="text-xs text-red-600">{reel.voice_error}</p>}
      {!open ? (
        <button type="button" onClick={() => setOpen(true)} className="text-xs font-medium text-amber-700 underline">
          {voiced ? 'Change voice' : 'Add voice'}
        </button>
      ) : (
        <fieldset className="space-y-2 rounded-lg border border-gray-200 p-2">
          <legend className="px-1 text-xs font-medium text-gray-700">Voice language</legend>
          {choices.map((c) => (
            <label key={c.key} className="flex cursor-pointer items-start gap-2 text-xs">
              <input type="radio" name={`voice-lang-${key}`} checked={language === c.key} onChange={() => setLanguage(c.key)}
                className="mt-0.5" />
              <span><span className="font-medium">{c.label}</span>: <span className="text-gray-600">&ldquo;{c.sample}&rdquo;</span></span>
            </label>
          ))}
          <div className="flex gap-3 text-xs" role="radiogroup" aria-label="Voice">
            {GENDERS.map((g) => (
              <label key={g.key} className="flex cursor-pointer items-center gap-1">
                <input type="radio" name={`voice-gender-${key}`} checked={gender === g.key} onChange={() => setGender(g.key)} />
                {g.label}
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={ask} className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white">
              {voiced ? 'Make with this voice' : 'Add this voice'}
            </button>
            <button type="button" onClick={() => setOpen(false)} className="px-2 text-xs text-gray-600">Cancel</button>
          </div>
          <p className="text-[11px] text-gray-500">Takes about a minute. Waiting calendar posts get the voiced reel.</p>
        </fieldset>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
