'use client'
import React, { useEffect, useRef, useState } from 'react'
import { API_BASE_URL } from '@/lib/config/api'
import { getAnonId, readAttribution, readVisitPages, trackEvent } from '@/lib/site/tracking'
import { chatContextFromPath, type ChatContext } from '@/lib/site/chatContext'
import { cardFacts, parseChatReply, WHATSAPP_QUICK, type ChatCard, type ChatLink } from '@/lib/site/chatApi'
import { addSeconds, askNow, isMuted, mute, nudgeAllowed, parseNudge, TICK_SECONDS, type Nudge } from '@/lib/site/chatNudge'
import { BRAND_NAME } from '@/lib/brand'

interface Msg { role: 'bot' | 'you'; text: string; cards?: ChatCard[] }
const SID_KEY = 'pp_chat_sid'
/** Any time, in the chat's header: tapping one sends the word, and the server carries on in that language. */
const LANGUAGES = ['हिंदी', 'मराठी', 'English']
const LOG_KEY = 'pp_chat_log'
/** Dispatched on window with { message, context? } to open the bubble and ask that question; `context` (a card's project on a
 *  list page) replaces the one read from the page path for the rest of the visit to this page. */
export const OPEN_CHAT_EVENT = 'avasetu:open-chat'

function sessionId(): string {
  try {
    const have = window.localStorage.getItem(SID_KEY)
    if (have && have.length >= 12) return have
    const id = (crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2) + Date.now().toString(36)).replace(/-/g, '')
    window.localStorage.setItem(SID_KEY, id)
    return id
  } catch {
    return 'anon' + Math.random().toString(36).slice(2, 14) + '000'
  }
}

/** One matching home: photo, title, area facts and the price, or a Sample badge (samples are illustrations and show no price). */
export function ChatHomeCard({ card }: { card: ChatCard }) {
  const facts = cardFacts(card)
  return (
    <li>
      <a href={card.url} data-testid="chat-home-card"
        className="flex min-h-[64px] items-stretch gap-3 overflow-hidden rounded-xl border border-slate-200 bg-white no-underline shadow-sm hover:border-[#102340] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f0b440]">
        <span className="relative block w-[64px] shrink-0 bg-[#102340]" aria-hidden="true">
          {card.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={card.image_url} alt="" width={64} height={64} loading="lazy" decoding="async" className="h-full w-full object-cover" />
          ) : (
            <span className="flex h-full w-full items-center justify-center text-2xl text-[#f0b440]">⌂</span>
          )}
        </span>
        <span className="flex min-w-0 flex-1 flex-col justify-center py-1.5 pr-3">
          <span className="truncate text-[14px] font-semibold leading-tight text-slate-900">{card.title}</span>
          {facts && <span className="mt-0.5 truncate text-[13px] text-slate-600">{facts}</span>}
          {card.fact && <span className="mt-0.5 line-clamp-2 text-[12px] leading-snug text-slate-600">{card.fact}</span>}
          <span className="mt-1 flex flex-wrap items-center gap-2">
            {card.hot && <span className="rounded-full bg-[#102340] px-2 py-0.5 text-[11px] font-bold text-[#f0b440]">Hot</span>}
            {card.sample ? (
              <span className="inline-block rounded-full bg-amber-300 px-2 py-0.5 text-[12px] font-bold text-slate-900">Sample</span>
            ) : card.price_text ? (
              <span className="text-[14px] font-extrabold text-[#102340]">{card.price_text}</span>
            ) : null}
          </span>
        </span>
      </a>
    </li>
  )
}

/** Where the bubble sits: above the agent site's mobile StickyBar (in the corner from md up), or in the corner; both clear the iPhone home bar. */
const CHAT_BOTTOM = {
  withBar: 'bottom-[calc(5rem+env(safe-area-inset-bottom,0px))] md:bottom-6',
  withoutBar: 'bottom-[calc(1rem+env(safe-area-inset-bottom,0px))] sm:bottom-6',
}

/**
 * Floating "Chat with us" for public pages. Answers basic questions, shows matching homes as cards, and, step by step, collects the visitor's
 * requirement and (with consent) a phone number. All logic is on the server; this component only shows the conversation.
 * `agentSlug` decides whose inbox a lead lands in. `bottomBar` (default true: agent sites) lifts the bubble above the mobile
 * WhatsApp / Call / Enquire bar; pages without that bar pass false so it sits in the corner. On phones the closed bubble is a small round
 * icon button (named "Chat with us" for screen readers) so it covers as little of the page as possible; from 640 px up it shows the words.
 */
export default function ChatWidget({ agentSlug, bottomBar = true }: { agentSlug: string; bottomBar?: boolean }) {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [quick, setQuick] = useState<string[]>([])
  const [waUrl, setWaUrl] = useState<string | null>(null)
  const [link, setLink] = useState<ChatLink | null>(null)
  const [nudge, setNudge] = useState<Nudge | null>(null)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  const anchor = useRef<HTMLDivElement>(null)
  const started = useRef(false)
  const counted = useRef(false) // chat_open goes once per page, so a visitor's story says they talked to us
  const asked = useRef<ChatContext | undefined>(undefined)
  // the newest reply with homes (it and its follow-up question are the last two messages): read from its first line, not from the bottom
  const anchorAt = msgs.findIndex((m, i) => i >= msgs.length - 2 && m.role === 'bot' && !!m.cards?.length)

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(LOG_KEY)
      if (saved) { setMsgs(JSON.parse(saved)); started.current = true }
    } catch { /* ignore */ }
  }, [])
  useEffect(() => {
    if (anchorAt >= 0) anchor.current?.scrollIntoView?.({ block: 'start' })
    else end.current?.scrollIntoView?.({ block: 'end' })
    try { if (msgs.length) window.localStorage.setItem(LOG_KEY, JSON.stringify(msgs.slice(-30))) } catch { /* ignore */ }
  }, [msgs, open, anchorAt])

  async function send(message: string) {
    const m = message.trim()
    if (!m || busy) return
    setBusy(true)
    setQuick([])
    setText('')
    setMsgs((x) => [...x, ...(m === 'hi' && !started.current ? [] : [{ role: 'you' as const, text: m }])])
    started.current = true
    if (!counted.current) {
      counted.current = true
      trackEvent('chat_open', agentSlug)
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId(), agent_slug: agentSlug, message: m, source: readAttribution().source, context: asked.current ?? chatContextFromPath(window.location.pathname), anon_id: getAnonId(), ...readVisitPages() }),
      })
      if (!res.ok) throw new Error(String(res.status))
      const data = parseChatReply(await res.json())
      const bot: Msg[] = [{ role: 'bot', text: data.reply, ...(data.cards.length ? { cards: data.cards } : {}) }]
      if (data.follow_up) bot.push({ role: 'bot', text: data.follow_up })
      setMsgs((x) => [...x, ...bot])
      setQuick(data.quick_replies)
      setWaUrl(data.whatsapp_url)
      setLink(data.link ?? null)
    } catch {
      setMsgs((x) => [...x, { role: 'bot', text: 'Sorry, I could not reach the team just now. Please try again in a moment.' }])
    } finally {
      setBusy(false)
    }
  }

  // a page's "Chat with us" button (OpenChatButton) opens the bubble with its question already asked
  useEffect(() => {
    function onAsk(e: Event) {
      const detail = (e as CustomEvent<{ message?: string; context?: ChatContext }>).detail
      const q = detail?.message || 'hi'
      if (detail?.context) asked.current = detail.context
      setOpen(true)
      started.current = true
      void send(q)
    }
    window.addEventListener(OPEN_CHAT_EVENT, onAsk)
    return () => window.removeEventListener(OPEN_CHAT_EVENT, onAsk)
  })

  // the visit in view, counted here; what to say, if anything, comes from the server, from what they read (chat/nudge.py)
  useEffect(() => {
    if (open || nudge) return
    const timer = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return
      const seconds = addSeconds(TICK_SECONDS)
      const path = window.location.pathname
      const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName ?? '')
      if (!askNow(seconds) || typing || !nudgeAllowed(path) || isMuted(Date.now())) return
      void fetch(`${API_BASE_URL}/api/v1/chat/nudge`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId(), agent_slug: agentSlug, seconds, context: chatContextFromPath(path), anon_id: getAnonId(), ...readVisitPages() }),
      }).then((r) => (r.ok ? r.json() : null)).then((d) => setNudge(parseNudge(d))).catch(() => { /* a note is a help, never a reason to complain */ })
    }, TICK_SECONDS * 1000)
    return () => window.clearInterval(timer)
  }, [agentSlug, open, nudge])

  /** They answered the note: it becomes the chat's first message, then their tap (if any) is sent like any quick reply. */
  function openNudge(n: Nudge, tapped?: string) {
    setNudge(null)
    setOpen(true)
    started.current = true
    setMsgs((x) => [...x, { role: 'bot', text: n.text }])
    setQuick(n.quick_replies)
    setLink(n.link)
    if (tapped) void send(tapped)
  }

  function dismissNudge() {
    setNudge(null)
    mute(Date.now())
  }

  function toggle() {
    const next = !open
    setOpen(next)
    if (next && msgs.length === 0) void send('hi')
  }

  return (
    <div className={'fixed right-3 z-40 sm:right-4 ' + (bottomBar ? CHAT_BOTTOM.withBar : CHAT_BOTTOM.withoutBar)} data-testid="chat-widget">
      {open && (
        <section aria-label={`Chat with ${BRAND_NAME}`} className="mb-3 flex h-[78vh] max-h-[640px] w-[min(92vw,380px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <header className="flex items-center justify-between bg-[var(--site-primary,#102340)] px-4 py-3 text-white">
            <div>
              <p className="font-semibold">{BRAND_NAME}</p>
              <p className="text-xs text-[var(--site-accent,#f0b440)]">Ask us anything about homes in Pune</p>
              <div role="group" aria-label="Choose a language" className="mt-1 flex gap-1">
                {LANGUAGES.map((l) => (
                  <button key={l} type="button" onClick={() => send(l)} disabled={busy}
                    className="min-h-[28px] rounded-full border border-white/40 px-2 text-xs text-white hover:bg-white/10">{l}</button>
                ))}
              </div>
            </div>
            <button type="button" onClick={toggle} aria-label="Close chat" className="flex h-11 w-11 items-center justify-center text-2xl text-white">×</button>
          </header>
          <div className="flex-1 space-y-2 overflow-y-auto bg-slate-50 p-3" role="log" aria-live="polite">
            {msgs.map((m, i) => (
              <div key={i} ref={i === anchorAt ? anchor : undefined} className={m.role === 'you' ? 'flex justify-end' : 'flex scroll-mt-2 flex-col items-start gap-2'}>
                <p className={'max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-[15px] leading-snug ' + (m.role === 'you' ? 'bg-[#102340] text-white' : 'bg-white text-slate-900 shadow-sm')}>{m.text}</p>
                {m.cards && m.cards.length > 0 && (
                  <ul aria-label="Matching homes" className="w-full max-w-[92%] space-y-2">
                    {m.cards.map((c) => <ChatHomeCard key={c.id} card={c} />)}
                  </ul>
                )}
              </div>
            ))}
            {busy && <p className="text-sm text-slate-500" aria-label="typing">…</p>}
            <div ref={end} />
          </div>
          {(quick.length > 0 || link) && (
            <div className="flex gap-2 overflow-x-auto border-t border-slate-100 bg-white px-3 py-2 [scrollbar-width:none]" role="group" aria-label="Quick replies">
              {link && (
                <a href={link.url} data-testid="chat-link"
                  className="inline-flex min-h-[40px] shrink-0 items-center whitespace-nowrap rounded-full bg-[#f0b440] px-3 text-sm font-bold text-[#18202c] no-underline">{link.label}</a>
              )}
              {quick.map((q) => q === WHATSAPP_QUICK ? (
                waUrl && (
                  <a key={q} href={waUrl} target="_blank" rel="noopener noreferrer"
                    className="inline-flex min-h-[40px] shrink-0 items-center whitespace-nowrap rounded-full bg-[#1f7a4d] px-3 text-sm font-semibold text-white no-underline">{q}</a>
                )
              ) : (
                <button key={q} type="button" onClick={() => send(q)} className="min-h-[40px] shrink-0 whitespace-nowrap rounded-full border border-[#102340] px-3 text-sm font-semibold text-[#102340]">{q}</button>
              ))}
            </div>
          )}
          <form onSubmit={(e) => { e.preventDefault(); void send(text) }} className="flex gap-2 border-t border-slate-200 bg-white p-2">
            <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} aria-label="Your message" placeholder="Type your message"
              className="min-h-[44px] flex-1 rounded-full border border-slate-300 px-4 text-[15px]" />
            <button type="submit" disabled={busy || !text.trim()} className="min-h-[44px] rounded-full bg-[#f0b440] px-4 font-bold text-[#18202c] disabled:opacity-50">Send</button>
          </form>
        </section>
      )}
      {!open && nudge && (
        <aside aria-label={`Message from ${BRAND_NAME}`} data-testid="chat-nudge"
          className="relative mb-2 ml-auto w-[min(84vw,300px)] rounded-2xl border border-slate-200 bg-white p-3 pr-9 shadow-xl">
          <button type="button" onClick={dismissNudge} aria-label="Dismiss message"
            className="absolute right-0 top-0 flex h-10 w-10 items-center justify-center text-xl text-slate-500">×</button>
          <button type="button" onClick={() => openNudge(nudge)} className="block text-left text-[14px] leading-snug text-slate-900">{nudge.text}</button>
          {(nudge.quick_replies.length > 0 || nudge.link) && (
            <div className="mt-2 flex flex-wrap gap-2">
              {nudge.quick_replies.map((q) => (
                <button key={q} type="button" onClick={() => openNudge(nudge, q)}
                  className="min-h-[36px] rounded-full bg-[#102340] px-3 text-[13px] font-semibold text-white">{q}</button>
              ))}
              {nudge.link && (
                <a href={nudge.link.url} className="inline-flex min-h-[36px] items-center rounded-full border border-[#102340] px-3 text-[13px] font-semibold text-[#102340] no-underline">{nudge.link.label}</a>
              )}
            </div>
          )}
        </aside>
      )}
      {!open && (
        <button type="button" onClick={toggle} aria-label="Chat with us" data-testid="chat-open"
          className="flex h-12 w-12 items-center justify-center rounded-full bg-[#102340] font-bold text-white shadow-xl ring-2 ring-white/80 focus:outline-none focus-visible:ring-[#f0b440] sm:h-auto sm:min-h-[52px] sm:w-auto sm:gap-2 sm:px-5">
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z" />
          </svg>
          <span aria-hidden="true" className="hidden sm:inline">Chat with us</span>
        </button>
      )}
    </div>
  )
}
