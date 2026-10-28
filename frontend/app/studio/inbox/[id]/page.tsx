'use client'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import React from 'react'
import { Bubble } from '@/components/app/ChatBubble'
import { Btn, ErrorBox, PageTitle, Spinner, inputCls } from '@/components/app/ui'
import { errorMessage } from '@/lib/app/client'
import { BRAND_NAME } from '@/lib/brand'
import { timeAgo } from '@/lib/app/format'
import { PassBox, PassedNote } from '@/components/app/PassBox'
import { CHANNEL_CHIP, CHANNEL_LABEL, QUICK_REPLIES, inboxApi, isComment, type InboxThreadFull, type PassResult } from '@/lib/app/inbox'

/** One conversation in full, oldest first, with a reply box for WhatsApp while the 24-hour window is open. */
export default function InboxThreadPage() {
  const { id } = useParams<{ id: string }>()
  const [doc, setDoc] = React.useState<InboxThreadFull | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const [text, setText] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [passed, setPassed] = React.useState<PassResult | null>(null)  // keeps the WhatsApp link on screen after the reload
  const end = React.useRef<HTMLDivElement>(null)

  const load = React.useCallback(() => {
    setError(null)
    inboxApi.thread(id).then(setDoc).catch((e) => setError(errorMessage(e)))
  }, [id])
  React.useEffect(load, [load])
  // braces: Chrome's scrollIntoView now returns a Promise, and an effect that returns one crashes the page on leaving it
  // ('destroy is not a function': every Inbox link from a conversation showed the error page)
  React.useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [doc?.thread.length])

  async function markDone() {
    setBusy(true)
    setError(null)
    try {
      setDoc(await inboxApi.done(id))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function send() {
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      setDoc(await inboxApi.reply(id, text.trim()))
      setText('')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function followUp() {
    if (!doc?.lead_id) return
    setBusy(true)
    setError(null)
    try {
      await inboxApi.startWithLead(doc.lead_id)
      setDoc(await inboxApi.thread(id))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (error && !doc) return <ErrorBox message={error} onRetry={load} />
  if (!doc) return <Spinner />
  const name = doc.name || (doc.role === 'agent' ? 'Agent' : doc.channel === 'website' ? 'Website visitor' : 'Buyer')
  return (
    <div className="space-y-4">
      <Link href="/studio/inbox" className="inline-flex min-h-[44px] items-center font-semibold text-blue-700">&lsaquo; Inbox</Link>
      <PageTitle>{name}</PageTitle>
      <div className="flex flex-wrap items-center gap-1.5 text-sm">
        <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (CHANNEL_CHIP[doc.channel] ?? CHANNEL_CHIP.website)}>{CHANNEL_LABEL[doc.channel] ?? doc.channel}</span>
        <span className={'rounded-full px-2 py-0.5 text-xs font-semibold ' + (doc.role === 'agent' ? 'bg-sky-100 text-sky-800' : 'bg-orange-100 text-orange-800')}>{doc.role === 'agent' ? 'Agent' : 'Buyer'}</span>
        {doc.phone && <span className="text-gray-600">{doc.phone}</span>}
        {doc.lead_id && <Link href={`/studio/leads/${encodeURIComponent(doc.lead_id)}`} className="font-semibold text-blue-700 underline">Open lead</Link>}
      </div>
      {doc.summary && <p className="text-sm text-gray-700">Wants: {doc.summary}</p>}
      {doc.post_url && (
        <a href={doc.post_url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-[44px] items-center font-semibold text-blue-700 underline">
          Open the post on {doc.channel === 'instagram_comment' ? 'Instagram' : 'Facebook'}
        </a>
      )}
      {doc.passed === 'out' && <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">Passed to {doc.passed_to_name || 'an agent'}{doc.passed_at ? ` ${timeAgo(doc.passed_at)}` : ''}. They handle this buyer now.</p>}
      {doc.passed === 'in' && <p className="rounded-xl bg-sky-50 p-3 text-sm font-semibold text-sky-900">{BRAND_NAME} passed this buyer to you. Call or message them soon.</p>}
      {passed ? <PassedNote r={passed} /> : doc.can_pass && <PassBox leadId={doc.lead_id} threadId={id} onPassed={(r) => { setPassed(r); load() }} />}

      <ol className="space-y-2" aria-label="Messages">{doc.thread.map((m, i) => <Bubble key={i} m={m} />)}</ol>
      <div ref={end} />

      {isComment(doc.channel) ? (
        doc.needs_you ? (
          <section aria-label="Needs you" className="space-y-2 rounded-2xl border border-amber-300 bg-amber-50 p-3">
            <p className="text-sm font-semibold text-amber-900">Needs you: {doc.reason || 'please answer this one'}</p>
            <p className="text-sm text-amber-900">Answer under the post on {doc.channel === 'instagram_comment' ? 'Instagram' : 'Facebook'}, then tap Done.</p>
            {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
            <Btn disabled={busy} onClick={markDone}>{busy ? 'Saving...' : 'Done'}</Btn>
          </section>
        ) : (
          <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">Comments are answered by the bot. To add something, reply under the post itself.</p>
        )
      ) : doc.opted_out ? (
        <p className="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-800">They replied STOP. Do not message them on WhatsApp.</p>
      ) : doc.can_reply ? (
        <section aria-label="Reply" className="space-y-2 rounded-2xl border border-gray-200 bg-white p-3">
          <label htmlFor="inbox-reply" className="text-sm font-semibold text-gray-800">Reply on WhatsApp</label>
          <div className="-mx-1 overflow-x-auto [scrollbar-width:none]" role="group" aria-label="Quick replies">
            <div className="gap-2 px-1 [display:flex]">
              {QUICK_REPLIES.map((q) => (
                <button key={q} type="button" onClick={() => setText(q)}
                  className="min-h-[40px] max-w-[16rem] flex-none truncate rounded-full border border-gray-300 bg-white px-3 text-sm text-gray-800 active:bg-gray-100">
                  {q}
                </button>
              ))}
            </div>
          </div>
          <textarea id="inbox-reply" rows={4} maxLength={1000} className={inputCls} value={text} onChange={(e) => setText(e.target.value)} placeholder="Write your message" />
          {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
          <Btn disabled={busy || !text.trim()} onClick={send}>{busy ? 'Sending...' : 'Send'}</Btn>
          <p className="text-xs text-gray-500">{doc.bot_paused_until ? 'The bot is quiet in this chat while you handle it.' : 'After you reply, the bot stays quiet in this chat for 12 hours.'}</p>
        </section>
      ) : doc.channel === 'whatsapp' ? (
        <section aria-label="Follow-up" className="space-y-2 rounded-2xl border border-gray-200 bg-gray-50 p-3">
          <p className="text-sm text-gray-700">
            {doc.follow_up_sent_at
              ? `Follow-up message sent ${timeAgo(doc.follow_up_sent_at)}. You can write freely once they reply.`
              : 'They have not written in the last 24 hours, so WhatsApp allows only our approved follow-up message.'}
          </p>
          {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
          {doc.lead_id && !(doc.follow_up_sent_at && Date.now() - Date.parse(doc.follow_up_sent_at) < 24 * 3600 * 1000) && (
            <Btn disabled={busy} onClick={followUp}>{busy ? 'Sending...' : 'Send the follow-up message'}</Btn>
          )}
        </section>
      ) : (
        <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-700">{doc.channel === 'website' ? 'Website chats are answered by the bot. If they leave a number, it is in Leads.' : 'Reply to this one from the Facebook or Instagram inbox.'}</p>
      )}
    </div>
  )
}
