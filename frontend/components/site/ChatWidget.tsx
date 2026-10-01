'use client'
import React, { useEffect, useRef, useState } from 'react'
import { API_BASE_URL } from '@/lib/config/api'
import { readAttribution } from '@/lib/site/tracking'
import { chatContextFromPath } from '@/lib/site/chatContext'
import { cardFacts, parseChatReply, WHATSAPP_QUICK, type ChatCard } from '@/lib/site/chatApi'
import { BRAND_NAME } from '@/lib/brand'

interface Msg { role: 'bot' | 'you'; text: string; cards?: ChatCard[] }
const SID_KEY = 'pp_chat_sid'
const LOG_KEY = 'pp_chat_log'

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
          <span className="mt-1">
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

/**
 * Floating "Chat with us" for public pages. Answers basic questions, shows matching homes as cards, and, step by step, collects the visitor's
 * requirement and (with consent) a phone number. All logic is on the server; this component only shows the conversation.
 * `agentSlug` decides whose inbox a lead lands in.
 */
export default function ChatWidget({ agentSlug }: { agentSlug: string }) {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [quick, setQuick] = useState<string[]>([])
  const [waUrl, setWaUrl] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  const anchor = useRef<HTMLDivElement>(null)
  const started = useRef(false)
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
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId(), agent_slug: agentSlug, message: m, source: readAttribution().source || 'chat', context: chatContextFromPath(window.location.pathname) }),
      })
      if (!res.ok) throw new Error(String(res.status))
      const data = parseChatReply(await res.json())
      const bot: Msg[] = [{ role: 'bot', text: data.reply, ...(data.cards.length ? { cards: data.cards } : {}) }]
      if (data.follow_up) bot.push({ role: 'bot', text: data.follow_up })
      setMsgs((x) => [...x, ...bot])
      setQuick(data.quick_replies)
      setWaUrl(data.whatsapp_url)
    } catch {
      setMsgs((x) => [...x, { role: 'bot', text: 'Sorry, I could not reach the team just now. Please try again in a moment.' }])
    } finally {
      setBusy(false)
    }
  }

  function toggle() {
    const next = !open
    setOpen(next)
    if (next && msgs.length === 0) void send('hi')
  }

  return (
    <div className="fixed bottom-20 right-4 z-40 md:bottom-6" data-testid="chat-widget">
      {open && (
        <section aria-label={`Chat with ${BRAND_NAME}`} className="mb-3 flex h-[78vh] max-h-[640px] w-[min(92vw,380px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <header className="flex items-center justify-between bg-[var(--site-primary,#102340)] px-4 py-3 text-white">
            <div>
              <p className="font-semibold">{BRAND_NAME}</p>
              <p className="text-xs text-[var(--site-accent,#f0b440)]">Ask us anything about homes in Pune</p>
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
          {quick.length > 0 && (
            <div className="flex gap-2 overflow-x-auto border-t border-slate-100 bg-white px-3 py-2 [scrollbar-width:none]" role="group" aria-label="Quick replies">
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
      {!open && (
        <button type="button" onClick={toggle} className="flex min-h-[52px] items-center gap-2 rounded-full bg-[#102340] px-5 font-bold text-white shadow-xl">
          <span aria-hidden>💬</span> Chat with us
        </button>
      )}
    </div>
  )
}
