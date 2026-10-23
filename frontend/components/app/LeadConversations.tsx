'use client'
import Link from 'next/link'
import React from 'react'
import { Bubble } from '@/components/app/ChatBubble'
import { timeAgo } from '@/lib/app/format'
import { CHANNEL_CHIP, CHANNEL_LABEL, type InboxThreadFull } from '@/lib/app/inbox'

const SHOWN = 6

/** The server sends naive UTC: read it as UTC. */
const utc = (iso: string) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z')
const clock = (d: Date, day = false) => d.toLocaleString('en-IN', { ...(day ? { weekday: 'short' as const } : {}), hour: 'numeric', minute: '2-digit' })

/** When the free-reply window closes: 24 hours after their last message (WhatsApp only). */
function windowUntil(t: InboxThreadFull): string | null {
  const last = [...t.thread].reverse().find((m) => m.from === 'them' && m.at)
  return last?.at ? clock(new Date(utc(last.at).getTime() + 24 * 3600 * 1000), true) : null
}

/**
 * The lead page's "what was said": every chat with this person (WhatsApp, Messenger/Instagram, website chat), last messages of each,
 * whether the bot is holding back, and how long we can still write on WhatsApp for free. Replying happens in the Inbox thread.
 */
export function LeadConversations({ threads }: { threads: InboxThreadFull[] }) {
  const [all, setAll] = React.useState(false)
  return (
    <section aria-label="Messages" className="space-y-3">
      <h2 className="font-semibold">Messages</h2>
      {threads.length === 0 && (
        <p className="rounded-xl bg-white p-3 text-sm text-gray-600">No messages with them yet. Call them, or send the WhatsApp follow-up from Avasetu.</p>
      )}
      {threads.map((t) => {
        const msgs = all ? t.thread : t.thread.slice(-SHOWN)
        const until = t.channel === 'whatsapp' && t.window_open ? windowUntil(t) : null
        return (
          <div key={t.id} className="space-y-2 rounded-2xl border border-gray-200 bg-gray-50 p-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (CHANNEL_CHIP[t.channel] ?? CHANNEL_CHIP.website)}>{CHANNEL_LABEL[t.channel] ?? t.channel}</span>
              {t.needs_you && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">Waiting for you</span>}
              {t.bot_paused_until && <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-semibold text-gray-800">Bot paused until {clock(utc(t.bot_paused_until))}</span>}
              {t.opted_out && <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">Said STOP</span>}
            </div>
            {t.thread.length > msgs.length && (
              <button type="button" onClick={() => setAll(true)} className="text-sm font-semibold text-blue-700 underline">Show all {t.thread.length} messages</button>
            )}
            <ol className="space-y-2">{msgs.map((m, i) => <Bubble key={i} m={m} />)}</ol>
            {t.channel === 'whatsapp' && (
              <p className="text-xs text-gray-600">
                {t.opted_out ? 'Do not message them on WhatsApp.'
                  : until ? `You can write freely until ${until}.`
                    : t.follow_up_sent_at ? `Follow-up sent ${timeAgo(t.follow_up_sent_at)}. You can write freely once they reply.`
                      : 'More than 24 hours since they wrote: only the approved follow-up message can go out.'}
              </p>
            )}
            <Link href={`/studio/inbox/${encodeURIComponent(t.id)}`}
              className="flex min-h-[44px] items-center justify-center rounded-xl border border-gray-300 bg-white text-sm font-semibold text-[#0f2340]">
              {t.can_reply ? 'Reply in this chat' : 'Open this chat'}
            </Link>
          </div>
        )
      })}
    </section>
  )
}
