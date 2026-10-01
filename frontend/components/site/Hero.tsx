import React from 'react'
import type { AgentProfile } from '@/lib/site/types'
import { BANNER_OVERLAY, type HeroArt } from '@/lib/site/presets'
import { displayName, monogram, resolveTheme, safeImage } from '@/lib/site/theme'
import ContactButtons from './ContactButtons'
import Skyline from './Skyline'
import { whatsappMessage } from '@/lib/site/links'

export const DEFAULT_HEADLINE = 'Homes in Pune, shared clearly'
const DEFAULT_SUB = 'Price, area, possession and RERA in one place. Tell us what you are looking for and we will send you the details.'

/** Preset-specific background texture (CSS only, decorative). The skyline is drawn separately along the bottom edge. */
function artStyle(art: HeroArt): React.CSSProperties {
  switch (art) {
    case 'arcs':
      return { backgroundImage: 'radial-gradient(circle at 92% 8%, transparent 0 60px, rgba(255,255,255,.10) 61px 62px, transparent 63px 110px, rgba(255,255,255,.08) 111px 112px, transparent 113px 170px, rgba(255,255,255,.06) 171px 172px, transparent 173px)' }
    case 'sun':
      return { backgroundImage: 'radial-gradient(circle at 80% 100%, rgba(255,214,140,.6) 0 70px, rgba(255,214,140,.2) 71px 130px, transparent 131px)' }
    case 'diagonal':
      return { backgroundImage: 'repeating-linear-gradient(135deg, rgba(255,255,255,.07) 0 2px, transparent 2px 22px)' }
    case 'grid':
      return { backgroundImage: 'linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px)', backgroundSize: '36px 36px' }
    case 'paper':
      return { backgroundImage: 'radial-gradient(rgba(43,33,24,.10) 1px, transparent 1.2px)', backgroundSize: '18px 18px' }
    default:
      return {}
  }
}

/** The agent's own hero: banner photo under a dark overlay when he uploaded one, else his preset's gradient, texture and skyline. */
export default function Hero({ agent, city }: { agent: AgentProfile; city: string }) {
  const b = agent.branding_data
  const t = resolveTheme(b)
  const banner = safeImage(b?.banner)
  const name = displayName(agent)
  const tagline = (b?.tagline || '').trim()
  const photo = safeImage(agent.photo) || (agent.photo && /^https:\/\//.test(agent.photo) ? agent.photo : null)
  const light = !banner && t.id === 'cream-ink'
  const areas = (b?.areas || []).slice(0, 2)
  const eyebrow = areas.length ? [...areas, city || 'Pune'].join(' · ') : `Homes in ${city || 'Pune'}`  // area first; never reads like a brand name
  const bg: React.CSSProperties = banner ? { backgroundColor: BANNER_OVERLAY.solid } : { backgroundImage: 'linear-gradient(165deg, var(--site-hero-from), var(--site-hero-to))' }
  const fill = light ? 'var(--site-primary)' : 'var(--site-accent)'
  const fillInk = light ? '#ffffff' : 'var(--site-on-accent)'
  const ghost = light ? 'var(--site-primary)' : 'rgba(255,255,255,.75)'

  return (
    <section aria-labelledby="hero-title" data-hero={banner ? 'banner' : t.art} data-preset={t.id} className="relative overflow-hidden" style={{ ...bg, color: banner ? '#ffffff' : 'var(--site-hero-fg)' }}>
      {banner ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={banner} alt="" className="absolute inset-0 h-full w-full object-cover" />
          <div aria-hidden className="absolute inset-0" style={{ backgroundImage: `linear-gradient(180deg, ${BANNER_OVERLAY.from}, ${BANNER_OVERLAY.to})` }} />
        </>
      ) : (
        <div aria-hidden className="absolute inset-0" style={artStyle(t.art)} />
      )}
      <div className="relative mx-auto max-w-5xl px-4 pb-8 pt-9 sm:pb-10 sm:pt-14">
        <div className="flex items-center gap-3">
          {photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={photo} alt={'Photo of ' + agent.agent_name} width={56} height={56} className="h-14 w-14 rounded-full border-2 object-cover" style={{ borderColor: light ? 'var(--site-accent)' : '#ffffff' }} />
          ) : (
            <span aria-hidden className="flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold" style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>{monogram(agent.agent_name)}</span>
          )}
          <div className="min-w-0 text-sm leading-tight">
            <p className="truncate font-semibold">{agent.agent_name}</p>
            <p className="truncate opacity-90">{[name !== agent.agent_name ? name : 'Property advisor', b?.years_experience ? b.years_experience + ' years in property' : ''].filter(Boolean).join(' · ')}</p>
          </div>
        </div>
        <p className="mt-6 inline-block rounded-full px-4 py-1 text-xs font-bold uppercase tracking-wide" style={{ background: 'var(--site-accent)', color: 'var(--site-on-accent)' }}>{eyebrow}</p>
        <h1 id="hero-title" className="mt-4 max-w-2xl text-4xl font-extrabold leading-tight sm:text-5xl">{tagline || DEFAULT_HEADLINE}</h1>
        <p className="mt-3 max-w-xl text-lg opacity-95">{tagline ? 'Price, area, possession and RERA, stated clearly for every home.' : DEFAULT_SUB}</p>
        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          <a href="#enquire" className="inline-flex min-h-[52px] items-center justify-center px-8 text-lg font-bold no-underline" style={{ background: fill, color: fillInk, borderRadius: 'var(--site-radius)' }}>I&apos;m interested</a>
          <a href="#listings" className="inline-flex min-h-[52px] items-center justify-center border-2 px-8 text-lg font-semibold no-underline" style={{ borderColor: ghost, color: 'inherit', borderRadius: 'var(--site-radius)' }}>See properties</a>
        </div>
        <div className="mt-5 max-w-md"><ContactButtons agentSlug={agent.slug} phone={agent.phone} waMessage={whatsappMessage(agent.agent_name)} /></div>
      </div>
      {!banner && <Skyline tower={light ? '#2b2118' : 'var(--site-secondary)'} lit="var(--site-accent)" />}
    </section>
  )
}
