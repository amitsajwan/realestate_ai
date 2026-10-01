'use client'
import React, { useEffect, useRef, useState } from 'react'
import { API_BASE_URL } from '@/lib/config/api'
import { readAttribution } from '@/lib/site/tracking'
import { chatContextFromPath } from '@/lib/site/chatContext'

interface Msg { role: 'bot' | 'you'; text: string }
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

/**
 * Floating "Chat with us" for public pages. Answers basic questions and, step by step, collects the visitor's requirement and (with consent) a phone
 * number. All logic is on the server; this component only shows the conversation. `agentSlug` decides whose inbox a lead lands in.
 */
export default function ChatWidget({ agentSlug }: { agentSlug: string }) {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [quick, setQuick] = useState<string[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  const started = useRef(false)

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(LOG_KEY)
      if (saved) { setMsgs(JSON.parse(saved)); started.current = true }
    } catch { /* ignore */ }
  }, [])
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: 'end' })
    try { if (msgs.length) window.localStorage.setItem(LOG_KEY, JSON.stringify(msgs.slice(-30))) } catch { /* ignore */ }
  }, [msgs, open])

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
      const data = (await res.json()) as { reply: string; quick_replies: string[] }
      setMsgs((x) => [...x, { role: 'bot', text: data.reply }])
      setQuick(data.quick_replies || [])
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
        <section aria-label="Chat with PUNE Property" className="mb-3 flex h-[70vh] max-h-[560px] w-[min(92vw,380px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <header className="flex items-center justify-between bg-[var(--site-primary,#102340)] px-4 py-3 text-white">
            <div>
              <p className="font-semibold">PUNE Property</p>
              <p className="text-xs text-[var(--site-accent,#f0b440)]">Ask us anything about buying in Pune</p>
            </div>
            <button type="button" onClick={toggle} aria-label="Close chat" className="flex h-11 w-11 items-center justify-center text-2xl text-white">×</button>
          </header>
          <div className="flex-1 space-y-2 overflow-y-auto bg-slate-50 p-3" role="log" aria-live="polite">
            {msgs.map((m, i) => (
              <div key={i} className={m.role === 'you' ? 'flex justify-end' : 'flex justify-start'}>
                <p className={'max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-[15px] leading-snug ' + (m.role === 'you' ? 'bg-[#102340] text-white' : 'bg-white text-slate-900 shadow-sm')}>{m.text}</p>
              </div>
            ))}
            {busy && <p className="text-sm text-slate-500" aria-label="typing">…</p>}
            <div ref={end} />
          </div>
          {quick.length > 0 && (
            <div className="flex flex-wrap gap-2 border-t border-slate-100 bg-white px-3 py-2">
              {quick.map((q) => (
                <button key={q} type="button" onClick={() => send(q)} className="min-h-[40px] rounded-full border border-[#102340] px-3 text-sm font-semibold text-[#102340]">{q}</button>
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
