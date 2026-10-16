'use client'
import React, { useState } from 'react'
import { api, errorMessage } from '@/lib/app/client'
import type { MarketingRun, MarketingReel, VoiceChoice, VoiceGender, VoiceLanguage, VoiceStyle } from '@/lib/app/types'

/** "16 Oct, 3:05 pm" in the viewer's time. */
function when(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
}

/** "4 min 10 s", "45 s". */
function took(s?: number): string {
  if (s == null) return ''
  return s >= 60 ? `${Math.floor(s / 60)} min ${s % 60} s` : `${s} s`
}

/** When the reel was drawn and voiced, how long each took, its length and its music: one small line under it. */
export function ReelTimes({ reel }: { reel: MarketingReel }) {
  const parts = [
    reel.made_at && `made ${when(reel.made_at)}${reel.made_in_s != null ? ` in ${took(reel.made_in_s)}` : ''}`,
    reel.voiced_at && `voiced ${when(reel.voiced_at)}${reel.voice_took_s != null ? ` in ${took(reel.voice_took_s)}` : ''}`,
    reel.seconds != null && `${Math.round(reel.seconds)} s long`,
    reel.music?.title && `music: ${reel.music.title}${reel.music.artist ? ` (${reel.music.artist})` : ''}`,
  ].filter(Boolean)
  return parts.length ? <p className="mt-0.5 text-[11px] text-gray-500">{parts.join(' · ')}</p> : null
}

const GENDERS: { key: VoiceGender; label: string }[] = [
  { key: 'female', label: 'Female' },
  { key: 'male', label: 'Male' },
]
const STYLES: { key: VoiceStyle; label: string; hint: string }[] = [
  { key: 'story', label: 'Story', hint: 'talks to one viewer: a feeling, a small story, the key facts' },
  { key: 'facts', label: 'Facts', hint: 'says each screen line plainly' },
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
  const [style, setStyle] = useState<VoiceStyle>(reel.voice_style || 'story')
  const [error, setError] = useState<string | null>(null)
  const busy = reel.voice_state === 'queued' || reel.voice_state === 'making'
  const voiced = reel.voice === 'spoken'
  const label = (l?: VoiceLanguage) => choices.find((c) => c.key === l)?.label || l

  const ask = async () => {
    setError(null)
    try {
      onRun(await api.voiceReel(listingId, key, language, gender, style))
      setOpen(false)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (busy) return <p className="mt-1 text-xs text-gray-600">Adding the voice…{reel.voice_asked_at ? ` (asked ${when(reel.voice_asked_at)})` : ''}</p>
  return (
    <div className="mt-1 space-y-1">
      {voiced && !open && (
        <p className="text-xs text-gray-600">Voice: {label(reel.voice_language)}, {reel.voice_gender}{reel.voice_style ? `, ${reel.voice_style}` : ''}</p>
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
          <div className="space-y-1 text-xs" role="radiogroup" aria-label="Style">
            {STYLES.map((st) => (
              <label key={st.key} className="flex cursor-pointer items-start gap-2">
                <input type="radio" name={`voice-style-${key}`} checked={style === st.key} onChange={() => setStyle(st.key)} className="mt-0.5" />
                <span><span className="font-medium">{st.label}</span>: <span className="text-gray-600">{st.hint}</span></span>
              </label>
            ))}
          </div>
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
